"""Realistic Superpowers adapter — drives the real plugin in a host agent as a user runs it.

Per docs/SPEC.md §2 (realistic mode) + §7 (cli column): test the Superpowers review capability as
a USER uses it — the real `obra/superpowers` plugin installed in a host agent (`claude -p` or
`codex exec`), invoked naturally, with the real agent loop + subagent dispatch — NOT a
stripped-down methodology prompt (that's the api-direct secondary column, superpowers.py).

Realistic flow (matches skills/requesting-code-review/SKILL.md + code-reviewer.md @ pinned SHA):
  1. Materialize the PR diff into a throwaway git repo (dataset/materialize.py) — unchanged from
     the metareview realistic adapter.
  2. Install the real Superpowers plugin into a throwaway host config (Claude Code plugin dir or
     Codex agents config) and run a real `claude -p` / `codex exec` agentic session that:
     a. resolves BASE_SHA / HEAD_SHA from the repo;
     b. dispatches a `general-purpose` code-reviewer SUBAGENT with the code-reviewer.md template
        (this is the core Superpowers review methodology — a coordinator dispatches a reviewer
        subagent so the diff + evaluation live in the subagent's context, not the coordinator's);
     c. returns Strengths + Issues (Critical/Important/Minor) + Assessment.
  3. Capture the real transcript + real token/time cost (incl. subagent overhead) — this is what
     a user actually pays, not an idealized single-API-call cost. Per SPEC §6.3.1, Claude Code
     routes `general-purpose` subagent dispatches to Haiku by default regardless of --model, so
     "superpowers-realistic @ opus" = opus coordinator + Haiku reviewer subagent (the realistic
     default — record it honestly via per_model_usage, do not force anything).

The scoring pipeline (extract -> judge -> score -> adjudicate) is identical regardless of how the
reviewer arm ran, so A.1/A.3 calibration still holds. Only the reviewer-arm execution changed.

Methodology source (auditable): third_party/superpowers @ SHA b36e0829c6d0140e93cfef2ca599b1b07d4a7797
  - skills/requesting-code-review/SKILL.md
  - skills/requesting-code-review/code-reviewer.md
  - skills/subagent-driven-development/task-reviewer-prompt.md
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from harnesseval.adapters.base import PRSample, ReviewRun
from harnesseval.dataset.materialize import materialize
from harnesseval.finding import Finding
from harnesseval.cli_backends import session_timeout, is_transient_claude_error, codex_slug_for

SUPERPOWERS_ROOT = Path(__file__).resolve().parents[2] / "third_party" / "superpowers"

# The realistic orchestration prompt — instructs the host agent (with the Superpowers plugin
# installed) to perform the `requesting-code-review` skill: dispatch a `general-purpose`
# code-reviewer subagent with the code-reviewer.md template on the git range. We inline the
# code-reviewer.md template so the subagent gets exactly the methodology the skill ships,
# regardless of whether the host has already loaded it — the plugin's skill discovery is best-
# effort under headless `claude -p`; inlining guarantees the methodology is invoked faithfully.
REALISTIC_PROMPT = """You are a developer using the Superpowers `requesting-code-review` skill to review a local change before merging, as a user would.

You have the Superpowers plugin installed (the `requesting-code-review` skill). Use it to review the change.

Steps:
1. Get the git SHAs for the change under review:
   BASE_SHA=$(git rev-parse HEAD~1)
   HEAD_SHA=$(git rev-parse HEAD)
2. Dispatch a `general-purpose` code-reviewer SUBAGENT via your host's subagent-spawn tool \
   (in Claude Code that is the `Agent` tool; in Codex that is `collaboration.spawn_agent` then \
`collaboration.wait_agent` to collect the result) with the following prompt, filling the \
placeholders. Do NOT review the diff yourself in-session — the whole point of Superpowers is \
that the coordinator dispatches a reviewer subagent so the diff and the evaluation live in the \
subagent's context, and only the findings come back. Spawning a reviewer you then re-review \
duplicates the seat at full cost for nothing.

   Subagent prompt (fill [DESCRIPTION], [PLAN_OR_REQUIREMENTS], [BASE_SHA], [HEAD_SHA]):
   ----
   You are a Senior Code Reviewer with expertise in software architecture, design patterns, and \
