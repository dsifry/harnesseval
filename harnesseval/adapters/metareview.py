"""metareview adapter — real bin/metareview deterministic gates + 8 LLM lenses (API, v0.8.0).

The structurally interesting adapter (docs/SPEC.md §2, §6.3):
  1. DETERMINISTIC GATES (free, model-independent, zero tokens): run the real
     `bin/metareview review task-done` on a materialized throwaway git repo. Gates:
     eval-injection, TODO/FIXME, missing-test-changes, duplicate-path, truncated-diff,
     context-risk. These fire identically across the whole (model x effort) matrix.
  2. LLM LENSES (paid, model-dependent): the 8 required artifact-review lenses run
     API-direct — Feasibility, Completeness, Scope&Alignment, Architecture, Intent
     Preservation, Security, Testing-quality, Data-migration — all in the adversarial stance
     with anchored-confidence suppression + per-lens anti-overlap (per
     skills/review-artifact/SKILL.md + rubrics/artifact-review-rubric.md + the per-lens
     rubric files at the pinned 0.8.0 SHA, third_party/metareview_sha.txt).
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

# The 8 required artifact-review lenses (skills/review-artifact/SKILL.md +
# rubrics/artifact-review-rubric.md + the per-lens rubric files) at the pinned 0.8.0 SHA.
# Each lens takes the adversarial stance with anchored-confidence suppression + per-lens
# anti-overlap, mirroring the rubric. We run them API-direct and aggregate findings.
# 0.8.0 (PR #11) re-stanced all 6 existing lenses adversarially + added Testing-quality +
# Data-migration + security/architecture content grafts. See docs/HANDOFF.md §4.4.

# Shared system prompt: the rubric's cross-cutting Adversarial Stance + Anchored Confidence &
# Suppression + Evidence Rules + Output structure (applies to ALL lenses).
LENS_SYSTEM = """You are an expert code reviewer using the metareview artifact-review rubric (v0.8.0).

ADVERSARIAL STANCE: assume the creator's intent is GOOD (you are NOT hostile to the author) but you ARE hostile to unexamined assumptions. Assume there may be a fundamental mistake hiding in this design — find it. Hunt for invalid assumptions, missing requirements, failure modes, hidden coupling, and cases the happy-path cannot represent. You may conclude the best improvement is to throw away part or all of the design. Do NOT confirm the artifact is well-shaped.

ANCHORED CONFIDENCE: each finding carries a confidence anchor (100=verifiable from code alone, mechanical; 75=double-checked, will affect users; 50=real but may be a nitpick; 25=might be a false positive; 0=not confident) and a severity (P0=critical/data loss; P1=high; P2=moderate; P3=low). SUPPRESSION: only report findings at confidence >= 50, OR any P0 finding regardless of confidence. Suppress everything below that threshold — it lowers precision without adding real recall.

EVIDENCE: every finding must cite a concrete source — file path + line, the verbatim code that makes it true, and the failure mode (what breaks / what an attacker gains / what data is lost). No generic advice; no "consider adding tests" boilerplate.

