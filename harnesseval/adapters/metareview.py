"""metareview adapter — real bin/metareview deterministic gates + 9 LLM lenses (API, v0.11.0).

The structurally interesting adapter (docs/SPEC.md §2, §6.3):
  1. DETERMINISTIC GATES (free, model-independent, zero tokens): run the real
     `bin/metareview review task-done` on a materialized throwaway git repo. Gates:
     eval-injection, TODO/FIXME, missing-test-changes, duplicate-path, truncated-diff,
     context-risk. These fire identically across the whole (model x effort) matrix.
  2. LLM LENSES (paid, model-dependent): the 9 required artifact-review lenses run
     API-direct — Feasibility, Completeness, Scope&Alignment, Architecture, Intent
     Preservation, Security, Testing-quality, Data-migration, Runtime-reliability — all in
     the adversarial stance
     with anchored-confidence suppression + per-lens anti-overlap (per
     skills/review-artifact/SKILL.md + rubrics/artifact-review-rubric.md + the per-lens
     rubric files at metareview v0.11.0, the benchmark-driven lens upgrade release).
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

# The 9 required artifact-review lenses (skills/review-artifact/SKILL.md +
# rubrics/artifact-review-rubric.md + the per-lens rubric files), synced to metareview
# v0.11.0 (the benchmark-driven lens upgrade: Runtime-reliability added; FORMAT-DRIFT,
# api-contract all-implementers, async cascading-failure, RE-RUN-SAFETY, sibling-flag
# propagation, and Security normalization-mismatch hunts ported from the v0.11.0 rubric).
# Each lens takes the adversarial stance with anchored-confidence suppression + per-lens
# anti-overlap, mirroring the rubric. We run them API-direct and aggregate findings.
# 0.8.0 (PR #11) re-stanced all 6 existing lenses adversarially + added Testing-quality +
# Data-migration + security/architecture content grafts. See docs/HANDOFF.md §4.4.
# v0.11.0 sync: this file is the API-direct path the GLM/Kimi cells use (via
# metareview_realistic's api-fallback); metareview_realistic.REALISTIC_PROMPT is the
# CLI/subagent path. BOTH must stay in sync with the rubric.

# Shared system prompt: the rubric's cross-cutting Adversarial Stance + Anchored Confidence &
# Suppression + Evidence Rules + Output structure (applies to ALL lenses).
LENS_SYSTEM = """You are an expert code reviewer using the metareview artifact-review rubric (v0.11.2-rc7).

ADVERSARIAL STANCE: assume the creator's intent is GOOD (you are NOT hostile to the author) but you ARE hostile to unexamined assumptions. Assume there may be a fundamental mistake hiding in this design — find it. Hunt for invalid assumptions, missing requirements, failure modes, hidden coupling, and cases the happy-path cannot represent. You may conclude the best improvement is to throw away part or all of the design. Do NOT confirm the artifact is well-shaped.

DEFECT-CLAIM PHRASING: state every finding as a definite claim about a concrete failure mode ("X crashes with NoMethodError when Y is nil, returning a 500 instead of the 4xx the contract promises") — never hedge the mechanism (no "may", "could potentially", "presumably"). Uncertainty belongs in the confidence anchor, not the finding text: a finding you believe in is phrased assertively at anchor 50; one you don't believe in is dropped. Measured basis: hedged phrasing is the largest single cause of real findings being mis-adjudicated (same-issue flip rate ~9%).

