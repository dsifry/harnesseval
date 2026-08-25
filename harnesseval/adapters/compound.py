"""Compound Engineering adapter — API-direct methodology (the secondary column, SPEC §7).

Compound Engineering (`EveryInc/compound-engineering-plugin`, pinned SHA in
third_party/compound_sha.txt) is an external plugin whose review methodology is the `ce-code-review`
skill: a risk-driven persona roster. `correctness` runs on every review; then conditionals
(security, performance, api-contract, reliability, testing, maintainability, data-migration,
adversarial, ...) are selected by diff signals; each persona is a `general-purpose` subagent
seeded with a prompt from references/personas/. Findings use a P0-P3 severity scale + an anchored
confidence rubric (0/25/50/75/100) + an action-class route (gated_auto/manual/advisory).

This adapter extracts that methodology to bare API prompts (the "methodology isolated" academic
column per SPEC §7). It runs the core persona (correctness, always-on) API-direct plus the
conditionals justified by the diff (selection rules per references/select-and-route.md), one API
call per selected persona, and aggregates the findings. It does NOT invoke the real plugin
plumbing (subagent dispatch, cross-model peer) — that's the realistic adapter
(`compound_realistic.py`). Both columns are recorded; api vs cli are never compared head-to-head.

The methodology source (auditable):
  - skills/ce-code-review/SKILL.md (the skill spine)
  - skills/ce-code-review/references/persona-catalog.md (the roster + selection gates)
  - skills/ce-code-review/references/select-and-route.md (selection rules)
  - skills/ce-code-review/references/action-class-rubric.md (severity P0-P3 + confidence anchors)
  - skills/ce-code-review/references/findings-schema.json (the structured finding schema)
  - skills/ce-code-review/references/personas/correctness-reviewer.md (always-on persona)
  at repo SHA a32c9474c658f3e33b6e3615a5d51089046d4c79.

Output is prose (one section per persona, P0-P3 severity-tagged findings); the harness extracts
atomic Findings via extract.py (Martian EXTRACT_PROMPT) so findings are comparable across all
frameworks.
"""

from __future__ import annotations

import asyncio
import re
import time

from harnesseval.adapters.base import PRSample, ReviewRun
from harnesseval.finding import Finding

# The persona prompts, extracted from references/personas/*.md @ SHA a32c9474. Each is the focus
# of one reviewer persona; we render them API-direct (no subagent spawn) and aggregate. Per
# persona-catalog.md, `correctness` is ALWAYS-ON; the rest are conditional on diff signals
# (selection rules below). We keep the persona's focus verbatim from the upstream prompt asset.
PERSONA_PROMPTS: dict[str, str] = {
    "correctness": "You are a logic and behavioral correctness expert who reads code by mentally "
    "executing it. Hunt for: off-by-one/boundary errors; null/undefined propagation; sentinel "
    "meaning changes; race conditions and ordering assumptions; incorrect state transitions; "
    "broken error propagation (errors swallowed, re-thrown without context, fallback values "
    "masking failures). For each issue give file:line, what's wrong, why it matters (the failure "
    "mode, not 'what is wrong'), and a confidence anchor (0/25/50/75/100).",
    "security": "You are a security reviewer. Hunt for: authz/authn gaps (missing ownership "
    "checks, IDOR); user-input handling (injection, SSRF, path traversal); secret/credential "
    "handling; permission checks. For each issue give file:line, what's wrong, why it matters, "
    "and a confidence anchor (0/25/50/75/100).",
    "performance": "You are a performance reviewer. Hunt for: unbounded queries/materialization; "
    "N+1 query shape; missing pagination; large in-memory transforms; cache policy with material "
    "resource impact; algorithmic complexity. For each issue give file:line, what's wrong, why it "
    "matters, and a confidence anchor (0/25/50/75/100).",
    "api-contract": "You are an API-contract reviewer. Hunt for: externally consumed boundary "
    "changes (routes, serializers, event schemas, versioning, public package signatures) without "
    "caller consideration; response shape drift. For each issue give file:line, what's wrong, why "
    "it matters, and a confidence anchor (0/25/50/75/100).",
    "reliability": "You are a reliability reviewer. Hunt for: error handling gaps; retry logic "
    "errors; missing timeouts; circuit-breaker gaps; background-job/async-handler issues; health "
    "check gaps. For each issue give file:line, what's wrong, why it matters, and a confidence "
    "anchor (0/25/50/75/100).",
    "testing": "You are a testing reviewer. Hunt for: tests that verify mocks not real behavior; "
    "missing edge-case coverage; missing integration tests where they matter; behavioral change "
    "without corresponding test work. For each issue give file:line, what's wrong, why it matters, "
    "and a confidence anchor (0/25/50/75/100).",
    "maintainability": "You are a maintainability reviewer. Hunt for: coupling/type-boundary "
    "leaks; premature abstraction; duplication risk; dead code; missing separation of concerns. "
    "For each issue give file:line, what's wrong, why it matters, and a confidence anchor "
    "(0/25/50/75/100).",
    "data-migration": "You are a data-migration reviewer. Hunt for: destructive DDL without "
    "rollback; backfill gaps; NOT NULL without default; column renames/drops without safety. For "
    "each issue give file:line, what's wrong, why it matters, and a confidence anchor "
    "(0/25/50/75/100).",
    "adversarial": "You are an adversarial reviewer. Assume the change is hostile or buggy. Hunt "
    "for: silent-pass verification mechanisms (a guard that can go green while the real thing is "
    "red); cascade failures; abuse cases; partial-failure/ordering bugs; race conditions. For "
    "each issue give file:line, what's wrong, why it matters, and a confidence anchor "
    "(0/25/50/75/100).",
}

