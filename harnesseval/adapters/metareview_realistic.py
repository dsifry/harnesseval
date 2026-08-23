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
     c. dispatches the 5 required lenses (Feasibility, Completeness, Scope, Architecture,
        Intent) as PARALLEL SUBAGENTS via Claude Code's subagent/Task tool — "Invoking this
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

MRV_BIN = Path(__file__).resolve().parents[2] / "bin" / "metareview"

# The realistic orchestration prompt — instructs the host agent to run the real binary +
# dispatch the 5 lenses as parallel subagents, exactly as the skill authorizes.
REALISTIC_PROMPT = """You are running metareview's task-done review on a local change, as a user would.

Steps:
1. Run this command and read its output (it writes a review scaffold + context pack):
   {mrv_bin} review task-done {task_path} --base {base_ref}
   The command prints the path to the generated review markdown; read that file.
2. Read the review scaffold + context pack it generated.
3. Per the metareview review-artifact skill, dispatch the 5 required reviewer lenses as
   PARALLEL SUBAGENTS using the Agent tool (one Agent call per lens, with run_in_background=true
   so they run concurrently; then collect each result). Invoking this workflow is explicit
   authorization to delegate those lenses — do NOT run them in-session. The 5 lenses:
   - Feasibility: verify paths/commands/dependencies against the diff reality; block on fabricated paths.
   - Completeness: map change to intent; block on missing acceptance criteria/edge cases.
   - Scope-and-Alignment: check for scope drift or unrelated expansion.
   - Architecture: check boundaries, ownership, duplication, integration shape.
   - Intent-Preservation: check the change drifts from the PR title/intent.
   Give each Agent subagent the diff context (run `git diff {base_ref}..HEAD`) + its lens focus.
4. Collect each lens's findings (distinct issues, one per item, with file:line if identifiable).
5. Also include the deterministic-gate findings from the metareview scaffold (step 1).
6. Return a consolidated list of ALL findings (deterministic gates + 5 lenses), one per line,
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
    """Run a real multi-turn claude -p session in repo_dir with tools. Returns (text, per_model_usage, resolved_model)."""
    from harnesseval.cli_backends import _parse_claude_effort
    args = ["claude", "-p", "--model", model_alias, "--effort", _parse_claude_effort(effort),
            "--output-format", "json", "--max-turns", str(max_turns),
            "--dangerously-skip-permissions",  # allow git + bash + subagents in the throwaway repo
            "--append-system-prompt", "You are an expert code reviewer using the metareview harness. Use tools (Bash, Read, Task/subagents) as needed.",
            prompt]
    proc = await asyncio.to_thread(subprocess.run, args, capture_output=True, text=True,
                                   timeout=timeout, cwd=str(repo_dir))
    if proc.returncode != 0:
        raise RuntimeError(f"claude -p failed: {proc.stderr.strip()[:300]}")
    d = json.loads(proc.stdout)
    mu = d.get("modelUsage") or {}
    resolved = ",".join(mu.keys()) if isinstance(mu, dict) and mu else ""
    from harnesseval.usage import from_claude_cli
    return d.get("result", ""), from_claude_cli(d), resolved


def _extract_findings_from_session(text: str) -> list[Finding]:
    """Parse the consolidated findings list from the session output.

    Lines like: [deterministic/test-reviewer] <issue>  OR  [lens/architecture] <issue>
    Fallback: also extract numbered/bulleted issues if no bracketed prefix.
    """
    findings = []
    for line in text.splitlines():
        line = line.strip().lstrip("-*").strip()
        if not line:
            continue
        m = re.match(r"^\[(deterministic|lens)/([^\]]+)\]\s*(.+)$", line)
        if m:
            kind, reviewer, issue = m.groups()
            src = f"metareview-{kind}/{reviewer}"
            findings.append(Finding(issue_text=issue.strip(), source=src, raw=line))
            continue
        # fallback: numbered/bulleted issue lines (skip headers/empty)
        if re.match(r"^\d+\.\s+\S", line) or (line and not line.startswith(("#", "Step", "Run ", "Read ", "The diff"))):
            # only treat as finding if it looks like an issue (heuristic: contains a colon or "issue"/"bug")
            if ":" in line or any(k in line.lower() for k in ("bug", "issue", "error", "missing", "unsafe", "race", "inject")):
                findings.append(Finding(issue_text=line, source="metareview-session", raw=line))
    return findings


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
            text, per_model, resolved = await _run_claude_session(repo_dir, alias, effort, prompt)
        elif is_codex:
            slug = "gpt-5.6-sol"  # valid Codex CLI slug (gpt-5.2 is API-only)
            text, per_model, resolved = await _run_codex_session(repo_dir, slug, effort, prompt)
        else:
            # GLM/Kimi: no realistic CLI; fall back to api-direct metareview (recorded as cli mode but uses API lenses)
            from harnesseval.adapters import metareview as mrv
            r = await mrv.review_async(pr, model=model, effort=effort, mode="api")
            return ReviewRun(framework=name, model=model, effort=effort, execution_mode="api-fallback",
                             raw_output=r.raw_output, findings=r.findings, tokens_in=r.tokens_in,
                             tokens_out=r.tokens_out, wall_ms=r.wall_ms)
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
