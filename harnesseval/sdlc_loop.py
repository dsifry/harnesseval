"""SDLC loop prototype — structured (discover → adjudicate → fix → repeat) vs unstructured control.

Both conditions use the SAME model (claude-opus-5) so the only variable is the PROCESS.

Structured loop (the §8.1 recommendation from docs/FRAMEWORK_COMPARISON.md):
  each iteration:
    (b) discover   — run the ACTUAL metareview-realistic adapter (same REALISTIC_PROMPT,
                      same _run_claude_session, same _extract_findings_from_session) on the
                      current repo state. Reuses the eval's discovery path verbatim.
    (c) adjudicate — judge candidates vs goldens (cross-family, judge.py) + reclassify
                      unmatched into real-but-ungold vs hallucination (adjudicate.py). The
                      survivors = the confirmed bug list.
    measure        — recall / confirmed / hidden-gold / hallucinations / tokens for this iter.
    (d) fix        — run a `claude -p` session that edits the repo to fix the confirmed bugs,
                      adds a test for each, and commits. (d) is the only new step.
  loop until the confirmed-bug count stops growing (convergence) or max_iterations.

Control loop (the unstructured baseline):
  one long autonomous `claude -p --max-turns N` session with a single prompt:
    "review this code, find bugs, fix each, add tests, keep going until you're confident."
  The agent's OWN judgment for when to stop. No explicit discover/adjudicate/fix staging,
  no confirmed-bug list. This is "vanilla model with /loop" — the agent loops itself.

Final measurement (both): a "goldens still present in the fixed code" judge pass — for each
golden, judge whether the bug it describes still exists in the final diff. Compares
bugs-fixed, total tokens, wall time, and (for structured) per-iteration convergence.

Reuses: harnesseval.adapters.metareview_realistic (discovery), harnesseval.judge +
harnesseval.adjudicate (scoring), harnesseval.dataset.materialize (repo), run_model_matrix
helpers (judge routing). The ONLY new code is the fix step + the loop orchestration.
"""

from __future__ import annotations
import asyncio, json, shutil, subprocess, time, os
from pathlib import Path
from dataclasses import dataclass, field

from harnesseval.adapters.metareview_realistic import (
    REALISTIC_PROMPT, MRV_BIN, _run_claude_session, _run_codex_session, _extract_findings_from_session,
)
from harnesseval.adapters.base import PRSample
from harnesseval.judge import judge_pairs_router, score_from_matches
from harnesseval.adjudicate import reclassify_async
from harnesseval.cli_backends import session_timeout, codex_slug_for
from harnesseval.dataset.materialize import materialize

def _is_codex(model: str) -> bool:
    m = model.lower(); return "gpt" in m or "codex" in m

def _claude_alias(model: str) -> str:
    m = model.lower()
    return "opus" if "opus" in m else "sonnet" if "sonnet" in m else "fable" if "fable" in m else "sonnet"

async def _run_session(work: Path, model_full: str, effort: str, prompt: str,
                       max_turns: int = 12, timeout: int = 900, phase: str = "",
                       tag: str = "") -> tuple[str, dict, str]:
    """Generic host-agent session: claude -p OR codex exec, picked by model_full. Returns
    (text, per_model_usage, resolved_model). Routes through the SAME session helpers the
    mrv adapter uses, so discovery/fix on Codex is the eval's real Codex path. Captures the
    full JSONL transcript (claude ~/.claude/projects, codex ~/.codex/sessions) into
    results/sdlc_sessions/ for later analysis."""
    started = time.time()
    if _is_codex(model_full):
        text, pm, resolved = await _run_codex_session(work, codex_slug_for(model_full), effort, prompt, timeout=timeout)
    else:
        text, pm, resolved = await _run_claude_session(work, _claude_alias(model_full), effort, prompt,
                                      max_turns=max_turns, timeout=timeout)
    if phase and tag:
        _capture_session_transcripts(work, model_full, phase, tag, started)
    return text, pm, resolved

GIT_ENV = {**os.environ, "GIT_AUTHOR_NAME": "x", "GIT_AUTHOR_EMAIL": "x@x",
           "GIT_COMMITTER_NAME": "x", "GIT_COMMITTER_EMAIL": "x@x"}

def _log(tag: str, msg: str):
    """Verbose progress logger — prints to stdout with timestamp + tag. Zero token cost (Python
    print, not a prompt change). tag identifies the condition so parallel runs are distinguishable."""
    ts = time.strftime("%H:%M:%S", time.localtime())
    print(f"  [{ts}] {tag} {msg}", flush=True)

# ---- session-transcript capture (for later analysis) ---------------------------------
# claude -p and codex exec both save full JSONL transcripts to ~/.claude/projects/<cwd>/<uuid>.jsonl
# and ~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<uuid>.jsonl. We snapshot the newest one(s) into
# results/sdlc_sessions/<run-id>/ after each session so the experiment is fully auditable later.
SESSIONS_DIR = Path(__file__).resolve().parents[1] / "results" / "sdlc_sessions"

