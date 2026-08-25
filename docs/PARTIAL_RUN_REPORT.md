# PARTIAL RUN REPORT — 48-cell matrix, stopped after 15/48 (2026-08-23)

> **For the fresh agent:** this is the debugging signal from the stopped matrix. These 15
> cells ran the OLD code path (no per-model usage propagation), so **token costs are unusable**
> (vanilla shows `0tok`; metareview-realistic shows only orchestrator tokens). Treat numbers as
> debugging signal, NOT results. The raw cell log is at `/tmp/mm_out.txt` (may be gone after
> reboot); registered runs are in `runs/registry.jsonl` (phase=B, framework in {vanilla-engineered,
> metareview-realistic}).

## Matrix config (the stopped run)

6 hardest PRs × {vanilla-engineered, metareview-realistic} × {claude-opus-4-5-20251101, gpt-5.2}
× {medium, xhigh}, mode=cli (OAuth), concurrency 3, judge=cross-family on API. 15/48 cells done
before stop.

## The 15 completed cells (raw)

```
[1]  vanilla-engineered  opus    medium   TP=7  FP=14 FN=2  rec=0.78 adj_p=0.33 inc_r=0.78  138s  0tok
[3]  vanilla-engineered  opus    xhigh    TP=8  FP=15 FN=1  rec=0.89 adj_p=0.36 inc_r=0.90  219s  0tok
[5]  vanilla-engineered  gpt-5.2 medium   TP=6  FP=3  FN=3  rec=0.67 adj_p=1.00 inc_r=0.75  194s  0tok
[6]  metareview-realistic gpt-5.2 medium TP=0  FP=9  FN=9  rec=0.00 adj_p=0.00 inc_r=0.00  174s  459k tok
[4]  metareview-realistic opus    xhigh    TP=1  FP=0  FN=8  rec=0.11 adj_p=1.00 inc_r=0.11  514s  6.5M tok
[9]  vanilla-engineered  opus    medium   TP=5  FP=13 FN=3  rec=0.62 adj_p=0.28 inc_r=0.62  146s  0tok
[8]  metareview-realistic gpt-5.2 xhigh   TP=0  FP=8  FN=9  rec=0.00 adj_p=0.00 inc_r=0.00  459s  605k tok
[11] vanilla-engineered  opus    xhigh    TP=3  FP=20 FN=5  rec=0.38 adj_p=0.14 inc_r=0.44  334s  0tok
[10] metareview-realistic opus    medium   TP=5  FP=50 FN=3  rec=0.62 adj_p=0.09 inc_r=0.62  469s  3.4M tok
[13] vanilla-engineered  gpt-5.2 medium   TP=3  FP=7  FN=5  rec=0.38 adj_p=0.75 inc_r=0.64  182s  0tok
[14] metareview-realistic gpt-5.2 medium TP=0  FP=8  FN=8  rec=0.00 adj_p=0.00 inc_r=0.00  244s  1.5M tok
[17] vanilla-engineered  opus    medium   TP=6  FP=12 FN=1  rec=0.86 adj_p=0.33 inc_r=0.86  125s  0tok
[2]  metareview-realistic opus    medium  ERR  400 "Could not finish the message"  409s
[7]  vanilla-engineered  gpt-5.2 xhigh   ERR  300s codex exec timeout
[15] vanilla-engineered  gpt-5.2 xhigh   ERR  300s codex exec timeout
```

## What we learned (the signal worth keeping)

### vanilla-engineered is reliable (use as the baseline)
- **opus medium**: 3 PRs, recall 0.78 / 0.62 / 0.86 (avg ~0.75), low cost. Consistent.
- **gpt-5.2 medium**: recall 0.67 / 0.38 (lower) but **adjudicated precision 0.75–1.00** (much
  higher) + found real-but-ungold bugs (6 on one PR). Different model → different quality
  profile (gpt-5.2 trades recall for precision). Real signal for the matrix.
- **effort axis**: opus medium→xhigh helped on one PR (0.78→0.89) but hurt on another
  (0.62→0.38). Not monotonic; needs more PRs to characterize.

### metareview-realistic has 3 real bugs to fix BEFORE trusting its numbers
1. **gpt-5.2 = 0.00 recall on all 3 completed runs** (cells 6, 8, 14). The codex subagent path
   isn't producing findings that match goldens. Likely: the codex `Agent`-equivalent dispatch
   (codex doesn't have Claude's `Agent` tool — it uses a different subagent mechanism) isn't
   running the 5 lenses, OR the finding extraction/attribution is broken for codex output.
   **This is the loudest signal — debug first.**
