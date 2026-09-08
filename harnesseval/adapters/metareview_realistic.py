"""Realistic metareview adapter — drives the real harness as a user runs it (v0.8.2 slim).

v0.8.2 (this branch, mrv-0.8.1-slim-orchestration, evolved): orchestration-slim experiment.
v0.8.1 bundled 4 fixes and showed a token win (opus −35%, codex −24%) but a recall loss
(0.89→0.78, lost the jsforce stale-token golden — needs surrounding-file context the
embedded-diff lenses couldn't read). v0.8.2 DROPS fix #1 (revert: lenses can read files again)
and keeps fixes 2,3,4 (orchestrator: no post-lens re-verification, no skill-ref, be terse).
Hypothesis: capture most of the token win without the recall loss.

Kept fixes (all orchestrator-side, no lens-recall impact):
  2. After the 9 lenses return, consolidate directly — do NOT re-read files / re-run git diff /
     re-verify lens findings (cuts post-lens orchestrator turns).
  3. Drop the "Per the metareview review-artifact skill" reference (skill isn't installed in
     the throwaway repo; the mention triggered a fruitless skill-search on codex).
  4. Be terse — no planning monologue / narration (cuts orchestrator output tokens).

Dropped fix (v0.8.2 reverts this from v0.8.1):
  1. [REVERTED] Embed the diff / forbid lens file-exploration. Cost the jsforce golden —
     lenses need to read surrounding files for some findings. Lenses again get the diff
     context via `git diff {base_ref}..HEAD` and may read surrounding files as needed.

Per docs/SPEC.md §2 (realistic mode): test the harness as a USER uses it. The scoring pipeline
(extract -> judge -> score -> adjudicate) is identical regardless of how the reviewer arm ran.
For the api-direct (pure) column, adapters/metareview.py review() still exists unchanged.
"""

from __future__ import annotations

import asyncio
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from harnesseval import keys
from harnesseval.adapters.base import PRSample, ReviewRun
from harnesseval.dataset.materialize import materialize
from harnesseval.finding import Finding
from harnesseval.cli_backends import session_timeout, codex_slug_for

_DEFAULT_MRV_BIN = Path(__file__).resolve().parents[2] / "bin" / "metareview"
# HARNESS_MRV_BIN: point the SAME adapter at a different metareview binary without swapping
# the vendored 0.8.0-gates binary that batch_083 ran on. Used for version-comparison arms
# (e.g. a 0.10.1 build) -- the LLM-lens prompt stays byte-identical, so only the deterministic
# gate/scaffold binary differs between arms.
MRV_BIN = Path(os.environ.get("HARNESS_MRV_BIN") or _DEFAULT_MRV_BIN)