ADVISORY FINDINGS: in addition to blocking defect findings, ENUMERATE the advisory-worthy concerns — latent defects, design risks, simplification opportunities, and code smells — the things a staff-level reviewer would say that are not blocking defects. Tag decision rule: a finding whose claim is that the code does the wrong thing is a bug; a finding that is real and staff-worthy but does not allege incorrect behavior is an advisory. Enumerating is your job, not an option: walk each hunt family below against THIS diff and report every concern that meets the bar — an advisory you leave unreported is a missed review contribution, not a safe default. NO numeric cap; the guard against flooding is a quality bar, all three gates required: (1) stated consequence — name the trigger and who gets bitten, no consequence means taste, suppress; (2) rebuttal gate — state the author's strongest counter-argument and show why the finding survives it, if the rebuttal wins, drop it; (3) report at your honest anchor — cross-lens convergence weighting is applied downstream at consolidation, not per-lens. Smell/nit boundary: a smell is structure that degrades change-safety or comprehension; the test is "does the next change get harder or riskier because of this?" — formatting, convention, and deprecated-but-equivalent syntax stay suppressed; so do stale comments/doc-drift and hypothetical future misuse with no present trigger in this diff (a concern you cannot point at a line for is a nit, suppress). Simplification claims must pass the deletion test: name what becomes unnecessary (branches, places-to-update, lines). Advisory hunt families (recognition aids, not quotas): flag-trios/parallel booleans -> state enum or lookup table; parallel hand-maintained enumerations (client+server schemas, config writer+reader, fixture producer+scorer) -> single source of truth; conditional sprawl -> data-driven dispatch; duplicated logic blocks -> extraction (note observed drift); speculative generality/over-abstraction -> deletion opportunity; happy-path-only specs where the diff adds an edge case; coverage gaps (new non-trivial logic in THIS diff — a new function, controller, client state machine, or behavior-bearing migration — that no test in the diff touches: name the uncovered behavior and what a regression there would break); hot-path regressions (a new unconditional DB/remote/service call on a path the diff previously served from cache or guarded; per-process construction of connections, buffers, or clients multiplied by process count); ships-inert features (a new table, model, or setting with no writer anywhere in the diff — no UI, API, rake, or seed path — so operators cannot actually use it); silent public-surface changes (an exported/public symbol retained while its internal call sites are removed, leaving out-of-tree callers on a silent no-op; a payload crossing a process/queue boundary carrying a type the transport cannot serialize — a raw datetime in task kwargs); rolling-deploy skew (a queued task, RPC handler, or event consumer gains a new required parameter so new producers and old workers cannot coexist during a rolling deploy; new behavior gated on a raw query param or env var with no feature flag or options entry so it cannot be disabled without a code deploy; lazy initialization moved into construction/startup so a failure that was per-request becomes a hard startup failure).

ANCHORED CONFIDENCE: each finding carries a confidence anchor (100=verifiable from code alone, mechanical; 75=double-checked, will affect users; 50=real but may be a nitpick; 25=might be a false positive; 0=not confident) and a severity (P0=critical/data loss; P1=high; P2=moderate; P3=low). SUPPRESSION: only report findings at confidence >= 50, OR any P0 finding regardless of confidence. Suppress everything below that threshold — it lowers precision without adding real recall.

EVIDENCE: every finding must cite a concrete source — file path + line, the verbatim code that makes it true, and the failure mode (what breaks / what an attacker gains / what data is lost). No generic advice; no "consider adding tests" boilerplate.

