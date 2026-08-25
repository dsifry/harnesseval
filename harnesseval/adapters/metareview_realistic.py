"""Realistic metareview adapter — drives the real harness as a user runs it (v0.8.1 slim).

v0.8.1 (this branch, mrv-0.8.1-slim-orchestration): orchestration-slim experiment on top of
the 0.8.0 8-lens adversarial prompt. Four slimming fixes to the REALISTIC_PROMPT, tested
against the 0.8.0 baseline for token cost + recall/precision impact:
  1. Embed the diff in the orchestrator prompt; lenses receive it verbatim in their dispatch
     and do NOT each re-run `git diff` / explore files (cuts per-lens opus exploration turns).
  2. After the 8 lenses return, consolidate directly — do NOT re-read files / re-run git diff /
     re-verify lens findings (cuts post-lens orchestrator turns).
  3. Drop the "Per the metareview review-artifact skill" reference (the skill isn't installed
     in the throwaway repo; the mention triggered a fruitless skill-search on codex).
  4. Be terse — no planning monologue / narration (cuts orchestrator output tokens).

Per docs/SPEC.md §2 (realistic mode): test the harness as a USER uses it — installed in a host
agent, invoked naturally, with the real agent loop + tools + subagents. The scoring pipeline
(extract -> judge -> score -> adjudicate) is identical regardless of how the reviewer arm ran.
For the api-direct (pure) column, adapters/metareview.py review() still exists unchanged.
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
from harnesseval.cli_backends import session_timeout

MRV_BIN = Path(__file__).resolve().parents[2] / "bin" / "metareview"

# v0.8.1 slim-orchestration prompt. The 8-lens adversarial methodology is identical to v0.8.0
# (isolating the orchestration fixes as the only variable); only the orchestration wrapper
# changed (see module docstring). The <<DIFF>> sentinel is replaced with the truncated diff
# after .format() (not a {field} so .format() leaves it alone; avoids breakage on { } in code).
REALISTIC_PROMPT = """You are running metareview's task-done review (v0.8.1) on a local change, as a user would.

Be terse. Do NOT narrate your plan, reasoning, or progress — just run the commands, dispatch the lenses, and consolidate. No planning monologues.

Steps:
1. Run this command and read its output (it writes a review scaffold + context pack):
   {mrv_bin} review task-done {task_path} --base {base_ref}
   The command prints the path to the generated review markdown; read that file.
2. Read the review scaffold + context pack it generated.
3. Dispatch the 8 required reviewer lenses as PARALLEL SUBAGENTS via your host's subagent-spawn
   tool — in Claude Code that is the `Agent` tool (one `Agent` call per lens, run in
   background; then collect each result); in Codex that is `collaboration.spawn_agent` (one
   spawn per lens) then `collaboration.wait_agent` to collect each result. Do NOT run the
   lenses in-session; do NOT fall back to a single in-session pass.

   ADVERSARIAL STANCE (applies to ALL 8 lenses): assume the creator's intent is GOOD but be
   hostile to unexamined assumptions — assume there may be a fundamental mistake hiding in
   this design and find it. Do NOT confirm the artifact is well-shaped. Each finding carries
   a confidence anchor (100/75/50/25/0) + severity (P0-P3); SUPPRESS findings below confidence
   50 unless they are P0. Cite file:line + the verbatim code + the failure mode for every finding.

   THE DIFF UNDER REVIEW is provided in full at the end of this prompt between <<<DIFF>>> and
   <<<END DIFF>>> markers. Include this diff VERBATIM in each lens subagent's dispatch prompt.
   Each subagent reviews the diff AS PROVIDED — it should NOT run `git diff` itself, and should
   NOT read surrounding files unless a specific finding requires reading ONE additional file for
   context. (This keeps each lens a single focused pass over the provided diff.)

   The 8 lenses (each subagent gets the verbatim diff below + its lens focus):
   - Feasibility: attack the assumption that paths/commands/dependencies are correct against the
     diff reality; block on fabricated paths, impossible ordering, missing tools, invalid commands.
     Does NOT flag: requirements completeness (Completeness) or architecture soundness (Architecture).
   - Completeness: attack the assumption the artifact covers every requirement; block on missing
     acceptance criteria, missing verification, unhandled obvious edge cases. Does NOT flag:
     feasibility (Feasibility), scope drift (Scope), architecture soundness (Architecture).
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
     semantics shifted so existing callers misbehave); CASCADING-FAILURE (trace failure propagation —
     when one dependency fails does it degrade gracefully or cascade? a sync call chain with no
     timeout/circuit-breaker/fallback; a queue consumer whose failure poisons the batch; a shared
     resource whose exhaustion takes down all tenants); STAND-IN-GUARD-FIDELITY (a CI gate/check/test
     that can go green while production is red — tests a proxy/mock instead of the real code path;
     a check that passes because the prod-only branch is #ifdef/feature-flagged away; a 'green' build
     that never exercised the changed code); API-CONTRACT-BREAKING-CHANGES (renamed/removed fields,
     narrowed inputs, widened returns, missing versioning on breaking changes; a response shape
     existing callers depend on but the diff silently changes; a field re-typed int->string with no
     version bump). Does NOT flag: security (Security), test quality (Testing-quality), migration
     safety (Data-migration).
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
     column repurposed same-name-new-meaning; ALTER COLUMN TYPE that narrows/truncates). Block on
     irreversible migrations without rollback, missing backfills, expand+contract violations,
     silent data loss, or orphaned refs. Does NOT flag: security (Security), test quality
     (Testing-quality), architecture soundness beyond migration safety (Architecture — this lens
     judges only whether the transition from old to new schema is safe and reversible).
