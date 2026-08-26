"""Realistic Compound Engineering adapter — drives the real plugin in a host agent as a user runs it.

Per docs/SPEC.md §2 (realistic mode) + §7 (cli column): test the Compound Engineering review
capability as a USER uses it — the real `EveryInc/compound-engineering-plugin` plugin installed in
a host agent (`claude -p` or `codex exec`), invoked naturally, with the real agent loop + persona
subagent dispatch + synthesis — NOT a stripped-down methodology prompt (that's the api-direct
secondary column, compound.py).

Realistic flow (matches skills/ce-code-review/SKILL.md @ pinned SHA):
  1. Materialize the PR diff into a throwaway git repo (dataset/materialize.py) — unchanged.
  2. Install the real Compound Engineering plugin into a throwaway host config and run a real
     `claude -p` / `codex exec` agentic session that:
     a. resolves the review scope (the diff: HEAD~1..HEAD);
     b. writes the intent summary (the PR title);
     c. selects the risk-driven persona roster (correctness always-on + conditionals by diff
        signals) per references/select-and-route.md;
     d. dispatches each selected persona as a PARALLEL SUBAGENT (Claude Code `Agent` tool /
        Codex subagent dispatch) seeded with the persona prompt from references/personas/;
     e. synthesizes the findings (severity P0-P3 + confidence anchors) into the report per
        references/review-output-template.md + references/finish-review.md.
  3. Capture the real transcript + real token/time cost (incl. subagent fanout) — this is what a
     user actually pays, not an idealized per-persona API-call cost. Per SPEC §6.3.1, Claude Code
     routes `general-purpose` persona subagent dispatches to Haiku by default regardless of
     --model, so "compound-realistic @ opus" = opus orchestrator + Haiku persona subagents (the
     realistic default — record it honestly via per_model_usage, do not force anything).

The scoring pipeline (extract -> judge -> score -> adjudicate) is identical regardless of how the
reviewer arm ran, so A.1/A.3 calibration still holds. Only the reviewer-arm execution changed.

Methodology source (auditable): third_party/compound-engineering-plugin @ SHA
a32c9474c658f3e33b6e3615a5d51089046d4c79
  - skills/ce-code-review/SKILL.md (the skill spine)
  - skills/ce-code-review/references/persona-catalog.md (roster + selection gates)
  - skills/ce-code-review/references/select-and-route.md (selection rules)
  - skills/ce-code-review/references/personas/*.md (the persona prompts)
  - skills/ce-code-review/references/review-output-template.md (the synthesized report shape)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import time
from pathlib import Path

from harnesseval.adapters.base import PRSample, ReviewRun
from harnesseval.dataset.materialize import materialize
from harnesseval.finding import Finding
from harnesseval.cli_backends import session_timeout, is_transient_claude_error, codex_slug_for

COMPOUND_ROOT = Path(__file__).resolve().parents[2] / "third_party" / "compound-engineering-plugin"

# The realistic orchestration prompt — instructs the host agent (with the Compound Engineering
# plugin installed) to perform the `ce-code-review` skill: select the risk-driven persona roster,
# dispatch each persona as a parallel subagent, and synthesize the report. We inline the persona
# catalog + the report shape so the methodology is invoked faithfully regardless of whether the
# host auto-loaded the skill (headless `claude -p` skill discovery is best-effort).
REALISTIC_PROMPT = """You are a developer using the Compound Engineering `ce-code-review` skill to review a local change, as a user would.

You have the Compound Engineering plugin installed (the `ce-code-review` skill). Use it to review the change HEAD~1..HEAD in this repository. Report only; do NOT apply or push anything.

Steps:
1. Read the diff: run `git diff HEAD~1` and `git diff --stat HEAD~1`.
2. Write a one-line intent summary from the PR title: {pr_title}
3. Select the risk-driven reviewer roster per the persona catalog:
   - ALWAYS spawn `correctness` (logic/behavioral correctness — off-by-one, null propagation, races, state transitions, broken error propagation).
   - Spawn conditionals ONLY when the diff shows their concrete surface:
     - `security`: auth, public endpoints, user input, permissions, secrets.
     - `performance`: db queries, unbounded materialization, caching, large transforms.
     - `api-contract`: externally consumed boundary changes (routes, serializers, schemas, versioning).
     - `reliability`: error handling, retries, timeouts, background jobs, async handlers.
     - `testing`: test files changed, OR meaningful runtime behavior changed without test work.
     - `maintainability`: large/structural diff (>=200 changed lines), new abstractions, file moves.
     - `data-migration`: migration files / schema dumps / backfills in the diff.
     - `adversarial`: >=50 changed code lines, OR auth/payments/persistence/event/external-api, OR a silent-pass verification mechanism (a CI/gate that can go green while the real thing is red).
   This is judgment, not keyword matching. Announce the team with a one-line justification per conditional reviewer.