def _claude_project_dir(cwd: Path) -> Path:
    """The escaped-cwd project dir claude uses (~/.claude/projects/-escaped-cwd)."""
    home = Path.home()
    escaped = "/" + str(cwd).replace("/", "-")
    return home / ".claude" / "projects" / escaped

def _capture_session_transcripts(cwd: Path, model_full: str, phase: str, tag: str,
                                 started_at: float) -> list[str]:
    """Snapshot the newest claude/codex session JSONL(s) created since `started_at` into
    results/sdlc_sessions/<tag>_<phase>/. Returns the list of copied paths. Captures claude
    subagent transcripts too (the mrv lens subagents live in <session-uuid>/subagents/)."""
    try:
        out_dir = SESSIONS_DIR / f"{tag.replace('/', '_')}_{phase}"
        out_dir.mkdir(parents=True, exist_ok=True)
        copied = []
        if _is_codex(model_full):
            codex_sess = Path.home() / ".codex" / "sessions"
            files = [f for f in codex_sess.rglob("rollout-*.jsonl") if f.stat().st_mtime >= started_at]
            for f in files:
                dest = out_dir / f.name
                shutil.copy2(f, dest); copied.append(str(dest))
        else:
            proj = _claude_project_dir(cwd)
            if proj.exists():
                # newest session jsonl(s) created since started_at
                files = [f for f in proj.glob("*.jsonl") if f.stat().st_mtime >= started_at]
                for f in files:
                    dest = out_dir / f.name
                    shutil.copy2(f, dest); copied.append(str(dest))
                    # also capture subagent transcripts for this session
                    sub_dir = f.with_suffix("") / "subagents"
                    if sub_dir.exists():
                        sub_dest = out_dir / f.stem / "subagents"
                        sub_dest.mkdir(parents=True, exist_ok=True)
                        for sf in sub_dir.glob("*.jsonl"):
                            shutil.copy2(sf, sub_dest / sf.name); copied.append(str(sub_dest / sf.name))
        if copied:
            _log(tag, f"captured {len(copied)} session transcript(s) -> {out_dir}")
        return copied
    except Exception as e:
        _log(tag, f"transcript capture failed: {e}")
        return []

# ---- the two new prompts (fix + control) -----------------------------------------------

FIX_PROMPT = """You are fixing confirmed bugs in a local code change. Edit the files directly.

The diff under review (base..HEAD):
```diff
{diff}
```

Confirmed bugs to fix (adjudicated real; fix EACH one):
{bug_list}

Instructions:
- Edit the source files in this repo to fix every confirmed bug above. Make the minimal,
  correct fix for each. Do NOT rewrite unrelated code.
- Add or update a test that would catch each bug (in the repo's test files, or a new test
  file if none exists). The test should FAIL on the buggy code and PASS after your fix.
- Stage and commit ALL your changes with: git add -A && git commit -m "fix: N confirmed bugs"
- Do NOT push. Do NOT amend previous commits. Do NOT run the test suite (just write the tests).
- Be terse. Do NOT narrate. When done, reply with ONLY: "Fixed N bugs, committed."

Confirmed bug {n}:"""
CONTROL_PROMPT = """/goal Review the git diff in this repo (base..HEAD) for bugs, security issues, correctness problems, and missing tests. PR title (the intent): {pr_title}

For each bug you find:
- Fix it directly in the source files (minimal, correct fix)
- Add or update a test that would catch it (should FAIL on the buggy code, PASS after your fix)
- Commit each fix: `git add -A && git commit -m "fix: <one-line>"`

After fixing everything, RE-REVIEW the updated code. If you find more bugs, fix and test those too. Keep reviewing and fixing in a loop until you are confident the code is correct and well-tested.

Do NOT push. Do NOT amend. Do NOT run the test suite (just write the tests). Be terse. Start now."""

# Codex has no /goal slash-command, but loops autonomously when asked to (verified 2026-08-26).
# Same instructions, no slash-command prefix.
CONTROL_PROMPT_CODEX = """Review the git diff in this repo (base..HEAD) for bugs, security issues, correctness problems, and missing tests. PR title (the intent): {pr_title}

For each bug you find:
- Fix it directly in the source files (minimal, correct fix)
- Add or update a test that would catch it (should FAIL on the buggy code, PASS after your fix)
- Commit each fix: `git add -A && git commit -m "fix: <one-line>"`

After fixing everything, RE-REVIEW the updated code. If you find more bugs, fix and test those too. Keep reviewing and fixing in a loop until you are confident the code is correct and well-tested.

Do NOT push. Do NOT amend. Do NOT run the test suite (just write the tests). Be terse. Start now."""


