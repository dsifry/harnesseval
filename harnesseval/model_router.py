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
                     execution_mode: str = "api") -> tuple[str, int, int]:
    """Call any supported model. Returns (text, input_tokens, output_tokens).

    execution_mode: "api" (paid, clean token counts, concurrent) | "cli" (OAuth, free,
      ~15k scaffolding tax, serial). Per SPEC §7, record mode with every measurement and
      never compare api vs cli numbers head-to-head. The REVIEWER arm may use cli (free);
      the JUDGE arm must use api (calibrated trio + no scaffolding tax on judge calls).
    """
    if execution_mode == "cli":
        return await _call_cli(model, system, user, effort)
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


async def _call_cli(model: str, system: str, user: str, effort: str) -> tuple[str, int, int]:
    """Dispatch to claude/codex OAuth CLI. Returns (text, in, out). GLM/Kimi have no CLI -> fall back to API."""
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
        return text, usage.get("total_tokens",0)-usage.get("output_tokens",0), usage.get("output_tokens",0)
    slug = None
    for mid, sl in _CODEX_SLUGS.items():
        if ml == mid.lower(): slug = sl; break
    if slug or "gpt" in ml:
        slug = slug or "gpt-5.6-sol"
        text, usage, _ = await _codex_cli(slug, effort, user, system=system)
        return text, usage.get("total_tokens",0)-usage.get("output_tokens",0), usage.get("output_tokens",0)
    # GLM/Kimi: no OAuth CLI; fall back to API (Lunaroute, flat-fee)
    return await _call_openai_compat(model, system, user, effort, 2048, 0.0)


async def _call_anthropic(model, system, user, effort, max_tokens, temperature) -> tuple[str, int, int]:
    client = keys.anthropic_client()
    body = anthropic_effort_body(effort, max_tokens=max_tokens)
    thinking_enabled = body.get("thinking", {}).get("type") == "enabled"
    mt = max_tokens + (body.get("thinking", {}).get("budget_tokens", 0) if body else 0)
    extra = {"thinking": body["thinking"]} if body else {}
    if not thinking_enabled:
        extra["temperature"] = temperature
    resp = await asyncio.to_thread(
        client.messages.create, model=model, max_tokens=mt, system=system,
        messages=[{"role": "user", "content": user}], extra_body=extra,
    )
    return text_content(resp), resp.usage.input_tokens, resp.usage.output_tokens


async def _call_openai_compat(model, system, user, effort, max_tokens, temperature) -> tuple[str, int, int]:
    # Lunaroute (glm/kimi) or native OpenAI (gpt) — both OpenAI-compat
    if "glm" in model.lower() or "kimi" in model.lower():
        client = keys.lunaroute_client()
    else:
        client = keys.openai_client()
    kwargs = openai_effort_kwargs(effort, model=model)
    # OpenAI reasoning models need max_completion_tokens, not max_tokens
    call_kwargs = dict(model=model, messages=[{"role": "system", "content": system},
                                              {"role": "user", "content": user}],
                       max_completion_tokens=max_tokens, temperature=temperature if not kwargs else 1)
    call_kwargs.update(kwargs)
    resp = await asyncio.to_thread(client.chat.completions.create, **call_kwargs)
    text = resp.choices[0].message.content or ""
    u = resp.usage
    return text, u.prompt_tokens, u.completion_tokens


async def call_model_json(model: str, system: str, user: str, *, effort: str = "medium",
                          max_tokens: int = 1024, execution_mode: str = "api") -> tuple[dict, int, int]:
    """Call any model and parse JSON output. Returns (parsed, in_tokens, out_tokens)."""
    text, tin, tout = await call_model(model, system, user, effort=effort, max_tokens=max_tokens, execution_mode=execution_mode)
    try:
        parsed = json.loads(_strip_fences(text))
    except Exception:
        parsed = {}
    return parsed, tin, tout