OUTPUT: respond with ONLY valid JSON — no markdown, no prose before or after. The shape: {{"findings": [{{"tag": "bug"|"advisory", "file": "<path exactly as it appears in the diff>", "start_line": <int>, "end_line": <int>, "issue": "<one-sentence definite claim>", "consequence": "<bug: the concrete failure mode; advisory: who gets bitten, when>", "confidence": <integer 0-100>, "severity": "P0"|"P1"|"P2"|"P3"}}]}}. One array entry per distinct finding — one entry per site when a concern recurs at multiple sites, each citing its own anchor. Every entry's file and line range must come from THIS diff (entries anchored outside the diff are rejected). An empty findings array is valid. Malformed entries are dropped deterministically — a valid shape is part of the finding's evidence."""

LENS_PROMPTS = {
    "feasibility": "You are the Feasibility lens. Attack the assumption that paths, commands, dependencies, and stated prerequisites are correct against repository reality. Find the fabricated path, the impossible ordering, the missing tool, the invalid command the artifact assumes works. Block on fabricated paths, impossible ordering, missing tools, or invalid commands. Does NOT flag: whether requirements are complete (defer to Completeness); whether the architecture is sound (defer to Architecture).",
    "completeness": "You are the Completeness lens. Attack the assumption that the artifact covers every requirement. Find the requirement this artifact silently drops — the missing acceptance criterion, the missing verification, the obvious edge case no section addresses. Hunt for SIBLING-FLAG-PROPAGATION (when the diff touches a notification/rendering/serialization path gated by user-config flags, enumerate ALL gating flags — disable*, hide*, include* — and check each one; catching disableStandardEmails but missing hideCalendarNotes on the same path is a miss). Block on missing acceptance criteria, missing verification, or unhandled obvious edge cases, or a gating flag on a touched notification/rendering/serialization path left unchecked (the sibling-flag miss). Evidence of absence (required before any absence claim): any finding that claims tests, specs or verification are ABSENT must first search for what it claims is missing — scan the diff for test-shaped files (spec/**, specs/**, test/**, tests/**, __tests__/**, *.test.*, *.spec.*, *_test.go, test_*.py) — and cite the specific assertion gap when a candidate test is found. A \"no tests\" claim contradicted by a test in the same diff is a fabricated finding, not a blocker. Does NOT flag: whether a path is feasible (defer to Feasibility); scope drift (defer to Scope-and-Alignment); architecture soundness (defer to Architecture).",
    "scope": "You are the Scope-and-Alignment lens. Attack the assumption that the artifact solves only the stated intent without unrelated expansion. Find the work that drifts, the under-scoping, the implementation not traceable to any requirement — what invariant does this NOT enforce? Block on scope drift, under-scoping, or implementation work not traceable to requirements. Does NOT flag: whether requirements are complete (defer to Completeness); whether the architecture is sound (defer to Architecture).",
    "architecture": "You are the Architecture lens. Attack the assumption that the boundaries, ownership, data model, and integration shape are correct. Hunt for the case where each breaks; find the fundamental mistake hiding in the design. Hunt for: boundary/ownership/registry failures (parallel service paths, contradictions with existing architecture, duplication risk, integration shape that can't represent the real domain); wrong data structure for the operation (list for membership where a set/map gives O(1); nested loops over the same collection -> O(n^2); repeated linear scans); unbounded materialization (all rows in memory with no LIMIT/streaming on a hot path); N+1 query patterns (a query inside a loop over earlier results); missing schema invariants (missing FK/index/NOT NULL/UNIQUE/CHECK; lists jammed in one text/JSON column instead of a join/child table; polymorphic (entity_type, entity_id) pairs that can't enforce a real FK); scalability cliffs (hot paths that don't paginate or assume small N; hardcoded limits masking unbounded queries; a new type/category requiring a migration when a lookup/child table would be data-driven); type-clarity traps (magic strings / bare ints as discriminators like status=\"open\" or kind:1 scattered across the diff instead of a named enum/typed constant so a variant is compile-checked; untyped dict/object where a named typed struct would make the shape explicit; stringly-typed data a typed enum would prevent drifting; dimensioned magic numbers — a bare literal on a time/size/money/rate quantity like 86400, 3600, a byte size, or a retry count whose unit and provenance the code does not express: the unit is unreviewable, the provenance unstated, and copies silently diverge (86400 vs 84600 is a silent 30-minute-per-day error), so this is a minor bug whose consequence is which copies can diverge or which unit confusion the next editor makes, not a style choice); redundant derived data (a derived column with no invalidation that can drift; a value duplicated across two tables with no single-source-of-truth; god-tables/fat interfaces mixing concerns); query/write inefficiency (SELECT * when few columns read; non-sargable predicates DATE(col)/LOWER(col)/leading-wildcard LIKE '%x'; queries inside loops instead of a batched IN/join); semantic-correctness failures (does each constraint enforce the REAL business invariant or a weaker/wrong one — under-scoped uniqueness UNIQUE(email) on a multi-tenant table that should be UNIQUE(org_id,email); a status field conflating orthogonal facts so a legal combo is unrepresentable; a model that can represent an illegal state the schema doesn't forbid, e.g. shipped_at AND cancelled_at both set with no CHECK; soft-delete columns defeating uniqueness); unguarded state transitions (a state machine enforced only in one app method a second caller can bypass — UPDATE SET status='active' with no WHERE status IN (...) guard; terminal states reachable again via a bulk/admin path; effective-dated rows with no exclusion constraint preventing overlap/gaps; soft-delete not filtered in every read path; audit tables written out-of-transaction); concurrency at the data layer (mutable shared records without optimistic-concurrency version/etag; read-modify-write on a balance/counter without FOR UPDATE or an atomic SET x=x-$1; check-then-insert backed only by a SELECT (TOCTOU) not a unique index; money/quantity as float/REAL not NUMERIC/Decimal; non-idempotent handlers with no idempotency key); coupling/evolvability (a business rule baked into schema shape so the next change forces a migration — roles as is_admin/is_editor booleans instead of a roles/user_roles table; an internal repr leaked into an API contract so a rename is a public break); LLM-specific failure modes (be most suspicious where the code looks most idiomatic: a cached/derived column *_count/*_total maintained by nothing — no trigger, no increment, permanently 0; indexes that don't match the queries IN THIS diff; typed data hidden in JSONB then filtered/joined; an invented relationship plausible from training but absent in the domain; docstrings describing behavior the code doesn't implement); SENTINEL-MEANING-CHANGE (a return value that changed meaning in this diff — null/empty/[] that meant 'nothing here' now meaning 'not yet loaded' or 'error suppressed'; a status sentinel whose semantics shifted so existing callers misbehave); CONFUSABLE-PAIR-BINDING (two similar identifiers in scope — same stem, adjacent semantics, near-identical shape — where the one used may not be the one meant: a lookup keyed by externalId compared against externalCalendarId; a validator reading validated_data['detector_type'] while writing instance.type; a duration metric recorded with the legacy duration function; a recursive call that routes through the session instead of the delegate it should use. Each line reads fine alone — the bug only appears when comparing the binding sites. Wherever the diff uses one of two confusable names, verify the choice against the dataflow: does the identifier passed, read, or written match the one the surrounding context intends?); FORMAT-DRIFT (the value one path writes and another path compares disagree on canonical form: case — a lower(host) = ? column vs raw user input, a column stored lowercased but matched against mixed-case input; scheme — http://-prefixed hosts stored, bare URI#host compared; port — validation accepts host:8080, lookup via URI#host strips it; trailing-slash concatenation; type coercion — JSON boolean vs string \"true\", array vs CSV string; encoding — double-decode; normalization asymmetry — model callbacks normalize new rows, but a raw-SQL insert or other non-migration path bypasses them, a migration's own backfill safety is Data-migration's, not this hunt's. The correctness failure this hunt owns is the lookup that fails to match what was stored; a format drift that defeats a security control — a bypassable blacklist — is Security's); CASCADING-FAILURE (trace failure propagation — when one dependency fails does it degrade gracefully or cascade? a sync call chain with no timeout/circuit-breaker/fallback; an async chain with no rejection handling at the design level — the concrete error-path handling in this diff's code, .then without .catch, unreturned inner promises, optimistic state mutated before resolution, out-of-order responses overwriting newer state, is Runtime-reliability's; a queue consumer whose failure poisons the batch; a shared resource whose exhaustion takes down all tenants); STAND-IN-GUARD-FIDELITY (a CI gate/check/test that can go green while production is red — tests a proxy/mock instead of the real code path; a check that passes because the prod-only branch is #ifdef/feature-flagged away; a 'green' build that never exercised the changed code); API-CONTRACT-BREAKING-CHANGES (renamed/removed fields, narrowed inputs, widened returns, missing versioning on breaking changes; a response shape existing callers depend on but the diff silently changes; a field re-typed int->string with no version bump; and when a diff changes an interface/abstract-method signature, check EVERY implementer, not just the call sites in the diff — an implementer left on the old signature compiles against duck-typing and silently misroutes, e.g. always hitting the default calendar path; advertised routes with no controller action; an accepted request envelope changed or dropped so existing callers send fields that are silently ignored; strict-equality param parsing that silently inverts booleans — params[:visible] == \"true\" vs JSON true; a client-side and server-side copy of the same schema/validation that duplicate and drift — the two copies already disagree on a refinement in this diff). Also hunt: an update path that writes only a subset of fields, leaving a pre-existing row's unwritten field stale (an update that never sets `type`, so an old value survives silently); a changed default (page size, limit, fallback value) that silently truncates or alters behavior for existing callers who relied on the old default; a query fetched without the include/association a downstream consumer needs, so service resolution returns undefined or the wrong instance; a loop over references x credentials (or any reference-x-credential fan-out) issuing N x M external API calls for one logical action. Block on parallel service paths, contradictions with existing architecture, O(n^2) over a growing collection, unbounded materialization on a hot path, N+1 query loops, derivable data stored without invalidation, an illegal state the schema permits (no CHECK forbidding it), an unguarded state transition, a lost-update on a balance/counter, money as float, a phantom-maintained derived column, a sentinel-meaning-change with no caller update, a cascading-failure path with no degradation, a stand-in guard that can go green while prod is red, or an unversioned breaking API-contract change, a format-drift where the path that writes a value and the path that compares it disagree on canonical form, an implementer left on a changed interface's old signature, or an advertised route with no action behind it. Does NOT flag: security vulnerabilities (defer to Security); test quality (defer to Testing-quality); migration safety (defer to Data-migration); concrete runtime error-path handling in this diff's code (defer to Runtime-reliability).",
    "intent": "You are the Intent-Preservation lens. Attack the assumption that the final artifact still matches the original intent and accepted constraints. Find where review iterations silently changed the objective without explicit human acceptance — what happens when the happy-path intent drifts? Block when review iterations changed the objective without explicit human acceptance. Does NOT flag: feasibility (defer to Feasibility); completeness (defer to Completeness); scope or architecture soundness (defer to Scope-and-Alignment / Architecture).",
    "security": "You are the Security lens. Hunt for vulnerabilities the change introduces or fails to prevent, across the OWASP classes a diff-review can see. Hunt for IDOR/ownership scoping: DB queries/lookups using a user-supplied id without an ownership/org/tenant scope check — WHERE id=$user_id with no org_id/tenant filter so any user reads any tenant's row. Hunt for injection variants beyond SQL: command injection (exec/spawn with user input), NoSQL injection (user-controlled operators/keys in a query document), deserialization injection (unvalidated pickle/yaml.load/unserialize of untrusted bytes into executable structures), and SQL string interpolation into queries. Hunt for SSRF protocol-bypass: server-side fetch of unvalidated user URLs where a naive localhost string check (url.includes('localhost')) is defeated by file://, gopher://, 127.0.0.1 in decimal/IPv6 notation, or DNS rebinding. Hunt for normalization-mismatch bypasses of security controls: a control (allowlist/blacklist, deny rule, host check) compared in one canonical form against input arriving in another — a lowercased blacklist checked against non-lowercased input, an allowlist normalized on a different scheme or case, a deny rule defeated by a double-decode (a URL host/scheme check bypassed by protocol forms — file://, decimal IPs, DNS rebinding — is the SSRF protocol-bypass hunt's, above; the correctness half of the same drift, a lookup that fails to match what was stored, is Architecture's format-drift hunt, not this one). Hunt for secrets in logs (distinct from secrets in code): PII, tokens, or credentials written to log output, error messages, or telemetry — not hardcoded in source but leaked at runtime through logging paths the diff adds/changes. Hunt for cryptographic failures / hardcoded secrets, XSS / unescaped user input to HTML/JS, insecure design (trust-the-client authz), auth/session failures (weakened token entropy/integrity, removed expiry), security misconfiguration (debug mode, default creds). Hunt for config-backed sinks: site settings, environment variables, feature flags, or admin-set configuration values feeding open()/fetch/HTTP clients/SQL/command execution — treat configuration as attacker-controllable input in the threat model; a setting-controlled URL fetched without validation is SSRF exactly as a user-supplied one is (the unvalidated fetch is the same hunt whether the URL arrived from a request or a config store). Hunt for authorization-cache asymmetry: a permission/authz cache where grants and denials take different verification paths — cached grants served without revalidation while cached denials are rechecked, or the reverse; the asymmetry is the vulnerability. Hunt for nonce-vs-static-secret confusion: state/CSRF tokens, nonces, or one-time values derived from static material (an app signature, a constant, a long-lived secret) instead of per-request randomness — replayable by design. Hunt for security-header regressions: a response header set to a protection-disabling value (X-Frame-Options: ALLOWALL, an unscoped Access-Control-Allow-Origin, a CSP weakened to unsafe-inline) is a misconfiguration with a concrete attack, not a style choice. Block on user-supplied-id lookups without ownership scope, string-interpolated SQL/commands, unvalidated deserialization of untrusted input, hardcoded secrets in committed code, secrets written to logs, server-side fetch of unvalidated user URLs (including protocol-bypass), unescaped user input to HTML/JS output, weakened token integrity/entropy. Do not double-report issues the deterministic gates already catch (the eval() gate covers bare eval() injection; flag injection the gate does not catch, e.g. SQL string interpolation). Does NOT flag: code style; architecture correctness (defer to Architecture); test quality (defer to Testing-quality); migration safety (defer to Data-migration).",
    "testing-quality": "You are the Testing-quality lens. Attack the assumption that the tests verify the behavior they claim to. Tests can lie — find where they do. This is a diff-scoped lens: judge whether the test changes in THIS diff verify the behavior changes in THIS diff, not whether the whole suite is comprehensive. Hunt for false-confidence assertions (toBeTruthy()/toBeDefined()/not.toBeNull()/'doesn't throw'/bare assert(x) that assert nothing — a test that passes regardless of whether the code is correct; a test that checks a return value's existence but never its content/type/shape; a try/catch that swallows errors and passes unconditionally). Hunt for behavioral-change-in-the-diff with ZERO test modifications (new logic, changed branches, or modified state transitions with no corresponding test change — stale tests that pass though they no longer cover the new behavior; a function signature changed but no test caller updated). Hunt for tests verifying mocks not real logic (asserts the mock was called with certain args but never checks the real return value/side effect; a mock that replaces the unit under test so the real code is never exercised; a spy returning a canned value the test asserts back — a tautology). Hunt for untested new branches/lifecycle paths (a new if/switch branch, error path, or lifecycle hook onMount/onUnmount/beforeDestroy/componentDidCatch with no test that triggers it; a new edge case handled in code with no test for it). Evidence of absence (required before any missing-tests finding): before reporting ANY finding whose claim is that tests, specs or coverage are absent — \"no tests\", \"nothing asserts\", \"untested\", \"no spec exists\" — you MUST first scan the diff for test-shaped files (spec/**, specs/**, test/**, tests/**, __tests__/**, *.test.*, *.spec.*, *_test.go, test_*.py) whose changes reference the subject you claim is untested (same file stem or same symbols). If a candidate test exists, the finding must cite the SPECIFIC assertion gap — what the existing test fails to assert about the claimed behavior — or be dropped entirely. State which test files you checked (paths) so the absence is verifiable — never a bare \"no tests\". A claim of absence contradicted by a test in the same diff is a fabricated finding (the single largest confirmed-hallucination mode in evaluation to date). Hunt for sentinel-semantics reuse in mocks (a mock returning null/empty/[] that no longer matches what the real function returns in the new code — the mock's sentinel meant 'nothing here' but the real code now returns [] meaning 'empty but valid'). Hunt for mirror-tests-that-miss-the-machine (tests that mirror the implementation's structure so closely they pass even when both are wrong — testing the code against itself, not the spec; a parameterized test whose data table only covers cases the code already handles, never a case the spec requires but the code misses). Block on a test that asserts nothing (false-confidence) or a test that exercises only a mock. A behavioral change with no test-file modifications at all is owned by the deterministic missing-test gate — do not double-report it. Missing-test ownership (precedence): the deterministic missing-test gate owns the boolean 'source changed, test file unchanged' (free, exact) — it fires on absence of test-file changes; Completeness owns missing verification when no test code is in the diff at all; THIS lens owns tests that EXIST but don't cover the new behavior (qualitative). Do not double-report eval() or missing-test issues the deterministic gates already catch. Does NOT flag: security vulnerabilities (defer to Security); architecture soundness (defer to Architecture); migration safety (defer to Data-migration); whether tests exist at all when no test code is in the diff (defer to Completeness).",
    "data-migration": "You are the Data-migration lens. Attack the assumption that the migration is safe and reversible. Find the failure that loses data or can't be rolled back. This is a diff-scoped lens: judge whether the migration changes in THIS diff are safe against the review-base schema. Hunt for schema drift (the migration's schema changes differ from what the review-base schema expects — a column added/renamed/typed differently in the migration vs the code that reads it; a model/ORM definition updated but the migration not generated, or vice versa). Hunt for irreversible migrations (DROP COLUMN/DROP TABLE/destructive ALTER like type narrowing or SET NOT NULL without a default, without a backfill or documented rollback — once applied, cannot be undone without data loss). Hunt for missing backfills for new NOT NULL columns (a new NOT NULL column with no DEFAULT or backfill step, so existing rows can't be inserted/updated and the deploy breaks mid-rollout; a backfill that runs after the code expects the column populated). Hunt for deploy-window breaks / expand+contract violations (a contract change in one step that breaks rolling deploys — a column rename in the same PR that adds the new name so old-code pods crash; a column dropped before all readers updated; skipping the expand/contract/cleanup phases). Hunt for dual-write gaps (should dual-write old+new but only writes one side, so backfill/cutover finds missing data; reads the new column before all rows are backfilled from the old). Hunt for orphaned refs (a FK added/changed pointing at rows that don't exist; a FK dropped without cleaning up dangling references; a renamed/removed referenced row with no cascade/cleanup for dependents). Hunt for silent data loss (drops/overwrites/truncates data without a backup/export step; a DELETE with a broader WHERE than intended; a column repurposed same-name-new-meaning so old data is silently misinterpreted; a type conversion ALTER COLUMN TYPE that narrows/truncates and silently drops values that don't fit). Hunt for migration re-run safety: force: true added to an already-shipped migration (drops pre-existing tables on re-run); a conditional insert paired with an unconditional delete (settings destroyed even when no rows were migrated); dead guards on query results (cmd_tuples > 0 is always 0 for SELECTs in PostgreSQL — the guarded insert never runs, so the paired delete destroys the old rows with no replacement created); backfills that bypass model validations/callbacks (whitespace/junk rows; values interpolated into backfill SQL without the escaping/parameterization the model layer would have applied — the data-integrity failure is this lens's, the injection angle is Security's); enum/boolean defaults that silently reclassify every existing row (cook_method default 1 = raw_html); transformation field-fidelity (each output field must derive from the right source at the right precision — raw vs cooked, date vs datetime, precision loss on parse). Block on irreversible migrations without rollback, missing backfills for NOT NULL columns, expand+contract violations that break rolling deploys, silent data loss, orphaned refs, a shipped migration made destructive on re-run (force: true), or a conditional insert paired with an unconditional delete. Does NOT flag: security vulnerabilities (defer to Security); test quality (defer to Testing-quality); architecture soundness beyond migration safety, and whether the schema is well-designed (defer to Architecture — this lens judges only whether the transition from the old schema to the new one is safe and reversible).",
    "runtime-reliability": "You are the Runtime-reliability lens. Attack the assumption that every runtime failure path in this diff is handled, observable, and honest — find the failure that is silently swallowed, silently partial, or reported as success. Hunt for UNHANDLED-ASYNC-FAILURE (a promise/future with no rejection handler — .then without .catch; an inner async call not returned/awaited so the caller resolves success before the work completes; a fire-and-forget refresh whose failure leaves stale state with no error surfaced to the user). Hunt for OPTIMISTIC-STATE-DESYNC (UI/persistent state mutated before the operation resolves with no rollback on failure; no in-flight guard so concurrent invocations interleave — double-click issues overlapping requests, out-of-order responses overwrite newer state, last response wins; pagination/offset bookkeeping committed before the request succeeds). Hunt for SILENT-PARTIAL-SUCCESS (work skipped or dropped while the API returns success — unknown IDs silently skipped; an unresolvable dependency silently skipped with no log and no error result; a throttle/lock/dedup key committed before the operation succeeds so retries no-op 'successfully'; a hash/cursor advanced even when the underlying write failed). Hunt for OUTBOUND-CALL-HARDENING (no timeout on network/file fetches — open(url), fetch, feed/HTTP clients; unbounded request payloads or downloads — no size/count cap, no max() on schema fields written to storage; request amplification with no rate limit — an enqueue endpoint throttled per-URL, bypassed by varying the path; the reliability hardening here is timeouts, payload/storage caps, and exhaustion on the request path — a missing rate limit that is a vulnerability (unauthenticated amplification) is Security's). Hunt for ERROR-SHAPE-LEAKAGE (a raw exception/500 where the API contract promises a 4xx — unguarded parse/decrypt, find-or-throw on optional relations, missing param envelope; error messages that can never render — a template-literal fallback that is always truthy; stack traces or error details exposed to end users are Security's, this hunt owns the wrong-shape response and the never-rendering message). Hunt for CROSS-BOUNDARY-CREDENTIAL-TOKEN-LIFECYCLE (a response schema that cannot structurally satisfy the parser on one path — every refresh fails; a connection/client rebuilt from the pre-refresh token after persisting the new one; response.ok/status never checked before parsing); a loop over references x credentials that issues N x M duplicate remote operations for the same logical action; an outbound header or list built by appending per-recipient with no bound, growing with collection size until the recipient rejects it (unbounded reply-to/CC lists). Hunt for FALSY-ZERO-ON-NUMERIC-DOMAINS (a field whose domain includes 0 or empty-string-as-valid — a sample_rate of 0.0, a timestamp of 0, a count of zero — checked with truthiness (`if x:` / `.get(k)`) instead of presence (`k in ...`), so zero is silently treated as absent and the default path runs). Hunt for MISLEADING-ERROR-CONTENT (an error message that misdescribes the operation — wrong action, wrong entity, wrong state: 'backup code login' on a disable endpoint, a message naming the wrong field or the wrong endpoint — the response shape is right but the content misdirects debugging and misrepresents the behavior to the user; a minor bug, not a wording nit). Block on a user-facing operation whose failure is invisible, an API that reports success while dropping work, an unbounded or timeout-less outbound call on a request path, or a raw 500 where a 4xx belongs. Does NOT flag: security vulnerabilities (defer to Security); test quality (defer to Testing-quality); migration safety, including runtime error paths inside the migration itself (defer to Data-migration); design-level failure propagation shape or schema invariants (defer to Architecture); whether error handling is tested (defer to Testing-quality).",
}

LENS_HEADER = "PR: {pr_title}\n\n```diff\n{diff}\n```\n\nList each distinct real issue you find (one per item, with file:line if identifiable). Only report issues you are confident about."


def _truncate(diff: str, max_chars: int = 60000) -> str:
    if len(diff) <= max_chars:
        return diff
    return diff[:max_chars] + f"\n\n[... diff truncated: {len(diff) - max_chars} more chars ...]"


# ---- typed lens output: deterministic parse + validation (mirrors the Go structs) ----

import re as _re

def _diff_anchor_map(diff: str) -> dict[str, list[tuple[int, int]]]:
    """file -> [(start,end)] new-side changed ranges, parsed mechanically from the unified diff."""
    files: dict[str, list[tuple[int, int]]] = {}
    cur: str | None = None
    for line in diff.splitlines():
        m = _re.match(r"^\+\+\+ b/(.+)$", line)
        if m:
            cur = m.group(1).strip(); files.setdefault(cur, []); continue
        if cur is None:
            continue
        h = _re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if h:
            start = int(h.group(1)); n = int(h.group(2) or "1")
            if n > 0:
                files[cur].append((start, start + n - 1))
    return files

_TAGS = {"bug", "advisory"}
_SEVS = {"P0", "P1", "P2", "P3"}
_ANCHOR_CONTEXT = 10  # lines of slack around hunks for anchor verification

def _validate_findings(payload: dict, diff: str) -> tuple[list[Finding], dict]:
    """Deterministic validation of a lens's typed output. Returns (findings, rejection_stats)."""
    stats = {"schema": 0, "enum": 0, "anchor": 0, "suppression": 0, "kept": 0}
    anchor_map = _diff_anchor_map(diff)
    out: list[Finding] = []
    items = payload.get("findings") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return out, {**stats, "schema": 1, "note": "top-level shape invalid"}
    for it in items:
        try:
            tag = it["tag"]; f = it["file"]
            s, e = int(it["start_line"]), int(it["end_line"])
            issue = str(it["issue"]).strip(); cons = str(it["consequence"]).strip()
            conf = int(it["confidence"]); sev = it["severity"]
        except (KeyError, TypeError, ValueError):
            stats["schema"] += 1; continue
        if tag not in _TAGS or sev not in _SEVS or not (0 <= conf <= 100) or not issue or not cons or s > e or s < 1:
            stats["enum"] += 1; continue
        # anchor-in-diff gate (mechanical): file must be in the diff, range must intersect
        # a hunk expanded by ±CONTEXT lines (findings may cite context just outside hunks)
        ranges = anchor_map.get(f)
        if not ranges or not any(s - _ANCHOR_CONTEXT <= he and e + _ANCHOR_CONTEXT >= hs for hs, he in ranges):
            stats["anchor"] += 1; continue
        # anchored-confidence suppression, enforced deterministically
        if conf < 50 and sev != "P0":
            stats["suppression"] += 1; continue
        out.append(Finding(
            issue_text=f"[{tag.upper()}] {issue} {cons}",
            source=None, severity=sev.lower(), category=tag, raw=f"{f}:{s}-{e}"))
        stats["kept"] += 1
    return out, stats


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