LENS_HEADER = "PR: {pr_title}\n\n```diff\n{diff}\n```\n\nList each distinct real issue you find (one per item, with file:line if identifiable). Only report issues you are confident about; categorize each P0 (critical breakage/data loss), P1 (high-impact defect), P2 (moderate), or P3 (low). Do not report style nits."

# The severity scale + confidence anchors, from references/action-class-rubric.md + findings-schema.json.
METHODOLOGY_SYSTEM = ("You are an expert code reviewer using the Compound Engineering ce-code-review "
                      "methodology. Severity: P0=critical breakage/exploitable/data loss; P1=high-impact "
                      "defect likely hit in normal usage; P2=moderate; P3=low. Confidence anchors: "
                      "100=verifiable from code alone; 75=double-checked, will affect users/callers; "
                      "50=real but may be a nitpick; 25=might be a FP; 0=not confident. Do not report "
                      "style preferences or missing optimizations that don't affect correctness.")


def _truncate(diff: str, max_chars: int = 60000) -> str:
    if len(diff) <= max_chars:
        return diff
    return diff[:max_chars] + f"\n\n[... diff truncated: {len(diff) - max_chars} more chars ...]"


# ---- persona selection (references/select-and-route.md) ----

def _select_personas(pr: PRSample) -> list[str]:
    """Select the risk-driven persona roster per references/select-and-route.md.

    `correctness` is always-on. The conditionals are selected by reading the diff for concrete
    signals (not keyword matching). We use a lightweight heuristic over the diff + file list
    that mirrors the catalog's spawn gates; the orchestrator in a real run does this with agent
    judgment, but the api-direct column isolates methodology so a deterministic selection is the
    faithful approximation.
    """
    selected = ["correctness"]
    diff = pr.diff or ""
    dlow = diff.lower()
    files = " ".join(f.get("filename", "") for f in pr.files).lower()
    # security: auth, public endpoints, user input, permissions, secrets
    if re.search(r"\b(auth|login|password|token|secret|permission|rbac|acl|session|cookie|jwt|csrf|xss|inject)\b",
                 dlow) or any("auth" in f or "login" in f for f in (files.split())):
        selected.append("security")
    # performance: db queries, transforms, caching, loops
    if re.search(r"\b(select|query|find_each|to_a|materialize|cache|loop|for\s|while\s|map\(|batch)\b", dlow):
        selected.append("performance")
    # api-contract: routes, serializers, schemas, versioning
    if re.search(r"\b(route|router|endpoint|controller|serializer|schema|api/v|response|request)\b", dlow):
        selected.append("api-contract")
    # reliability: error handling, retries, timeouts, background jobs
    if re.search(r"\b(try|catch|raise|throw|retry|timeout|rescue|background|async|await|promise|future)\b", dlow):
        selected.append("reliability")
    # testing: test files or behavioral change without test work
    test_files = [f for f in (files.split()) if "test" in f or "spec" in f or f.endswith(".test.ts")
                  or f.endswith("_test.go") or f.endswith("_test.py") or f.endswith("_spec.rb")]
    if test_files:
        selected.append("testing")
    # maintainability: large or structural diff (>=200 changed lines proxy)
    changed_lines = sum(f.get("additions", 0) + f.get("deletions", 0) for f in pr.files)
    if changed_lines >= 200:
        selected.append("maintainability")
    # data-migration: migration/schema artifacts
    if re.search(r"\b(db/migrate|schema\.rb|structure\.sql|alembic|flyway|liquibase|migration|backfill)\b", files):
        selected.append("data-migration")
    # adversarial: >=50 changed code lines, auth/payments/persistence/event/external-api/concurrency,
    # or a silent-pass verification mechanism (CI/gate). The adversarial lens is the default-risk
    # reviewer for any non-trivial change; include it when the diff has substance.
    if changed_lines >= 50 or any(p in selected for p in ("security", "data-migration")) or \
       re.search(r"\b(ci|workflow|gate|check|deploy|build)\b", files):
        selected.append("adversarial")
    # dedup preserving order
    seen = set(); out = []
    for p in selected:
        if p not in seen:
            seen.add(p); out.append(p)
    return out