best practices. Your job is to review completed work against its plan or requirements and \
identify issues before they cascade.

   ## What Was Implemented
   [DESCRIPTION]

   ## Requirements / Plan
   [PLAN_OR_REQUIREMENTS]

   ## Git Range to Review
   **Base:** [BASE_SHA]
   **Head:** [HEAD_SHA]
   Run: `git diff --stat [BASE_SHA]..[HEAD_SHA]` and `git diff [BASE_SHA]..[HEAD_SHA]` to see the change.

   ## Read-Only Review
   Your review is read-only. Do not mutate the working tree, the index, HEAD, or branch state. \
Use `git show`, `git diff`, `git log` to inspect history.

   ## You Do Not Dispatch Subagents
   Do all of this review yourself. Never spawn a subagent to review part of the diff, and never \
spawn another reviewer for a second opinion.

   ## What to Check
   - Plan alignment: does it match the intent? are deviations justified? is all intended \
functionality present?
   - Code quality: separation of concerns, error handling, type safety, DRY, edge cases.
   - Architecture: sound design, scalability, performance, security, integration.
   - Testing: real behavior (not mocks), edge cases, integration tests, all passing.
   - Production readiness: migration strategy, backward compatibility, documentation, no bugs.

   ## Calibration
   Categorize issues by ACTUAL severity. Not everything is Critical. Acknowledge what was done \
well before listing issues.

   ## Output Format
   ### Strengths
   ### Issues
   #### Critical (Must Fix)
   #### Important (Should Fix)
   #### Minor (Nice to Have)
   For each issue: File:line reference, What's wrong, Why it matters, How to fix.
   ### Assessment
   **Ready to merge?** [Yes | No | With fixes]
   **Reasoning:** [1-2 sentence technical assessment]
   ----

   IMPORTANT: Write your full review report directly to the file {findings_path} yourself (using
   your file-writing tool). Do NOT return the report as your reply message — the report can be
   too long for a single message. After writing the file, return ONLY: "Wrote report to
   {findings_path}" as your reply.

3. Fill the placeholders from the repo:
   - [DESCRIPTION]: a one-line summary of the PR: {pr_title}
   - [PLAN_OR_REQUIREMENTS]: "The PR title states the intent: {pr_title}. Review against that intent and production-readiness standards."
   - [BASE_SHA]: the BASE_SHA from step 1
   - [HEAD_SHA]: the HEAD_SHA from step 1
4. The subagent writes its report directly to {findings_path} (instructed in its prompt above).
   Collect only the subagent's one-line ack — do NOT collect a full report in-message.