# v0.8.2 slim-orchestration prompt. The 8-lens adversarial methodology is identical to v0.8.0
# (isolating the orchestration fixes as the only variable); only the orchestration wrapper
# changed (see module docstring). v0.8.2 = fixes 2,3,4 only (fix #1 reverted — lenses keep file access).
REALISTIC_PROMPT = """You are running metareview's task-done review (v0.8.2) on a local change, as a user would.

Be terse. Do NOT narrate your plan, reasoning, or progress — just run the commands, dispatch the lenses, and consolidate. No planning monologues.

Steps:
1. Run this command and read its output (it writes a review scaffold + context pack):
   {mrv_bin} review task-done {task_path} --base {base_ref}
   The command prints the path to the generated review markdown; read that file.
2. Read the review scaffold + context pack it generated.
3. Dispatch the 9 required reviewer lenses as PARALLEL SUBAGENTS via your host's subagent-spawn
   tool — in Claude Code that is the `Agent` tool (one `Agent` call per lens, run in
   background; then collect each result); in Codex that is `collaboration.spawn_agent` (one
   spawn per lens) then `collaboration.wait_agent` to collect each result. Do NOT run the
   lenses in-session; do NOT fall back to a single in-session pass.

   ADVERSARIAL STANCE (applies to ALL 9 lenses): assume the creator's intent is GOOD but be
   hostile to unexamined assumptions — assume there may be a fundamental mistake hiding in
   this design and find it. Do NOT confirm the artifact is well-shaped. Each finding carries
   a confidence anchor (100/75/50/25/0) + severity (P0-P3); SUPPRESS findings below confidence
   50 unless they are P0. Cite file:line + the verbatim code + the failure mode for every finding.

   The 9 lenses (each subagent gets the diff context — run `git diff {base_ref}..HEAD` — + its lens focus):
   - Feasibility: attack the assumption that paths/commands/dependencies are correct against the
     diff reality; block on fabricated paths, impossible ordering, missing tools, invalid commands.
     Does NOT flag: requirements completeness (Completeness) or architecture soundness (Architecture).
   - Completeness: attack the assumption the artifact covers every requirement; block on missing
     acceptance criteria, missing verification, unhandled obvious edge cases. Hunt for
     SIBLING-FLAG-PROPAGATION (when the diff touches a notification/rendering/serialization path
     gated by user-config flags, enumerate ALL gating flags — disable*, hide*, include* — and check
     each one; catching disableStandardEmails but missing hideCalendarNotes on the same path is a
     miss). Does NOT flag:
     feasibility (Feasibility), scope drift (Scope), architecture soundness (Architecture),
     concrete runtime error-path handling in this diff's code (Runtime-reliability).
   - Scope-and-Alignment: attack the assumption the artifact solves only the stated intent without
     unrelated expansion; block on scope drift, under-scoping, work not traceable to requirements.
     Does NOT flag: completeness (Completeness) or architecture soundness (Architecture).
   - Architecture: attack the assumption that boundaries, ownership, data model, and integration
     shape are correct; find the fundamental mistake hiding in the design. Hunt for: wrong data
     structure for the operation (list for membership where set/map is O(1); nested loops -> O(n^2);
     repeated linear scans); unbounded materialization (all rows in memory, no LIMIT/streaming on a
     hot path); N+1 query patterns (query inside a loop over earlier results); missing schema
     invariants (missing FK/index/NOT NULL/UNIQUE/CHECK; lists in one text/JSON column instead of a
     join/child table; polymorphic entity_type/entity_id pairs that can't enforce a real FK);
     scalability cliffs (hot paths that don't paginate or assume small N; new type/category
     requiring a migration when a lookup table would be data-driven); type-clarity traps (magic
     strings/bare ints as discriminators like status="open"/kind:1 scattered across the diff
     instead of a named enum/typed constant; untyped dict/object where a named typed struct would
     make the shape explicit; stringly-typed data a typed enum would prevent drifting); redundant
     derived data (a derived column with no invalidation that can drift; duplicated values across
     two tables; god-tables); query/write inefficiency (SELECT *; non-sargable predicates
     DATE(col)/LOWER(col)/leading-wildcard LIKE '%x'; queries inside loops instead of batched IN/join);
     semantic-correctness failures (does each constraint enforce the REAL business invariant or a
     weaker/wrong one — under-scoped uniqueness UNIQUE(email) on a multi-tenant table that should
     be UNIQUE(org_id,email); a status conflating orthogonal facts so a legal combo is
     unrepresentable; a model that can represent an illegal state the schema doesn't forbid, e.g.
     shipped_at AND cancelled_at both set with no CHECK; soft-delete defeating uniqueness); unguarded
     state transitions (a state machine enforced only in one app method a second caller bypasses —
     UPDATE SET status='active' with no WHERE status IN (...) guard; terminal states reachable
     again; effective-dated rows with no exclusion constraint preventing overlap/gaps; soft-delete not
     filtered in every read path; audit tables out-of-transaction); concurrency at the data layer
     (mutable shared records without optimistic-concurrency version/etag; read-modify-write on a
     balance without FOR UPDATE or atomic SET x=x-$1; check-then-insert backed only by SELECT (TOCTOU)
     not a unique index; money/quantity as float/REAL not NUMERIC/Decimal; non-idempotent handlers
     with no idempotency key); coupling/evolvability (a business rule baked into schema shape so the
     next change forces a migration, e.g. roles as is_admin/is_editor booleans; an internal repr
     leaked into an API contract so a rename is a public break); LLM-specific failure modes (be most
     suspicious where the code looks most idiomatic: a cached/derived column *_count/*_total
     maintained by nothing — no trigger, no increment; indexes that don't match the queries IN THIS
     diff; typed data hidden in JSONB then filtered/joined; an invented relationship plausible from
     training but absent in the domain; docstrings describing behavior the code doesn't implement);
     SENTINEL-MEANING-CHANGE (a return value that changed meaning in this diff — null/empty/[] that
     meant 'nothing here' now meaning 'not yet loaded' or 'error suppressed'; a status sentinel whose
     semantics shifted so existing callers misbehave); FORMAT-DRIFT (the value one path writes and
     another path compares disagree on canonical form: case — a lower(host) column vs raw user input,
     a column stored lowercased but matched against mixed-case input; scheme — http://-prefixed
     hosts stored, bare URI#host compared; port — validation accepts host:8080, lookup via URI#host
     strips it; trailing-slash concatenation; type coercion — JSON boolean vs string "true", array
     vs CSV string; encoding — double-decode; normalization asymmetry — model callbacks normalize new
     rows but a raw-SQL insert or other non-migration path bypasses them, a migration's own backfill
     safety is Data-migration's; the correctness failure this hunt owns is the lookup that fails to
     match what was stored, a drift that defeats a security control is Security's); CASCADING-FAILURE
     (trace failure propagation — when one dependency fails does it degrade gracefully or cascade?
     a sync call chain with no timeout/circuit-breaker/fallback; an async chain with no rejection
     handling at the design level — the concrete error-path handling in this diff's code (.then
     without .catch, unreturned inner promises, optimistic state mutated before resolution,
     out-of-order responses overwriting newer state) is Runtime-reliability's; a queue consumer
     whose failure poisons the batch; a shared resource whose exhaustion takes down all tenants);
     STAND-IN-GUARD-FIDELITY (a CI gate/check/test
     that can go green while production is red — tests a proxy/mock instead of the real code path;
     a check that passes because the prod-only branch is #ifdef/feature-flagged away; a 'green' build
     that never exercised the changed code); API-CONTRACT-BREAKING-CHANGES (renamed/removed fields,
     narrowed inputs, widened returns, missing versioning on breaking changes; a response shape
     existing callers depend on but the diff silently changes; a field re-typed int->string with no
     version bump; and when a diff changes an interface/abstract-method signature, check EVERY
     implementer, not just the call sites in the diff — an implementer left on the old signature
     compiles against duck-typing and silently misroutes, e.g. always hitting the default calendar
     path; advertised routes with no controller action; an accepted request envelope changed or
     dropped so existing callers send fields that are silently ignored; strict-equality param parsing
     that silently inverts booleans — params[:visible] == "true" vs JSON true). Does NOT flag:
     security (Security), test quality (Testing-quality), migration
     safety (Data-migration), concrete runtime error-path handling in this diff's code
     (Runtime-reliability — design-level failure propagation shape stays here).
   - Intent-Preservation: attack the assumption the final artifact still matches the original intent;
     block when review iterations changed the objective without explicit human acceptance. Does
     NOT flag: feasibility/completeness/scope/architecture soundness.
   - Security: hunt for vulnerabilities the change introduces or fails to prevent, across the OWASP
     classes a diff-review can see. Hunt for IDOR/ownership scoping (DB lookups using a user-supplied
     id without an ownership/org/tenant scope check); injection variants beyond SQL (command
     injection exec/spawn with user input, NoSQL injection, deserialization injection of untrusted
     pickle/yaml.load/unserialize, SQL string interpolation); SSRF protocol-bypass (server-side fetch
     of unvalidated user URLs where a naive localhost string check is defeated by file://, gopher://,
     127.0.0.1 in decimal/IPv6, or DNS rebinding); secrets in logs (PII/tokens/credentials written to
     log output/error messages/telemetry — distinct from hardcoded secrets in code); hardcoded
     secrets; XSS/unescaped user input to HTML/JS; weakened token entropy/integrity; insecure
     design; auth/session failures; security misconfiguration (debug mode, default creds). Do not
     double-report bare eval() (a deterministic gate covers that). Give file:line + the vulnerable
     code + the failure mode. Does NOT flag: code style, architecture correctness (Architecture),
     test quality (Testing-quality), migration safety (Data-migration).
   - Testing-quality: attack the assumption the tests verify the behavior they claim to — tests can
     lie. Diff-scoped: judge whether test changes in THIS diff verify the behavior changes in THIS
     diff. Hunt for false-confidence assertions (toBeTruthy()/toBeDefined()/bare assert(x) that
     assert nothing); behavioral-change-in-the-diff with ZERO test modifications (stale tests);
     tests verifying mocks not real logic (asserts the mock was called but never the real return
     value/side effect; a mock that replaces the unit under test); untested new branches/lifecycle
     paths (new if/switch/error path/lifecycle hook with no test triggering it); sentinel-semantics
     reuse in mocks (a mock returning null/[] that no longer matches the real code's new semantics);
     mirror-tests-that-miss-the-machine (tests mirroring the implementation so closely they pass
     even when both are wrong). Block on a behavioral change with no test modification, a
     false-confidence assertion, or a test exercising only a mock. Missing-test ownership: the
     deterministic missing-test gate owns the boolean 'source changed, test file unchanged';
     Completeness owns missing verification when no test code is in the diff; THIS lens owns tests
     that EXIST but don't cover the new behavior. Do not double-report eval()/missing-test issues the
     deterministic gates catch. Does NOT flag: security (Security), architecture soundness
     (Architecture), migration safety (Data-migration), or whether tests exist at all when no test
     code is in the diff (Completeness).
   - Data-migration: attack the assumption the migration is safe and reversible; find the failure
     that loses data or can't be rolled back. Diff-scoped: judge whether migration changes in THIS
     diff are safe against the review-base schema. Hunt for schema drift (migration schema vs the
     code that reads it disagree); irreversible migrations (DROP COLUMN/TABLE/destructive ALTER
     without backfill or rollback); missing backfills for new NOT NULL columns (no DEFAULT/backfill
     -> deploy breaks mid-rollout); deploy-window breaks / expand+contract violations (a contract
     change in one step breaking rolling deploys — column rename in the same PR, column dropped
     before readers updated); dual-write gaps (should dual-write old+new but only writes one side);
     orphaned refs (FK pointing at nonexistent rows, or FK dropped without cleanup); silent data
     loss (drops/overwrites/truncates without backup; DELETE with broader WHERE than intended;
     column repurposed same-name-new-meaning; ALTER COLUMN TYPE that narrows/truncates);
     MIGRATION-RE-RUN-SAFETY (force: true added to an already-shipped migration — drops
     pre-existing tables on re-run; a conditional insert paired with an unconditional delete —
     settings destroyed even when no rows were migrated; dead guards on query results —
     cmd_tuples > 0 is always 0 for SELECTs in PostgreSQL, so the guarded insert never runs while
     the paired delete destroys the old rows, settings deleted with no replacement created;
     backfills that bypass model validations/callbacks — whitespace/junk rows, values interpolated
     into backfill SQL without the escaping/parameterization the model layer would have applied
     (the data-integrity failure is this lens's, the injection angle is Security's);
     enum/boolean defaults that silently reclassify every existing row — cook_method default 1 =
     raw_html; transformation field-fidelity — each output field must derive from the right source
     at the right precision, raw vs cooked, date vs datetime, precision loss on parse). Block on
     irreversible migrations without rollback, missing backfills, expand+contract violations,
     silent data loss, or orphaned refs, a shipped migration made destructive on re-run
     (force: true), a conditional insert paired with an unconditional delete, a dead guard that
     leaves a delete unreplaced (no replacement rows created), an enum/boolean default that
     silently reclassifies existing rows, a backfill that bypasses validations, or a
     transformation that derives an output field from the wrong source or at the wrong
     precision. Does NOT flag: security (Security), test quality
     (Testing-quality), architecture soundness beyond migration safety (Architecture — this lens
     judges only whether the transition from old to new schema is safe and reversible), runtime
     error-path handling outside the migration itself (Runtime-reliability; runtime error paths
     INSIDE the migration code stay here).
   - Runtime-reliability: attack the assumption that every runtime failure path in this diff is
     handled, observable, and honest — find the failure that is silently swallowed, silently
     partial, or reported as success. Hunt for UNHANDLED-ASYNC-FAILURE (a promise/future with no
     rejection handler — .then without .catch; an inner async call not returned/awaited so the
     caller resolves success before the work completes; a fire-and-forget refresh whose failure
     leaves stale state with no error surfaced to the user); OPTIMISTIC-STATE-DESYNC (UI/persistent
     state mutated before the operation resolves with no rollback on failure; no in-flight guard so
     concurrent invocations interleave — double-click issues overlapping requests, out-of-order
     responses overwrite newer state, last response wins; pagination/offset bookkeeping committed
     before the request succeeds); SILENT-PARTIAL-SUCCESS (work skipped or dropped while the API
     returns success — unknown IDs silently skipped; an unresolvable dependency silently skipped
     with no log and no error result; a throttle/lock/dedup key committed before the operation
     succeeds so retries no-op "successfully"; a hash/cursor advanced even when the underlying
     write failed); OUTBOUND-CALL-HARDENING (no timeout on network/file fetches — open(url), fetch,
     feed/HTTP clients; unbounded request payloads or downloads — no size/count cap, no max() on
     schema fields written to storage; request amplification with no rate limit — an enqueue
     endpoint throttled per-URL, bypassed by varying the path; the reliability hardening here is
     timeouts, payload/storage caps, and exhaustion on the request path — a missing rate limit that
     is a vulnerability (unauthenticated amplification) is Security's); ERROR-SHAPE-LEAKAGE (a raw
     exception/500 where the API contract promises a 4xx — unguarded parse/decrypt, find-or-throw
     on optional relations, missing param envelope; error messages that can never render — a
     template-literal fallback that is always truthy; stack traces or error details exposed to end
     users are Security's A05, this hunt owns the wrong-shape response and the never-rendering
     message); CROSS-BOUNDARY-CREDENTIAL-TOKEN-LIFECYCLE (a response schema that cannot
     structurally satisfy the parser on one path — every refresh fails; a connection/client rebuilt
     from the pre-refresh token after persisting the new one; response.ok/status never checked
     before parsing). Block on a user-facing operation whose failure is invisible, an API that
     reports success while dropping work, an unbounded or timeout-less outbound call on a request
     path, or a raw 500 where a 4xx belongs. Does NOT flag: security vulnerabilities (Security);
     test quality (Testing-quality); migration safety, including runtime error paths inside the
     migration itself (Data-migration); design-level failure propagation shape or schema
     invariants (Architecture); whether error handling is tested (Testing-quality).
4. Each lens subagent must WRITE its own findings directly to a per-lens file
   {findings_path}.<lens-name> (e.g. {findings_path}.architecture) as it finishes — ONE finding per
   line in this exact format: `[lens/<lens-name>] file:line — one-sentence failure mode`. Do NOT return
   findings to the orchestrator in-message — write them to the file. This keeps each message small
   (the combined 8-lens output can exceed the model output limit on large diffs).
5. The deterministic-gate findings from the metareview scaffold (step 1) are already written to a
   file by the scaffold command; you do not need to re-collect them. (If they are printed to stdout
   in step 1, append them to {findings_path}.deterministic yourself, one per line in the format
   `[deterministic/<gate-name>] <issue>`.)
6. After all 9 lens subagents finish, concatenate ALL the per-lens/per-gate files into {findings_path}
   yourself by running: `cat {findings_path}.* > {findings_path}`. Do NOT read, re-verify, or
   synthesize the findings in-session — just concatenate the files. Do NOT re-read files, re-run git
   diff, or re-verify lens findings — trust the lenses.
7. Return ONLY this one line as your reply: "Wrote N findings to {findings_path}". Do NOT repeat
   the findings in your reply message — they live in the file. This keeps your final message small."""

