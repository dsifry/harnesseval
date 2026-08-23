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
                     max_turns: int = 1, timeout: int = 300) -> tuple[str, int, int, str]:
    """Run a review via `claude -p` OAuth. Returns (text, input_tokens, output_tokens, resolved_model).

    IMPORTANT: ALWAYS pass a system prompt via --append-system-prompt. Without it, `claude -p`
    can silently fall back to Haiku for the work turn even when --model sonnet/opus is set
    (modelUsage shows both Haiku + the requested model). The system-prompt presence affects
    which model runs the turn (verified 2026-08-22). We record the resolved model from modelUsage.
    """
    args = ["claude", "-p", "--model", model_alias, "--effort", _parse_claude_effort(effort),
            "--output-format", "json", "--max-turns", str(max_turns)]
    # always set a system prompt (prevents the Haiku fallback); append so we keep base behavior
    args += ["--append-system-prompt", system or "You are an expert code reviewer."]
    args += [prompt]
    proc = await asyncio.to_thread(subprocess.run, args, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"claude -p failed: {proc.stderr.strip()[:300]}")
    d = json.loads(proc.stdout)
    u = d.get("usage", {})
    text = d.get("result", "")
    # resolved model: modelUsage keys (could be multiple if Haiku fallback happened — record all)
    mu = d.get("modelUsage") or {}
    resolved = ",".join(mu.keys()) if isinstance(mu, dict) and mu else ""
    return text, int(u.get("input_tokens", 0)), int(u.get("output_tokens", 0)), resolved


async def _codex_cli(model_slug: str, effort: str, prompt: str, system: str | None = None,
                    timeout: int = 300) -> tuple[str, int, int, str]:
    """Run a review via `codex exec` OAuth. Returns (text, input_tokens, output_tokens, resolved_model)."""
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
    return text, int(usage.get("input_tokens", 0)), int(usage.get("output_tokens", 0)), model_slug
