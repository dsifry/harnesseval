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
