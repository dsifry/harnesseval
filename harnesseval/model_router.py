"""Provider-agnostic model client router.

Routes a model id to the right provider client + call signature, so adapters/reviewers can
treat any model uniformly. Handles:
  - Anthropic native (claude-*)  -> Anthropic client, messages.create, thinking for effort
  - OpenAI native (gpt-*)        -> OpenAI client, chat.completions, reasoning_effort
  - Lunaroute (glm-*/kimi-*)      -> OpenAI-compat client at LUNAROUTE_BASE_URL, reasoning_effort

Returns (text, input_tokens, output_tokens) per call. Keeps keys via harnesseval.keys
(HARNESS_-prefixed, no env pollution).
"""

from __future__ import annotations

import asyncio
import json

from harnesseval import keys
from harnesseval.effort import anthropic_effort_body, openai_effort_kwargs, is_anthropic, is_openai_compat
from harnesseval.anthropic_util import text_content


def _strip_fences(s: str) -> str:
    if s.startswith("```"):
        s = s.split("```")[1]
        if s.startswith("json"):
            s = s[4:]
    return s.strip()


async def call_model(model: str, system: str, user: str, *, effort: str = "medium",
                     max_tokens: int = 2048, temperature: float = 0.0,
                     execution_mode: str = "api") -> tuple[str, int, int, dict]:
    """Call any supported model. Returns (text, input_tokens, output_tokens, per_model_usage).

    `per_model_usage` is the apples-to-apples cost unit (usage.py, SPEC §10/gotcha #2): a
    {model_id: {input_tokens, cache_read_input_tokens, cache_creation_input_tokens, output_tokens,
    reasoning_output_tokens, total_tokens, cost_usd}} dict. For cli (OAuth) it carries the
    ~15k scaffolding tax in cache_creation/cache_read (NOT input_tokens); for api it is the
    single under-test model. Callers SHOULD store it on ReviewRun.per_model_usage.

    execution_mode: "api" (paid, clean token counts, concurrent) | "cli" (OAuth, free,
      ~15k scaffolding tax, serial). Per SPEC §7, record mode with every measurement and
      never compare api vs cli numbers head-to-head. The REVIEWER arm may use cli (free);
      the JUDGE arm must use api (calibrated trio + no scaffolding tax on judge calls).
    """
    from harnesseval.usage import grand_total
    if execution_mode == "cli":
        text, per_model = await _call_cli(model, system, user, effort)
        gt = grand_total(per_model)
        return text, gt["total_tokens"] - sum(u.get("output_tokens", 0) for u in per_model.values()), \
               sum(u.get("output_tokens", 0) for u in per_model.values()), per_model
    if is_anthropic(model):
        return await _call_anthropic(model, system, user, effort, max_tokens, temperature)
    elif is_openai_compat(model):
        return await _call_openai_compat(model, system, user, effort, max_tokens, temperature)
    raise ValueError(f"unknown model provider for: {model}")


# model id -> (host, alias/slug) for CLI execution
_CLAUDE_ALIASES = {
    "claude-opus-4-5-20251101": "opus", "claude-opus-4-8": "opus", "claude-opus-5": "opus",
    "claude-fable-5": "fable", "claude-sonnet-4-5-20250929": "sonnet", "claude-sonnet-5": "sonnet",
}
_CODEX_SLUGS = {
    # map API model ids -> valid Codex CLI slugs. gpt-5.2 is API-only (not a Codex slug);
    # a user running `codex` uses the current default. Map to gpt-5.6-sol for realistic CLI.
    "gpt-5.2": "gpt-5.6-sol", "gpt-5.6-sol": "gpt-5.6-sol", "gpt-5.6-terra": "gpt-5.6-terra", "gpt-5": "gpt-5.6-sol",
}


async def _call_cli(model: str, system: str, user: str, effort: str) -> tuple[str, dict]:
    """Dispatch to claude/codex OAuth CLI. Returns (text, per_model_usage). GLM/Kimi have no CLI -> fall back to API."""
    from harnesseval.cli_backends import _claude_cli, _codex_cli
    ml = model.lower()
    # map full ids to aliases/slugs
    alias = None
    for mid, al in _CLAUDE_ALIASES.items():
        if ml == mid.lower() or ml.startswith(al) and "claude" in ml:
            alias = al; break
    if alias or "claude" in ml or "opus" in ml or "sonnet" in ml or "fable" in ml:
        # resolve alias
        if not alias:
            for al in ("opus", "sonnet", "fable", "haiku"):
                if al in ml: alias = al; break
        alias = alias or "sonnet"
        text, usage, _ = await _claude_cli(alias, effort, user, system=system)
        return text, usage  # usage is already the per-model dict from from_claude_cli
    slug = None
    for mid, sl in _CODEX_SLUGS.items():
        if ml == mid.lower(): slug = sl; break
    if slug or "gpt" in ml:
        slug = slug or "gpt-5.6-sol"
        text, usage, _ = await _codex_cli(slug, effort, user, system=system)
        return text, usage  # usage is already the per-model dict from from_codex_cli
    # GLM/Kimi: no OAuth CLI; fall back to API (Lunaroute, flat-fee). Capture the text properly
    # (the earlier `_, _, _, per_model` unpack discarded the text into `_` and returned `_` = per_model).
    text, _, _, per_model = await _call_openai_compat(model, system, user, effort, 2048, 0.0)
    return text, per_model