5. Return ONLY: "Done. Report at {findings_path}". Do NOT repeat the findings."""

NAIVE_REALISTIC_PROMPT = """Review the code change in this repository (the diff is HEAD~1..HEAD).
Run `git diff HEAD~1` to see it. List each distinct issue you find, one per line, with file:line.
Be thorough but only report real issues you are confident about."""


# ---- host config: install the real plugin for a throwaway headless session ----

def _claude_plugins_dir() -> Path:
    """A throwaway plugins dir we point claude -p at via CLAUDE_PLUGIN_PATH. Lives in .cache."""
    d = Path(__file__).resolve().parents[2] / ".cache" / "claude_plugins"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _install_superpowers_claude_plugin() -> Path:
    """Symlink the real Superpowers plugin into a throwaway Claude Code plugin dir. Returns dir.

    Claude Code discovers plugins from ~/.claude/plugins or CLAUDE_PLUGIN_PATH. We point a
    headless `claude -p` session at an isolated plugins dir (via env) containing a symlink to
    the real plugin checkout, so the session sees the genuine requesting-code-review skill + the
    code-reviewer.md template — exactly what a user with the plugin installed gets. This is
    best-effort: even if the host doesn't auto-load the skill, the inlined prompt above carries
    the verbatim methodology, so the review methodology is invoked faithfully either way.
    """
    pd = _claude_plugins_dir()
    link = pd / "superpowers"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(SUPERPOWERS_ROOT)
    return pd


async def _run_claude_session(repo_dir: Path, model_alias: str, effort: str, prompt: str,
                              max_turns: int = 12, timeout: int = 900) -> tuple[str, dict, str]:
    """Run a real multi-turn `claude -p` session with the Superpowers plugin installed.

    Returns (text, per_model_usage, resolved_model). Mirrors metareview_realistic._run_claude_session.
    """
    from harnesseval.cli_backends import _parse_claude_effort, _parse_codex_effort, session_timeout
    plugins_dir = _install_superpowers_claude_plugin()
    args = ["claude", "-p", "--model", model_alias, "--effort", _parse_claude_effort(effort),
            "--output-format", "json", "--max-turns", str(max_turns),
            "--dangerously-skip-permissions",  # allow git + bash + subagent dispatch in the throwaway repo
            "--append-system-prompt",
            "You are a developer using the Superpowers plugin. Use the requesting-code-review "
            "skill: dispatch a general-purpose code-reviewer subagent for the diff; do NOT review "
            "it in-session. Use tools (Bash, Read, Agent/subagents) as needed."]
    args += [prompt]
    env = {**os.environ, "CLAUDE_PLUGIN_PATH": str(plugins_dir)}
    proc = None
    for attempt in (1, 2):  # one retry on transient Claude API error (529/rate-limit)
        proc = await asyncio.to_thread(subprocess.run, args, capture_output=True, text=True,
                                       timeout=timeout, cwd=str(repo_dir), env=env)
        if not is_transient_claude_error(proc.returncode, proc.stdout, proc.stderr):
            break
        if attempt == 1:
            await asyncio.sleep(20)
    if proc.returncode != 0:
        raise RuntimeError(f"claude -p failed: {proc.stderr.strip()[:300]}")
    d = json.loads(proc.stdout)
    result = d.get("result", "")
    if isinstance(result, str) and result.strip().startswith("API Error: 5"):
        raise RuntimeError(f"claude -p transient overload persisted after retry: {result[:120]}")
    mu = d.get("modelUsage") or {}
    resolved = ",".join(mu.keys()) if isinstance(mu, dict) and mu else ""
    from harnesseval.usage import from_claude_cli
    return result, from_claude_cli(d), resolved


async def _run_codex_session(repo_dir: Path, model_slug: str, effort: str, prompt: str,
                             timeout: int = 900) -> tuple[str, dict, str]:
    """Run a real multi-turn `codex exec` session. Returns (text, per_model_usage, slug).

    Codex doesn't have a Superpowers plugin shim the way Claude Code does, but its subagent
    dispatch tool lets the coordinator dispatch a reviewer subagent the same way — we inline the
    methodology prompt so the subagent gets the verbatim code-reviewer.md template regardless.
    """
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


def _extract_findings_from_session(text: str) -> list[Finding]:
    """Parse the Superpowers reviewer report into atomic Findings.

    The code-reviewer.md output has severity-grouped sections (#### Critical / Important / Minor)
    each with numbered issues. We extract each issue line (file:line + what's wrong) as a Finding
    and tag source with the severity for the decomposition. Fallback: numbered/bulleted issue lines.
    """
    findings: list[Finding] = []
    current_sev: str | None = None
    for line in text.splitlines():
        raw = line.rstrip()
        stripped = raw.strip()
        if not stripped:
            continue
        # severity section headers
        m_sev = re.match(r"^#+\s*(Critical|Important|Minor)\b", stripped, re.I)
        if m_sev:
            current_sev = m_sev.group(1).lower()
            continue
        if re.match(r"^#+\s*(Strengths|Assessment|Recommendations)\b", stripped, re.I):
            current_sev = None
            continue
        # numbered issue line: "1. file.py:42 — desc" or "- file.py:42 — desc"
        m_item = re.match(r"^(?:\d+\.\s+|[-*]\s+)(.+)$", stripped)
        if m_item and current_sev:
            issue = m_item.group(1).strip()
            # skip non-issue lines (headings, meta)
            if re.match(r"^(File|For each issue|What's wrong|Why it matters|How to fix)", issue, re.I):
                continue
            if len(issue) < 8:
                continue
            src = f"superpowers-realistic/{current_sev}"
            findings.append(Finding(issue_text=issue, source=src, severity=current_sev,
                                     category="bug", raw=raw))
            continue
        # fallback: a bare line with a file:line reference under a severity header
        if current_sev and re.search(r"[\w/.\-]+\.(?:py|go|ts|js|rb|java|rs|c|cpp|jsx|tsx):\d+", stripped):
            if len(stripped) < 8:
                continue
            findings.append(Finding(issue_text=stripped, source=f"superpowers-realistic/{current_sev}",
                                     severity=current_sev, category="bug", raw=raw))
    # fallback: if no severity sections found, extract any line with file:line
    if not findings:
        for line in text.splitlines():
            stripped = line.strip()
            if re.search(r"[\w/.\-]+:\d+", stripped) and not stripped.startswith(("#", "```", "**")):
                findings.append(Finding(issue_text=stripped, source="superpowers-realistic", raw=line))
    return findings


def review_realistic(pr: PRSample, model: str, effort: str = "medium") -> ReviewRun:
    """Realistic Superpowers: drive the real plugin in a host agent (OAuth, multi-turn + subagent)."""
    return asyncio.run(review_realistic_async(pr, model, effort))


async def review_realistic_async(pr: PRSample, model: str, effort: str = "medium") -> ReviewRun:
    t0 = time.time()
    name = "superpowers-realistic"
    ml = model.lower()
    is_claude = any(k in ml for k in ("opus", "sonnet", "fable", "haiku", "claude"))
    is_codex = "gpt" in ml or "codex" in ml
    try:
        repo_dir = materialize(pr.url)
        # §output-cap fix: write findings to a file (unbounded) instead of returning in the final
        # message (which overflows the model's per-message output cap on hard PRs).
        findings_path = repo_dir / "findings.md"
        try: findings_path.unlink()
        except FileNotFoundError: pass
        prompt = REALISTIC_PROMPT.format(pr_title=pr.pr_title, findings_path=str(findings_path))
        if is_claude:
            alias = "opus" if "opus" in ml else "sonnet" if "sonnet" in ml else "fable" if "fable" in ml else "sonnet"
            text, per_model, resolved = await _run_claude_session(repo_dir, alias, effort, prompt,
                                                                 timeout=session_timeout(effort, base=900))
        elif is_codex:
            slug = codex_slug_for(model)  # gpt-5.6-* pass through; gpt-5.2/gpt-5 fall back to gpt-5.6-sol
            text, per_model, resolved = await _run_codex_session(repo_dir, slug, effort, prompt,
                                                                timeout=session_timeout(effort, base=900))
        else:
            # GLM/Kimi: no realistic CLI; fall back to api-direct superpowers (recorded as api-fallback)
            from harnesseval.adapters import superpowers as sp
            r = await sp.review_async(pr, model=model, effort=effort, mode="api")
            return ReviewRun(framework=name, model=model, effort=effort, execution_mode="api-fallback",
                             raw_output=r.raw_output, findings=r.findings, tokens_in=r.tokens_in,
                             tokens_out=r.tokens_out, wall_ms=r.wall_ms)
    except Exception as e:  # noqa: BLE001
        return ReviewRun(framework=name, model=model, effort=effort, execution_mode="cli",
                         raw_output="", wall_ms=(time.time() - t0) * 1000, error=str(e))
    # §output-cap fix: prefer findings written to the file; fall back to session text if absent.
    file_text = ""
    try:
        if findings_path.exists(): file_text = findings_path.read_text()
    except Exception:
        file_text = ""
    findings = _extract_findings_from_session(file_text if file_text.strip() else text)
    from harnesseval.usage import grand_total
    gt = grand_total(per_model)
    # Realistic Claude Code behavior: coordinator on the requested model, but `general-purpose`
    # subagent dispatch defaults to Haiku regardless of --model (SPEC §6.3.1). `resolved` captures
    # the full modelUsage set (e.g. 'claude-haiku-4-5-20251001,claude-opus-5'). Record honestly.
    return ReviewRun(framework=name, model=(resolved or model), effort=effort, execution_mode="cli",
                     raw_output=text, findings=findings, tokens_in=gt["total_tokens"],
                     tokens_out=sum(u.get("output_tokens", 0) for u in per_model.values()),
                     wall_ms=(time.time() - t0) * 1000, per_model_usage=per_model,
                     total_cost_usd=gt["total_cost_usd"])
