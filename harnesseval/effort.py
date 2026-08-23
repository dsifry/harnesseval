"""Effort abstraction — map our {low, medium, xhigh} effort cells to provider-native knobs.

Verified 2026-08-22 (docs/SPEC.md §6.1):
  - Anthropic (Opus 4.5 etc.): `thinking` config. `disabled` = no extended thinking;
    `enabled` with budget_tokens = extended thinking. `adaptive` NOT supported on Opus 4.5.
    -> low/medium -> disabled; xhigh -> enabled (budget proportional to max_tokens).
  - OpenAI (gpt-5.x): `reasoning_effort` {low, medium, high}. `minimal` unsupported on gpt-5.2.
    -> low -> low; medium -> medium; xhigh -> high.
  - Lunaroute (GLM/Kimi, OpenAI-compat): `reasoning_effort` per pi's thinkingLevelMap.

Returns the extra_body / kwarg to merge into the model call, or {} if the model doesn't
support an effort knob.
"""

from __future__ import annotations

EFFORT_LEVELS = ("low", "medium", "xhigh")


def anthropic_effort_body(effort: str, max_tokens: int) -> dict:
    """Anthropic thinking config for an effort level. Returns extra_body dict."""
    if effort in ("low", "medium"):
        return {"thinking": {"type": "disabled"}}
    if effort == "xhigh":
        # enabled thinking; budget must be >= 1024 and < max_tokens. Use ~40% of max_tokens, min 1024.
        budget = max(1024, int(max_tokens * 0.4))
        if budget >= max_tokens:
            budget = max(1024, max_tokens - 1024)  # keep >=1024 floor if room; else cap
        if budget >= max_tokens:  # max_tokens itself too small for thinking
            return {}  # can't enable thinking safely; fall back to default
        return {"thinking": {"type": "enabled", "budget_tokens": budget}}
    return {}  # unknown -> default (no knob)


def openai_effort_kwargs(effort: str, model: str = "") -> dict:
    """OpenAI reasoning_effort. Returns kwargs for chat.completions.create.

    Model-specific (per pi thinkingLevelMap, SPEC §6.1): Kimi has no 'medium' level
    (medium->high, xhigh->max) and rejects 'medium' with a 500. GLM accepts the ladder directly.
    """
    ml = (model or "").lower()
    if "kimi" in ml:
        mapping = {"low": "low", "medium": "high", "xhigh": "max"}  # kimi: no 'medium' level
    else:
        mapping = {"low": "low", "medium": "medium", "xhigh": "high"}  # gpt + glm
    val = mapping.get(effort)
    return {"reasoning_effort": val} if val else {}


def is_anthropic(model: str) -> bool:
    return "claude" in model.lower() or model.startswith("anthropic/")


def is_openai_compat(model: str) -> bool:
    return "gpt" in model.lower() or model.startswith("openai/") or "glm" in model.lower() or "kimi" in model.lower()
