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
    return {"low": "low", "medium": "medium", "xhigh": "xhigh"}.get(effort, "medium")


def _parse_codex_effort(effort: str) -> str:
    # Codex model_reasoning_effort: low, medium, high, xhigh, max, ultra
    return {"low": "low", "medium": "medium", "xhigh": "xhigh"}.get(effort, "medium")


async def _claude_cli(model_alias: str, effort: str, prompt: str, system: str | None = None,
                     max_turns: int = 1, timeout: int = 300) -> tuple[str, dict, str]:
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
                    timeout: int = 300) -> tuple[str, dict, str]:
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
