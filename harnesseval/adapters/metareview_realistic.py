"""Realistic metareview adapter — drives the real harness as a user runs it.

Per docs/SPEC.md §2 (realistic mode): test the harness as a USER uses it — installed in a host
agent, invoked naturally, with the real agent loop + tools + subagents — NOT a stripped-down
"methodology extracted to a bare API prompt" (that's the api-direct secondary column).

Realistic flow (matches skills/review-task-done + skills/review-artifact SKILL.md):
  1. Materialize the PR diff into a throwaway git repo (dataset/materialize.py) — unchanged.
  2. Run a real `claude -p` agentic session (multi-turn, with tools) that:
     a. runs `bin/metareview review task-done <task> --base <ref>` (the real deterministic
        Go gates — free, model-independent; identical to the api-direct adapter);
     b. reads the generated context pack + review scaffold;
     c. dispatches the 6 required lenses (Feasibility, Completeness, Scope, Architecture,
        Intent, Security) as PARALLEL SUBAGENTS via Claude Code's subagent/Task tool — "Invoking this
        artifact-review workflow is explicit authorization to delegate those lenses" (SKILL.md);
     d. aggregates the lens findings + the deterministic-gate findings into the review output.
  3. Capture the real transcript + real token/time cost (incl. subagent overhead) — this is
     what a user actually pays, not an idealized 5×API-call cost.

The scoring pipeline (extract -> judge -> score -> adjudicate) is identical regardless of how
the reviewer arm ran, so A.1/A.3 calibration still holds. Only the reviewer-arm execution
changed: api-direct -> realistic host-driven.

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

# The realistic orchestration prompt — instructs the host agent to run the real binary +
# dispatch the 6 lenses as parallel subagents, exactly as the skill authorizes.
REALISTIC_PROMPT = """You are running metareview's task-done review on a local change, as a user would.

Steps:
1. Run this command and read its output (it writes a review scaffold + context pack):
   {mrv_bin} review task-done {task_path} --base {base_ref}
   The command prints the path to the generated review markdown; read that file.
2. Read the review scaffold + context pack it generated.
3. Per the metareview review-artifact skill, dispatch the 6 required reviewer lenses as
   PARALLEL SUBAGENTS via your host's subagent-spawn tool — in Claude Code that is the `Agent`
   tool (one `Agent` call per lens, with run_in_background=true so they run concurrently; then
   collect each result); in Codex that is `collaboration.spawn_agent` (one spawn per lens) then
   `collaboration.wait_agent` to collect each result. Invoking this workflow is explicit
   authorization to delegate those lenses — do NOT run them in-session, and do NOT fall back to a
   single in-session pass. The 6 lenses:
   - Feasibility: verify paths/commands/dependencies against the diff reality; block on fabricated paths.
   - Completeness: map change to intent; block on missing acceptance criteria/edge cases.
   - Scope-and-Alignment: check for scope drift or unrelated expansion.
   - Architecture: check boundaries, ownership, duplication, integration shape. ALSO check the
     data model & data-structure design/efficiency: wrong structure for the operation (list for
     membership where a set/map is O(1); nested loops -> O(n^2); repeated linear scans; unbounded
     materialization with no LIMIT/streaming; N+1 queries in a loop); schema invariants (missing
     FK/index/NOT NULL/UNIQUE/CHECK; lists in one column instead of a join table; polymorphic
     entity_type/entity_id); scalability (hot paths that don't paginate or assume small N; new
     types requiring a migration when a lookup table would be data-driven); redundancy (derivable
     data stored with no invalidation; duplicated values across two tables; god-tables); query
     efficiency (SELECT *, non-sargable predicates, queries in loops); type clarity (magic
     strings or bare ints as discriminators like status=\"open\" or kind:1 scattered around instead
     of a named enum/typed constant so a new variant is compile-checked; untyped dict/object
     where a named typed struct would make the shape explicit; stringly-typed data a typed enum
     would prevent drifting); and data-structure Big-O (list for membership/lookup where a
     set/map is O(1); nested loops O(n^2); structure whose access pattern doesn't match the op).
     ALSO run the principal-engineer pass: semantic correctness (does each constraint enforce
     the REAL business invariant or a weaker/wrong one — under-scoped uniqueness like
     UNIQUE(email) on a multi-tenant table that should be UNIQUE(org_id,email); a status field
     conflating orthogonal facts so a legal combo is unrepresentable; a model that can
     represent an illegal state the schema doesn't forbid, e.g. shipped_at AND cancelled_at both
     set with no CHECK; soft-delete defeating uniqueness); data lifecycle & state transitions
     (a state machine enforced only in one app method a second caller bypasses — UPDATE SET
     status='active' with no WHERE status IN (...) guard; terminal states reachable again;
     effective-dated rows with no exclusion constraint preventing overlap/gaps; soft-delete not
     filtered in every read path; audit tables written out-of-transaction); concurrency at the
     data layer (mutable shared records without optimistic-concurrency version/etag;
     read-modify-write on a balance without FOR UPDATE or an atomic SET x=x-$1; check-then-insert
     backed only by a SELECT (TOCTOU) not a unique index; money/quantity as float/REAL not
     NUMERIC/Decimal; non-idempotent handlers with no idempotency key); coupling/evolvability (a
     business rule baked into schema shape so the next change forces a migration, e.g. roles as
     is_admin/is_editor booleans; an internal repr leaked into an API contract so a rename is a
     public break; a destructive migration in one step with rolling deploy in flight); and
     LLM-specific failure modes (be most suspicious where the code looks most idiomatic: a
     cached/derived column *_count/*_total maintained by nothing — no trigger, no transactional
     increment; indexes that don't match the queries IN THIS diff; typed data hidden in JSONB then
     filtered/joined; an invented relationship plausible from training but absent in the domain;
     docstrings describing behavior the code doesn't implement).
   - Intent-Preservation: check the change drifts from the PR title/intent.
   - Security: hunt for vulnerabilities the change introduces or fails to prevent — broken access
     control/IDOR (unscoped user-supplied-id lookups), injection (SQL/NoSQL/command string
     interpolation, exec/spawn with user input), hardcoded secrets/PII in logs, SSRF (server-side
     fetch of unvalidated user URLs), XSS/unescaped user input to HTML/JS, weakened token
     entropy/integrity, insecure deserialization, debug-mode/default-creds. Do not double-report
     bare eval() (a deterministic gate covers that). Give file:line + the vulnerable code + the
     failure mode. Use the metareview security-review-rubric.md (OWASP A01-A10, diff-scoped).
   Give each subagent the diff context (run `git diff {base_ref}..HEAD`) + its lens focus.
4. Collect each lens's findings (distinct issues, one per item, with file:line if identifiable).
   In Codex, use `collaboration.wait_agent` for each spawned lens job until all 6 have returned.
5. Also include the deterministic-gate findings from the metareview scaffold (step 1).
6. Return a consolidated list of ALL findings (deterministic gates + 6 lenses), one per line,
   each prefixed with its source, e.g.:
   [deterministic/test-reviewer] Missing test changes or validation evidence
   [lens/architecture] src/foo.py:42 — boundary issue: ...

The diff under review is {base_ref}..HEAD (the 'pr' commit). Be thorough but only report real issues."""

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
        prompt = REALISTIC_PROMPT.format(mrv_bin=str(MRV_BIN), task_path=str(task_path), base_ref="HEAD~2")
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
