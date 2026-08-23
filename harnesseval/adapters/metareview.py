"""metareview adapter — real bin/metareview deterministic gates + 5 LLM lenses (API).

The structurally interesting adapter (docs/SPEC.md §2, §6.3):
  1. DETERMINISTIC GATES (free, model-independent, zero tokens): run the real
     `bin/metareview review task-done` on a materialized throwaway git repo. Gates:
     eval-injection, TODO/FIXME, missing-test-changes, duplicate-path, truncated-diff,
     context-risk. These fire identically across the whole (model x effort) matrix.
  2. LLM LENSES (paid, model-dependent): the 5 required artifact-review lenses run
     API-direct — Feasibility, Completeness, Scope&Alignment, Architecture, Intent
     Preservation (per skills/review-artifact/SKILL.md + rubrics/artifact-review-rubric.md).
  Combined findings -> extract.py -> judge vs golden. Score decomposes into
  deterministic_gate_recall + llm_lens_recall (SPEC §6.3).
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import time
from pathlib import Path

from harnesseval import keys
from harnesseval.adapters.base import PRSample, ReviewRun
from harnesseval.dataset.materialize import materialize
from harnesseval.finding import Finding

MRV_BIN = Path(__file__).resolve().parents[2] / "bin" / "metareview"

# The 5 required artifact-review lenses (skills/review-artifact/SKILL.md) — each is a focused
# reviewer prompt; we run them API-direct and aggregate findings.
LENS_PROMPTS = {
    "feasibility": "You are a Feasibility reviewer. Given the PR diff below, verify paths, commands, dependencies, and stated changes against the diff reality. Block on fabricated paths, impossible ordering, or invalid commands. List each distinct issue found, one per item.",
    "completeness": "You are a Completeness reviewer. Given the PR diff below, map the change to its stated intent and check for missing acceptance criteria, missing verification, or unhandled obvious edge cases. List each distinct issue found, one per item.",
    "scope": "You are a Scope-and-Alignment reviewer. Given the PR diff below, check whether it solves its stated intent without unrelated expansion, scope drift, or under-scoping. List each distinct issue found, one per item.",
    "architecture": "You are an Architecture reviewer. Given the PR diff below, check boundaries, ownership, duplication risk, and integration shape. List each distinct issue found, one per item.",
    "intent": "You are an Intent-Preservation reviewer. Given the PR diff below, compare the change direction against the PR title/intent and check whether it drifts from the stated goal. List each distinct issue found, one per item.",
}

LENS_HEADER = "PR: {pr_title}\n\n```diff\n{diff}\n```\n\nList each distinct real issue you find (one per item, with file:line if identifiable). Only report issues you are confident about."


def _truncate(diff: str, max_chars: int = 60000) -> str:
    if len(diff) <= max_chars:
        return diff
    return diff[:max_chars] + f"\n\n[... diff truncated: {len(diff) - max_chars} more chars ...]"


# ---- deterministic gates via real bin/metareview ----

def _run_deterministic(pr: PRSample) -> tuple[list[Finding], str, dict]:
    """Run real bin/metareview task-done on a materialized repo. Returns (findings, raw_md, meta)."""
    repo_dir = materialize(pr.url)
    task_path = repo_dir / "docs" / "tasks" / "task-001.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(f"# Task: {pr.pr_title}\nReview the change.\n")
    subprocess.run(["git", "-C", str(repo_dir), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo_dir), "commit", "--quiet", "--allow-empty", "-m", "task"],
                   check=True, capture_output=True,
                   env={**__import__("os").environ, "GIT_AUTHOR_NAME": "x", "GIT_AUTHOR_EMAIL": "x@x",
                        "GIT_COMMITTER_NAME": "x", "GIT_COMMITTER_EMAIL": "x@x"})
    base_ref = "HEAD~2"  # base commit (before 'pr' and 'task')
    r = subprocess.run([str(MRV_BIN), "review", "task-done", str(task_path), "--base", base_ref],
                       cwd=str(repo_dir), capture_output=True, text=True, check=False)
    review_rel = r.stdout.strip().splitlines()[-1] if r.stdout else ""
    review_md = ""
    if review_rel and review_rel.endswith(".md"):
        rp = repo_dir / review_rel
        if rp.exists():
            review_md = rp.read_text()
    findings = _parse_deterministic_findings(review_md)
    meta = {"verdict": _extract_verdict(review_md), "raw_md_path": str(review_rel)}
    return findings, review_md, meta


def _parse_deterministic_findings(md: str) -> list[Finding]:
    """Extract the blocking + advisory findings metareview emitted from its review markdown."""
    findings: list[Finding] = []
    # findings look like: ### mrvf-...: <Title>\n- Reviewer: ...\n- Severity: ...\n- Finding: <text>
    for m in re.finditer(r"###\s+\S+:\s*(.+?)\n(.+?)(?=\n###|\n##\s|$)", md, re.S):
        title = m.group(1).strip()
        body = m.group(2)
        sev = re.search(r"Severity:\s*(\w+)", body)
        rev = re.search(r"Reviewer:\s*(\S+)", body)
        # the finding text is the Title (deterministic gates use Title as the issue)
        findings.append(Finding(issue_text=title, source=f"metareview-deterministic/{rev.group(1) if rev else '?'}",
                                severity=(sev.group(1).lower() if sev else None),
                                category="bug", raw=title))
    return findings


def _extract_verdict(md: str) -> str:
    m = re.search(r"##\s+Verdict\s*\n\s*(\S+)", md)
    return m.group(1) if m else ""


# ---- LLM lenses (API-direct) ----

async def _run_lens(model: str, lens: str, prompt_body: str, effort: str = "medium") -> tuple[str, int, int]:
    prompt = f"{LENS_PROMPTS[lens]}\n\n{prompt_body}"
    from harnesseval.model_router import call_model
    max_tok = 4096 if effort == "xhigh" else 2048
    return await call_model(model, system="You are an expert code reviewer.",
                            user=prompt, effort=effort, max_tokens=max_tok)


async def _run_all_lenses(model: str, pr: PRSample, effort: str = "medium") -> tuple[list[Finding], int, int, list[str]]:
    body = LENS_HEADER.format(pr_title=pr.pr_title, diff=_truncate(pr.diff))
    sem = asyncio.Semaphore(5)
    async def bounded(l):
        async with sem:
            return await _run_lens(model, l, body, effort=effort)
    results = await asyncio.gather(*[bounded(l) for l in LENS_PROMPTS])
    findings: list[Finding] = []
    tin = tout = 0
    raws: list[str] = []
    from harnesseval.model_router import call_model_json
    from harnesseval.extract import EXTRACT_PROMPT, EXTRACT_SYSTEM
    for (lens, (text, i, o)) in zip(LENS_PROMPTS.keys(), results):
        tin += i; tout += o; raws.append(f"## {lens}\n{text}")
        parsed, pi, po = await call_model_json(model, EXTRACT_SYSTEM, EXTRACT_PROMPT.format(comment=text),
                                               effort=effort, max_tokens=1024)
        tin += pi; tout += po
        for issue in parsed.get("issues", []):
            findings.append(Finding(issue_text=issue, source=f"metareview-lens/{lens}", raw=text[:500]))
    return findings, tin, tout, raws


# ---- combined review ----

async def review_async(pr: PRSample, model: str, effort: str = "medium", mode: str = "api") -> ReviewRun:
    """Async core — safe inside a running event loop. Combine deterministic gates + 5 LLM lenses."""
    t0 = time.time()
    name = "metareview"
    try:
        det_findings, det_md, det_meta = _run_deterministic(pr)
    except Exception as e:  # noqa: BLE001
        return ReviewRun(framework=name, model=model, effort=effort, execution_mode=mode,
                         raw_output="", wall_ms=(time.time() - t0) * 1000, error=f"deterministic: {e}")
    try:
        lens_findings, tin, tout, lens_raws = await _run_all_lenses(model, pr, effort=effort)
    except Exception as e:  # noqa: BLE001
        return ReviewRun(framework=name, model=model, effort=effort, execution_mode=mode,
                         raw_output=det_md, findings=det_findings, wall_ms=(time.time() - t0) * 1000,
                         error=f"lenses: {e}")
    all_findings = det_findings + lens_findings
    raw = f"# Deterministic gates (bin/metareview)\n{det_md}\n\n# LLM lenses ({model})\n" + "\n\n".join(lens_raws)
    return ReviewRun(framework=name, model=model, effort=effort, execution_mode=mode,
                     raw_output=raw, findings=all_findings, tokens_in=tin, tokens_out=tout,
                     wall_ms=(time.time() - t0) * 1000)


def review(pr: PRSample, model: str, effort: str = "medium", mode: str = "api") -> ReviewRun:
    """Sync wrapper (top-level use)."""
    return asyncio.run(review_async(pr, model, effort, mode))