def _git(repo: Path, *a: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, env=GIT_ENV)
    return r.stdout.strip()

def _diff(repo: Path, base_ref: str = "mrv-pr^") -> str:
    """The diff under review: base..HEAD. Same context the adjudicator sees."""
    return subprocess.run(["git", "-C", str(repo), "diff", base_ref, "HEAD"],
                          capture_output=True, text=True, env=GIT_ENV).stdout

def _work_copy(repo_dir: Path, suffix: str = "sdlc-work") -> Path:
    """Copy a materialized repo so the loop can mutate it without the materialize cache reset.
    suffix distinguishes conditions (mrv/vanilla/control) so they don't clobber each other."""
    work = repo_dir.parent / (repo_dir.name + "-" + suffix)
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(repo_dir, work)
    _git(work, "tag", "-f", "mrv-pr", "HEAD")
    return work


# ---- structured loop steps -------------------------------------------------------------

async def _discover(work: Path, pr: PRSample, model_alias: str, effort: str,
                    base_ref: str = "mrv-pr^", framework: str = "metareview-realistic",
                    model_full: str = "claude-opus-5", tag: str = "") -> tuple[list, dict, str, int, int]:
    """Run a discovery adapter on `work` (a working copy at current HEAD).
    framework="metareview-realistic": the ACTUAL mrv adapter (REALISTIC_PROMPT + _run_claude_session +
      per-lens file extraction) on the working repo — the eval's discovery path, verbatim.
    framework="vanilla-engineered": the ACTUAL vanilla adapter (review_async, ENGINEERED_PROMPT,
      single model call on pr.diff) — same as the eval. A working copy isn't needed for vanilla
      (it reviews the diff, not the repo) but we keep the signature uniform.
    Returns (findings, per_model, resolved, tokens_in, tokens_out).
    """
    if framework == "vanilla-engineered":
        _log(tag, f"vanilla discovery: calling review_async ({model_full}/{effort})...")
        from harnesseval.adapters import vanilla
        from harnesseval.adapters.base import PRSample as _PR
        cur_diff = _diff(work, base_ref)
        cur_pr = _PR(url=pr.url, pr_title=pr.pr_title, source_repo=pr.source_repo,
                     diff=cur_diff, files=[], golden_comments=pr.golden_comments)
        run = await vanilla.review_async(cur_pr, model=model_full, effort=effort, mode="cli",
                                         variant="engineered")
        _log(tag, f"vanilla discovery done: {len(run.findings)} findings, error={run.error!r}")
        if run.error:
            return [], {}, model_full, 0, 0, 0, 0
        pm = run.per_model_usage or {}
        tin = run.tokens_in; tout = run.tokens_out
        cr = sum(u.get("cache_read_input_tokens", 0) for u in pm.values())
        cc = sum(u.get("cache_creation_input_tokens", 0) for u in pm.values())
        return run.findings, pm, (run.model or model_full), tin, tout, cr, cc
    # ---- metareview-realistic (default) ----
    _log(tag, f"mrv discovery: task commit + dispatching 8-lens session ({model_full}/{effort})...")
    # task commit on top of current HEAD (mirrors the adapter); diff reviewed is base..HEAD
    task_path = work / "docs" / "tasks" / "task-001.md"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(f"# Task: {pr.pr_title}\nReview the change.\n")
    findings_path = work / "docs" / "tasks" / "findings.md"
    try: findings_path.unlink()
    except FileNotFoundError: pass
    _git(work, "add", "-A")
    _git(work, "commit", "--quiet", "--allow-empty", "-m", "task")
    prompt = REALISTIC_PROMPT.format(mrv_bin=str(MRV_BIN), task_path=str(task_path),
                                     findings_path=str(findings_path), base_ref=base_ref)
    text, per_model, resolved = await _run_session(
        work, model_full, effort, prompt, max_turns=12, timeout=session_timeout(effort, base=900),
        phase="discover-iter", tag=tag)
    _log(tag, f"mrv discovery: session returned, extracting findings from files...")
    try:
        if findings_path.exists(): file_text = findings_path.read_text()
        if not file_text.strip():
            per_lens = sorted(findings_path.parent.glob(f"{findings_path.name}.*"))
            if per_lens: file_text = "\n".join(p.read_text() for p in per_lens)
    except Exception: file_text = ""
    findings = _extract_findings_from_session(file_text if file_text.strip() else text)
    _log(tag, f"mrv discovery: extracted {len(findings)} findings")
    tin = sum(u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
              + u.get("cache_creation_input_tokens", 0) for u in per_model.values())
    tout = sum(u.get("output_tokens", 0) for u in per_model.values())
    cache_read = sum(u.get("cache_read_input_tokens", 0) for u in per_model.values())
    cache_create = sum(u.get("cache_creation_input_tokens", 0) for u in per_model.values())
    return findings, per_model, resolved, tin, tout, cache_read, cache_create