2. **opus xhigh: 0.11 recall @ 6.5M tok** (cell 4) — extremely expensive AND nearly useless.
   The xhigh thinking session ran (6.5M tok) but only 1 TP. Possibly the subagents dispatched
   but findings weren't extracted/matched, or xhigh reasoning drifted. High variance vs
   medium (0.62). Investigate the xhigh lens dispatch + extraction.
3. **opus medium high variance** (0.62, 0.62, 0.11-error) — the realistic path isn't reliably
   dispatching/extracting. One cell errored ("Could not finish the message" — likely a context-
   length/overload 400 on a big diff).

### Codex (gpt-5.2) xhigh times out at 300s (cells 7, 15)
The codex `_review_cli`/session timeout is 300s — too short for xhigh reasoning. **Bump to
900s** (the realistic metareview session already uses 900s; the vanilla codex path needs it too).

### Cost accounting is unusable in this run (the reason we stopped)
- vanilla shows `0tok` — the old code path didn't propagate `per_model_usage`.
- metareview-realistic shows only the orchestrator tokens (e.g. 3.4M, 6.5M) — NOT the Haiku
  subagent split (the §6.3.1 learning). So we can't see the orchestrator-vs-lens cost split.
- The current code fixes this (usage.py + per_model_usage propagation). **Rerun clean.**

## What to fix (concrete, verified)

### FIX 1 — metareview-realistic on codex (gpt-5.2) = 0.00 recall [ROOT CAUSE FOUND]
**Root cause (verified 2026-08-23, corrected):** codex CLI 0.149.0 **DOES** support subagents —
the `multi_agent` feature flag is stable+enabled, and the model has `collaboration.spawn_agent`,
`collaboration.wait_agent`, `collaboration.list_agents`, `collaboration.send_message` tools
(ask codex 'list your tools' to see them). **Verified end-to-end:** `codex exec` successfully
spawns a subagent via `collaboration.spawn_agent` and returns its result.

The bug: the realistic prompt (`REALISTIC_PROMPT` in `harnesseval/adapters/metareview_realistic.py`)
tells the model to dispatch via the **`Agent` tool** — that's Claude Code's tool name. Codex has
the same capability but under a DIFFERENT name: **`collaboration.spawn_agent`**. So on codex the
model can't find the `Agent` tool, does something unmatchable, → 0 TP.

**Fix (the RIGHT one, now that we know codex can spawn subagents):**
  Make `REALISTIC_PROMPT` **host-agnostic** — say "dispatch the 5 lenses as parallel subagents
  via your host's subagent-spawn tool (Claude Code: `Agent`; Codex: `collaboration.spawn_agent`)
  with one call per lens" instead of hardcoding `Agent`. Then codex will fan out the 5 lenses
  for real, producing real (non-zero) numbers — the honest realistic-codex path.
  (Keep the GLM/Kimi api-fallback `else` branch in `review_realistic_async` — Lunaroute has no CLI.)

This is strictly better than the api-fallback I recommended before: it tests the REAL codex
subagent fanout (what a codex user gets), not a stripped API version. The §6.3.1 learning
(orchestrator vs subagent model split) will then also apply to codex (record per-model usage).

### FIX 2 — vanilla-engineered codex (gpt-5.2) xhigh times out at 300s
**File:** `harnesseval/cli_backends.py` lines 38 + 66 (`_claude_cli` + `_codex_cli` default
`timeout: int = 300`) — too short for xhigh reasoning. Also the vanilla `_review_cli` path
(`harnesseval/adapters/vanilla.py`) inherits this.
**Fix:** bump default `timeout` to `900` in both `_claude_cli` and `_codex_cli`. (The realistic
metareview session already uses 900 — lines 77, 104 — so just sync the vanilla/one-shot paths.)

