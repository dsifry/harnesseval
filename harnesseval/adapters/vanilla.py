"""Vanilla adapter — the single-prompt baselines (naive + engineered).

Two baselines (docs/SPEC.md §2) to separate "good prompt engineering value" from
"framework methodology value":
  - vanilla-naive: bare "review this diff for bugs"
  - vanilla-engineered: a carefully-built single prompt with the rubric + severity guidance

Supports both execution modes (docs/SPEC.md §7):
  - api: Anthropic API direct (Phase C; also used for minimal Phase B checks)
  - cli: `claude -p` OAuth (Phase B free iteration)

Both produce PROSE; the harness extracts atomic Findings via extract.py (same as all
adapters) so findings are comparable.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import time

from harnesseval import keys
from harnesseval.adapters.base import PRSample, ReviewRun
from harnesseval.finding import Finding

NAIVE_PROMPT = """Review the following code diff for bugs, issues, and problems. List each issue you find.

PR: {pr_title}

```diff
{diff}
```

Respond with a numbered list of issues found."""

ENGINEERED_PROMPT = """You are an expert code reviewer. Review the following code diff for real, actionable issues.

PR: {pr_title}

```diff
{diff}
```

Find issues in these categories: bug, security, concurrency, data, api, performance, test_gap, doc_defect.
For each issue:
- State the specific problem concisely (one issue per item — do not bundle).
- Note the file and line if identifiable from the diff.
- Classify severity as Low, Medium, High, or Critical.
- Only report real issues you are confident about; do not pad with style nits or speculation.

Respond with a numbered list, one issue per line, e.g.:
1. [High/bug] path/to/file.py:71 — description of the specific problem
2. [Medium/performance] ..."""


def _truncate(diff: str, max_chars: int = 60000) -> str:
    """Keep the diff within prompt limits (Phase B context is diff-only per SPEC §6.2)."""
    if len(diff) <= max_chars:
        return diff
    return diff[:max_chars] + f"\n\n[... diff truncated: {len(diff) - max_chars} more chars ...]"


async def _review_api(pr: PRSample, model: str, prompt_template: str) -> tuple[str, int, int]:
    """Anthropic API direct. Returns (output_text, input_tokens, output_tokens)."""
    client = keys.anthropic_client()
    prompt = prompt_template.format(pr_title=pr.pr_title, diff=_truncate(pr.diff))
    resp = await asyncio.to_thread(
        client.messages.create, model=model, max_tokens=2048,
        messages=[{"role": "user", "content": prompt}], extra_body={"temperature": 0.0},
    )
    return resp.content[0].text, resp.usage.input_tokens, resp.usage.output_tokens


async def _review_cli(pr: PRSample, model: str, effort: str, prompt_template: str) -> tuple[str, int, int]:
    """Claude Code `claude -p` OAuth (free, Phase B). Returns (output_text, in_tokens, out_tokens)."""
    prompt = prompt_template.format(pr_title=pr.pr_title, diff=_truncate(pr.diff))
    # claude -p --model <m> --effort <e> --output-format json --max-turns 1
    args = ["claude", "-p", "--model", model, "--effort", effort,
            "--output-format", "json", "--max-turns", "1", prompt]
    t0 = time.time()
    r = await asyncio.to_thread(subprocess.run, args, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"claude -p failed: {r.stderr.strip()[:300]}")
    d = json.loads(r.stdout)
    return d.get("result", ""), int(d.get("usage", {}).get("input_tokens", 0)), int(d.get("usage", {}).get("output_tokens", 0))


def review(pr: PRSample, model: str, effort: str, mode: str = "api",
           variant: str = "engineered") -> ReviewRun:
    """Run a vanilla review. variant: 'naive' | 'engineered'. mode: 'api' | 'cli'."""
    tmpl = NAIVE_PROMPT if variant == "naive" else ENGINEERED_PROMPT
    name = f"vanilla-{variant}"
    t0 = time.time()
    try:
        if mode == "api":
            out, tin, tout = asyncio.run(_review_api(pr, model, tmpl))
        elif mode == "cli":
            out, tin, tout = asyncio.run(_review_cli(pr, model, effort, tmpl))
        else:
            raise ValueError(f"unknown mode: {mode}")
    except Exception as e:  # noqa: BLE001
        return ReviewRun(framework=name, model=model, effort=effort, execution_mode=mode,
                         raw_output="", tokens_in=0, tokens_out=0, wall_ms=(time.time() - t0) * 1000,
                         error=str(e))
    # extract atomic findings (Martian EXTRACT_PROMPT) — same path as all adapters
    from harnesseval.extract import extract_findings
    findings = extract_findings(out, model=model, source=name) if out else []
    return ReviewRun(framework=name, model=model, effort=effort, execution_mode=mode,
                     raw_output=out, findings=findings, tokens_in=tin, tokens_out=tout,
                     wall_ms=(time.time() - t0) * 1000)