async def _score(findings, pr: PRSample, judge_model: str, tag: str = "") -> dict:
    """Judge candidates vs goldens (cross-family) + adjudicate → scored with confirmed bugs.
    Preserves file:line from the Finding objects so the union dedup can group by location."""
    goldens = pr.golden_comments
    cand_texts = [f.issue_text for f in findings]
    # build issue_text → (file, line) map so confirmed_bugs carry location metadata
    text_to_loc = {f.issue_text: (f.file or "", f.line or 0) for f in findings}
    if not goldens or not cand_texts:
        return {"tp": 0, "fp": 0, "fn": len(goldens), "precision": 0, "recall": 0,
                "adjudicated_precision": 0.0, "incremental_recall": 0.0,
                "n_real_ungold": 0, "n_hallucination": 0,
                "confirmed_bugs": [], "n_findings": len(findings)}
    pairs = [(g["comment"], c) for g in goldens for c in cand_texts]
    _log(tag, f"judging: {len(pairs)} golden×candidate pairs via {judge_model}...")
    results = await judge_pairs_router(judge_model, pairs, concurrency=15, max_tokens=1024)
    scored = score_from_matches(goldens, cand_texts, results)
    _log(tag, f"judging done: TP={scored['tp']} FP={scored['fp']} FN={scored['fn']}. Adjudicating {len(scored.get('false_positives',[]))} unmatched...")
    adjudicated = await reclassify_async(scored, cand_texts, pr.diff, model=judge_model)
    confirmed = scored.get("true_positives", []) + adjudicated.get("real_but_ungold", [])
    # attach file:line to each confirmed bug (for union dedup by location)
    for b in confirmed:
        text = b.get("golden_comment") or b.get("candidate") or ""
        loc = text_to_loc.get(text, ("", 0))
        b["file"] = loc[0]; b["line"] = loc[1]
    adjudicated["confirmed_bugs"] = confirmed
    adjudicated["n_findings"] = len(findings)
    adjudicated["n_real_ungold"] = len(adjudicated.get("real_but_ungold", []))
    adjudicated["n_hallucination"] = len(adjudicated.get("hallucination", []))
    return adjudicated


async def _fix(work: Path, confirmed_bugs: list, pr: PRSample, model_alias: str, effort: str,
               base_ref: str = "mrv-pr^", model_full: str = "claude-opus-5", tag: str = "") -> tuple[int, int, str]:
    """Run a fix session: edit the repo to fix the confirmed bugs + add tests, commit. Returns (tin, tout, resolved)."""
    bug_list = "\n".join(f"{i+1}. {b.get('golden_comment') or b.get('candidate','')}"
                         for i, b in enumerate(confirmed_bugs))
    prompt = FIX_PROMPT.format(diff=_diff(work, base_ref)[:30000], bug_list=bug_list,
                               n=len(confirmed_bugs))
    _log(tag, f"fix: dispatching fix session ({model_full}/{effort}) for {len(confirmed_bugs)} bugs...")
    text, per_model, resolved = await _run_session(
        work, model_full, effort, prompt, max_turns=15, timeout=session_timeout(effort, base=600),
        phase="fix-iter", tag=tag)
    _log(tag, f"fix: session returned, checking commit status...")
    tin = sum(u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
              + u.get("cache_creation_input_tokens", 0) for u in per_model.values())
    tout = sum(u.get("output_tokens", 0) for u in per_model.values())
    cache_read = sum(u.get("cache_read_input_tokens", 0) for u in per_model.values())
    cache_create = sum(u.get("cache_creation_input_tokens", 0) for u in per_model.values())
    # ensure the model committed (if it edited but didn't commit, commit for it)
    st = subprocess.run(["git", "-C", str(work), "status", "--porcelain"], capture_output=True, text=True, env=GIT_ENV)
    if st.stdout.strip():
        _git(work, "add", "-A"); _git(work, "commit", "--quiet", "-m", "fix: uncommitted edits")
    return tin, tout, resolved, cache_read, cache_create



async def _bug_still_present(golden_comment: str, repo: Path, base_ref: str = "mrv-pr^",
                             judge_model: str = "gpt-5.2") -> bool:
    """Judge whether the bug described in `golden_comment` still exists in the current diff.
    Returns True if the bug is STILL present (not fixed)."""
    from harnesseval.model_router import call_model_json
    prompt = f"""You are verifying whether a specific bug still exists in the current code.

Original bug description (from a human reviewer):
{golden_comment}

Current diff (base..HEAD, after fixes were applied):
```diff
{repo and _diff(repo, base_ref)[:30000]}
```

Does the bug described above STILL EXIST in the current code? (True = bug is still present /
not fixed. False = the bug has been fixed or no longer applies.)
Respond with ONLY a JSON object: {{"reasoning": "...", "still_present": true/false}}"""
    parsed, _, _, _ = await call_model_json(judge_model, "You are a strict code review verifier. Always respond with valid JSON.",
                                            prompt, effort="medium", max_tokens=512)
    return bool(parsed.get("still_present", True)) if parsed else True