4. Dispatch each selected persona as a PARALLEL SUBAGENT via your host's subagent-spawn \
   tool (in Claude Code that is the `Agent` tool with run_in_background=true, one `Agent` call \
   per persona, then collect each result; in Codex that is `collaboration.spawn_agent` — one \
   spawn per persona — then `collaboration.wait_agent` to collect each result). Do NOT review \
   in-session — the orchestrator dispatches persona subagents and only synthesizes their \
   findings. Give each subagent its persona focus (below) + the diff.
   Persona focuses:
   - correctness: off-by-one/boundary errors; null/undefined propagation; sentinel meaning changes; \
race conditions; incorrect state transitions; broken error propagation.
   - security: authz/authn gaps (IDOR, missing ownership checks); injection/SSRF/path traversal; \
secret/credential handling; permission checks.
   - performance: unbounded queries/materialization; N+1; missing pagination; large in-memory \
transforms; cache policy with material resource impact.
   - api-contract: externally consumed boundary changes without caller consideration; response \
shape drift; versioning.
   - reliability: error handling gaps; retry errors; missing timeouts; background-job/async issues.
   - testing: tests verifying mocks not real behavior; missing edge-case coverage; behavioral \
change without test work.
   - maintainability: coupling/type-boundary leaks; premature abstraction; duplication; dead code.
   - data-migration: destructive DDL without rollback; backfill gaps; NOT NULL without default.
   - adversarial: silent-pass verification mechanisms; cascade failures; abuse cases; \
partial-failure/ordering bugs; race conditions.
   Each persona returns findings as: severity P0/P1/P2/P3, file:line, what's wrong, why it matters, \
confidence anchor (0/25/50/75/100).
5. Each persona subagent must WRITE its own findings directly to a per-persona file \
   {findings_path}.<persona> (e.g. {findings_path}.correctness) as it finishes — one finding per \
   line in this exact format: `| P{{sev}} | file:line | issue (one short sentence) | <persona> | <confidence> |`. \
   Do NOT return findings to the orchestrator in-message — write them to the file. This keeps each \
   message small (the combined report can exceed the model output limit).
6. After all persona subagents finish, concatenate their per-persona files into {findings_path} \
   yourself by running: `cat {findings_path}.* > {findings_path}`. Do NOT read or synthesize the \
   findings in-session — just concatenate the files.
