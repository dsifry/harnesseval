"""Per-model usage accounting — the apples-to-apples unit for realistic (multi-model) runs.

A realistic run legitimately uses MULTIPLE models (e.g. opus orchestrator + haiku subagents
by default in Claude Code — that IS what vanilla does). We must count EACH model's tokens
separately, with the cached/uncached split (caching changes cost ~10x), plus costUSD per
model — NOT mash everything into one total.

This module normalizes usage from all sources into one shape:
  {model_id: {input_tokens, cache_read_input_tokens, cache_creation_input_tokens,
              output_tokens, reasoning_output_tokens, total_tokens, cost_usd}}

Sources:
  - claude -p: d["modelUsage"] (per-model, with cacheRead/cacheCreation/costUSD)
  - codex exec: turn.completed usage (single model; cached_input_tokens + reasoning_output_tokens)
  - Anthropic API: resp.usage (single model)
  - OpenAI/Lunaroute API: resp.usage (single model; reasoning tokens in completion_tokens_details)

Aggregated into a UsageReport with per-model totals + grand total tokens + total cost.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict


@dataclass
class ModelUsage:
    input_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_output_tokens: int = 0  # OpenAI reasoning / Anthropic thinking
    cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        # total billable-side tokens: input (incl. cache read/creation) + output (+ reasoning)
        return (self.input_tokens + self.cache_read_input_tokens +
                self.cache_creation_input_tokens + self.output_tokens +
                self.reasoning_output_tokens)


def from_claude_cli(d: dict) -> dict[str, dict]:
    """Parse claude -p modelUsage into {model: usage_dict}. Includes the cached split + costUSD."""
    out: dict[str, dict] = {}
    mu = d.get("modelUsage") or {}
    if not isinstance(mu, dict):
        return out
    for mid, m in mu.items():
        if not isinstance(m, dict):
            continue
        u = ModelUsage(
            input_tokens=int(m.get("inputTokens", 0)),
            cache_read_input_tokens=int(m.get("cacheReadInputTokens", 0)),
            cache_creation_input_tokens=int(m.get("cacheCreationInputTokens", 0)),
            output_tokens=int(m.get("outputTokens", 0)),
            cost_usd=float(m.get("costUSD", 0) or 0),
        )
        out[mid] = asdict(u)
        out[mid]["total_tokens"] = u.total_tokens
    # fallback: if no modelUsage, synthesize from top-level usage under a single 'unknown' model
    if not out:
        u = d.get("usage", {})
        m = ModelUsage(input_tokens=int(u.get("input_tokens", 0)),
                       cache_read_input_tokens=int(u.get("cache_read_input_tokens", 0)),
                       cache_creation_input_tokens=int(u.get("cache_creation_input_tokens", 0)),
                       output_tokens=int(u.get("output_tokens", 0)),
                       cost_usd=float(d.get("total_cost_usd", 0) or 0))
        out["unknown"] = asdict(m)
        out["unknown"]["total_tokens"] = m.total_tokens
    return out


def from_codex_cli(usage: dict, model_slug: str) -> dict[str, dict]:
    """Parse codex exec turn.completed usage into {model: usage_dict}."""
    u = ModelUsage(
        input_tokens=int(usage.get("input_tokens", 0)) - int(usage.get("cached_input_tokens", 0)),
        cache_read_input_tokens=int(usage.get("cached_input_tokens", 0)),
        output_tokens=int(usage.get("output_tokens", 0)),
        reasoning_output_tokens=int(usage.get("reasoning_output_tokens", 0)),
    )
    return {model_slug: asdict(u) | {"total_tokens": u.total_tokens}}


def from_anthropic_api(resp, model: str) -> dict[str, dict]:
    """Anthropic messages.create response -> {model: usage_dict}."""
    u = resp.usage
    mu = ModelUsage(
        input_tokens=int(getattr(u, "input_tokens", 0)),
        cache_read_input_tokens=int(getattr(u, "cache_read_input_tokens", 0)),
        cache_creation_input_tokens=int(getattr(u, "cache_creation_input_tokens", 0)),
        output_tokens=int(getattr(u, "output_tokens", 0)),
    )
    return {model: asdict(mu) | {"total_tokens": mu.total_tokens}}


def from_openai_api(resp, model: str) -> dict[str, dict]:
    """OpenAI/Lunaroute chat.completions response -> {model: usage_dict}."""
    u = resp.usage
    rt = getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", 0) or 0
    mu = ModelUsage(input_tokens=int(getattr(u, "prompt_tokens", 0)),
                    output_tokens=int(getattr(u, "completion_tokens", 0)) - int(rt),
                    reasoning_output_tokens=int(rt))
    return {model: asdict(mu) | {"total_tokens": mu.total_tokens}}


def merge(into: dict[str, dict], other: dict[str, dict]) -> dict[str, dict]:
    """Merge per-model usage dicts (sum each model's fields). Returns into (mutated)."""
    for mid, u in other.items():
        if mid not in into:
            into[mid] = {k: 0 for k in ("input_tokens", "cache_read_input_tokens",
                                        "cache_creation_input_tokens", "output_tokens",
                                        "reasoning_output_tokens", "cost_usd", "total_tokens")}
        for k, v in u.items():
            if k == "total_tokens":
                into[mid][k] = (into[mid].get(k, 0) + v)
            elif isinstance(v, (int, float)):
                into[mid][k] = into[mid].get(k, 0) + v
    # recompute totals
    for mid, u in into.items():
        u["total_tokens"] = (u["input_tokens"] + u["cache_read_input_tokens"] +
                            u["cache_creation_input_tokens"] + u["output_tokens"] +
                            u["reasoning_output_tokens"])
    return into


def grand_total(per_model: dict[str, dict]) -> dict:
    """Sum across all models. Returns {total_tokens, total_cost_usd, n_models}."""
    return {
        "total_tokens": sum(u.get("total_tokens", 0) for u in per_model.values()),
        "total_cost_usd": sum(u.get("cost_usd", 0) for u in per_model.values()),
        "n_models": len(per_model),
        "models": list(per_model.keys()),
    }