async def discover_only(pr: PRSample, model_alias: str = "opus", effort: str = "low",
                          judge_model: str = "gpt-5.2", framework: str = "metareview-realistic",
                          model_full: str = "claude-opus-5") -> dict:
    """ONE discovery + adjudicate pass on the ORIGINAL code (no fix loop). Returns the condition's
    confirmed bugs (golden + hidden gold), its hallucinations, and token/time costs. This is the
    Phase-1 discovery for each condition — used to build the UNION bug universe."""
    repo_dir = materialize(pr.url)
    work = _work_copy(repo_dir, f"sdlc-disc-{framework.split('-')[0]}-{model_full}")
    base_ref = "mrv-pr^"
    tag = f"{model_full}/{framework.split('-')[0]}/disc"
    t0 = time.time()
    findings, per_model, resolved, din, dout, dcr, dcc = await _discover(
        work, pr, model_alias, effort, base_ref, framework=framework, model_full=model_full, tag=tag)
    scored = await _score(findings, pr, judge_model, tag=tag)
    confirmed = scored.get("confirmed_bugs", [])
    def _desc(b): return b.get("golden_comment") or b.get("candidate") or str(b)
    # preserve file:line for union dedup
    confirmed_descs = [_desc(b) for b in confirmed]
    confirmed_locs = [(b.get("file", ""), b.get("line", 0)) for b in confirmed]
    hal_descs = [h.get("candidate", str(h)) for h in scored.get("hallucination", [])]
    result = {"framework": framework, "model_full": model_full,
              "confirmed_bugs": confirmed_descs, "confirmed_locs": confirmed_locs,
              "n_confirmed": len(confirmed_descs),
              "n_golden_found": scored["tp"], "n_hidden_gold": scored["n_real_ungold"],
              "n_hallucination": scored["n_hallucination"], "hallucinations": hal_descs,
              "recall": scored["recall"], "incr_recall": scored.get("incremental_recall", 0.0),
              "tokens_in": din, "tokens_out": dout, "cache_read": dcr, "cache_create": dcc,
              "wall_s": time.time()-t0}
    _log(tag, f"discovery: {len(confirmed_descs)} confirmed ({scored['tp']} golden + "
              f"{scored['n_real_ungold']} hidden gold), {scored['n_hallucination']} hallucinations, "
              f"recall {scored['recall']:.2f}")
    return result