async def _call_anthropic(model, system, user, effort, max_tokens, temperature) -> tuple[str, int, int, dict]:
    from harnesseval.usage import from_anthropic_api, grand_total
    client = keys.anthropic_client()
    body = anthropic_effort_body(effort, max_tokens=max_tokens)
    thinking_enabled = body.get("thinking", {}).get("type") == "enabled"
    mt = max_tokens + (body.get("thinking", {}).get("budget_tokens", 0) if body else 0)
    extra = {"thinking": body["thinking"]} if body else {}
    if thinking_enabled:
        # thinking requires temperature=1 (gotcha #5)
        extra["temperature"] = 1
    else:
        # thinking disabled: older Anthropic models (opus-4.5/sonnet-4.5) accept temperature=0
        # for determinism, but newer models (opus-5+) reject it ("temperature is deprecated for
        # this model"). Only pass it for the calibrated older trio; let newer models use the API
        # default. Detect by snapshot id; the under-test set (opus-5, opus-4.8, fable, sonnet-5)
        # all reject temperature, the judge trio (opus-4.5, sonnet-4.5) accepts it.
        if any(old in model.lower() for old in ("opus-4-5", "sonnet-4-5")):
            extra["temperature"] = temperature
    resp = await asyncio.to_thread(
        client.messages.create, model=model, max_tokens=mt, system=system,
        messages=[{"role": "user", "content": user}], extra_body=extra,
    )
    per_model = from_anthropic_api(resp, model)
    gt = grand_total(per_model)
    return text_content(resp), gt["total_tokens"] - sum(u.get("output_tokens", 0) for u in per_model.values()), \
           sum(u.get("output_tokens", 0) for u in per_model.values()), per_model


async def _call_openai_compat(model, system, user, effort, max_tokens, temperature) -> tuple[str, int, int, dict]:
    from harnesseval.usage import from_openai_api, grand_total
    # Lunaroute (glm/kimi) or native OpenAI (gpt) — both OpenAI-compat
    is_lunaroute = "glm" in model.lower() or "kimi" in model.lower()
    if is_lunaroute:
        client = keys.lunaroute_client()
    else:
        client = keys.openai_client()
    kwargs = openai_effort_kwargs(effort, model=model)
    # OpenAI reasoning models need max_completion_tokens, not max_tokens.
    # Lunaroute GLM/Kimi (reasoning models) return EMPTY content (finish_reason=length,
    # message.content="") when max_completion_tokens is too low: they spend ~5k+ tokens on hidden
    # reasoning before emitting visible content, so a 1024/2048/4096/8192 cap is hit mid-reasoning
    # -> empty string. Verified 2026-08-23: GLM+Kimi both need 16384 to reach finish_reason=stop and
    # produce content on the real review prompts. Without this floor, every GLM/Kimi cell scored
    # 0.00 (review prose produced at 2048 but the extract step at 1024 returned empty -> 0 findings).
    # Enforce a 16384 floor for both Lunaroute reasoning models on every call (review + extract).
    if is_lunaroute:
        max_tokens = max(max_tokens, 16384)
    call_kwargs = dict(model=model, messages=[{"role": "system", "content": system},
                                              {"role": "user", "content": user}],
                       max_completion_tokens=max_tokens, temperature=temperature if not kwargs else 1)
    call_kwargs.update(kwargs)
    resp = await asyncio.to_thread(client.chat.completions.create, **call_kwargs)
    text = resp.choices[0].message.content or ""
    # Lunaroute GLM/Kimi can non-deterministically return empty content even at the 16384 floor
    # (reasoning finished but content not emitted, or a transient finish=length). Retry once —
    # empty content means 0 findings downstream, so the retry is cheap insurance. Native OpenAI
    # (gpt) doesn't hit this (separately-budgeted reasoning), so retry only for Lunaroute.
    if is_lunaroute and not text.strip():
        resp = await asyncio.to_thread(client.chat.completions.create, **call_kwargs)
        text = resp.choices[0].message.content or ""
    per_model = from_openai_api(resp, model)
    gt = grand_total(per_model)
    return text, gt["total_tokens"] - sum(u.get("output_tokens", 0) for u in per_model.values()), \
           sum(u.get("output_tokens", 0) for u in per_model.values()), per_model


async def call_model_json(model: str, system: str, user: str, *, effort: str = "medium",
                          max_tokens: int = 1024, execution_mode: str = "api") -> tuple[dict, int, int, dict]:
    """Call any model and parse JSON output. Returns (parsed, in_tokens, out_tokens, per_model_usage).

    For Lunaroute reasoning models (GLM/Kimi), retry once if the first call returns empty content
    OR unparseable text — under concurrent load they intermittently emit empty/prose instead of
    JSON, which silently yields 0 findings downstream. The retry is cheap insurance against a
    0-recall cell. Native OpenAI/Anthropic don't hit this.
    """
    text, tin, tout, per_model = await call_model(model, system, user, effort=effort, max_tokens=max_tokens, execution_mode=execution_mode)
    def _try_parse(t):
        try:
            return json.loads(_strip_fences(t))
        except Exception:
            return None
    parsed = _try_parse(text)
    is_lunaroute = "glm" in model.lower() or "kimi" in model.lower()
    if is_lunaroute and not parsed:
        # empty or unparseable under load -> retry once
        text2, tin2, tout2, per_model2 = await call_model(model, system, user, effort=effort, max_tokens=max_tokens, execution_mode=execution_mode)
        tin += tin2; tout += tout2
        from harnesseval.usage import merge
        per_model = merge(per_model, per_model2)
        parsed = _try_parse(text2) or {}
    return parsed or {}, tin, tout, per_model