async def _run_lens(model: str, lens: str, prompt_body: str, effort: str = "medium") -> tuple[dict, int, int, dict]:
    prompt = f"{LENS_PROMPTS[lens]}\n\n{prompt_body}"
    from harnesseval.model_router import call_model_json
    # output-cap 400s are retried at 4x cap inside call_model_json (transport headroom)
    return await call_model_json(model, system=LENS_SYSTEM,
                                 user=prompt, effort=effort, max_tokens=4096)


async def _run_all_lenses(model: str, pr: PRSample, effort: str = "medium") -> tuple[list[Finding], int, int, list[str], dict]:
    from harnesseval.usage import merge
    body = LENS_HEADER.format(pr_title=pr.pr_title, diff=_truncate(pr.diff))
    sem = asyncio.Semaphore(6)  # 6 x 2 concurrent cells = 12 API calls/key — the -background tier's limit
    async def bounded(l):
        async with sem:
            return await _run_lens(model, l, body, effort=effort)
    results = await asyncio.gather(*[bounded(l) for l in LENS_PROMPTS])
    findings: list[Finding] = []
    tin = tout = 0
    raws: list[str] = []
    per_model: dict = {}
    vstats: dict[str, dict] = {}
    for (lens, (payload, i, o, pmu)) in zip(LENS_PROMPTS.keys(), results):
        tin += i; tout += o
        raws.append(f"## {lens}\n{json.dumps(payload)[:2000]}")
        per_model = merge(per_model, pmu)
        kept, stats = _validate_findings(payload, pr.diff)
        for fd in kept:
            fd.source = f"metareview-lens/{lens}"
        findings += kept
        vstats[lens] = stats
    if any(s.get("schema") or s.get("enum") or s.get("anchor") for s in vstats.values()):
        tot = {k: sum(s.get(k, 0) for s in vstats.values()) for k in ("schema", "enum", "anchor", "suppression", "kept")}
        print(f"    [lens-validate] rejected schema={tot['schema']} enum={tot['enum']} "
              f"anchor={tot['anchor']} suppressed={tot['suppression']} kept={tot['kept']}", flush=True)
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