async def dedup_bugs_llm(bug_lists: dict[str, list[str]],
                            bug_locs: dict[str, list[tuple[str, int]]],
                            judge_model: str = "gpt-5.2") -> tuple[list[str], dict[str, list[int]]]:
    """Deduplicate the UNION of all conditions' confirmed bugs using file:line grouping + ONE LLM call per file.

    O(F) LLM calls (F = number of unique files), not O(N²). For each file, sends ALL bugs in that
    file to the LLM in a single call and asks it to cluster them into groups representing the same
    underlying issue. Bugs in different files are assumed distinct (no comparison).

    bug_lists  = {"structured-mrv": ["bug1", ...], "structured-vanilla": [...]}
    bug_locs   = {"structured-mrv": [(file, line), ...], ...}  (parallel to bug_lists)
    Returns (union_bugs, per_condition_membership).
    """
    from harnesseval.model_router import call_model_json

    DEDUP_SYSTEM = "You are a precise code review deduplicator. Always respond with valid JSON."
    DEDUP_PROMPT = """You are grouping duplicate bug reports. The following bug reports all concern the same file: {file}

Bugs (numbered 0..N-1):
{bugs}

Group them into clusters where each cluster represents the SAME underlying issue (different wording
for the same problem). Bugs about genuinely different issues go in separate clusters.

Respond with ONLY a JSON object mapping each bug index to a cluster number (0-based):
{{"0": 0, "1": 0, "2": 1, "3": 0, ...}}
where bugs with the same cluster number are duplicates of each other."""

    # flatten all bugs with their source condition + file:line
    all_bugs = []  # (desc, condition, file, line)
    for cond, bugs in bug_lists.items():
        locs = bug_locs.get(cond, [])
        for i, b in enumerate(bugs):
            loc = locs[i] if i < len(locs) else ("", 0)
            all_bugs.append((b, cond, loc[0], loc[1]))
    if not all_bugs:
        return [], {c: [] for c in bug_lists}

    # group by file
    file_groups = {}  # file -> [(global_idx, desc, condition), ...]
    for idx, (desc, cond, file, line) in enumerate(all_bugs):
        file_groups.setdefault(file or "unknown", []).append((idx, desc, cond))

    _log("dedup", f"file grouping: {len(all_bugs)} bugs across {len(file_groups)} files -> {len(file_groups)} LLM calls (one per file)")

    # one LLM call per file to cluster its bugs
    async def cluster_file(file, members):
        if len(members) <= 1:
            return {members[0][0]: 0} if members else {}
        bugs_text = "\n".join(f"{i}. [{m[2]}] {m[1]}" for i, m in enumerate(members))
        prompt = DEDUP_PROMPT.format(file=file, bugs=bugs_text)
        parsed, _, _, _ = await call_model_json(judge_model, DEDUP_SYSTEM, prompt, effort="medium", max_tokens=4096)
        if not parsed:
            # fallback: each bug its own cluster
            return {m[0]: i for i, m in enumerate(members)}
        # parsed = {"0": 0, "1": 0, "2": 1, ...} — map bug index (within file) -> cluster number
        result = {}
        for i, m in enumerate(members):
            result[m[0]] = parsed.get(str(i), i)  # fallback: own index
        return result

    file_results = await asyncio.gather(*[cluster_file(f, m) for f, m in file_groups.items()])

    # merge all file-level cluster results into global clusters
    # each file's clusters are independent (different files = different bugs)
    # so we offset cluster numbers per file
    global_clusters = {}  # global_idx -> global_cluster_num
    cluster_offset = 0
    for file, members in file_groups.items():
        fr = file_results[list(file_groups.keys()).index(file)]
        # normalize cluster numbers within this file to start at cluster_offset
        local_clusters = set(fr.values()) if fr else set()
        local_to_global = {lc: cluster_offset + i for i, lc in enumerate(sorted(local_clusters))}
        for global_idx, cluster_num in fr.items():
            global_clusters[global_idx] = local_to_global.get(cluster_num, cluster_offset)
        cluster_offset += len(local_clusters)

    # build clusters from global_clusters
    cluster_members = {}  # global_cluster_num -> [global_idx, ...]
    for global_idx, cluster_num in global_clusters.items():
        cluster_members.setdefault(cluster_num, []).append(global_idx)

    # union = one rep per cluster (longest desc = most specific); membership = which conditions contributed
    union_bugs = []
    membership = {c: [] for c in bug_lists}
    for ci, members in enumerate(cluster_members.values()):
        rep = max(members, key=lambda i: len(all_bugs[i][0]))
        union_bugs.append(all_bugs[rep][0])
        for i in members:
            cond = all_bugs[i][1]
            if ci not in membership[cond]:
                membership[cond].append(ci)

    _log("dedup", f"dedup done: {len(all_bugs)} input bugs -> {len(union_bugs)} unique bugs "
          f"({len(all_bugs) - len(union_bugs)} duplicates removed)")
    return union_bugs, membership