7. Return ONLY this one line as your reply: "Wrote N findings to {findings_path}". Do NOT repeat \
   the findings in your reply message — they live in the file. This keeps your final message small."""


def _claude_plugins_dir() -> Path:
    """A throwaway plugins dir we point claude -p at via CLAUDE_PLUGIN_PATH. Lives in .cache."""
    d = Path(__file__).resolve().parents[2] / ".cache" / "claude_plugins"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _install_compound_claude_plugin() -> Path:
    """Symlink the real Compound Engineering plugin into a throwaway Claude Code plugin dir.

    Best-effort: even if the host doesn't auto-load the skill, the inlined prompt above carries
    the verbatim methodology + persona catalog, so the review methodology is invoked faithfully.
    """
    pd = _claude_plugins_dir()
    link = pd / "compound-engineering"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(COMPOUND_ROOT)
    return pd


async def _run_claude_session(repo_dir: Path, model_alias: str, effort: str, prompt: str,
                              max_turns: int = 16, timeout: int = 1200) -> tuple[str, dict, str]:
    """Run a real multi-turn `claude -p` session with the Compound Engineering plugin installed.

    Returns (text, per_model_usage, resolved_model). max_turns higher than superpowers —
    ce-code-review dispatches N persona subagents + synthesis, so the orchestrator needs more
    turns. Mirrors metareview_realistic._run_claude_session.
    """
    from harnesseval.cli_backends import _parse_claude_effort, _parse_codex_effort, session_timeout
    plugins_dir = _install_compound_claude_plugin()
    args = ["claude", "-p", "--model", model_alias, "--effort", _parse_claude_effort(effort),
            "--output-format", "json", "--max-turns", str(max_turns),
            "--dangerously-skip-permissions",  # allow git + bash + subagent dispatch in the throwaway repo
            "--append-system-prompt",
            "You are a developer using the Compound Engineering plugin. Use the ce-code-review "
            "skill: select the risk-driven persona roster, dispatch each persona as a parallel "
            "subagent, and synthesize the report. Do NOT review in-session. Use tools (Bash, Read, "
            "Agent/subagents) as needed."]
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
                             timeout: int = 1200) -> tuple[str, dict, str]:
    """Run a real multi-turn `codex exec` session. Returns (text, per_model_usage, slug)."""
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
    """Parse the Compound ce-code-review synthesized report into atomic Findings.

    The report (references/review-output-template.md) has severity-grouped sections
    (### P0 -- Critical / P1 -- High / P2 -- Moderate / P3 -- Low) with table rows or keyed
    detail lines:
      | # | file:line | issue | reviewer | confidence |
      - **#N** — issue at file:line ...
    We extract each finding row, tag source with the persona + severity. Fallback: any line
    with a file:line reference.
    """
    findings: list[Finding] = []
    current_sev: str | None = None
    for line in text.splitlines():
        raw = line.rstrip()
        stripped = raw.strip()
        if not stripped:
            continue
        # flat per-persona format (output-cap fix): `| P0 | file:line | issue | persona | confidence |`
        # one line per finding, severity inline — no section headers needed.
        m_flat = re.match(r"^\|\s*P([0-3])\s*\|\s*(`?[\w/ .\-]+(?::\d+)?`?)\s*\|\s*(.+?)\s*\|\s*([\w-]+)\s*\|\s*(0|25|50|75|100)\s*\|$",
                          stripped)
        if m_flat:
            sev = f"p{m_flat.group(1)}"; file_cell = m_flat.group(2).strip("` ")
            issue = m_flat.group(3).strip().strip("` ").strip(); reviewer = m_flat.group(4)
            if issue and len(issue) > 3:
                issue = f"{file_cell} — {issue}" if file_cell else issue
                src = f"compound-realistic/{sev}/{reviewer}"
                findings.append(Finding(issue_text=issue, source=src, severity=sev, category="bug", raw=raw))
            continue
        # severity section headers: "### P0 -- Critical" etc.
        m_sev = re.match(r"^#+\s*P([0-3])\b.*?(Critical|High|Moderate|Low)?", stripped, re.I)
        if m_sev:
            current_sev = f"p{m_sev.group(1)}"
            continue
        if re.match(r"^#+\s*(Coverage|Verdict|Strengths|Actionable|Pre-existing|Learnings|Deployment|Applied|Triage|Agent-Native)\b",
                    stripped, re.I):
            current_sev = None
            continue
        # table row: | # | file:line | issue | reviewer | confidence |
        if current_sev and stripped.startswith("|") and not re.match(r"^\|[\s\-|]+\|$", stripped):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            # header row?
            if cells and any(h.lower() in ("file", "issue", "reviewer", "confidence", "route", "notes", "fix")
                           for h in cells) and not any(re.match(r"^[`\w/ .\-]+:\d+", c) for c in cells):
                continue
            if len(cells) >= 3:
                # classify cells
                file_cell = next((c for c in cells if re.match(r"^[`\w/ .\-]+:\d+", c)), "")
                reviewer = next((c for c in cells if c.lower() in
                                 ("correctness", "security", "performance", "api-contract", "reliability",
                                  "testing", "maintainability", "data-migration", "adversarial")), "")
                # candidate issue cells: not the #/index, not file:line, not reviewer, not a
                # confidence anchor, not a route like 'gated_auto -> downstream-resolver'
                skip = {file_cell, reviewer}
                issue_cells = [c for c in cells
                               if c and c not in skip
                               and not re.fullmatch(r"#?\d*", c)
                               and not re.fullmatch(r"(0|25|50|75|100)", c)
                               and not re.match(r"^(gated_auto|manual|advisory)\s*->", c)
                               and c.lower() not in ("reviewer", "confidence", "file", "issue",
                                                    "route", "notes", "fix", "#")]
                issue = (issue_cells[0] if issue_cells else "").strip()
                if issue and len(issue) > 4:
                    # prefix the file:line so the Martian judge sees location context (matches
                    # the keyed-detail shape the template uses: `- **#N** — issue at file:line`)
                    if file_cell:
                        issue = f"{file_cell.strip('` ')} — {issue}"
                    src = (f"compound-realistic/{current_sev}/{reviewer}"
                           if reviewer else f"compound-realistic/{current_sev}")
                    findings.append(Finding(issue_text=issue, source=src, severity=current_sev,
                                            category="bug", raw=raw))
            continue
        # keyed detail line: "- **#N** — issue at file:line"
        if current_sev:
            m_key = re.match(r"^[-*]\s*\*\*#?\d+\**\s*[—-]\s*(.+)$", stripped)
            if m_key:
                issue = m_key.group(1).strip()
                if len(issue) > 6:
                    findings.append(Finding(issue_text=issue, source=f"compound-realistic/{current_sev}",
                                             severity=current_sev, category="bug", raw=raw))
                continue
            # bare file:line line under a severity header
            if re.search(r"[\w/.\-]+:\d+", stripped) and not stripped.startswith(("```", "**Verdict")):
                if len(stripped) > 6:
                    findings.append(Finding(issue_text=stripped, source=f"compound-realistic/{current_sev}",
                                             severity=current_sev, category="bug", raw=raw))
    # fallback: if no severity sections found, extract any line with file:line
    if not findings:
        for line in text.splitlines():
            stripped = line.strip()
            if re.search(r"[\w/.\-]+:\d+", stripped) and not stripped.startswith(("#", "```", "**")):
                findings.append(Finding(issue_text=stripped, source="compound-realistic", raw=line))
    return findings


def review_realistic(pr: PRSample, model: str, effort: str = "medium") -> ReviewRun:
    """Realistic Compound: drive the real plugin in a host agent (OAuth, multi-turn + subagents)."""
    return asyncio.run(review_realistic_async(pr, model, effort))


async def review_realistic_async(pr: PRSample, model: str, effort: str = "medium") -> ReviewRun:
    t0 = time.time()
    name = "compound-realistic"
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
                                                                 timeout=session_timeout(effort, base=1200))
        elif is_codex:
            slug = codex_slug_for(model)  # gpt-5.6-* pass through; gpt-5.2/gpt-5 fall back to gpt-5.6-sol
            text, per_model, resolved = await _run_codex_session(repo_dir, slug, effort, prompt,
                                                                timeout=session_timeout(effort, base=1200))
        else:
            # GLM/Kimi: no realistic CLI; fall back to api-direct compound (recorded as api-fallback)
            from harnesseval.adapters import compound as cp
            r = await cp.review_async(pr, model=model, effort=effort, mode="api")
            return ReviewRun(framework=name, model=model, effort=effort, execution_mode="api-fallback",
                             raw_output=r.raw_output, findings=r.findings, tokens_in=r.tokens_in,
                             tokens_out=r.tokens_out, wall_ms=r.wall_ms)
    except Exception as e:  # noqa: BLE001
        return ReviewRun(framework=name, model=model, effort=effort, execution_mode="cli",
                         raw_output="", wall_ms=(time.time() - t0) * 1000, error=str(e))
    # §output-cap fix: prefer findings written to the file; fall back to session text if absent.
    # Each persona writes to {findings_path}.<persona>; the orchestrator concatenates them via
    # `cat {findings_path}.* > {findings_path}`. If the orchestrator didn't run that, do it here.
    file_text = ""
    try:
        if findings_path.exists():
            file_text = findings_path.read_text()
        if not file_text.strip():
            # orchestrator may not have concatenated — gather per-persona files ourselves
            per_persona = sorted(findings_path.parent.glob(f"{findings_path.name}.*"))
            if per_persona:
                file_text = "\n".join(p.read_text() for p in per_persona)
    except Exception:
        file_text = ""
    findings = _extract_findings_from_session(file_text if file_text.strip() else text)
    from harnesseval.usage import grand_total
    gt = grand_total(per_model)
    # Realistic Claude Code behavior: orchestrator on the requested model, persona subagent
    # dispatch defaults to Haiku regardless of --model (SPEC §6.3.1). `resolved` captures the
    # full modelUsage set (e.g. 'claude-haiku-4-5-20251001,claude-opus-5'). Record honestly.
    return ReviewRun(framework=name, model=(resolved or model), effort=effort, execution_mode="cli",
                     raw_output=text, findings=findings, tokens_in=gt["total_tokens"],
                     tokens_out=sum(u.get("output_tokens", 0) for u in per_model.values()),
                     wall_ms=(time.time() - t0) * 1000, per_model_usage=per_model,
                     total_cost_usd=gt["total_cost_usd"])