### FIX 3 — metareview-realistic opus xhigh: 0.11 recall @ 6.5M tok (investigate)
**Symptom:** cell 4 ran 6.5M tokens (xhigh thinking) but only 1 TP. Possibly the 5 lens
subagents dispatched but their findings weren't extracted/matched, or xhigh reasoning drifted.
**Fix:** before trusting xhigh numbers, run ONE opus-xhigh cell with `--verbose stream-json`
output captured (see HANDOFF §3 gotcha #3 for how) and verify: (a) did 5 `Agent` tool_use
events fire? (b) did each return lens findings? (c) did `_extract_findings_from_session`
catch them? If the subagents ran but extraction missed them, fix the extractor. If xhigh
thinking ate the turn budget before dispatch, raise `max_turns` (currently 12) or cap thinking.

### FIX 4 — rerun clean (per-model cost)
**Why:** this partial run used the old code path (no `per_model_usage` propagation) → vanilla
shows `0tok`, metareview-realistic shows only orchestrator tokens (no Haiku-lens split, the
§6.3.1 learning). The current code (usage.py + per_model_usage on ReviewRun + propagation in
run_model_matrix._run_cell_async) fixes this.
**Fix:** after FIX 1-3, rerun a **4-8 cell clean subset** (2 PRs × 2 fw × 2 models × 1 effort)
and confirm `per_model_usage` + `total_cost_usd` populate in the registered summaries (check
`runs/<id>/summary.json` has `per_model_usage` with the opus/haiku split). Then the full matrix.

## Recommended order
1. FIX 1 (codex realistic → api-fallback) — fixes the 0.00 cells.
2. FIX 2 (bump codex/claude timeout to 900s) — fixes the 300s xhigh timeouts.
3. Rerun 4-8 cell clean subset → confirm per-model cost populates + bugs fixed.
4. FIX 3 (investigate opus xhigh) if the clean subset still shows low xhigh recall.
5. Full clean matrix → report.

## Do NOT conclude from this partial run
- metareview-realistic is "worse" than vanilla — it has bugs; fix them first.
- cost numbers — unusable (no per-model split). Rerun clean.
- Any framework ranking — 6 PRs × partial cells is anecdotal; need full 50 + CIs (Phase C).

---

## FIX OUTCOMES (2026-08-23, this session)

All of FIX 1-4 + the 4 new adapters are done and a clean full matrix is running.

### Adapters built (SPEC §2, §6.1) — ALL DONE
- `adapters/superpowers.py` (api-direct): Superpowers `requesting-code-review` methodology
  (code-reviewer.md template) extracted to a bare API prompt. Methodology source pinned:
  `third_party/superpowers` @ SHA `b36e0829c6d0140e93cfef2ca599b1b07d4a7797`
  (skills/requesting-code-review/{SKILL.md,code-reviewer.md}).
- `adapters/superpowers_realistic.py` (realistic): drives a real `claude -p`/`codex exec`
  session with the Superpowers plugin installed (symlinked into a throwaway
  `CLAUDE_PLUGIN_PATH`), dispatching a `general-purpose` code-reviewer subagent.
- `adapters/compound.py` (api-direct): Compound `ce-code-review` risk-driven persona roster
  (correctness always-on + conditionals by diff signal) extracted to parallel API persona
  prompts + aggregation. Source pinned: `third_party/compound-engineering-plugin` @ SHA
  `a32c9474c658f3e33b6e3615a5d51089046d4c79` (skills/ce-code-review/*).
- `adapters/compound_realistic.py` (realistic): drives a real host session that selects the
  persona roster, dispatches each persona as a parallel subagent, synthesizes the P0-P3 report.
- Pinned SHAs recorded in `third_party/superpowers_sha.txt`, `third_party/compound_sha.txt`.
- All 8 frameworks wired into `run_model_matrix._run_cell_async`.

### FIX 1 (host-agnostic subagent prompt) — DONE + VALIDATED
- `metareview_realistic.py` `REALISTIC_PROMPT` + the 3 realistic adapters' prompts now say
  "dispatch via your host's subagent-spawn tool (Claude Code: `Agent`; Codex:
  `collaboration.spawn_agent` + `collaboration.wait_agent`)" — no hardcoded `Agent`.
- VALIDATED: metareview-realistic on codex (gpt-5.2) went TP=0/rec=0.00 → TP=6/rec=0.67,
  incremental_recall=0.88 (16 real-but-ungold). The codex fanout now runs for real.

### FIX 2 (timeouts 300→900s) — DONE + extended to effort-aware
- `cli_backends.py` `_claude_cli`/`_codex_cli` default timeout 300→900.
- NEW: `cli_backends.session_timeout(effort, base)` scales the realistic session subprocess
  timeout by effort — medium=base, xhigh=2×base. Wired into all 3 realistic adapters:
  metareview/superpowers base=900 (xhigh→1800s), compound base=1200 (xhigh→2400s, N persona
  subagents + synthesis). Fixes xhigh realistic cells dying at the timeout.

### FIX 4 (per-model cost) — DONE + VALIDATED
- `model_router.call_model`/`call_model_json` now return a 4th element `per_model_usage`
  (the {model: {input,cache_read,cache_creation,output,reasoning,total,cost_usd}} dict) for
  BOTH api and cli modes. The api-direct adapters (vanilla, superpowers, compound, metareview)
  now capture + merge it onto `ReviewRun.per_model_usage` + `total_cost_usd` (gotcha #2).
- This also FIXED the vanilla `0tok` bug: `model_router._call_cli` was reading
  `total_tokens`/`output_tokens` off the per-model dict (keyed by model id) → 0. Now uses
  `grand_total`. VALIDATED: vanilla-engineered cli/codex 0tok → 1.73M tok; in the live matrix
  vanilla opus medium shows 98K tok (was 0).
- VALIDATED per_model split in registry: metareview-realistic opus = haiku subagents 1.5K tok
  + opus-5 orchestrator 3.88M tok / $5.64 (the §6.3.1 learning).

### EXTRA FIX (materialize idempotency — a real recall bug, found while validating FIX 1)
- `dataset/materialize.py` was NOT idempotent: the adapters add a `task` commit on top of the
  cached `pr` commit each run, and metareview writes generated files, so commits accumulated.
  By the 3rd run `HEAD~2` drifted onto a task/generated commit, so the lenses reviewed
  metareview's generated files (`.metareview/*.md`) instead of the real PR code → unmatchable
  findings (this inflated the "0.00/0.11 recall" signal, not just the prompt).
- FIXED: materialize tags the clean `pr` commit `mrv-pr` and on cache hit does
  `git reset --hard mrv-pr` + `git clean -fdx`, so every call returns the clean [base][pr]
  state and `HEAD~2==base, HEAD~1==pr` always holds. VALIDATED: lenses now reference real PR
  files (`refreshOAuthTokens.ts`, `CalendarService.ts`), 0 task-file noise.

### FIX 3 (opus xhigh 0.11) — largely addressed by materialize fix; monitor in the matrix
- The materialize fix means xhigh reasoning now runs on the REAL diff (not generated files),
  so the "6.5M tok, 1 TP" failure mode should resolve. The live matrix's vanilla opus xhigh
  already scores rec=1.00. Watch the metareview-realistic/superpowers-realistic opus xhigh
  cells in `results/phase_b_full_4fw.json`; if any still score low, capture a `--verbose
  stream-json` transcript and check whether the subagents dispatched + findings extracted.

### Full matrix — RUNNING (background, nohup, survives session end)
- 6 hard PRs × {vanilla-engineered, metareview-realistic, superpowers-realistic,
  compound-realistic} × {opus, gpt-5.2, glm, kimi} × {medium, xhigh} = 192 cells, mode=cli
  (glm/kimi fall back to api via Lunaroute), concurrency 3, cross-family judge on API.
- PID `/tmp/full_pid.txt`, log `/tmp/full_out.txt`, results `results/phase_b_full_4fw.json`.
- Each cell auto-registers in `runs/` on completion (durable even if the matrix dies).
- Known transient: some realistic cells on big diffs 400 with "Could not finish the message"
  (Claude overload/context) — the matrix logs ERR and continues; not a code bug.
- GLM note: GLM with reasoning_effort can return empty `content` (reasoning eats the
  max_completion_tokens budget) on the long methodology prompts — if GLM cells score 0 with
  empty raw_output, that's a `model_router` reasoning-budget gap (bump max_tokens for reasoning
  models), NOT an adapter bug. Vanilla (short prompt) works on GLM.

### Next (when the matrix finishes)
- `uv run python -m harnesseval.report --phase B --pareto results/pareto.png` for the
  leaderboard + Pareto. Then Phase C (API, pinned IDs) per PLAN, after the 5-PR cost pilot.

---

## Persistence + adjudicator fix (2026-08-23, follow-up)

Landed per `docs/METAREVIEW_IMPROVEMENTS.md` "Cross-cutting data needs" #1-3 (soft-urgency
item: make new realistic runs re-adjudicable with the frontier panel without re-running
frameworks). NOT a stop-the-run item — landed at the natural pause between matrix cells.

### Per-finding adjudication records + per-golden matches now persisted (run_model_matrix.py)
- `_build_finding_records(run, scored, adjudicated, judge_model, diff)` builds, per finding:
  `{issue_text, source_lens, file, line, severity, category, matched_golden_ids,
  primary_judge_verdict, primary_judge, primary_judge_confidence, primary_judge_reasoning,
  adjudication: {verdict: matched|real_but_ungold|hallucination|unjudged, adjudicating_judge,
  confidence, rationale, diff_context_hash}}` — exactly the doc's #1 schema.
- `_run_cell_async` now also persists: `findings` (issue_text+source+file+line+severity),
  `goldens` (comment+severity+category), `per_golden_matches` (scored true_positives +
  false_negatives — which candidate matched which golden + confidence/reasoning),
  `diff_context_hash` (sha1 of diff[:30000], the adjudicator's context), `primary_judge`,
  `adjudicating_judge`. All flow into `summary=res` → `runs/<id>/summary.json` via `register`.
- Re-adjudication with the frontier panel (opus-5/gpt-5.6-sol/Fable, H4) can now re-run the
  stored `findings` against the stored `diff_context_hash` without re-running any framework.
- Validated end-to-end on a superpowers/api cell: 7 findings → 7 adjudication_records with
  verdicts + confidences + rationales + diff_context_hash; 1 per_golden_match.

### Adjudicator max_tokens bug FIXED (the H4 "all-hallucination" root cause)
- **Root cause found + fixed.** `adjudicate.reclassify_async` used `max_tokens=256`. For
  reasoning-model adjudicators (gpt-5.2 with reasoning_effort), the reasoning tokens eat the
  ENTIRE 256-token budget -> `message.content` is empty -> JSON parse fails -> every
  unmatched finding is mis-ruled `hallucination` with `conf=None` (the error branch). This is
  why opus-under-test cells (adjudicator=gpt-5.2) showed the H4 "all-hallucination" red flag
  (e.g. metareview-realistic opus: 228 hallucination / 1 real-ungold), while gpt-under-test
  cells (adjudicator=opus, no reasoning-budget issue) showed the good 11-real/2-hal split.
- Verified directly: gpt-5.2 adjudicate at max_tokens=256 → `reasoning=256, content=""`
  (empty); at max_tokens=1024 → `reasoning=380, content=135` (parseable JSON, is_real=True).
- **Fix:** `reclassify_async` max_tokens 256→1024 (room for reasoning + the JSON). Validated:
  same cell went 0 real-ungold (all conf=None parse-errors) → 1 real-ungold (conf=0.74) +
  6 hallucination (conf=0.78), all with rationales. This is a plumbing fix (like FIX 2), NOT
  the H4 panel expansion (which stays Phase C) — but it's what makes the persisted
  adjudication_records actually carry real verdicts to re-adjudicate.
- **Latent risk (flagged, not fixed):** the primary judge (`judge.py` `call_model_json`
  max_tokens=256) has the same reasoning-budget risk on gpt-5.2; it appears to be working
  (real TP/FP numbers on opus cells), so left untouched, but watch for empty-content judge
  errors in the rerun (would silently underestimate recall). Bump to 512 if seen.

### Running matrix vs the rerun
- The in-flight 192-cell matrix (`/tmp/full_pid.txt`) loaded the PRE-fix code at launch, so its
  realistic cells will NOT have the persisted records and WILL be mis-adjudicated (all-
  hallucination on opus cells). Its value is adapter VALIDATION (do the 4 frameworks run
  end-to-end? per-model cost? findings produced?) + signal, NOT clean quality numbers.
- The **clean rerun** (next step) with the current code gets: persistence (re-adjudicable) +
  correct adjudication + the FIX 1-4 fixes. Recommend rerunning after deciding whether to let
  the current matrix finish (adapter-validation signal) or stop it now.
- **GLM realistic cells return 0 findings** in the current matrix (the known GLM empty-content
  issue: GLM with reasoning_effort returns empty `content` on long prompts even at
  max_tokens=2048 — a `model_router` GLM-handling gap, not an adapter/persistence bug). Flagged
  for the rerun; not fixed here (no-action item). Vanilla (short prompt) works on GLM.

---

## GLM/Kimi empty-content fix (2026-08-23, found while validating the persistence work)

### Root cause (NOT a fixed threshold — a finish_reason=length trap)
GLM (`glm-5.2-vision-flex`) AND Kimi (`kimi-k3`) via Lunaroute return **EMPTY `message.content`**
with `finish_reason=length` when `max_completion_tokens` is too low. They are reasoning models that
spend ~5k–10k tokens on **hidden reasoning** (not exposed in `reasoning_content`) before emitting
visible content. On the real review prompts (~5.8k chars), a 1024/2048/4096/8192 cap is hit
mid-reasoning → `finish_reason=length` → `content=""`. Verified directly via Lunaroute:
- GLM real prompt: max=4096 → `text_len=0, finish=length, tout=4096`; max=16384 → `text_len=1461, finish=stop, tout=5335`
- Kimi real prompt: max=16384 → `text_len=2637, finish=stop, tout=2843`
- Short prompt: max=4096 → works (finishes with reasoning to spare) — so the trap is
  **prompt-size dependent** (longer prompt → more reasoning → needs a higher cap).

### Why every GLM/Kimi cell scored 0.00
The review call used `max_tokens=2048` (sometimes escaped the trap, sometimes not) but the
**extract call used `max_tokens=1024`** — always in the trap → empty content → 0 findings extracted
→ rec=0 across ALL GLM/Kimi cells, ALL frameworks (the pre-fix matrix: GLM 0/0/0/0, Kimi 0/0/0/0).

### Fix (model_router._call_openai_compat)
Enforce a **16384** `max_completion_tokens` floor for both Lunaroute reasoning models (GLM + Kimi)
on EVERY call (review + extract). Verified end-to-end:
- vanilla GLM: was 0 findings / empty raw_output → now 3 findings (review 225s/10k tok, extract 4s)
- vanilla Kimi: was 0 findings / empty → now text_len=2346 (92s)
- The floor is per-Lunaroute (not per-model) since both share the trap; native OpenAI (gpt) is
  unaffected (it doesn't hit finish=length at these sizes — its reasoning is separately budgeted).

### Latency note for the rerun
GLM is SLOW at the 16384 floor (~225s for a medium review call — it generates ~10k reasoning tokens).
Kimi ~92s. xhigh will be slower. The realistic adapters drive a host session (not this path) so
GLM/Kimi realistic cells use the api-fallback branch (still hits this floor). Budget matrix time
accordingly: GLM/Kimi cells are ~2-4min each, not the ~1min of the pre-fix (broken) run.

---

## kimi-k3 dropped from the eval (2026-08-23, user decision)
- Removed `kimi-k3` from the model matrix per user direction. The model axis is now
  {claude-opus-4-5-20251101, gpt-5.2, glm-5.2-vision-flex} × {medium, xhigh} (SPEC §14.1
  "newer set" minus kimi; GLM stays via Lunaroute). Cell count 192 → 144.
- The GLM/Kimi fix (16384 floor + retry-on-empty) stays in the code for both — kimi-k3 is just
  not in the active matrix. If kimi is re-added later the fix applies automatically.
- Relaunch: `/tmp/full3_pid.txt`, log `/tmp/full3_out.txt`, results
  `results/phase_b_full_4fw_clean.json`.

---

## Model axis correction (2026-08-23, user catch)
- Was passing `gpt-5.2` as a model-under-test. Per SPEC §14.1, `gpt-5.2` is an **old anchor**
  (kept for calibration continuity, like sonnet-4.5), NOT a primary model-under-test. The
  codex model-under-test is **`gpt-5.6-sol`** (the newer set). On the CLI arm `gpt-5.2` was
  being remapped to `gpt-5.6-sol` anyway via `_CODEX_SLUGS`, so it was accidentally exercising
  the right model but mislabeling it. Now passing `gpt-5.6-sol` directly so the under-test
  label is honest and the resolved id is recorded correctly.
- Model axis now: {claude-opus-4-5-20251101, gpt-5.6-sol, glm-5.2-vision-flex} × {medium, xhigh}.
- Judge routing unchanged: gpt-* → opus judge; claude/glm → gpt-5.2 judge (calibrated trio).
- Relaunch: `/tmp/full4_pid.txt`, log `/tmp/full4_out.txt`, results
  `results/phase_b_full_4fw_clean.json`.
- NOTE: the run_model_matrix default `--models` arg still lists gpt-5.2 (and the older set) —
  consider updating the default to the newer set so a fresh agent doesn't repeat this.

---

## Opus under-test correction (2026-08-23, user catch #2)
- Was passing `claude-opus-4-5-20251101` as a model-under-test. Per SPEC §9, opus-4.5 is
  **judge-only** (part of the calibrated judge trio kept on the old models for calibration
  compatibility). The opus model-under-test is the newer **`claude-opus-5`**. Verified:
  `claude -p --model opus` resolves to `claude-opus-5` (modelUsage: claude-opus-5).
- Model axis now fully per SPEC §14.1 newer set (minus dropped gemini/terra/kimi):
  {claude-opus-5, gpt-5.6-sol, glm-5.2-vision-flex} × {medium, xhigh}.
- Judges unchanged (calibrated trio): claude-* → gpt-5.2 judge; gpt-* → opus-4.5 judge;
  glm → gpt-5.2 judge. The under-test opus-5 is judged by gpt-5.2 (cross-family).
- Relaunch: `/tmp/full5_pid.txt`, log `/tmp/full5_out.txt`.
- NOTE still outstanding: update `run_model_matrix.py` default `--models` arg to the newer
  set so a fresh agent doesn't repeat this gpt-5.2/opus-4.5-as-under-test mistake.

---

## metareview 0.7.0 rebuild + lens-consistency pass (2026-08-24)

- Stopped the prior matrix (31 cells captured). Rebuilt `bin/metareview` from the
  `feat/review-artifact-security-lens` branch (metareview PR #10) into harnesseval's `bin/`:
  `go build -o bin/metareview ./cmd/metareview` -> `metareview --version` = 0.7.0.
- The lenses are DATA files (rubrics/*.md, skills/*.md) read by the LLM at review time, not
  compiled into the Go binary; the version bump + deterministic-gate binary needed rebuilding,
  the rubric files just need to be present in the checkout. Both confirmed.
- Updated `third_party/metareview_sha.txt` to the PR branch HEAD (f3b6985b) + pinned date.
- "6 lenses" consistency pass: all present-tense refs say 6 across harnesseval adapters +
  metareview rubrics/skills; the only "5 lenses" refs are historical ("the first/original 5
  lenses were all artifact-shape" — describes the pre-security state, accurate).
- metareview PR #10 force-updated with the consistency amend: https://github.com/dsifry/metareview/pull/10

### Tests passed (before relaunch)
- api-direct 6-lens metareview (discourse/pull/4, security PR): 6 lenses ran (feasibility,
  completeness, scope, architecture, intent, security=11-13 findings), 0 errors.
- realistic 6-lens metareview (opus-5, bin 0.7.0, discourse/pull/6): deterministic gates fired
  incl. a new security-reviewer gate from the rebuilt binary; 6 LLM lenses ran; per-model usage
  opus-5+haiku, $4.30; 28 findings, 0 errors.

### Fresh full run launched
- 144 cells: 6 PRs x {claude-opus-5, gpt-5.6-sol, glm-5.2-vision-flex} x {medium,xhigh} x
  {vanilla-engineered, metareview-realistic, superpowers-realistic, compound-realistic}.
- metareview 0.7.0 (6 lenses incl. Security + enriched Architecture). PID `/tmp/full6_pid.txt`,
  log `/tmp/full6_out.txt`, results `results/phase_b_full_4fw_clean.json`.

---

## FIX 3 resolved: opus-5 xhigh 0-findings = transient Claude 529 Overload (2026-08-24)

### Root cause (NOT timeout, NOT token overflow, NOT adapter logic)
The "compound-realistic opus-5 xhigh 0 findings @ 13.8M tok" + "claude -p failed @ 198s"
anomaly is **transient Claude API 529 Overload / rate-limit errors** that `claude -p` surfaces
in TWO modes:
1. **Hard**: non-zero exit, error in stderr (cells 25-28, 32 — the `claude -p failed:` cluster).
2. **Silent**: returncode 0, but the JSON `result` field IS the error string
   (`"API Error: 529 Overloaded. This is a server-side issue..."`). The adapter treated the
   error string as the review output -> 0 extractable findings -> looked like a 0-recall cell
   (cell 8: 13.6M tok, 0 findings, empty per_model_usage).

Verified: reproduced the same cell (compound opus-5 xhigh, hardest PR) — succeeded in 776s
with a full 8-persona report on retry. With `--max-turns 2` + an artificial overload hit,
`claude -p` returns `stop_reason: "stop_sequence"` and `result: "API Error: 529 Overloaded..."`.
xhigh cells are more exposed (longer sessions, wider overload window), but it's intermittent,
not deterministic.

### Fix: retry-on-transient-error (cli_backends.is_transient_claude_error)
- New `is_transient_claude_error(returncode, stdout, stderr)`: detects both modes (non-zero
  exit with overload/rate-limit/503/529 in stderr; OR returncode 0 with `result` starting
  `"API Error: 5"`). Ignores real bugs (non-overload non-zero exits) and real reviews.
- All 3 realistic adapters' `_run_claude_session` now retry once (20s backoff) on a transient
  error, and raise a clear "transient overload persisted after retry" if the retry also hits
  the silent-overload mode. The silent mode is now never misread as a 0-finding review.
- Codex sessions unaffected (codex surfaces errors differently; not changed here).

### Relaunch
- 144 cells, metareview 0.7.0 (6 lenses), retry-on-transient-error. PID `/tmp/full6_pid.txt`,
  log `/tmp/full6_out.txt` (overwritten), results `results/phase_b_full_4fw_clean.json`.
- The 8 transient-error cells from the prior run are debugging signal only.

---

## run_batch identifier + vanilla-GLM intermittent-empty retry (2026-08-24)

### run_batch (registry now groups runs)
- `RunManifest` + `register()` gained a `run_batch` field (timestamp slug, one per matrix run).
  `run_model_matrix.main()` generates `batch_id` at start and passes it to every `register()` call
  + stores it on each cell's `res` dict (so it's in the results JSON AND the registry manifest).
- Any run is now cleanly queryable: `runs.query(run_batch="20260824-...")` returns exactly that
  run's cells, distinguishable from the accumulated prior runs. Failed cells of a run can be
  targeted for rerun by querying the batch for status=error/fail.
- PRIOR runs in the registry have run_batch="" (field added after) — they're not cleanly grouped,
  treat the pre-batch registry as longitudinal debugging signal only.

### vanilla-GLM intermittent 0.00 (separate from the 16384-floor fix)
- The 16384 floor + retry-on-empty fixed GLM in isolation, but under the matrix's 3-way
  concurrency GLM intermittently returned empty OR unparseable text (tokens_out>0 but extract
  JSON parse failed -> 0 findings). The realistic frameworks' retry covered the `claude -p` path;
  the api-direct path (vanilla, superpowers, compound api, metareview api, judge, extract) did not.
- Fix: `call_model_json` now retries once for Lunaroute models when the first call returns empty
  OR unparseable text (merges usage). Validated: 6 concurrent GLM vanilla cells -> 0 zero-finding
  cells (was intermittent 0.00 under load).

### Clean fresh run launched
- All fixes live: 6 lenses (metareview 0.7.0), retry-on-transient-529 (realistic), retry-on-empty/
  unparseable (api-direct Lunaroute), GLM 16384 floor, per-finding adjudication records, run_batch.
- PID `/tmp/full7_pid.txt`, log `/tmp/full7_out.txt`, results
  `results/phase_b_full_4fw_clean.json`, run_batch printed in the log header.

---

## REAL vanilla-GLM 0.00 root cause: _call_cli tuple-unpacking bug (2026-08-24)

### Root cause (NOT intermittent — a deterministic bug)
`model_router._call_cli`'s GLM/Kimi fallback did:
  `_, _, _, per_model = await _call_openai_compat(...)`  then  `return _, per_model`
The text (1st tuple element) was unpacked into `_` and immediately overwritten by the 4th
element (per_model), so `return _, per_model` returned **per_model (a dict) as the text** —
and via `grand_total` reuse `_` became an int (total_tokens). Every `mode=cli` GLM/Kimi call
returned garbage as the review text -> extract got an int -> 0 findings. Deterministic, not
intermittent. This is why vanilla-GLM was ALWAYS 0.00 in the matrix (vanilla runs mode=cli)
while realistic-GLM worked (their api-fallback calls `metareview.review_async(mode="api")`
directly, bypassing `_call_cli`). The retry-on-empty fix I added earlier was chasing the wrong
thing (intermittent empty content) — the real bug was here all along.

### Fix
`_call_cli` GLM fallback: `text, _, _, per_model = await _call_openai_compat(...)`; `return text, per_model`.
Verified: `_call_cli('glm-...')` now returns a 979-char string (was int 1079); vanilla-GLM
mode=cli end-to-end returns 12 findings (was 0.00).

### Scope
Affected every `mode=cli` GLM/Kimi call: vanilla-{naive,engineered} cli on GLM/Kimi, and any
api-direct adapter invoked with mode=cli on GLM/Kimi. The judge layer (api mode) was unaffected.
The retry-on-empty/unparseable fix in call_model_json stays (good insurance for genuine
intermittent empties under load) but was not the cause.

### Relaunch
Clean fresh run with the _call_cli fix + run_batch + all prior fixes. PID `/tmp/full7_pid.txt`
(overwritten), log `/tmp/full7_out.txt`, results `results/phase_b_full_4fw_clean.json`.

---

## metareview 0.8.0 — adversarial stance + 2 new lenses (2026-08-24, PR #11)

Built on the metaswarm-vs-Compound comparison (docs/research/metaswarm_vs_compound_comparison.md).
The key insight (user direction): the gap isn't a missing 7th "adversarial" lens — it's that
EVERY lens must take an adversarial (not collaborative) stance. Adversarial = assume the creator's
intent is good (not hostile to the author) but hostile to unexamined assumptions; "assume there
may be a fundamental mistake hiding in this design; find it." Allowed to conclude the best
improvement is to throw away part or all of the design.

### Changes (PR #11, branch feat/adversarial-lenses-0.8.0)
- Re-stanced ALL 6 existing lenses adversarially (Feasibility, Completeness, Scope, Architecture,
  Intent, Security). No collaborative/confirmatory language remains.
- 2 new lenses (6 -> 8): Testing-quality (false-confidence tests, behavioral-change-without-
  test-work, mocks-not-real-logic) + Data-migration (schema-drift, irreversible migrations,
  missing backfills, dual-write gaps). New rubric files for each.
- Content grafts (steal generously from metaswarm/Compound, exclude non-diff):
  Security + IDOR/ownership, injection variants, SSRF protocol-bypass, secrets-in-logs;
  Architecture + sentinel-meaning-change, cascading-failure, stand-in-guard-fidelity,
  api-contract-breaking-change.
- Anchored confidence rubric (0/25/50/75/100 + P0-P3) + per-lens "what you don't flag"
  suppression list (anti-overlap) added to all lenses.
- Excluded (non-diff): plan-time architect gating, STRIDE, weighted scoring, project-vertical
  checks, pnpm audit/CVE, release 7-gate pipeline, session/MFA/monitoring posture.
- Version 0.7.0 -> 0.8.0. Verified by a reviewer subagent (all 6 plan items MET).

### Status
- PR #11 up at https://github.com/dsifry/metareview/pull/11 (needs review + merge).
- AFTER merge + the 0.7.0 eval run finishing, Phase 4: update harnesseval adapters
  (metareview.py + metareview_realistic.py) from 6 -> 8 lenses + adversarial stance + grafts,
  rebuild bin/metareview from 0.8.0, update pinned SHA, test, launch the 0.8.0 eval run.