async def run_structured(pr: PRSample, model_alias: str = "opus", effort: str = "low",
                        judge_model: str = "gpt-5.2", max_iter: int = 3,
                        framework: str = "metareview-realistic",
                        model_full: str = "claude-opus-5",
                        baseline_confirmed: list | None = None) -> dict:
    """The structured SDLC loop. Returns per-iteration metrics + fixation on ALL confirmed bugs
    (golden + hidden gold), not just goldens.
    If baseline_confirmed (list of bug descriptions) is provided, uses it for final scoring
    (so all 3 conditions score against the SAME precomputed baseline, in parallel).
    framework="metareview-realistic" (default) or "vanilla-engineered"."""
    repo_dir = materialize(pr.url)
    work_suffix = f"sdlc-{framework.split('-')[0]}-{model_full}"
    work = _work_copy(repo_dir, work_suffix)
    base_ref = "mrv-pr^"
    tag = f"{model_full}/{framework.split('-')[0]}"
    iters = []
    total_tin = total_tout = total_cache_read = total_cache_create = 0
    t0 = time.time()
    prev_unfixed = float('inf')  # track UNFIXED bugs per iteration (converge on fixation, not discovery)
    all_found_bugs = set()  # cumulative set of bug descriptions found across ALL iterations
    for i in range(max_iter):
        it_t0 = time.time()
        # wrap each iteration in try/except so a transient claude -p / codex failure (quota spike,
        # empty-stderr non-zero exit, etc.) doesn't crash the whole experiment — break the loop and
        # keep the previous iteration's committed fixes. This is resilient, not silent: the error
        # is logged + recorded in the iter dict so we can see what failed.
        try:
            findings, per_model, resolved, din, dout, dcr, dcc = await _discover(
                work, pr, model_alias, effort, base_ref, framework=framework, model_full=model_full, tag=tag)
            scored = await _score(findings, pr, judge_model, tag=tag)
            confirmed = scored.get("confirmed_bugs", [])
            total_tin += din + scored.get("_score_tin", 0); total_tout += dout
            total_cache_read += dcr; total_cache_create += dcc
            # ALWAYS fix before checking convergence — the old code broke BEFORE _fix on the converged
            # iteration, leaving the last-discovered bugs unfixed. Now we fix every iteration, then
            # check how many confirmed bugs are STILL PRESENT to decide convergence.
            n_unfixed = len(confirmed)
            if confirmed:
                ftin, ftout, _, fcr, fcc = await _fix(work, confirmed, pr, model_alias, effort, base_ref,
                                                       model_full=model_full, tag=tag)
                total_tin += ftin; total_tout += ftout
                total_cache_read += fcr; total_cache_create += fcc
                # check fixation: which of THIS iteration's confirmed bugs are still present after the fix?
                def _desc(b): return b.get("golden_comment") or b.get("candidate") or str(b)
                confirmed_descs = [_desc(b) for b in confirmed]
                still = await asyncio.gather(*[_bug_still_present(b, work, base_ref, judge_model)
                                               for b in confirmed_descs])
                n_unfixed = sum(1 for s in still if s)
            n_fixed_this_iter = len(confirmed) - n_unfixed
            # track the CUMULATIVE found set across all iterations — convergence must be against
            # ALL bugs ever found, not just this iteration's. The old "→ ALL FIXED" checked only the
            # current iteration's confirmed bugs, so it could declare victory on a 1-bug iter 3 while
            # 7 union bugs from iters 1-2 remained unfixed. Now we re-check the full cumulative set.
            all_found_bugs |= {b.get("golden_comment") or b.get("candidate") or str(b) for b in confirmed}
            # re-score fixation on the FULL cumulative found set (not just this iter) so the
            # convergence signal reflects ALL found bugs, and so we don't double-count a bug fixed
            # in an earlier iter as "unfixed" just because this iter re-discovered it.
            still_all_found = await asyncio.gather(*[_bug_still_present(b, work, base_ref, judge_model)
                                                      for b in all_found_bugs])
            n_cumulative_unfixed = sum(1 for s in still_all_found if s)
            iters.append({"iter": i+1, "n_findings": len(findings), "tp": scored["tp"], "fp": scored["fp"],
                          "fn": scored["fn"], "recall": scored["recall"],
                          "n_confirmed": len(confirmed), "n_hidden_gold": scored["n_real_ungold"],
                          "n_hallucination": scored["n_hallucination"],
                          "n_fixed_this_iter": n_fixed_this_iter, "n_unfixed_this_iter": n_unfixed,
                          "n_cumulative_found": len(all_found_bugs),
                          "n_cumulative_unfixed": n_cumulative_unfixed,
                          "incr_recall": scored.get("incremental_recall", 0.0),
                          "discover_tin": din, "discover_tout": dout, "wall_s": time.time()-it_t0})
            # converge on FIXATION of the CUMULATIVE found set: all ever-found bugs fixed, or no
            # fixation progress vs last iteration on the cumulative set.
            converged = (n_cumulative_unfixed == 0) or (i > 0 and n_cumulative_unfixed >= prev_unfixed)
            status = ("→ ALL FIXED" if n_cumulative_unfixed == 0
                      else ("→ CONVERGED (no fixation progress)" if converged else ""))
            print(f"  [structured iter {i+1}] findings={len(findings)} confirmed={len(confirmed)} "
                  f"recall={scored['recall']:.2f} fixed={n_fixed_this_iter}/{len(confirmed)} "
                  f"cumulative={len(all_found_bugs)}-found/{n_cumulative_unfixed}-unfixed "
                  f"hidden={scored['n_real_ungold']} hal={scored['n_hallucination']} {status}", flush=True)
            if converged:
                break
            prev_unfixed = n_cumulative_unfixed
        except Exception as e:
            _log(tag, f"iter {i+1} FAILED ({type(e).__name__}: {str(e)[:150]}) — keeping prior commits, breaking loop")
            iters.append({"iter": i+1, "error": f"{type(e).__name__}: {str(e)[:200]}",
                          "wall_s": time.time()-it_t0})
            break
    # final: score fixation on the SHARED baseline (precomputed, or this run's own iter-1 if none).
    # baseline_confirmed is a list of bug-description strings (from the union dedup, or discover_only).
    if baseline_confirmed is None:
        baseline_confirmed = []  # fallback: no baseline -> 0 fixed (shouldn't happen with the pre-step)
    _log(tag, f"final scoring: checking {len(baseline_confirmed)} baseline bugs for fixation...")
    still_all = await asyncio.gather(*[_bug_still_present(b, work, base_ref, judge_model)
                                       for b in baseline_confirmed])
    n_confirmed_fixed = sum(1 for s in still_all if not s)
    _log(tag, f"final scoring done: {n_confirmed_fixed}/{len(baseline_confirmed)} confirmed bugs fixed")
    # goldens-only subset for comparability with the old metric
    golden_descs = {g["comment"] for g in pr.golden_comments}
    golden_idx = [i for i, b in enumerate(baseline_confirmed) if b in golden_descs]
    n_goldens_fixed = sum(1 for i in golden_idx if not still_all[i])
    return {"condition": "structured", "iters": iters, "n_goldens": len(pr.golden_comments),
            "n_goldens_fixed": n_goldens_fixed, "n_goldens_still_present": len(pr.golden_comments)-n_goldens_fixed,
            "n_baseline_confirmed": len(baseline_confirmed),
            "n_confirmed_fixed": n_confirmed_fixed, "n_confirmed_still_present": len(baseline_confirmed)-n_confirmed_fixed,
            "baseline_confirmed": baseline_confirmed,
            "total_tin": total_tin, "total_tout": total_tout,
            "cache_read": total_cache_read, "cache_create": total_cache_create,
            "wall_s": time.time()-t0, "final_diff_lines": len(_diff(work, base_ref).splitlines()),
            "work_dir": str(work)}