OUTPUT: list each distinct issue, one per item, as: <file:line> — <issue> — <failure mode>. Only report issues you are confident are real defects in THIS diff."""

LENS_PROMPTS = {
    "feasibility": "You are the Feasibility lens. Attack the assumption that paths, commands, dependencies, and stated prerequisites are correct against repository reality. Find the fabricated path, the impossible ordering, the missing tool, the invalid command the artifact assumes works. Block on fabricated paths, impossible ordering, missing tools, or invalid commands. Does NOT flag: whether requirements are complete (defer to Completeness); whether the architecture is sound (defer to Architecture).",
    "completeness": "You are the Completeness lens. Attack the assumption that the artifact covers every requirement. Find the requirement this artifact silently drops — the missing acceptance criterion, the missing verification, the obvious edge case no section addresses. Block on missing acceptance criteria, missing verification, or unhandled obvious edge cases. Does NOT flag: whether a path is feasible (defer to Feasibility); scope drift (defer to Scope-and-Alignment); architecture soundness (defer to Architecture).",
    "scope": "You are the Scope-and-Alignment lens. Attack the assumption that the artifact solves only the stated intent without unrelated expansion. Find the work that drifts, the under-scoping, the implementation not traceable to any requirement — what invariant does this NOT enforce? Block on scope drift, under-scoping, or implementation work not traceable to requirements. Does NOT flag: whether requirements are complete (defer to Completeness); whether the architecture is sound (defer to Architecture).",
    "architecture": "You are the Architecture lens. Attack the assumption that the boundaries, ownership, data model, and integration shape are correct. Hunt for the case where each breaks; find the fundamental mistake hiding in the design. Hunt for: boundary/ownership/registry failures (parallel service paths, contradictions with existing architecture, duplication risk, integration shape that can't represent the real domain); wrong data structure for the operation (list for membership where a set/map gives O(1); nested loops over the same collection -> O(n^2); repeated linear scans); unbounded materialization (all rows in memory with no LIMIT/streaming on a hot path); N+1 query patterns (a query inside a loop over earlier results); missing schema invariants (missing FK/index/NOT NULL/UNIQUE/CHECK; lists jammed in one text/JSON column instead of a join/child table; polymorphic (entity_type, entity_id) pairs that can't enforce a real FK); scalability cliffs (hot paths that don't paginate or assume small N; hardcoded limits masking unbounded queries; a new type/category requiring a migration when a lookup/child table would be data-driven); type-clarity traps (magic strings / bare ints as discriminators like status=\"open\" or kind:1 scattered across the diff instead of a named enum/typed constant so a variant is compile-checked; untyped dict/object where a named typed struct would make the shape explicit; stringly-typed data a typed enum would prevent drifting); redundant derived data (a derived column with no invalidation that can drift; a value duplicated across two tables with no single-source-of-truth; god-tables/fat interfaces mixing concerns); query/write inefficiency (SELECT * when few columns read; non-sargable predicates DATE(col)/LOWER(col)/leading-wildcard LIKE '%x'; queries inside loops instead of a batched IN/join); semantic-correctness failures (does each constraint enforce the REAL business invariant or a weaker/wrong one — under-scoped uniqueness UNIQUE(email) on a multi-tenant table that should be UNIQUE(org_id,email); a status field conflating orthogonal facts so a legal combo is unrepresentable; a model that can represent an illegal state the schema doesn't forbid, e.g. shipped_at AND cancelled_at both set with no CHECK; soft-delete columns defeating uniqueness); unguarded state transitions (a state machine enforced only in one app method a second caller can bypass — UPDATE SET status='active' with no WHERE status IN (...) guard; terminal states reachable again via a bulk/admin path; effective-dated rows with no exclusion constraint preventing overlap/gaps; soft-delete not filtered in every read path; audit tables written out-of-transaction); concurrency at the data layer (mutable shared records without optimistic-concurrency version/etag; read-modify-write on a balance/counter without FOR UPDATE or an atomic SET x=x-$1; check-then-insert backed only by a SELECT (TOCTOU) not a unique index; money/quantity as float/REAL not NUMERIC/Decimal; non-idempotent handlers with no idempotency key); coupling/evolvability (a business rule baked into schema shape so the next change forces a migration — roles as is_admin/is_editor booleans instead of a roles/user_roles table; an internal repr leaked into an API contract so a rename is a public break); LLM-specific failure modes (be most suspicious where the code looks most idiomatic: a cached/derived column *_count/*_total maintained by nothing — no trigger, no increment, permanently 0; indexes that don't match the queries IN THIS diff; typed data hidden in JSONB then filtered/joined; an invented relationship plausible from training but absent in the domain; docstrings describing behavior the code doesn't implement); SENTINEL-MEANING-CHANGE (a return value that changed meaning in this diff — null/empty/[] that meant 'nothing here' now meaning 'not yet loaded' or 'error suppressed'; a status sentinel whose semantics shifted so existing callers misbehave); CASCADING-FAILURE (trace failure propagation — when one dependency fails does it degrade gracefully or cascade? a sync call chain with no timeout/circuit-breaker/fallback; a queue consumer whose failure poisons the batch; a shared resource whose exhaustion takes down all tenants); STAND-IN-GUARD-FIDELITY (a CI gate/check/test that can go green while production is red — tests a proxy/mock instead of the real code path; a check that passes because the prod-only branch is #ifdef/feature-flagged away; a 'green' build that never exercised the changed code); API-CONTRACT-BREAKING-CHANGES (renamed/removed fields, narrowed inputs, widened returns, missing versioning on breaking changes; a response shape existing callers depend on but the diff silently changes; a field re-typed int->string with no version bump). Block on parallel service paths, contradictions with existing architecture, O(n^2) over a growing collection, unbounded materialization on a hot path, N+1 query loops, derivable data stored without invalidation, an illegal state the schema permits (no CHECK forbidding it), an unguarded state transition, a lost-update on a balance/counter, money as float, a phantom-maintained derived column, a sentinel-meaning-change with no caller update, a cascading-failure path with no degradation, a stand-in guard that can go green while prod is red, or an unversioned breaking API-contract change. Does NOT flag: security vulnerabilities (defer to Security); test quality (defer to Testing-quality); migration safety (defer to Data-migration).",
    "intent": "You are the Intent-Preservation lens. Attack the assumption that the final artifact still matches the original intent and accepted constraints. Find where review iterations silently changed the objective without explicit human acceptance — what happens when the happy-path intent drifts? Block when review iterations changed the objective without explicit human acceptance. Does NOT flag: feasibility (defer to Feasibility); completeness (defer to Completeness); scope or architecture soundness (defer to Scope-and-Alignment / Architecture).",
    "security": "You are the Security lens. Hunt for vulnerabilities the change introduces or fails to prevent, across the OWASP classes a diff-review can see. Hunt for IDOR/ownership scoping: DB queries/lookups using a user-supplied id without an ownership/org/tenant scope check — WHERE id=$user_id with no org_id/tenant filter so any user reads any tenant's row. Hunt for injection variants beyond SQL: command injection (exec/spawn with user input), NoSQL injection (user-controlled operators/keys in a query document), deserialization injection (unvalidated pickle/yaml.load/unserialize of untrusted bytes into executable structures), and SQL string interpolation into queries. Hunt for SSRF protocol-bypass: server-side fetch of unvalidated user URLs where a naive localhost string check (url.includes('localhost')) is defeated by file://, gopher://, 127.0.0.1 in decimal/IPv6 notation, or DNS rebinding. Hunt for secrets in logs (distinct from secrets in code): PII, tokens, or credentials written to log output, error messages, or telemetry — not hardcoded in source but leaked at runtime through logging paths the diff adds/changes. Hunt for cryptographic failures / hardcoded secrets, XSS / unescaped user input to HTML/JS, insecure design (trust-the-client authz), auth/session failures (weakened token entropy/integrity, removed expiry), security misconfiguration (debug mode, default creds). Block on user-supplied-id lookups without ownership scope, string-interpolated SQL/commands, unvalidated deserialization of untrusted input, hardcoded secrets in committed code, secrets written to logs, server-side fetch of unvalidated user URLs (including protocol-bypass), unescaped user input to HTML/JS output, weakened token integrity/entropy. Do not double-report issues the deterministic gates already catch (the eval() gate covers bare eval() injection; flag injection the gate does not catch, e.g. SQL string interpolation). Does NOT flag: code style; architecture correctness (defer to Architecture); test quality (defer to Testing-quality); migration safety (defer to Data-migration).",
    "testing-quality": "You are the Testing-quality lens. Attack the assumption that the tests verify the behavior they claim to. Tests can lie — find where they do. This is a diff-scoped lens: judge whether the test changes in THIS diff verify the behavior changes in THIS diff, not whether the whole suite is comprehensive. Hunt for false-confidence assertions (toBeTruthy()/toBeDefined()/not.toBeNull()/'doesn't throw'/bare assert(x) that assert nothing — a test that passes regardless of whether the code is correct; a test that checks a return value's existence but never its content/type/shape; a try/catch that swallows errors and passes unconditionally). Hunt for behavioral-change-in-the-diff with ZERO test modifications (new logic, changed branches, or modified state transitions with no corresponding test change — stale tests that pass though they no longer cover the new behavior; a function signature changed but no test caller updated). Hunt for tests verifying mocks not real logic (asserts the mock was called with certain args but never checks the real return value/side effect; a mock that replaces the unit under test so the real code is never exercised; a spy returning a canned value the test asserts back — a tautology). Hunt for untested new branches/lifecycle paths (a new if/switch branch, error path, or lifecycle hook onMount/onUnmount/beforeDestroy/componentDidCatch with no test that triggers it; a new edge case handled in code with no test for it). Hunt for sentinel-semantics reuse in mocks (a mock returning null/empty/[] that no longer matches what the real function returns in the new code — the mock's sentinel meant 'nothing here' but the real code now returns [] meaning 'empty but valid'). Hunt for mirror-tests-that-miss-the-machine (tests that mirror the implementation's structure so closely they pass even when both are wrong — testing the code against itself, not the spec; a parameterized test whose data table only covers cases the code already handles, never a case the spec requires but the code misses). Block on a behavioral change in the diff with no test modifications, a test that asserts nothing (false-confidence), or a test that exercises only a mock. Missing-test ownership (precedence): the deterministic missing-test gate owns the boolean 'source changed, test file unchanged' (free, exact) — it fires on absence of test-file changes; Completeness owns missing verification when no test code is in the diff at all; THIS lens owns tests that EXIST but don't cover the new behavior (qualitative). Do not double-report eval() or missing-test issues the deterministic gates already catch. Does NOT flag: security vulnerabilities (defer to Security); architecture soundness (defer to Architecture); migration safety (defer to Data-migration); whether tests exist at all when no test code is in the diff (defer to Completeness).",
    "data-migration": "You are the Data-migration lens. Attack the assumption that the migration is safe and reversible. Find the failure that loses data or can't be rolled back. This is a diff-scoped lens: judge whether the migration changes in THIS diff are safe against the review-base schema. Hunt for schema drift (the migration's schema changes differ from what the review-base schema expects — a column added/renamed/typed differently in the migration vs the code that reads it; a model/ORM definition updated but the migration not generated, or vice versa). Hunt for irreversible migrations (DROP COLUMN/DROP TABLE/destructive ALTER like type narrowing or SET NOT NULL without a default, without a backfill or documented rollback — once applied, cannot be undone without data loss). Hunt for missing backfills for new NOT NULL columns (a new NOT NULL column with no DEFAULT or backfill step, so existing rows can't be inserted/updated and the deploy breaks mid-rollout; a backfill that runs after the code expects the column populated). Hunt for deploy-window breaks / expand+contract violations (a contract change in one step that breaks rolling deploys — a column rename in the same PR that adds the new name so old-code pods crash; a column dropped before all readers updated; skipping the expand/contract/cleanup phases). Hunt for dual-write gaps (should dual-write old+new but only writes one side, so backfill/cutover finds missing data; reads the new column before all rows are backfilled from the old). Hunt for orphaned refs (a FK added/changed pointing at rows that don't exist; a FK dropped without cleaning up dangling references; a renamed/removed referenced row with no cascade/cleanup for dependents). Hunt for silent data loss (drops/overwrites/truncates data without a backup/export step; a DELETE with a broader WHERE than intended; a column repurposed same-name-new-meaning so old data is silently misinterpreted; a type conversion ALTER COLUMN TYPE that narrows/truncates and silently drops values that don't fit). Block on irreversible migrations without rollback, missing backfills for NOT NULL columns, expand+contract violations that break rolling deploys, silent data loss, or orphaned refs. Does NOT flag: security vulnerabilities (defer to Security); test quality (defer to Testing-quality); architecture soundness beyond migration safety, and whether the schema is well-designed (defer to Architecture — this lens judges only whether the transition from the old schema to the new one is safe and reversible).",
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
    return await call_model(model, system=LENS_SYSTEM,
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
    """Async core — safe inside a running event loop. Combine deterministic gates + 8 LLM lenses."""
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