4. Collect each lens's findings. After the 8 lenses return, CONSOLIDATE their findings directly
   into the output list. Do NOT re-read files, re-run git diff, or re-verify lens findings — trust
   the lenses and consolidate what they returned.
5. Also include the deterministic-gate findings from the metareview scaffold (step 1).
6. Return a consolidated list of ALL findings (deterministic gates + 8 lenses), one per line,
   each prefixed with its source, e.g.:
   [deterministic/test-reviewer] Missing test changes or validation evidence
   [lens/architecture] src/foo.py:42 — boundary issue: ...

<<<DIFF>>>
{diff}
<<<END DIFF>>>

Be thorough but only report real issues you are confident about (confidence >= 50, or any P0)."""

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
        if not line:
            continue
        m = re.match(r"^\[(deterministic|lens)/([^\]]+)\]\s*(.+)$", line)
        if m:
            kind, reviewer, issue = m.groups()
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
    try:
        repo_dir = materialize(pr.url)
        task_path = repo_dir / "docs" / "tasks" / "task-001.md"
        task_path.parent.mkdir(parents=True, exist_ok=True)
        task_path.write_text(f"# Task: {pr.pr_title}\nReview the change.\n")
        subprocess.run(["git", "-C", str(repo_dir), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo_dir), "commit", "--quiet", "--allow-empty", "-m", "task"],
                       check=True, capture_output=True,
                       env={**__import__("os").environ, "GIT_AUTHOR_NAME": "x", "GIT_AUTHOR_EMAIL": "x@x",
                            "GIT_COMMITTER_NAME": "x", "GIT_COMMITTER_EMAIL": "x@x"})
        # v0.8.1 fix #1: embed the diff in the prompt so lens subagents don't each re-run git diff.
        # {diff} is filled by .format(); the <<<DIFF>>> sentinel is a redundant marker for the model.
        diff_text = pr.diff or ""
        if len(diff_text) > 60000:
            diff_text = diff_text[:60000] + f"\n\n[... diff truncated: {len(pr.diff) - 60000} more chars ...]"
        prompt = REALISTIC_PROMPT.format(mrv_bin=str(MRV_BIN), task_path=str(task_path),
                                         base_ref="HEAD~2", diff=diff_text)
        if is_claude:
            alias = "opus" if "opus" in ml else "sonnet" if "sonnet" in ml else "fable" if "fable" in ml else "sonnet"
            text, per_model, resolved = await _run_claude_session(repo_dir, alias, effort, prompt,
                                                                 timeout=session_timeout(effort, base=900))
        elif is_codex:
            slug = "gpt-5.6-sol"  # valid Codex CLI slug (gpt-5.2 is API-only)
            text, per_model, resolved = await _run_codex_session(repo_dir, slug, effort, prompt,
                                                                timeout=session_timeout(effort, base=900))
        else:
            # GLM/Kimi: no realistic CLI; fall back to api-direct metareview (recorded as cli mode but uses API lenses)
            from harnesseval.adapters import metareview as mrv
            r = await mrv.review_async(pr, model=model, effort=effort, mode="api")
            # §4.2: the api adapter returns deterministic gates + lens findings; drop the gates
            # (100% hallucination) so the GLM realistic path gets the same precision fix as the
            # claude/codex extractor path.
            return ReviewRun(framework=name, model=model, effort=effort, execution_mode="api-fallback",
                             raw_output=r.raw_output, findings=_skip_gate_session_findings(r.findings),
                             tokens_in=r.tokens_in, tokens_out=r.tokens_out, wall_ms=r.wall_ms)
    except Exception as e:  # noqa: BLE001
        return ReviewRun(framework=name, model=model, effort=effort, execution_mode="cli",
                         raw_output="", wall_ms=(time.time() - t0) * 1000, error=str(e))
    findings = _extract_findings_from_session(text)
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