async def run_control(pr: PRSample, model_alias: str = "opus", effort: str = "high",
                      judge_model: str = "gpt-5.2", max_turns: int = 40,
                      baseline_confirmed: list | None = None,
                      model_full: str = "claude-opus-5") -> dict:
    """The unstructured control: one long autonomous session (claude /goal or codex autonomous loop),
    the agent's own loop. Scores fixation on the SAME baseline_confirmed bugs (from structured's
    iter-1 discovery on the original code) so all conditions are comparable on the same bug set."""
    repo_dir = materialize(pr.url)
    work = _work_copy(repo_dir, f"sdlc-control-{model_full}")
    base_ref = "mrv-pr^"
    tag = f"{model_full}/control"
    t0 = time.time()
    prompt_tpl = CONTROL_PROMPT_CODEX if _is_codex(model_full) else CONTROL_PROMPT
    prompt = prompt_tpl.format(pr_title=pr.pr_title)
    _log(tag, f"control: launching autonomous session ({model_full}/{effort}, max {max_turns} turns)...")
    text, per_model, resolved = await _run_session(
        work, model_full, effort, prompt, max_turns=max_turns, timeout=3600,
        phase="control", tag=tag)
    _log(tag, f"control: session returned, checking commit status...")
    # ensure the model committed (if it edited but didn't commit, commit for it).
    # Codex's autonomous loop often edits files without git-committing them, leaving real
    # fixes uncommitted in the working tree — without this auto-commit, _diff(base_ref, HEAD)
    # sees nothing and the control scores 0 fixes despite doing real work.
    st = subprocess.run(["git", "-C", str(work), "status", "--porcelain"], capture_output=True, text=True, env=GIT_ENV)
    if st.stdout.strip():
        _git(work, "add", "-A"); _git(work, "commit", "--quiet", "-m", "control: uncommitted edits")
        _log(tag, f"control: auto-committed uncommitted edits (model didn't commit them itself)")
    tin = sum(u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
              + u.get("cache_creation_input_tokens", 0) for u in per_model.values())
    tout = sum(u.get("output_tokens", 0) for u in per_model.values())
    n_commits = int(_git(work, "rev-list", "--count", f"{base_ref}..HEAD") or "0")
    _log(tag, f"control: {n_commits} commits")
    cache_read = sum(u.get("cache_read_input_tokens", 0) for u in per_model.values())
    cache_create = sum(u.get("cache_creation_input_tokens", 0) for u in per_model.values())
    # score on the shared baseline confirmed bugs (golden + hidden gold) — same set as structured
    bugs = baseline_confirmed or [g["comment"] for g in pr.golden_comments]
    _log(tag, f"final scoring: checking {len(bugs)} baseline bugs for fixation...")
    still_all = await asyncio.gather(*[_bug_still_present(b, work, base_ref, judge_model) for b in bugs])
    n_confirmed_fixed = sum(1 for s in still_all if not s)
    _log(tag, f"final scoring done: {n_confirmed_fixed}/{len(bugs)} confirmed bugs fixed")
    golden_descs = {g["comment"] for g in pr.golden_comments}
    golden_idx = [i for i, b in enumerate(bugs) if b in golden_descs]
    n_goldens_fixed = sum(1 for i in golden_idx if not still_all[i])
    return {"condition": "naive-vanilla", "n_commits": n_commits, "n_goldens": len(pr.golden_comments),
            "n_goldens_fixed": n_goldens_fixed, "n_goldens_still_present": len(pr.golden_comments)-n_goldens_fixed,
            "n_baseline_confirmed": len(bugs),
            "n_confirmed_fixed": n_confirmed_fixed, "n_confirmed_still_present": len(bugs)-n_confirmed_fixed,
            "total_tin": tin, "total_tout": tout, "cache_read": cache_read, "cache_create": cache_create,
            "wall_s": time.time()-t0,
            "final_diff_lines": len(_diff(work, base_ref).splitlines()),
            "work_dir": str(work)}