# ---- LLM personas (API-direct) ----

async def _run_persona(model: str, persona: str, prompt_body: str, effort: str = "medium") -> tuple[str, int, int, dict]:
    prompt = f"{PERSONA_PROMPTS[persona]}\n\n{prompt_body}"
    from harnesseval.model_router import call_model
    max_tok = 4096 if effort == "xhigh" else 2048
    return await call_model(model, system=METHODOLOGY_SYSTEM, user=prompt, effort=effort, max_tokens=max_tok)


async def _run_all_personas(model: str, pr: PRSample, effort: str = "medium"
                            ) -> tuple[list[Finding], int, int, list[str], dict]:
    from harnesseval.usage import merge, grand_total
    personas = _select_personas(pr)
    body = LENS_HEADER.format(pr_title=pr.pr_title, diff=_truncate(pr.diff))
    sem = asyncio.Semaphore(5)
    async def bounded(p):
        async with sem:
            return await _run_persona(model, p, body, effort=effort)
    results = await asyncio.gather(*[bounded(p) for p in personas])
    findings: list[Finding] = []
    tin = tout = 0
    raws: list[str] = []
    per_model: dict = {}
    from harnesseval.model_router import call_model_json
    from harnesseval.extract import EXTRACT_PROMPT, EXTRACT_SYSTEM
    for (persona, (text, i, o, pmu)) in zip(personas, results):
        tin += i; tout += o; raws.append(f"## {persona}\n{text}")
        per_model = merge(per_model, pmu)
        parsed, pi, po, pmu_ext = await call_model_json(model, EXTRACT_SYSTEM, EXTRACT_PROMPT.format(comment=text),
                                               effort=effort, max_tokens=1024)
        tin += pi; tout += po; per_model = merge(per_model, pmu_ext)
        for issue in parsed.get("issues", []):
            findings.append(Finding(issue_text=issue, source=f"compound-persona/{persona}", raw=text[:500]))
    return findings, tin, tout, raws, per_model


async def review_async(pr: PRSample, model: str, effort: str = "medium",
                       mode: str = "api") -> ReviewRun:
    """Async core — safe inside a running event loop.

    mode: 'api' (paid, clean, methodology-only) | 'cli' (OAuth, free, realistic host-scaffolding
    tax). Records execution_mode. For the real-plugin realistic column use
    compound_realistic.review_realistic_async (drives a real host session with the plugin).
    """
    name = "compound"
    t0 = time.time()
    try:
        lens_findings, tin, tout, lens_raws, per_model = await _run_all_personas(model, pr, effort=effort)
    except Exception as e:  # noqa: BLE001
        return ReviewRun(framework=name, model=model, effort=effort, execution_mode=mode,
                         raw_output="", wall_ms=(time.time() - t0) * 1000, error=str(e))
    raw = f"# Compound ce-code-review ({model})\nSelected personas: {', '.join(_select_personas(pr))}\n\n" + \
          "\n\n".join(lens_raws)
    from harnesseval.usage import grand_total
    gt = grand_total(per_model)
    return ReviewRun(framework=name, model=model, effort=effort, execution_mode=mode,
                     raw_output=raw, findings=lens_findings, tokens_in=tin, tokens_out=tout,
                     wall_ms=(time.time() - t0) * 1000, per_model_usage=per_model,
                     total_cost_usd=gt["total_cost_usd"])


def review(pr: PRSample, model: str, effort: str = "medium", mode: str = "api") -> ReviewRun:
    """Sync wrapper (top-level use). mode: 'api' | 'cli'."""
    return asyncio.run(review_async(pr, model, effort, mode))