NAIVE_REALISTIC_PROMPT = """Review the code change in this repository (the diff is HEAD~1..HEAD).
Run `git diff HEAD~1` to see it. List each distinct issue you find, one per line, with file:line.
Be thorough but only report real issues you are confident about."""


async def _run_codex_session(repo_dir: Path, model_slug: str, effort: str, prompt: str,
                             timeout: int = 900) -> tuple[str, dict, str]:
    """Run a real multi-turn codex exec session in repo_dir with tools. Returns (text, per_model_usage, slug)."""
    from harnesseval.cli_backends import _parse_codex_effort
    args = ["codex", "exec", "--json", "--sandbox", "workspace-write", "--skip-git-repo-check",
            "-m", model_slug, "-c", f"model_reasoning_effort={_parse_codex_effort(effort)}", prompt]
    proc = await asyncio.to_thread(subprocess.run, args, capture_output=True, text=True,
                                   timeout=timeout, cwd=str(repo_dir), stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise RuntimeError(f"codex exec failed: {proc.stderr.strip()[:300]}")
    text = ""; usage = {}
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


async def _run_claude_session(repo_dir: Path, model_alias: str, effort: str, prompt: str,
                              max_turns: int = 12, timeout: int = 900) -> tuple[str, dict, str]:
    """Run a real multi-turn claude -p session in repo_dir with tools. Returns (text, per_model_usage, resolved_model).

    Retries on transient Claude API errors (529 Overloaded / rate-limit): claude -p surfaces
    these as either a non-zero exit (stderr) or, silently, as returncode 0 with the error string
    in `result` ("API Error: 529 Overloaded..."). The silent mode looks like a 0-finding review,
    so we detect both and retry once (cli_backends.is_transient_claude_error). NOT a timeout.
    """
    from harnesseval.cli_backends import _parse_claude_effort, is_transient_claude_error
    args = ["claude", "-p", "--model", model_alias, "--effort", _parse_claude_effort(effort),
            "--output-format", "json", "--max-turns", str(max_turns),
            "--dangerously-skip-permissions",  # allow git + bash + subagents in the throwaway repo
            "--append-system-prompt", "You are an expert code reviewer using the metareview harness. Use tools (Bash, Read, Task/subagents) as needed.",
            prompt]
    proc = None
    for attempt in (1, 2):  # one retry on transient API error
        proc = await asyncio.to_thread(subprocess.run, args, capture_output=True, text=True,
                                       timeout=timeout, cwd=str(repo_dir))
        if not is_transient_claude_error(proc.returncode, proc.stdout, proc.stderr):
            break
        if attempt == 1:
            await asyncio.sleep(20)  # brief backoff before the retry
    if proc.returncode != 0:
        raise RuntimeError(f"claude -p failed: {proc.stderr.strip()[:300]}")
    d = json.loads(proc.stdout)
    # guard: if the result string is an API error (silent overload on the retry too), surface it
    result = d.get("result", "")
    if isinstance(result, str) and result.strip().startswith("API Error: 5"):
        raise RuntimeError(f"claude -p transient overload persisted after retry: {result[:120]}")
    mu = d.get("modelUsage") or {}
    resolved = ",".join(mu.keys()) if isinstance(mu, dict) and mu else ""
    from harnesseval.usage import from_claude_cli
    return result, from_claude_cli(d), resolved


# HANDOFF §4.2 — eval-side extractor skip (the load-bearing fix for metareview's unfair
# precision penalty). Empirically (run_batch 20260824-101905-cli-144cells,
# results/per_lens_attribution.json) findings sourced from the deterministic gates
# (`metareview-deterministic/*`) are 100% hallucination under adjudication (match 0 goldens)
# and orchestrator/session prose (`metareview-session`) is ~92% hallucination. Keeping them
# in the LLM-judged finding stream penalizes metareview's precision unfairly — compound and
# superpowers have no gate/session layer. Only `metareview-lens/*` (the LLM lens subagent
# output) are real review findings. This is eval-side only: the deterministic gates stay
# `blocking` for metareview's own task-done verdict (the unsafe C1 metareview-side change was
# reverted). The §6.3 deterministic_gate_recall decomposition is computed downstream from
# matched goldens (run_model_matrix._decompose); gates match 0 goldens so it stays 0.00
# either way — this skip only removes the unfair FP/hallucination penalty. See metareview
# rubrics/artifact-review-rubric.md "Output Structure".
_SKIPPED_SOURCE_PREFIXES = ("metareview-deterministic/", "metareview-session")


def _skip_gate_session_findings(findings: list[Finding]) -> list[Finding]:
    """§4.2: drop deterministic-gate + orchestrator-session findings from the judged stream."""
    return [f for f in findings if not f.source.startswith(_SKIPPED_SOURCE_PREFIXES)]


def _extract_findings_from_session(text: str) -> list[Finding]:
    """Parse the consolidated findings list from the session output.

    Lines like: [deterministic/test-reviewer] <issue>  OR  [lens/architecture] <issue>.
    The orchestrator may bundle multiple lenses in one subagent call (e.g.
    '[lens/feasibility+architecture+scope]'); we keep the verbatim label for provenance but
    the per-lens decomposition (§6.3) treats a finding as 'lens' (not over-claiming which lens).
    Fallback: also extract numbered/bulleted issues if no bracketed prefix.

    §4.2: findings sourced from `metareview-deterministic/*` (the gates) or `metareview-session`
    (orchestrator prose) are SKIPPED before return — they are 100% / ~92% hallucination under
    adjudication and unfairly penalize metareview's precision. Only `metareview-lens/*` survive.
    """
    findings = []
    for line in text.splitlines():
        line = line.strip().lstrip("-*").strip()
        # also strip markdown wrappers the orchestrator non-deterministically adds around the
        # [lens/...] / [deterministic/...] tag: backticks (`[lens/...]`), bold (**[lens/...]**),
        # and a leading '**' on the issue text. Without this, a line like
        #   `- `[lens/architecture]` **src/foo.py:42 — bug**`
        # fails the ^\[ regex (starts with a backtick) -> 0 findings -> 0.00 recall cell.
        # (Seen in the 0.8.2 batch: opus mrv cells intermittently emit this wrapped format.)
        line = line.strip("`")
        if line.startswith("**"):
            line = line[2:].lstrip()
        if not line:
            continue
        m = re.match(r"^\[(deterministic|lens)/([^\]]+)\]`?\s*(.+)$", line)
        if m:
            kind, reviewer, issue = m.groups()
            # strip markdown wrappers the orchestrator adds to the issue text. The orchestrator
            # non-deterministically wraps the file:line in ** (bold) and/or backticks, e.g.
            #   `**src/foo.py:42** — the issue text`
            # Strip leading backticks, then a leading **...** wrapper around the file:line
            # (find the closing ** and drop both), plus stray backticks. Leaves file:line + issue.
            issue = issue.strip()
            while issue.startswith("`"):
                issue = issue[1:].strip()
            if issue.startswith("**"):
                end = issue.find("**", 2)
                if end != -1:
                    issue = (issue[2:end] + issue[end+2:]).strip()
            issue = issue.strip("`").strip()
            # if the reviewer label bundles multiple lenses (contains '+'), keep it verbatim but
            # mark as 'lens-mixed' so the decomposition doesn't over-attribute to one lens
            label = reviewer if '+' not in reviewer and 'all' not in reviewer.lower() else 'lens-mixed'
            src = f"metareview-{kind}/{label}"
            findings.append(Finding(issue_text=issue.strip(), source=src, raw=line))
            continue
        # fallback: numbered/bulleted issue lines (skip headers/empty)
        if re.match(r"^\d+\.\s+\S", line) or (line and not line.startswith(("#", "Step", "Run ", "Read ", "The diff"))):
            if ":" in line or any(k in line.lower() for k in ("bug", "issue", "error", "missing", "unsafe", "race", "inject")):
                findings.append(Finding(issue_text=line, source="metareview-session", raw=line))
    return _skip_gate_session_findings(findings)


def review_realistic(pr: PRSample, model: str, effort: str = "medium") -> ReviewRun:
    """Realistic metareview: drive the real harness in a host agent (OAuth, multi-turn + subagents)."""
    return asyncio.run(review_realistic_async(pr, model, effort))


async def review_realistic_async(pr: PRSample, model: str, effort: str = "medium") -> ReviewRun:
    t0 = time.time()
    name = "metareview-realistic"
    ml = model.lower()
    is_claude = any(k in ml for k in ("opus", "sonnet", "fable", "haiku", "claude"))
    is_codex = "gpt" in ml or "codex" in ml
    work_dir: Path | None = None   # the repo copy inside the unique work root
    work_root: Path | None = None  # the unique temp dir (cleanup target)
    try:
        # Per-run isolated work copy (CRITICAL for concurrent cells): materialize() returns a
        # SHARED per-PR cache dir that this adapter then mutates (task commit, per-lens
        # findings files, metareview-generated files, plus the session's own git ops). Two
        # concurrent cells on the same PR clobber each other -- materialize's reset_clean +
        # interleaved git state -- which silently corrupts results (observed: two different
        # models reporting byte-identical TP/FP/FN because both parsed the same findings.md).
        # Copy the clean [base][pr] repo into a unique temp dir per run; disposed before return.
        # The materialize+copy pair is serialized per PR with a cross-process file lock, so
        # concurrent arms materializing the SAME PR cannot race inside the shared cache dir
        # (reset-vs-copy and git index.lock collisions observed live at concurrency >= 2 arms).
        _h = hashlib.sha1(pr.url.encode()).hexdigest()[:16]
        _lock_path = Path(__file__).resolve().parents[2] / ".cache" / "mrv_repos" / f"{_h}.lock"
        _lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(_lock_path, "w") as _lf:
            fcntl.flock(_lf, fcntl.LOCK_EX)
            _cache_dir = materialize(pr.url)
            work_root = Path(tempfile.mkdtemp(prefix="mrvwork-"))
            work_dir = work_root / "repo"
            shutil.copytree(_cache_dir, work_dir, symlinks=True)
            fcntl.flock(_lf, fcntl.LOCK_UN)
        repo_dir = work_dir
        task_path = repo_dir / "docs" / "tasks" / "task-001.md"
        task_path.parent.mkdir(parents=True, exist_ok=True)
        task_path.write_text(f"# Task: {pr.pr_title}\nReview the change.\n")
        # §output-cap fix: the orchestrator writes consolidated findings to this file instead of
        # returning them in its final message (which overflows the model's per-message output cap
        # on hard PRs — the 3 v2 failures were all '400 max_tokens / output limit reached' on the
        # final consolidation). The file is unbounded; the final message becomes a one-line ack.
        findings_path = repo_dir / "docs" / "tasks" / "findings.md"
        # clear any stale findings file so we never parse a previous run's output
        try: findings_path.unlink()
        except FileNotFoundError: pass
        subprocess.run(["git", "-C", str(repo_dir), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo_dir), "commit", "--quiet", "--allow-empty", "-m", "task"],
                       check=True, capture_output=True,
                       env={**__import__("os").environ, "GIT_AUTHOR_NAME": "x", "GIT_AUTHOR_EMAIL": "x@x",
                            "GIT_COMMITTER_NAME": "x", "GIT_COMMITTER_EMAIL": "x@x"})
        prompt = REALISTIC_PROMPT.format(mrv_bin=str(MRV_BIN), task_path=str(task_path),
                                         findings_path=str(findings_path), base_ref="HEAD~2")
        if is_claude:
            alias = "opus" if "opus" in ml else "sonnet" if "sonnet" in ml else "fable" if "fable" in ml else "sonnet"
            text, per_model, resolved = await _run_claude_session(repo_dir, alias, effort, prompt,
                                                                 timeout=session_timeout(effort, base=900))
        elif is_codex:
            slug = codex_slug_for(model)  # gpt-5.6-* pass through; gpt-5.2/gpt-5 fall back to gpt-5.6-sol
            text, per_model, resolved = await _run_codex_session(repo_dir, slug, effort, prompt,
                                                                timeout=session_timeout(effort, base=900))
        else:
            # GLM/Kimi: no realistic CLI; fall back to api-direct metareview (recorded as cli mode but uses API lenses)
            from harnesseval.adapters import metareview as mrv
            r = await mrv.review_async(pr, model=model, effort=effort, mode="api")
            # §4.2: the api adapter returns deterministic gates + lens findings; drop the gates
            # (100% hallucination) so the GLM realistic path gets the same precision fix as the
            # claude/codex extractor path.
            if work_root is not None:
                shutil.rmtree(work_root, ignore_errors=True)
            return ReviewRun(framework=name, model=model, effort=effort, execution_mode="api-fallback",
                             raw_output=r.raw_output, findings=_skip_gate_session_findings(r.findings),
                             tokens_in=r.tokens_in, tokens_out=r.tokens_out, wall_ms=r.wall_ms)
    except Exception as e:  # noqa: BLE001
        if work_root is not None:
            shutil.rmtree(work_root, ignore_errors=True)
        return ReviewRun(framework=name, model=model, effort=effort, execution_mode="cli",
                         raw_output="", wall_ms=(time.time() - t0) * 1000, error=str(e))
    # §output-cap fix: each lens writes to {findings_path}.<lens>; the orchestrator concatenates via
    # `cat {findings_path}.* > {findings_path}`. If the orchestrator didn't run that, gather here.
    file_text = ""
    try:
        if findings_path.exists():
            file_text = findings_path.read_text()
        if not file_text.strip():
            # orchestrator may not have concatenated — gather per-lens files ourselves
            per_lens = sorted(findings_path.parent.glob(f"{findings_path.name}.*"))
            if per_lens:
                file_text = "\n".join(p.read_text() for p in per_lens)
    except Exception:
        file_text = ""
    src_text = file_text if file_text.strip() else text
    findings = _extract_findings_from_session(src_text)
    if work_root is not None:
        shutil.rmtree(work_root, ignore_errors=True)
    from harnesseval.usage import grand_total
    gt = grand_total(per_model)
    # Realistic Claude Code behavior: orchestrator on the requested model, but Task-tool subagent
    # dispatch defaults to Haiku for lightweight subtasks even with --model opus (verified
    # 2026-08-22). `resolved` captures the full modelUsage set (e.g. 'claude-haiku-4-5-20251001,
    # claude-opus-5'). We record this honestly rather than fighting the host — it IS what a user gets.
    return ReviewRun(framework=name, model=(resolved or model), effort=effort, execution_mode="cli",
                     raw_output=text, findings=findings, tokens_in=gt["total_tokens"],
                     tokens_out=sum(u.get("output_tokens",0) for u in per_model.values()),
                     wall_ms=(time.time() - t0) * 1000, per_model_usage=per_model,
                     total_cost_usd=gt["total_cost_usd"])
