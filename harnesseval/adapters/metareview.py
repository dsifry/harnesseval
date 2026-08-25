"""metareview adapter — real bin/metareview deterministic gates + 6 LLM lenses (API).

The structurally interesting adapter (docs/SPEC.md §2, §6.3):
  1. DETERMINISTIC GATES (free, model-independent, zero tokens): run the real
     `bin/metareview review task-done` on a materialized throwaway git repo. Gates:
     eval-injection, TODO/FIXME, missing-test-changes, duplicate-path, truncated-diff,
     context-risk. These fire identically across the whole (model x effort) matrix.
  2. LLM LENSES (paid, model-dependent): the 6 required artifact-review lenses run
     API-direct — Feasibility, Completeness, Scope&Alignment, Architecture, Intent
     Preservation, Security (per skills/review-artifact/SKILL.md + rubrics/artifact-review-rubric.md).
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

# The 6 required artifact-review lenses (skills/review-artifact/SKILL.md +
# rubrics/artifact-review-rubric.md + rubrics/security-review-rubric.md) — each is a focused
# reviewer prompt; we run them API-direct and aggregate findings. The Security lens is the H1
# addition (docs/METAREVIEW_IMPROVEMENTS.md): metareview's first 5 lenses were all artifact-shape
# checks with no vulnerability coverage, so it under-recalled on security goldens vs vanilla.
LENS_PROMPTS = {
    "feasibility": "You are a Feasibility reviewer. Given the PR diff below, verify paths, commands, dependencies, and stated changes against the diff reality. Block on fabricated paths, impossible ordering, or invalid commands. List each distinct issue found, one per item.",
    "completeness": "You are a Completeness reviewer. Given the PR diff below, map the change to its stated intent and check for missing acceptance criteria, missing verification, or unhandled obvious edge cases. List each distinct issue found, one per item.",
    "scope": "You are a Scope-and-Alignment reviewer. Given the PR diff below, check whether it solves its stated intent without unrelated expansion, scope drift, or under-scoping. List each distinct issue found, one per item.",
    "architecture": "You are an Architecture reviewer. Given the PR diff below, check boundaries, ownership, duplication risk, and integration shape. ALSO check the data model and data-structure design and efficiency: wrong structure for the operation (list for membership where a set/map gives O(1); nested loops over the same collection -> O(n^2); repeated linear scans; unbounded materialization loading all rows with no LIMIT/streaming; N+1 query patterns inside a loop); schema invariants (missing FK/index/NOT NULL/UNIQUE/CHECK; lists in one text/JSON column instead of a join table; polymorphic entity_type/entity_id pairs that can't enforce a real FK); scalability (hot paths that don't paginate or assume small N; hardcoded limits masking unbounded queries; adding a type/category requiring a migration when a lookup table would be data-driven); redundancy (derivable data stored as a column with no invalidation that can drift; a value duplicated across two tables with no single source of truth; god-tables mixing concerns); query/write efficiency (SELECT * when few columns read; non-sargable predicates like DATE(col)/LOWER(col)/leading-wildcard LIKE '%x'; queries inside loops instead of a batched IN/join); type clarity (magic strings or bare ints used as discriminators like status=\"open\" or kind:1 scattered across the diff instead of a named enum/typed constant so adding a variant is compile-checked; untyped dict/object containers where a named typed struct would make the shape explicit; stringly-typed data a typed enum would prevent drifting); and data-structure Big-O (a list for membership/lookup where a set/map is O(1); nested loops O(n^2); a structure whose access pattern doesn't match the operation). ALSO run the principal-engineer pass: semantic correctness (does each constraint enforce the REAL business invariant or a weaker/wrong one — under-scoped uniqueness like UNIQUE(email) on a multi-tenant table that should be UNIQUE(org_id,email); a status field conflating orthogonal facts so a legal combo is unrepresentable; a model that can represent an illegal state the schema doesn't forbid, e.g. shipped_at AND cancelled_at both set with no CHECK; soft-delete defeating uniqueness); data lifecycle & state transitions (a state machine enforced only in one app method a second caller bypasses — an UPDATE SET status='active' with no WHERE status IN (...) guard; terminal states reachable again; effective-dated rows with no exclusion constraint preventing overlap/gaps; soft-delete not filtered in every read path; audit tables written out-of-transaction); concurrency at the data layer (mutable shared records without optimistic-concurrency version/etag; read-modify-write on a balance without FOR UPDATE or an atomic SET x=x-$1; check-then-insert backed only by a SELECT (TOCTOU) not a unique index; money/quantity as float/REAL not NUMERIC/Decimal; non-idempotent handlers with no idempotency key); coupling/evolvability (a business rule baked into schema shape so the next change forces a migration, e.g. roles as is_admin/is_editor booleans; an internal repr leaked into an API contract so a rename is a public break; a destructive migration in one step with rolling deploy in flight); and LLM-specific failure modes (be most suspicious where the code looks most idiomatic: a cached/derived column *_count/*_total maintained by nothing — no trigger, no transactional increment; indexes that don't match the queries IN THIS diff; typed data hidden in JSONB then filtered/joined; an invented relationship plausible from training but absent in the domain; docstrings describing behavior the code doesn't implement). List each distinct issue found, one per item, with file:line.",
    "intent": "You are an Intent-Preservation reviewer. Given the PR diff below, compare the change direction against the PR title/intent and check whether it drifts from the stated goal. List each distinct issue found, one per item.",
    "security": "You are a Security reviewer. Given the PR diff below, hunt for security vulnerabilities the change introduces or fails to prevent, across the OWASP classes a diff-review can see: broken access control / IDOR (user-supplied-id lookups without ownership/org/tenant scope), injection (SQL/NoSQL/command — string interpolation into queries, exec/spawn with user input), cryptographic failures / hardcoded secrets / PII in logs, SSRF (server-side fetch of unvalidated user URLs), XSS / unescaped user input to HTML/JS output, insecure design (trust-the-client authz), auth/session failures (weakened token entropy/integrity, removed expiry), deserialization of untrusted input, security misconfiguration (debug mode, default creds). For each issue give file:line, the vulnerable code, and the failure mode (what an attacker gains / what breaks). Only report issues you are confident are real vulnerabilities in THIS diff, not generic hardening advice. Do not double-report bare eval() injection (a deterministic gate covers that). List each distinct issue found, one per item.",
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

async def _run_lens(model: str, lens: str, prompt_body: str, effort: str = "medium") -> tuple[str, int, int, dict]:
    prompt = f"{LENS_PROMPTS[lens]}\n\n{prompt_body}"
    from harnesseval.model_router import call_model
    max_tok = 4096 if effort == "xhigh" else 2048
    return await call_model(model, system="You are an expert code reviewer.",
                            user=prompt, effort=effort, max_tokens=max_tok)


async def _run_all_lenses(model: str, pr: PRSample, effort: str = "medium") -> tuple[list[Finding], int, int, list[str], dict]:
    from harnesseval.usage import merge
    body = LENS_HEADER.format(pr_title=pr.pr_title, diff=_truncate(pr.diff))
    sem = asyncio.Semaphore(5)
    async def bounded(l):
        async with sem:
            return await _run_lens(model, l, body, effort=effort)
    results = await asyncio.gather(*[bounded(l) for l in LENS_PROMPTS])
    findings: list[Finding] = []
    tin = tout = 0
    raws: list[str] = []
    per_model: dict = {}
    from harnesseval.model_router import call_model_json
    from harnesseval.extract import EXTRACT_PROMPT, EXTRACT_SYSTEM
    for (lens, (text, i, o, pmu)) in zip(LENS_PROMPTS.keys(), results):
        tin += i; tout += o; raws.append(f"## {lens}\n{text}")
        per_model = merge(per_model, pmu)
        parsed, pi, po, pmu_ext = await call_model_json(model, EXTRACT_SYSTEM, EXTRACT_PROMPT.format(comment=text),
                                               effort=effort, max_tokens=1024)
        tin += pi; tout += po; per_model = merge(per_model, pmu_ext)
        for issue in parsed.get("issues", []):
            findings.append(Finding(issue_text=issue, source=f"metareview-lens/{lens}", raw=text[:500]))
    return findings, tin, tout, raws, per_model


# ---- combined review ----

async def review_async(pr: PRSample, model: str, effort: str = "medium", mode: str = "api") -> ReviewRun:
    """Async core — safe inside a running event loop. Combine deterministic gates + 6 LLM lenses."""
    t0 = time.time()
    name = "metareview"
    try:
        det_findings, det_md, det_meta = _run_deterministic(pr)
    except Exception as e:  # noqa: BLE001
        return ReviewRun(framework=name, model=model, effort=effort, execution_mode=mode,
                         raw_output="", wall_ms=(time.time() - t0) * 1000, error=f"deterministic: {e}")
    try:
        lens_findings, tin, tout, lens_raws, per_model = await _run_all_lenses(model, pr, effort=effort)
    except Exception as e:  # noqa: BLE001
        return ReviewRun(framework=name, model=model, effort=effort, execution_mode=mode,
                         raw_output=det_md, findings=det_findings, wall_ms=(time.time() - t0) * 1000,
                         error=f"lenses: {e}")
    all_findings = det_findings + lens_findings
    raw = f"# Deterministic gates (bin/metareview)\n{det_md}\n\n# LLM lenses ({model})\n" + "\n\n".join(lens_raws)
    from harnesseval.usage import grand_total
    gt = grand_total(per_model)
    return ReviewRun(framework=name, model=model, effort=effort, execution_mode=mode,
                     raw_output=raw, findings=all_findings, tokens_in=tin, tokens_out=tout,
                     wall_ms=(time.time() - t0) * 1000, per_model_usage=per_model,
                     total_cost_usd=gt["total_cost_usd"])


def review(pr: PRSample, model: str, effort: str = "medium", mode: str = "api") -> ReviewRun:
    """Sync wrapper (top-level use)."""
    return asyncio.run(review_async(pr, model, effort, mode))
