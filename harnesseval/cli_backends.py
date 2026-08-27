"""OAuth CLI backends — run the reviewer layer for free via Claude Code / Codex subscriptions.

Per docs/SPEC.md §7: Phase B (build/tune) and the full matrix can run the REVIEWER arm via
OAuth CLI (free) instead of API (paid). The JUDGE layer stays on API (the calibrated trio;
CLI-judge would break calibration fidelity + add the ~15k scaffolding tax to every judge call).

Token accounting: both CLIs report usage in their JSON output (incl. thinking/reasoning tokens),
so cost is measurable even when $=0 (subscription). Record execution_mode="cli" with every
measurement; never compare CLI vs API numbers head-to-head (SPEC §7 honesty rule — CLI carries
the ~15k host-scaffolding tax, API does not).

Effort: Claude `--effort {medium,xhigh}`; Codex `-c model_reasoning_effort=...`. Map our
{low,medium,xhigh} per SPEC §6.1.

NOTE: model aliases (opus/sonnet) drift — we record the resolved model id from the response.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import time
from pathlib import Path


def _parse_claude_effort(effort: str) -> str:
    # Claude --effort: low, medium, high, xhigh, max. xhigh is our "Extra High".
    return {"low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh"}.get(effort, "medium")


def _parse_codex_effort(effort: str) -> str:
    # Codex model_reasoning_effort: low, medium, high, xhigh, max, ultra
    return {"low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh"}.get(effort, "medium")


def codex_slug_for(model: str) -> str:
    """Map a model-under-test to a valid Codex CLI slug.

    gpt-5.6-* variants (gpt-5.6-sol, gpt-5.6-terra) are valid Codex CLI slugs — pass through.
    gpt-5.2 / gpt-5 are API-only (not valid Codex slugs) — fall back to gpt-5.6-sol.
    """
    ml = model.lower()
    if ml.startswith("gpt-5.6"):
        return ml
    return "gpt-5.6-sol"


def session_timeout(effort: str, base: int = 900) -> int:
    """Scale a host-session subprocess timeout by effort.

    Realistic adapters drive multi-turn agent sessions with subagent fanout (one subagent per
    lens/persona + synthesis). xhigh reasoning makes each turn much slower than medium, so a
    fixed 900s ceiling kills xhigh cells (the stopped matrix's codex xhigh timed out at 300s;
    opus xhigh took 514s). xhigh gets 2x the base; high gets 1.5x; low/medium keep the base.
    """
    if effort == "xhigh": return base * 2
    if effort == "high":  return int(base * 1.5)
    return base


def is_transient_claude_error(returncode: int, stdout: str, stderr: str) -> bool:
    """Detect a transient Claude API error surfaced by `claude -p`.

    `claude -p` handles transient API errors (529 Overloaded, 500, rate limits) inconsistently:
    sometimes it exits non-zero with the error in stderr; sometimes it exits 0 but writes the
    error as the `result` string (e.g. result="API Error: 529 Overloaded. This is a server-side
    issue..."). The latter is the silent failure mode: the adapter sees returncode 0, treats the
    error string as the review output, and extracts 0 findings — so a transient overload looks
    like a 0-recall cell. xhigh cells are more exposed (longer sessions, more reasoning, wider
    overload window). Both modes are transient (a retry usually succeeds), so callers should
    retry the session when this returns True. NOT a timeout, NOT a token overflow, NOT the
    adapter logic.
    """
    if returncode != 0:
        # non-zero exit: overload/rate-limit if stderr mentions it; anything else is a real bug.
        # An EMPTY stderr with non-zero exit is also treated as transient — `claude -p` sometimes
        # dies on a quota spike / connection drop with no stderr output; a retry usually succeeds.
        s = (stderr or "").lower()
        if not s:
            return True  # empty-stderr non-zero exit: likely transient (quota/drop), retry
        return any(k in s for k in ("overload", "529", "rate", "503", "server-side", "temporarily"))
    # returncode 0 but the result string IS an API error (the silent mode). claude -p puts it
    # in the JSON "result" field; check both the raw stdout (cheap) and a parsed result.
    r = (stdout or "").strip()
    if not r:
        return False
    if r.startswith("API Error: 5"):
        return True
    try:
        result = json.loads(r).get("result", "")
        return isinstance(result, str) and result.strip().startswith("API Error: 5")
    except Exception:
        return False


async def _claude_cli(model_alias: str, effort: str, prompt: str, system: str | None = None,
                     max_turns: int = 1, timeout: int = 900) -> tuple[str, dict, str]:
    """Run a review via `claude -p` OAuth. Returns (text, usage_dict, resolved_model).

    usage_dict has the FULL token accounting: input_tokens + cache_creation_input_tokens +
    cache_read_input_tokens + output_tokens. Callers MUST sum all four — the ~15k system-prompt+
    tool scaffolding tax (SPEC §7) lives in cache_creation/cache_read, NOT input_tokens (which is
    just the user's literal prompt, often ~2). Reporting only input+output undercounts ~4000x.

    IMPORTANT: ALWAYS pass a system prompt via --append-system-prompt. Without it, `claude -p`
    can silently fall back to Haiku for the work turn even when --model sonnet/opus is set.
    """
    args = ["claude", "-p", "--model", model_alias, "--effort", _parse_claude_effort(effort),
            "--output-format", "json", "--max-turns", str(max_turns)]
    args += ["--append-system-prompt", system or "You are an expert code reviewer."]
    args += [prompt]
    proc = await asyncio.to_thread(subprocess.run, args, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"claude -p failed: {proc.stderr.strip()[:300]}")
    d = json.loads(proc.stdout)
    u = d.get("usage", {})
    text = d.get("result", "")
    mu = d.get("modelUsage") or {}
    resolved = ",".join(mu.keys()) if isinstance(mu, dict) and mu else ""
    from harnesseval.usage import from_claude_cli
    return text, from_claude_cli(d), resolved


async def _codex_cli(model_slug: str, effort: str, prompt: str, system: str | None = None,
                    timeout: int = 900) -> tuple[str, dict, str]:
    """Run a review via `codex exec` OAuth. Returns (text, usage_dict, resolved_model).
    usage_dict: input_tokens + cached_input_tokens + output_tokens + reasoning_output_tokens.
    """
    args = ["codex", "exec", "--json", "--sandbox", "read-only", "--skip-git-repo-check",
            "-m", model_slug, "-c", f"model_reasoning_effort={_parse_codex_effort(effort)}"]
    # codex reads prompt from arg; use arg
    full = (f"{system}\n\n{prompt}" if system else prompt)
    args += [full]
    # IMPORTANT: codex exec reads from stdin if no prompt arg -> close stdin (pass input=None via DEVNULL)
    proc = await asyncio.to_thread(subprocess.run, args, capture_output=True, text=True,
                                   timeout=timeout, stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise RuntimeError(f"codex exec failed: {proc.stderr.strip()[:300]}")
    # parse JSONL: skip non-JSON lines (e.g. 'Reading additional input from stdin...'), last turn.completed has usage
    text = ""
    usage = {}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") == "item.completed" and d.get("item", {}).get("type") == "agent_message":
            text = d["item"].get("text", "")
        if d.get("type") == "turn.completed":
            usage = d.get("usage", {})
    from harnesseval.usage import from_codex_cli
    return text, from_codex_cli(usage, model_slug), model_slug
