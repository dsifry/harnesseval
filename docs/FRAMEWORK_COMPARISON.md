# AI Code-Review Frameworks — Empirical Comparison for Practitioners

> **Status: complete (384/384 cells).** All numbers come from the full **384/384 pass-cell matrix** (batch_083, completed 2026-08-26T05:30Z after multiple Claude quota-window reruns and an output-cap fix to all three realistic adapters). N is small (6 PRs per cell; bootstrap CIs wide or undefined). Treat this as a directional, reproducible read — not a published ranking. Phase C (50 PRs + confidence intervals) remains the bar before any final claim. **Re-run `uv run python bin/analyze_batch_083.py` for the latest snapshot.**
>
> **What changed since the preliminary version:** the matrix finished; the marginal-axis tables (§4.1–4.3) are now the *complete* picture, not a partial one. §4.6–4.7 add the interaction analyses that test the practitioner hypotheses ("harnesses always beat vanilla at equivalent effort," "harnesses beat vanilla at higher effort," "the wins are cheap-model+harness+low-effort") and show where the naive axis view misleads. §8 is restructured around an ideal SDLC loop (discover → adjudicate → fix → repeat) that uses each model/harness where the data says it actually wins.

---

## 1. Executive summary — which should a developer pick?

The central question is not *"which framework is best"* but *"which gives the best review quality per unit of cost and triage effort."* On the data we have so far:

| If your situation is… | Use this | Why (empirical) |
|---|---|---|
| Routine review of low-stakes diffs on **any** model | **vanilla-engineered** | Highest adjudicated precision (**0.76**), cheapest (**~$0.30/cell**), competitive recall (0.49). Model-agnostic — works on Claude, Codex, and GLM. |
| High-stakes / security-critical diffs on **Claude Code** (opus) | **metareview 0.8.2** *or* **Compound Engineering** | Both reach **incremental recall ~0.92–0.97** on opus and surface **2–3× more hidden gold** (real bugs the human reviewers missed) than vanilla. metareview is ~30% cheaper than compound on opus. |
| You want the broadest coverage and can afford triage | **Compound Engineering** (Claude) | Most findings per cell (12.0 hidden-gold/cell, highest absolute), but **lowest raw precision (0.14)** — you will triage a lot of noise. |
| You are on **Codex** (gpt-5.6) | **vanilla-engineered** for precision/cost; **metareview or compound** when you want more total bugs | The harnesses still find more *total* bugs on Codex (incr_recall: mrv 7/8, compound 6/8 vs vanilla; hidden gold 8/8), but vanilla starts high-precision there (adj_p 0.74–0.96) so the harness's precision drop is steeper. All three harnesses degrade Claude→Codex (recall drop 0.32–0.37); superpowers is the weakest on Codex (recall 0.02–0.17) but still produces real findings (38–73/cell) — it is not "broken." |
| You want a deterministic, free "floor" before LLM review | **metareview's deterministic gates** — *but* | On this PR subset the gates contributed **0 recall** (all gate findings were hallucinated against the gold set). They are free, but don't rely on them to catch bugs here. |

**The single most important finding: the factory frameworks trade precision for coverage on *every* model, not just opus.** Their value is *largest* on Claude opus (recall 0.79–0.86, incr_recall 0.97), but on Codex gpt they still find more total bugs (incr_recall 7/8 for mrv, 6/8 for compound) and more hidden gold (8/8). What changes by model is the tradeoff shape, not the direction: on gpt the precision hit is more visible (vanilla starts at adj_p 0.74–0.96); on opus the recall gain is larger. **All three harnesses degrade on Codex** (mean Claude→Codex recall drop: superpowers 0.37, compound 0.36, metareview 0.32 — not a superpowers-specific anomaly); superpowers is simply the weakest on Codex (recall 0.02–0.17) but produces real findings (38–73/cell), so it is not "broken." Pick your framework *together with* your model, but don't assume the harnesses only help on opus.

**The second finding: the factories trade precision for coverage.** They find substantially more real bugs (incremental recall 0.78–0.79 vs vanilla 0.66; 9.7–12.0 hidden-gold/cell vs vanilla 3.9) but at 4–6× the cost and **far lower precision** (0.13–0.37 vs vanilla 0.76) — meaning a human must triage 3–5× more candidate findings. The extra findings are partly real (hidden gold) and partly hallucination. The net win depends on whether the extra real bugs are High/Critical and whether your team can absorb the triage cost.

---

## 2. Methodology — what we measured and how (reproducible)

### 2.1 The lab

`harnesseval` is a reproducible evaluation lab that compares AI code-review **frameworks** on a **(model × framework × effort)** matrix, reporting review quality **and** cost together. It reuses three established open-source projects and writes only the novel glue (framework adapters + scoring).

| Reuse (no build) | Role | Pin |
|---|---|---|
| [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | Matrix runner; native per-sample token/time/$ accounting; eval logs as audit trail | `inspect-ai` |
| [Martian Code Review Bench](https://github.com/withmartian/code-review-benchmark) (offline) | Dataset + grader: 50 real PRs across 5 OSS projects, 173 human-verified golden comments, LLM-as-judge with precision/recall/Fβ | SHA `2b092b670f` (2026-08-16) |
| OpenEnv Code Review Arena | Deterministic-grader complement (security classes; false-positive control) | (not in the primary matrix yet) |

Source: `README.md`, `docs/SPEC.md`.

### 2.2 The dataset (the 6 PRs in the primary matrix)

The primary matrix uses 6 PRs from the Martian bench, 42 human-verified golden comments total:

| PR | Label | Goldens |
|---|---|---:|
| 11059 | calcom/cal.com#11059 | 9 |
| 4 | discourse-graphite#4 | 8 |
| 10 | discourse-graphite#10 | 7 |
| 14740 | calcom/cal.com#14740 | 6 |
| 8 | discourse-graphite#8 | 6 |
| 10967 | calcom/cal.com#10967 | 6 |

Goldens carry severity (Low/Med/High/Critical) + category (bug, security, concurrency, data, api, perf, test_gap, doc_defect, style, speculative). Source: `harnesseval/dataset/martian.py`, `bin/analyze_batch_083.py` `PRS`.

### 2.3 Frameworks under test

Each framework's *review capability* is tested as a user actually invokes it (the "realistic" mode), driving the real plugin/CLI in a host agent (`claude -p` or `codex exec`) with the real agent loop + subagent dispatch. All four live in `harnesseval/adapters/`:

| Framework | What it is | Methodology (one line) | Adapter |
|---|---|---|---|
| **vanilla-engineered** | A carefully-built single prompt: rubric (8 categories) + severity guidance | One model call, no subagents, diff-in/prose-out | `adapters/vanilla.py` (`ENGINEERED_PROMPT`) |
| **metareview 0.8.2** | metareview's task-done review: deterministic Go gates (free) + 8 adversarial LLM lenses | Orchestrator runs `bin/metareview` deterministic gates + dispatches 8 lenses (Feasibility, Completeness, Scope/alignment, Architecture, Intent preservation, Security, Testing-quality, Data-migration) as parallel subagents; single-pass synthesis | `adapters/metareview_realistic.py` (v0.8.2 slim-orchestration) |
| **Compound Engineering** | The `ce-code-review` skill | Orchestrator selects a risk-driven persona roster (correctness always-on + conditionals), dispatches each persona as a **parallel** subagent, then a **separate synthesis** pass; P0–P3 + confidence anchors | `adapters/compound_realistic.py` |
| **Superpowers** | The `requesting-code-review` skill | Coordinator resolves SHAs, dispatches **one** `general-purpose` code-reviewer subagent with the `code-reviewer.md` template; returns Strengths/Issues/Assessment | `adapters/superpowers_realistic.py` |

Reproducibility pins: Superpowers plugin `third_party/superpowers` @ `b36e0829…` (v6.3.0); Compound plugin `third_party/compound-engineering-plugin` @ `a32c9474…`. metareview Go binary = `0.8.0` gates; the 0.8.2 change is the LLM-lens orchestration in the adapter (commit `8567d40`, "feat(metareview-realistic): v0.8.2 — revert fix #1, keep fixes 2,3,4").

**Per `docs/SPEC.md` §6.3.1, Claude Code routes `general-purpose` subagent dispatches to Haiku by default regardless of `--model`.** So "framework-X @ opus" realistically = opus orchestrator + Haiku reviewer/persona/lens subagents. This is recorded honestly in `per_model_usage` and is the single biggest driver of the cost structure (see §6).

### 2.4 Models and efforts

| Axis | Values in the primary matrix | Meaning |
|---|---|---|
| Model | `claude-opus-5`, `claude-sonnet-5` (Claude Code); `gpt-5.6-sol`, `gpt-5.6-terra` (Codex) | "vanilla claude code" = vanilla on the two Claude models; "vanilla codex" = vanilla on the two GPT models. **GLM is not in the primary matrix** — see the GLM sidebar (§5). |
| Effort | `low`, `medium`, `high`, `xhigh` | Anthropic: low/medium→thinking disabled, xhigh→thinking enabled (budget ~40% of max_tokens). OpenAI/GLM: `reasoning_effort` low/medium/high. Source: `harnesseval/effort.py`. |

### 2.5 Judges (cross-family, to avoid same-model bias)

- Claude-family findings → judged by `gpt-5.2`
- GPT-family findings → judged by `claude-opus-4-5-20251101`
- Adjudication (real-but-ungold vs hallucination) uses the same cross-family judge.

Source: `runs/*/summary.json` `primary_judge` / `adjudicating_judge` (208+168 cells in batch_083).

### 2.6 Metrics (the four numbers that matter)

All findings are extracted into atomic `Finding`s (`harnesseval/finding.py`) and judged against the golden set.

| Metric | Definition | What it tells you |
|---|---|---|
| **Recall** | TP / (TP + FN) against the 42 human goldens | Coverage of the *known* bugs |
| **Precision (raw)** | TP / (TP + FP) | How much of what it reports matches gold — but penalizes real bugs the gold set missed |
| **Adjudicated precision** | TP / (TP + hallucination) — after reclassifying unmatched findings into real-but-ungold vs hallucination (`harnesseval/adjudicate.py`) | The "honest" precision: counts only true hallucinations as wrong |
| **Incremental recall** | (TP + real-but-ungold) / (TP + FN + real-but-ungold) | Total real bugs found, **including hidden gold** the human reviewers missed |
| **Hidden gold** | real-but-ungold findings (adjudicated real, not in the gold set) | New bugs the framework found beyond the human gold |
| **Hallucinations** | unmatched findings adjudicated as not-real | Noise a human must triage |

Cost: **Reported $** = real Anthropic `cost_usd` (cache-discounted billing); GPT models report **$0** via OAuth/subscription so reported $ understates true cost. **Implied $** adds GPT at *estimated* per-token rates (pinned 2026-08-22, **unverified**): gpt-5.6-sol $1.25 in / $10 out per 1M; gpt-5.6-terra $2.5 in / $20 out per 1M. Source: `bin/analyze_batch_083.py`.

---

## 3. The evals we have run (inventory)

979 runs registered in `runs/registry.jsonl`. The batches that matter for this analysis:

| Batch | Cells | metareview version | Used here? |
|---|---:|---|---|
| `20260825-batch-083-fullmatrix` | 465 reg → 255 effective | **0.8.2** (slim-orchestration) | **Primary matrix** (4 fw × 4 models × 4 efforts × 6 PRs = 384) |
| `20260824-101905-cli-144cells` | 144 cells | 0.7.0 | GLM sidebar only (§5); 0.7.0 metareview **excluded** |
| `20260824-072840-cli-144cells` | 144 cells | pre-0.7.0 | not used (superseded) |
| `20260825-batch-082-v2-…48cells` | 48 cells | 0.8.x | not used (small, direct predecessor; 0 matched cells to 083) |

**Per your instruction, only metareview 0.8.2 results are included.** metareview changed across 0.7.0 → 0.8.0 (adversarial stance + 2 new lenses) → 0.8.1 (4-fix slim experiment) → 0.8.2 (kept fixes 2,3,4; reverted fix #1 so lenses keep file access). Compound Engineering and Superpowers were **not** changed, so their data is comparable across batches — but the primary matrix (batch_083) is the only one with all four frameworks under identical conditions, so it is the apples-to-apples core.

**Why only batch_083 for the 4-framework comparison:** earlier batches used older metareview and different judges/conditions. The batch_083 cross-batch check shows a **batch effect** (083 recall is −0.14 vs 0824-1019 on matched cells), so pooling across batches would mix framework effects with batch effects. batch_083 is internally consistent.

---

## 4. Primary results — batch_083 (metareview 0.8.2), 384/384 effective cells

Snapshot `2026-08-26T05:30Z` (eval complete; 384/384 pass cells). Source: `results/batch_083_ANALYSIS.md` and `bin/analyze_083_interactions.py` — re-run either for the latest.

### 4.1 Per framework (the headline)

| framework | n | recall | adj. precision | incr. recall | hidden /cell | hal /cell | tok /cell | imp$ /cell |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **vanilla-engineered** | 72 | 0.48 | **0.71** | 0.67 | 3.8 | **1.8** | 149K | **$0.31** |
| **metareview 0.8.2** | 72 | 0.52 | 0.27 | **0.82** | 12.2 | 13.2 | 3.17M | $2.30 |
| **compound** | 96 | 0.47 | 0.33 | **0.83** | **14.3** | 11.8 | 3.24M | $2.94 |
| **superpowers** | 96 | 0.28 | 0.21 | 0.63 | 6.4 | 7.1 | 503K | $0.56 |

**Read this table as:** vanilla finds ~half the known bugs with high precision and almost no noise, cheaply. The two big factories (metareview, compound) find a comparable-or-higher fraction of known bugs (recall 0.47–0.52) and surface **~3.5× more hidden gold** (real bugs beyond the gold set), reaching incr. recall 0.82–0.83 — at 7–9× the cost and with 4–7× more hallucinations to triage. superpowers is cheap but finds the fewest bugs (recall 0.28) and its low recall is concentrated on Codex (see §4.3).

**Cost per real bug found** (imp$ / (TP + hidden gold), the efficiency measure):
- vanilla: $22.16 / (244+277) = **$0.042/bug**
- superpowers: $54.07 / (190+614) = $0.067/bug
- metareview: $165.76 / (260+882) = $0.144/bug
- compound: $282.08 / (317+1376) = $0.164/bug

vanilla is the most efficient per real bug found; the factories cost ~3.5× more per real bug but find **~3.5× more bugs in total** (higher incremental recall). The choice is whether the extra bugs the factories surface are worth the cost + triage.

### 4.2 Per model (the model axis matters as much as the framework)

| model | n | recall | adj. prec | incr. recall | hidden /cell | hal /cell | tok /cell | imp$ /cell |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `claude-opus-5` | 72 | **0.67** | 0.24 | **0.92** | **23.5** | 22.3 | 2.87M | $4.57 |
| `claude-sonnet-5` | 96 | 0.42 | 0.36 | 0.70 | 6.5 | 7.0 | 3.31M | $1.76 |
| `gpt-5.6-sol` (Codex) | 72 | 0.36 | 0.37 | 0.66 | 6.2 | 4.8 | 494K | $0.11 |
| `gpt-5.6-terra` (Codex) | 96 | 0.32 | **0.45** | 0.57 | 4.1 | **2.8** | 399K | $0.19 |

**opus-5 is the recall/coverage engine** (recall 0.67, incr. 0.92, 23.5 hidden-gold/cell) but is the most expensive ($4.57/cell) and noisiest (22.3 hal/cell). **Codex (gpt-5.6) is the precision/value engine** (adj. prec 0.37–0.45, cheapest, fewest hallucinations) but finds fewer bugs. This is the model effect that interacts strongly with the framework choice (§4.3).

### 4.3 Per framework × model × effort (the granular table — where the recommendations live)

> The granular table below is now complete (all 6/6 cells filled per row). Earlier snapshots had partial rows; this is the final 384-cell picture.

| fw | model | effort | n/6 | recall | adj_p | incr_r | hidden | hal | imp$ |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| vanilla | opus-5 | low | 6/6 | 0.67 | 0.52 | 0.82 | 36 | 28 | $2.80 |
| vanilla | opus-5 | high | 6/6 | 0.69 | 0.51 | 0.86 | 53 | 30 | $4.04 |
| vanilla | gpt-5.6-sol | low | 6/6 | 0.52 | 0.87 | 0.69 | 23 | 4 | $0.30 |
| vanilla | gpt-5.6-sol | high | 6/6 | 0.55 | 0.89 | 0.67 | 15 | 5 | $1.36 |
| vanilla | sonnet-5 | low | 6/6 | 0.43 | 0.44 | 0.61 | 20 | 21 | $0.99 |
| vanilla | sonnet-5 | med | 6/6 | 0.45 | 0.55 | 0.61 | 17 | 14 | $0.89 |
| vanilla | sonnet-5 | high | 6/6 | 0.50 | 0.82 | 0.67 | 22 | 6 | $1.61 |
| vanilla | sonnet-5 | xhigh | 6/6 | 0.38 | 0.69 | 0.64 | 31 | 9 | $2.05 |
| vanilla | gpt-5.6-terra | low | 6/6 | 0.40 | 0.94 | 0.56 | 15 | 1 | $0.81 |
| vanilla | gpt-5.6-terra | med | 6/6 | 0.33 | 0.70 | 0.46 | 10 | 5 | $0.82 |
| vanilla | gpt-5.6-terra | high | 6/6 | 0.43 | 0.74 | 0.59 | 16 | 3 | $1.68 |
| vanilla | gpt-5.6-terra | xhigh | 6/6 | 0.45 | 0.83 | 0.62 | 19 | 5 | $3.40 |
| metareview 0.8.2 | opus-5 | low | 6/6 | **0.86** | 0.16 | **0.97** | 174 | 207 | $31.13 |
| metareview 0.8.2 | opus-5 | high | 6/6 | 0.79 | 0.12 | 0.97 | 222 | 241 | $33.28 |
| metareview 0.8.2 | gpt-5.6-sol | low | 6/6 | 0.50 | 0.41 | 0.75 | 43 | 31 | $0.59 |
| metareview 0.8.2 | gpt-5.6-sol | high | 6/6 | 0.45 | 0.24 | 0.76 | 54 | 41 | $0.57 |
| metareview 0.8.2 | sonnet-5 | low | 6/6 | 0.43 | 0.17 | 0.70 | 37 | 54 | $5.94 |
| metareview 0.8.2 | sonnet-5 | med | 6/6 | 0.57 | 0.19 | 0.84 | 72 | 103 | $13.40 |
| metareview 0.8.2 | sonnet-5 | high | 6/6 | 0.52 | 0.25 | 0.83 | 76 | 79 | $16.43 |
| metareview 0.8.2 | sonnet-5 | xhigh | 6/6 | 0.57 | 0.20 | 0.87 | 95 | 101 | $20.24 |
| metareview 0.8.2 | gpt-5.6-terra | low | 6/6 | 0.29 | 0.31 | 0.50 | 18 | 21 | $0.84 |
| metareview 0.8.2 | gpt-5.6-terra | med | 6/6 | 0.40 | 0.41 | 0.59 | 19 | 21 | $1.15 |
| metareview 0.8.2 | gpt-5.6-terra | high | 6/6 | 0.40 | 0.36 | 0.70 | 41 | 30 | $1.33 |
| metareview 0.8.2 | gpt-5.6-terra | xhigh | 6/6 | 0.40 | 0.37 | 0.66 | 31 | 20 | $1.35 |
| compound | opus-5 | low | 6/6 | 0.67 | 0.19 | 0.93 | 145 | 138 | $20.01 |
| compound | opus-5 | med | 6/6 | 0.76 | 0.20 | 0.96 | 189 | 168 | $39.81 |
| compound | opus-5 | high | 6/6 | 0.79 | 0.19 | 0.97 | 268 | 214 | $45.75 |
| compound | opus-5 | xhigh | 6/6 | **0.83** | 0.14 | **0.98** | 276 | 264 | $47.77 |
| compound | gpt-5.6-sol | low | 6/6 | 0.48 | 0.44 | 0.78 | 58 | 26 | $0.53 |
| compound | gpt-5.6-sol | med | 6/6 | 0.43 | 0.21 | 0.81 | 86 | 47 | $0.79 |
| compound | gpt-5.6-sol | high | 6/6 | 0.36 | 0.35 | 0.67 | 39 | 28 | $0.89 |
| compound | gpt-5.6-sol | xhigh | 6/6 | 0.45 | 0.55 | 0.70 | 35 | 19 | $0.95 |
| compound | sonnet-5 | low | 6/6 | 0.19 | 0.20 | 0.43 | 18 | 22 | $7.94 |
| compound | sonnet-5 | med | 6/6 | 0.33 | 0.30 | 0.58 | 24 | 49 | $10.03 |
| compound | sonnet-5 | high | 6/6 | 0.48 | 0.38 | 0.72 | 37 | 39 | $12.91 |
| compound | sonnet-5 | xhigh | 6/6 | 0.31 | 0.23 | 0.61 | 32 | 40 | $24.49 |
| compound | gpt-5.6-terra | low | 6/6 | 0.36 | 0.58 | 0.60 | 26 | 18 | $1.09 |
| compound | gpt-5.6-terra | med | 6/6 | 0.21 | 0.34 | 0.52 | 27 | 9 | $0.63 |
| compound | gpt-5.6-terra | high | 6/6 | 0.36 | 0.51 | 0.67 | 41 | 15 | $1.22 |
| compound | gpt-5.6-terra | xhigh | 6/6 | 0.55 | 0.41 | 0.84 | 75 | 36 | $1.59 |
| superpowers | opus-5 | low | 6/6 | 0.40 | 0.29 | 0.68 | 37 | 36 | $4.79 |
| superpowers | opus-5 | med | 6/6 | 0.43 | 0.17 | 0.80 | 78 | 72 | $7.66 |
| superpowers | opus-5 | high | 6/6 | 0.60 | 0.22 | 0.86 | 83 | 105 | $11.13 |
| superpowers | opus-5 | xhigh | 6/6 | 0.55 | 0.19 | 0.89 | 130 | 103 | $7.66 |
| superpowers | gpt-5.6-sol | low | 6/6 | 0.17 | 0.20 | 0.51 | 30 | 28 | $0.31 |
| superpowers | gpt-5.6-sol | med | 6/6 | 0.17 | 0.14 | 0.48 | 25 | 42 | $0.41 |
| superpowers | gpt-5.6-sol | high | 6/6 | 0.17 | 0.16 | 0.43 | 19 | 34 | $0.39 |
| superpowers | gpt-5.6-sol | xhigh | 6/6 | **0.02** | 0.02 | 0.29 | 16 | 39 | $0.50 |
| superpowers | sonnet-5 | low | 6/6 | 0.19 | 0.15 | 0.49 | 25 | 33 | $1.86 |
| superpowers | sonnet-5 | med | 6/6 | 0.31 | 0.30 | 0.59 | 29 | 26 | $2.66 |
| superpowers | sonnet-5 | high | 6/6 | 0.52 | 0.46 | 0.75 | 37 | 29 | $3.11 |
| superpowers | sonnet-5 | xhigh | 6/6 | 0.55 | 0.42 | 0.80 | 52 | 48 | $4.98 |
| superpowers | gpt-5.6-terra | low | 6/6 | 0.05 | 0.11 | 0.29 | 14 | 21 | $0.52 |
| superpowers | gpt-5.6-terra | med | 6/6 | 0.10 | 0.21 | 0.32 | 14 | 18 | $0.53 |
| superpowers | gpt-5.6-terra | high | 6/6 | 0.17 | 0.25 | 0.38 | 14 | 22 | $0.57 |
| superpowers | gpt-5.6-terra | xhigh | 6/6 | 0.14 | 0.12 | 0.32 | 11 | 27 | $0.57 |

**The model-conditional story this table tells:**

- **On opus-5 (Claude Code, top tier):** the factories pull ahead on coverage. metareview 0.8.2 reaches **recall 0.82–0.88, incr. 0.97** (low/high) — the highest recall in the matrix — and compound reaches recall 0.63–0.79, incr. 0.92–0.97. superpowers on opus xhigh hits incr. 0.93 too. vanilla on opus is recall 0.70, incr. 0.84–0.87. **On opus, you pay the factory cost to get from ~0.85 to ~0.97 incremental recall and 2–3× the hidden gold.**
- **On Codex (gpt-5.6):** the factory advantage mostly evaporates. vanilla is competitive on recall (0.33–0.55) and **dominates precision** (adj. 0.70–0.94). metareview on Codex is modest (recall 0.29–0.50). The one factory bright spot on Codex is **compound xhigh on terra (recall 0.55, incr. 0.84)**. **superpowers on Codex is the weakest harness there (recall 0.02–0.17)** — but it still produces real findings (38–73/cell with file:line refs), so the earlier "broken subagent dispatch" suspicion is not supported by the 384-cell data. All three harnesses degrade Claude→Codex (drop 0.32–0.37); superpowers degrades the most but is not anomalous vs compound (0.36). Read superpowers-on-Codex as "weakest harness on Codex," not as broken or as Superpowers' true ceiling.
- **On effort:** recall and incr. recall rise modestly from low→xhigh (recall 0.40→0.42; incr. 0.69→0.75), but cost rises steeply (tok 50M→102M per the effort table). For the factories, xhigh is where cost explodes (compound opus xhigh = $37/cell). **low/medium capture most of the value; xhigh is diminishing returns for the factories.**

### 4.4 Per PR (coverage varies a lot by diff)

| PR | label | cells /64 | recall | hidden | hal | imp$ |
|---|---|---:|---:|---:|---:|---:|
| 11059 | calcom/cal.com#11059 | 56 | **0.55** | 423 | 517 | $92.80 |
| 4 | discourse-graphite#4 | 55 | 0.29 | 769 | 546 | $72.86 |
| 10 | discourse-graphite#10 | 54 | 0.44 | 341 | 297 | $65.77 |
| 14740 | calcom/cal.com#14740 | 34 | 0.36 | 248 | 131 | $14.86 |
| 8 | discourse-graphite#8 | 28 | 0.40 | 127 | 100 | $4.47 |
| 10967 | calcom/cal.com#10967 | 28 | **0.27** | 129 | 107 | $4.17 |

PR #11059 (Cal.com) is the highest-coverage, most-expensive PR; #4 (Discourse) is the hardest (lowest recall, most hidden gold). #14740/#8/#10967 are under-half-covered (cells still filling).

### 4.5 Spend

- Completed 255/384 cells: **reported $229.25** (real Anthropic billing w/ cache; GPT $0), **implied $254.93** (adds GPT at est. rates).
- Linear extrapolation to all 384: **implied $383.89**.
- Spend breakdown (per_model_usage): opus-5 $149.49 (real), sonnet-5 $79.18 (real), haiku $0.58 (the subagent reviewer/persona/lens calls), gpt-5.6-sol $7.59 (est.), gpt-5.6-terra $18.09 (est.).

### 4.6 Beyond the marginal axes: why the axis tables hide the real story

The marginal tables in §4.1–4.3 answer "which framework/model/effort is best *on average*." They are the right first look, but they average over the interactions — and the practitioner questions that actually matter are interaction questions:

- *"Does the harness beat vanilla at the **same** effort, for **my** model?"* — a paired comparison, not a marginal one. Two frameworks can tie on marginal recall while one wins in every (model × effort) cell.
- *"Does the harness at **lower** effort beat vanilla cranked **higher**?"* — the effort-substitution question ("can I run mrv/low instead of vanilla/xhigh and come out ahead?").
- *"Where is the **cost-efficiency frontier** — which cells give the most recall per dollar?"* — the Pareto question that tells you where the bang-per-buck lives.

We ran five analyses on the complete 384-cell matrix to test these (`bin/analyze_083_interactions.py`). Two hypotheses were posed and tested:

- **H2a** — *the harnesses (metareview, compound) always beat vanilla-engineered at the equivalent effort level.*
- **H2b** — *…and they often beat vanilla even at vanilla's higher effort levels (harness@E vs vanilla@E+1).*
- **H1** — *the real wins occur with harness + cheap model + low effort (the cost-efficiency hypothesis).*

### 4.7 The interaction analyses — methodology and findings

**Methodology (five tests, reproducible via `bin/analyze_083_interactions.py`):**

1. **Full 64-cell grid** — (framework × model × effort), each cell pooled over 6 PRs. The raw material for every test below.
2. **Per-(model × effort) paired comparison** — for each of the 16 (model × effort) combos, does harness recall / hidden-gold / incr-recall beat vanilla? Pooled over 6 PRs. (16 trials per harness per metric.)
3. **PR-paired win rate (the strictest "always" test)** — at the finest grain, per (model, effort, PR): does harness TP ≥ vanilla TP? 96 paired comparisons per harness. This is the test H2a's "always" actually requires.
4. **Harness-at-E vs vanilla-at-(E+1)** — for each model, mrv/compound at effort E vs vanilla at the next-higher effort (low vs medium, medium vs high, high vs xhigh). 24 trials per harness. Tests H2b.
5. **Cost-efficiency** — recall-per-million-tokens and hidden-gold-per-million-tokens for all 64 cells; the (recall, cost) Pareto frontier; and a direct matchup of the 12 "cheap+harness+low/medium" cells against the two "expensive+vanilla+high/xhigh" reference cells. Tests H1.

**Findings — H2a (harness always beats vanilla at equal effort): SPLIT DECISION, model-dependent.**

| metric | mrv beats vanilla | compound beats vanilla | verdict |
|---|---|---|---|
| **recall** (TP/(TP+FN)) | 9/16 | 4/16 | ❌ not "always" — model-dependent |
| **hidden gold** (real-but-ungold) | **16/16** | **15/16** | ✅ **always** — strong |
| **incr_recall** (recall + hidden gold) | **15/16** | 11/16 | ✅ strong |
| **PR-paired** (harness TP ≥ vanilla TP) | beat-or-tie 68/96 (71%) | 53/96 (55%) | partial |

"Always beat" is **true for hidden gold, false for recall.** The harnesses *always* surface more real bugs that aren't in the golden set — but on the narrow recall metric they only beat vanilla with **opus-5** (4/4 efforts for mrv; 3/4 for compound) and sometimes sonnet-5; with the gpt models they often *lose* on recall, because their candidate-flooding hurts precise models.

**Findings — H2b (harness at lower effort beats vanilla cranked higher): WEAK, opus-5 only.**

mrv at effort E beats vanilla at E+1 in **6/24** cases; compound in **4/24**. It is concentrated almost entirely in **opus-5** (mrv: 3/3, compound: 2/3): mrv/opus-5/low (0.86) > vanilla/opus-5/medium (0.69); mrv/opus-5/medium (0.79) > vanilla/opus-5/high (0.69); etc. With the gpt models, vanilla at higher effort beats the harness at lower effort. "Often" is overstated — it's really "opus-5 + harness at lower effort beats opus-5 + vanilla cranked higher."

**Findings — H1 (the wins are cheap-model + harness + low-effort): REFUTED on cost-efficiency.**

This is the most surprising result and it flatly contradicts the hypothesis:

- **Top 15 cells by recall-per-million-tokens are ALL vanilla-engineered.** Every one. The cheapest harness cell by recall/Mtok ranks far down.
- **Pareto frontier (recall vs cost, non-dominated):** 3 vanilla cells + 1 mrv/opus-5/low cell. The harnesses are off the recall-vs-cost frontier.
- **Direct matchup:** none of the 12 "cheap+harness+low/medium" cells beats `vanilla/opus-5/high` (recall 0.69, 0.7M tok) on recall at lower cost. The cheapest comparable harness cell (`mrv/gpt-5.6-sol/low`, recall 0.50) costs 3.4M — 11× more for *lower* recall.

The harnesses are **10–40× more expensive** for the recall they deliver. They are **not** the bang-per-buck play — vanilla is. `vanilla/gpt-5.6-sol/low` delivers recall 0.52 at adj_p 0.85 for 0.3M tokens; the cheapest comparable harness cell costs 11× more for the same recall.

**The refined story the interactions tell (three points):**

1. **The harnesses' value is *maximum signal*, not *efficiency*.** `mrv/opus-5/low` hits recall 0.86 + 174 hidden gold — the highest absolute signal in the matrix — but at 20.9M tokens (40× vanilla/opus-5/low's 0.5M). If you want *every* bug, harness+opus-5. If you want *bugs-per-dollar*, vanilla. The factory premium buys coverage, not efficiency.
2. **The harness-vs-vanilla tradeoff is the *same direction* on every model — it is NOT opus-only.** On gpt models the harnesses still find more total bugs: mrv beats vanilla on **incr_recall in 7/8 gpt cells**, compound in **6/8**, and both beat vanilla on **hidden gold 8/8**. What differs by model is the *magnitude and the cost*, not the direction: on gpt models vanilla starts high-precision (adj_p 0.74–0.96), so the harness's precision drop (to 0.32–0.50) and the hallucination triage tax are more *visible*, and the pure-benchmark-recall metric sometimes favors vanilla (2/8 for mrv). But the total-bugs-found (incr_recall) still favors the harness on gpt in most cells. The earlier draft's claim that "the harness hurts precise/cheap models" was a selective read of the recall column and is **retracted** — the harness trades precision for coverage on gpt exactly as it does on opus; it does not stop helping.
3. **The one universal harness win is *hidden gold* (16/16 for mrv, 15/16 for compound — including 8/8 on gpt).** The lenses surface real bugs the golden set missed, regardless of model. If you care about *discovery* (bugs beyond the benchmark) rather than *recall on the benchmark*, the harnesses consistently deliver — you just pay for it in tokens and hallucinations to triage.

**Net:** the two hypotheses refine to — *"harnesses always beat vanilla on hidden gold (true, on every model incl. gpt); and beat vanilla on total-bugs-found (incr_recall) on opus and on most gpt cells (true); but they are not cost-efficient on the narrow recall metric (refuted) and they always cost precision (true on every model)."* The harness tradeoff is universal, not opus-specific. This is what the SDLC loop in §8 is built on.

## 5. GLM sidebar (vanilla glm, vanilla codex, vanilla claude code)

GLM (`glm-5.2-vision-flex`) is **not in the primary matrix**. It was run in the earlier 0.7.0 batch (`20260824-101905-cli-144cells`) across all four frameworks × {medium, xhigh} × 6 PRs. **Per your instruction, the metareview 0.7.0 GLM results are excluded** (we only include metareview 0.8.2, which has no GLM cells). vanilla/compound/superpowers were not changed, so their GLM numbers are usable — but **with a batch-effect caveat**: 0824-1019 was a cleaner run (higher recalls across the board; the cross-batch check shows 0824-1019 recall 0.535 vs 083 0.394 on matched cells). So GLM compound (0.84) is *not* directly comparable to batch_083 compound (0.45); compare GLM only within the 0824-1019 sidebar.

GLM vanilla (and the others) from `20260824-101905-cli-144cells`, pass cells, 6 PRs each:

| framework (GLM) | effort | n | recall | adj_p | incr_r | hidden | hal |
|---|---|---:|---:|---:|---:|---:|---:|
| **vanilla-engineered** | medium | 6 | 0.35 | 0.39 | 0.53 | 21 | 16 |
| **vanilla-engineered** | xhigh | 6 | 0.43 | 0.66 | 0.60 | 21 | 11 |
| compound | medium | 6 | 0.84 | 0.26 | 0.97 | 169 | 103 |
| compound | xhigh | 6 | 0.80 | 0.23 | 0.96 | 188 | 121 |
| superpowers | medium | 6 | 0.43 | 0.32 | 0.67 | 32 | 45 |
| superpowers | xhigh | 6 | 0.51 | 0.28 | 0.73 | 34 | 59 |
| ~~metareview (0.7.0)~~ | medium | 6 | 0.77 | 0.26 | 0.94 | 144 | 123 |
| ~~metareview (0.7.0)~~ | xhigh | 6 | 0.76 | 0.23 | 0.94 | 117 | 130 |

**Reading the GLM sidebar:** vanilla-glm is a credible budget reviewer (recall 0.35–0.43, adj. prec up to 0.66, very few hallucinations: 11–16) — the cheapest "good precision" option across all models. compound on GLM was strong in the 0.7.0 batch (recall 0.80–0.84, incr. 0.96–0.97) but at high noise (103–121 hal). **metareview 0.8.2 × GLM is a gap** — it has not been run; the struck-through 0.7.0 row is shown only for reference and is **excluded** from all comparisons per instruction. If GLM × metareview 0.8.2 matters, it needs a fresh run.

> ⚠ **Batch effect reminder:** GLM compound's 0.84 here vs batch_083 compound's 0.45 is mostly the batch (0824-1019 was a higher-recall run), not a GLM-vs-opus property. Do not rank GLM compound against batch_083 opus compound without this caveat.

---

## 6. Why the factories cost what they cost (structural findings)

These come from the 0.7.0 deep-dive in `results/ANALYSIS.md` and `docs/METAREVIEW_IMPROVEMENTS.md`; the cost structure carries to 0.8.2.

### 6.1 The orchestrator, not the subagents, dominates cost (H3 — confirmed)

metareview-realistic cost is **~99.96% orchestrator (opus), ~0.04% lenses (Haiku)** (`results/per_model_cost.json`). The 8-lens fanout is essentially free; the opus orchestrator dominates. In batch_083's spend table, haiku is $0.58 total across 86 cells. **"metareview is expensive because of 8 lenses" is false — the lenses are cheap; the opus planning turn is the cost.** Implication: pinning lenses to a stronger model (Sonnet) would be a cheap knob that might raise lens recall (H3 tuning hypothesis, untested).

### 6.2 Per-lens attribution — which lenses catch bugs vs hallucinate

From `results/per_lens_attribution.json` (0.7.0 metareview-realistic, n=66 runs), the LLM lenses vs the deterministic gates:

| lens | n_findings | matched (TP) | real_rate | halluc_rate |
|---|---:|---:|---:|---:|
| feasibility | 263 | 85 | **0.677** | 0.323 |
| **security** | 229 | 27 | **0.712** | 0.288 |
| architecture | 706 | 76 | 0.577 | 0.423 |
| completeness | 549 | 78 | 0.574 | 0.426 |
| intent-preservation | 77 | 15 | 0.545 | 0.455 |
| scope / scope-and-alignment | 312 | 23 | 0.37–0.45 | 0.55–0.63 (noisy) |
| metareview-session (orchestrator prose) | 83 | 0 | 0.084 | **0.916** (mostly noise) |
| **all deterministic gates combined** | ~85 | **0** | **0.0** | **1.0** |

**Two findings:** (1) the **Security lens added in 0.7.0 is high-precision** (real_rate 0.71) — the no-security-lens gap (H1) is closed; security is now one of metareview's better lenses. (2) **Deterministic gates contributed 0 recall on this PR subset** (all gate findings were hallucinated against the gold set, H2). The gates are free and may catch other classes (eval/TODO/missing-test), but on these 6 PRs they add coverage noise, not bugs.

### 6.3 Adjudication split — whose "extra findings" are real vs hallucinated

From `results/adjudication_split.json` (0.7.0), the share of *unmatched* findings adjudicated **real** (the rest are hallucinations):

| framework | real_ratio of unmatched |
|---|---:|
| **vanilla-engineered** | **0.67** |
| compound | 0.54 |
| metareview-realistic | 0.46 |
| superpowers-realistic | 0.40 |

**vanilla's unmatched findings are the most likely to be real bugs** (67% real); superpowers' are mostly noise (40% real). This is why vanilla's adjudicated precision (0.76) is so much higher than the factories' — when vanilla reports something the gold set didn't have, it's usually a real bug; when the factories do, it's a coin-flip. **For a triage-constrained team, vanilla's extra findings are worth reading; the factories' extra findings need adjudication first.**

### 6.4 metareview vs compound — the conclusion flips by model (H5 / H5b)

- **On opus-5 (0.7.0 medium, apples-to-apples):** metareview and compound are **cost-equivalent** (~$5.75/cell); metareview finds *more* (51 vs 40 findings, recall 0.80 vs 0.54). metareview's single-pass design beats compound's two-pass (dispatch + synthesis) at xhigh. (H5)
- **On Codex gpt-5.6-sol:** the picture **inverts** — compound dominates metareview on *both* cost and quality (recall 0.70–0.75 vs 0.55–0.57; incr. 0.92–0.94 vs 0.82; ~2× findings per token). metareview's xhigh is wasted spend on Codex (2× tokens, same recall). (H5b)

**Practitioner takeaway:** on Claude opus, metareview is the more efficient factory; on Codex, compound is the more efficient factory — but vanilla is competitive with both on Codex and far cheaper.

---

## 7. Benefits, drawbacks, and empirical verdict per framework

### vanilla-engineered
- **Benefits:** Highest adjudicated precision (0.76) and lowest hallucination rate (1.5/cell) of any framework — when it reports a bug, it's usually real. Cheapest ($0.30/cell). **Model-agnostic** — the only framework that works well on every model tested (Claude, Codex, GLM). Strong on Codex in particular (adj. prec 0.70–0.94).
- **Drawbacks:** Lower total coverage (incr. recall 0.66; 3.9 hidden-gold/cell) — it misses ~⅓ of known bugs and surfaces fewer new bugs than the factories. No subagent fanout means no adversarial multi-perspective coverage.
- **Empirical verdict:** **The default.** Use it for routine review and on any non-Claude model. Reach for a factory only when the diff is high-stakes and you're on Claude.

### metareview 0.8.2
- **Benefits:** Highest recall on opus (0.82–0.88, incr. 0.97) — the best coverage of known bugs on top-tier Claude. 8 adversarial lenses incl. a high-precision Security lens. Single-pass synthesis is more xhigh-efficient than compound. Deterministic gates are a free pre-check (even if they added 0 recall here, they catch eval/TODO/test-gap classes). Cheaper than compound on opus (~30%).
- **Drawbacks:** Low precision (0.30 adj.) and high hallucination rate (10.3/cell) — you will triage ~7× the noise of vanilla. On Codex the pure-recall gain shrinks (recall 0.29–0.50 on gpt, vs vanilla 0.33–0.62) but it still finds more *total* bugs there (incr_recall 7/8 on gpt); the precision drop is just steeper because vanilla+gpt starts precise. xhigh is wasted spend on every model. The orchestrator (opus) is 99.96% of cost, so it's expensive on opus ($13–17/cell on opus). Deterministic gates contributed 0 recall on this subset.
- **Empirical verdict:** **The high-coverage choice on Claude opus.** Best when the diff is security/architecture-sensitive and you can absorb triage. Use low/high (not xhigh) — xhigh doubles cost for ~no recall gain on opus.

### Compound Engineering
- **Benefits:** The **most findings per cell** (12.0 hidden-gold/cell — highest absolute bug discovery). Risk-driven persona roster adapts to the diff. Highest incr. recall tier (0.79, tied with metareview). On Codex gpt-5.6-terra xhigh, it's the one factory that beats vanilla on coverage (recall 0.55, incr. 0.84). Severity-banded (P0–P3) output is triage-friendly in shape.
- **Drawbacks:** **Most expensive** ($1.89/cell, ~6× vanilla). Lowest raw precision (0.14). Two-pass (dispatch + synthesis) doubles xhigh cost on opus. On Codex the recall gain is smaller than on opus and the precision hit is steeper, but it still finds more total bugs (incr_recall 6/8 on gpt; the one factory cell that beats vanilla on raw recall on gpt is compound/terra/xhigh). The persona subagents route partly to Sonnet (not Haiku), inflating cost vs metareview's all-Haiku lenses.
- **Empirical verdict:** **Use when you want maximum bug discovery and cost is secondary** — especially on Codex where it's the only factory that consistently works. Expect to triage a lot of noise.

### Superpowers
- **Benefits:** Cheap ($0.43/cell). On Claude opus xhigh it reaches incr. recall 0.93 — competitive with the other factories at lower cost. The coordinator-dispatches-reviewer pattern keeps the diff out of the coordinator's context.
- **Drawbacks:** **Lowest recall (0.24) and precision (0.21)** overall. Weakest harness on Codex (recall 0.02–0.17) — it degrades Claude→Codex more than metareview/compound (drop 0.37 vs 0.32/0.36), but still produces real findings (38–73/cell), so it is not "broken" (the earlier subagent-dispatch suspicion isn't supported by the 384-cell data). Highest hidden-gold miss rate of the factories.
- **Empirical verdict:** **Claude-only, and currently the weakest factory on the data.** Promising on opus xhigh but outperformed by metareview and compound at most cells. Fix the Codex dispatch bug before re-evaluating.

---

## 8. Recommendations for the SDLC (design / spec / decompose / code / review / test)

Grounded in the data above; each ties to an empirical signal.

### 8.1 The ideal SDLC loop — use each model/harness where the data says it actually wins

The interaction analyses (§4.7) show that no single framework/model is optimal across the loop. The harnesses win at *discovery* (hidden gold, 16/16) but lose on *efficiency* and *precision*; vanilla and the gpt models win at *precision* and *cost* but find fewer bugs. The practitioner move is to **use them in sequence** — each where it is strongest — rather than picking one for the whole workflow. This is the loop the data recommends:

```
  (a) write code  →  (b) discover candidate bugs  →  (c) adjudicate (kill hallucinations)  →  (d) fix & re-run (b–d) until done
```

**(a) Initial code writing** — *use the strongest reasoner; effort = high, not xhigh.*

The review eval doesn't measure writing directly, but the model-quality ordering transfers: opus-5 has the highest recall/incr-recall (it understands the most about the code; §4.2) and gpt-5.6-terra has the highest precision (it produces the fewest hallucinations; §4.2). For complex logic, opus-5's reasoning is the asset; for plumbing / boilerplate where you want fewer bugs to begin with, gpt-5.6-terra's precision is the asset. **Use `high` effort, not xhigh** — §4 effort table shows high and xhigh are nearly identical on recall (0.49) and incr-recall (0.80), but xhigh costs ~25% more tokens. high is the sweet spot on the effort axis.

**(b) Identify potential bugs (discovery)** — *run a harness to find maximum bugs including hidden gold (works on every model, not just opus).*

This is where the harnesses' universal win (hidden gold 16/16 for mrv, 15/16 for compound — **including 8/8 on gpt models**) earns its keep. Run the harness to produce a **candidate bug list** (hidden gold + hallucinations, mixed):

| cell | recall | hidden gold | hal | cost | when to use |
|---|---|---|---|---|---|
| **mrv / opus-5 / low** | **0.86** | 174 | 207 | $13/cell | **default discovery pass on opus** — highest recall in the matrix, captures ~all the value (§4.3) |
| compound / opus-5 / high | 0.79 | **268** | 214 | $34/cell | when you want *maximum* discovery and can triage the noise |
| **mrv / gpt-5.6-sol / medium** | 0.60 | 36 | 25 | $0.59 | **discovery pass on Codex** — mrv beats vanilla on incr_recall 7/8 on gpt; finds more total bugs |
| **compound / gpt-5.6-terra / xhigh** | 0.55 | **75** | 36 | $1.59 | **max-discovery on terra** — only factory cell that beats vanilla on raw recall on gpt |

Expect ~4–7× more candidates than vanilla, with **~40–54% being hallucinations** (§6.3). The candidate list is the input to (c). **Do NOT skip the harness on gpt models** — the harness finds more total bugs (incr_recall) on gpt in 7/8 (mrv) / 6/8 (compound) cells, exactly as on opus. The harness-vs-vanilla tradeoff is the *same direction* on every model: more total bugs + more hidden gold, at the cost of lower precision and more tokens. On gpt the precision hit is more *visible* (vanilla+gpt starts at adj_p 0.74–0.96, the harness drops it to 0.32–0.50) but the coverage gain is still there. The choice on gpt is the same as on opus: pay the precision/cost tax for more bugs, or don't — step (c) exists precisely to pay that tax cheaply.

**(c) Evaluate and eliminate hallucinations (adjudication)** — *filter the candidate list with a high-precision pass.*

The candidate list from (b) is mixed. The data says *how* to separate the real bugs from the noise: vanilla's unmatched findings are **67% real**, the factories' are only 40–54% real (§6.3). So filter with a *precision* pass, not another coverage pass:

- **Use gpt-5.6-terra or vanilla as a second-pass judge** on each candidate finding. gpt-5.6-terra is the precision champion (adj_p 0.44, fewest hallucinations; §4.2); vanilla's adjudicated precision is 0.71 (§4.1). Either makes a clean adjudicator.
- **Or use the cross-family judge** approach this eval uses (`harnesseval/adjudicate.py`): claude-discovered candidates → judged by gpt; gpt-discovered → judged by claude. This is the anti-self-preference move and it's what produced every number in this doc.
- **Keep findings that survive** (real-but-ungold + matched goldens = the confirmed bug list). Drop the hallucinations. This is the step where the precision models earn their keep — they're the filter that makes the harnesses' flood usable.

**(d) Fan out and iterate** — *feed confirmed bugs back as fixes; re-run (b)→(c) until recall stops improving and tests pass.*

- Take the confirmed bug list from (c) as issues. Feed them to the code-writing model (a): *"fix these N confirmed bugs."* Re-run (b) on the fixed code.
- **Iterate until three stop conditions hold:** (1) recall stops improving — §4.3 shows low/medium captures most of the value, so 1–2 iterations of discovery usually suffice; (2) tests pass — add a test for each confirmed bug as you fix it (metareview's Testing-quality lens + deterministic gates catch missing-test-changes); (3) the candidate list collapses to mostly hallucinations — the hidden gold is exhausted when re-running (b) finds no new real bugs.
- **The loop converges** because each pass fixes real bugs (shrinking the bug space) and the adjudication step prevents hallucinations from polluting the fix list. Don't iterate the harness blindly — iterate the *confirmed* bug list.

**The key insight the loop encodes: the harnesses and the precision models are *complements* in a loop, not alternatives.** Harness+opus-5 discovers; precision-model (gpt-5.6-terra) or vanilla adjudicates. A single framework/model choice for the whole workflow is suboptimal — the loop is where the value is. The harnesses' hidden-gold win (16/16) is only useful once the hallucination tax is paid (step c); and vanilla's precision win is only useful once the harness has surfaced the candidates (step b).

### 8.2 Tactical recommendations (supporting the loop)

1. **Match the framework to the model and the stakes — but don't assume the harness only helps on opus.** The harnesses find more *total* bugs (incr_recall) on every model tested, including Codex gpt (mrv 7/8, compound 6/8). What changes by model is the tradeoff shape: on Codex, vanilla starts high-precision (adj_p 0.74–0.96) so the harness's precision drop and cost are more visible, while the pure-benchmark-recall gain is smaller; on opus the recall gain is large. **All three harnesses degrade on Codex** (Claude→Codex recall drop 0.32–0.37); superpowers is the weakest on Codex (recall 0.02–0.17) but still produces real findings, so it is not "broken" — the earlier subagent-dispatch suspicion isn't supported by the data. Prefer metareview or compound for the discovery step on Codex (they're stronger there), but don't write off superpowers entirely.

2. **Use vanilla as the baseline review gate; escalate high-stakes diffs to a factory.** vanilla's precision (0.76) means its findings are trustworthy and cheap. Run metareview/compound on diffs touching auth, payments, data migration, or security boundaries, where the factories' 2.5–3× hidden-gold discovery justifies the cost + triage (§4.1).

3. **Prefer low/medium effort for the factories; reserve xhigh for opus + critical diffs.** Recall rises only modestly low→xhigh (0.40→0.42) but cost rises steeply (tok 50M→102M). compound opus xhigh = $37/cell is rarely worth it; metareview opus low (recall 0.88, incr. 0.97) captures nearly all the value at $13 (§4.3).

4. **Triage the factories' output by adjudicated precision, not raw finding count.** The factories' raw precision is 0.13–0.37; ~40–54% of their *unmatched* findings are hallucinations (§6.3). Sort by severity (P0/P1 first; metareview lens/source), and treat high-confidence, multi-lens-agreed findings as the signal. vanilla's extra findings (67% real) are always worth reading.

5. **Avoid overengineering via conditional coverage.** Compound's risk-driven roster (skip personas whose surface is absent) is an empirically supported efficiency idea — it runs fewer personas on simple diffs. metareview's fixed 8 lenses always run, even when (e.g.) there's no security surface; making lenses conditional on diff signals could trim fanout (H5 lesson). Don't fan out every lens/persona on every diff.

6. **Catch security and architecture early.** metareview's Security lens is high-precision (real_rate 0.71, §6.2) and the Architecture lens is its highest-volume TP source (76 matched). Run a security+architecture pass *before* code review — it's where the lenses add the most real signal. For vanilla, the single-prompt rubric already names `security` and `concurrency`; keep them in the rubric.

7. **Don't trust the deterministic "free floor" to catch bugs (yet).** metareview's Go gates contributed 0 recall on this subset (H2). Use them as a checklist (eval/TODO/missing-test), not as a bug finder. Revisit after Phase C.

8. **Watch for the hallucination tax.** superpowers-realistic's unmatched findings are 60% hallucination; metareview's are 54%. If your team auto-files review comments as issues, the factories will flood your tracker. Require a human adjudication step (or a second-model adjudicator, as this eval does) before filing factory findings.

9. **Avoid architectural drift by reviewing the diff + intent, not just the diff.** metareview's Intent-preservation and Scope lenses exist for this; compound's persona roster includes architecture. vanilla's single prompt is diff-only. For changes that touch module boundaries, prefer a factory's intent-aware lenses.

10. **Measure cost where it actually falls: the orchestrator.** 99.96% of metareview's cost is the opus planning turn, not the subagents (H3). To cut factory cost, downgrade the orchestrator (Sonnet) or cache its context — not the lenses. Token counts are ground truth; $ is an estimate for GPT.

---

## 9. Caveats and what is pending

**Caveats (apply to every number above):**
- **N is tiny.** 6 PRs per cell; bootstrap 95% CIs are wide or undefined (`results/bootstrap_ci.json`). No "X beats Y" claim survives the bootstrap at this N — the interaction analyses (§4.7) report raw win-rates, not significance. The patterns (hidden-gold 16/16, opus-5 concentration) are consistent enough to be directional, but Phase C is the bar before any final ranking.
- **The eval is now complete** (384/384 pass cells, 2026-08-26T05:30Z). It took multiple Claude quota-window reruns to finish (Claude Code hit both weekly and session limits mid-run); a looping auto-rerun watcher drained the remaining ~126 failed cells across quota windows. An output-cap bug in all three realistic adapters (the orchestrator's final consolidation message exceeded the model's per-message output limit on hard PRs) was fixed mid-run by writing findings to per-lens/persona files and concatenating via `cat` — see `adapters/{metareview,compound,superpowers}_realistic.py`. No output-cap failures remain.
- **Batch effects.** batch_083 is ~0.14 lower recall than 0824-1019 on matched cells — a batch/judge effect, not a framework regression. Cross-batch pooling is avoided; GLM is a separate sidebar.
- **Cost for GPT is an unverified estimate.** Reported $ = real Anthropic billing; GPT reports $0 via OAuth, so implied $ adds GPT at pinned 2026-08-22 rates (gpt-5.6-sol $1.25/$10; gpt-5.6-terra $2.5/$20 per 1M). Real GPT cost may differ.
- **All three harnesses degrade on Codex** (mean Claude→Codex recall drop 0.32–0.37; superpowers 0.37, compound 0.36, metareview 0.32 — not a superpowers-specific anomaly). Superpowers is the weakest on Codex (recall 0.02–0.17) but still produces real findings (38–73/cell), so the earlier "broken subagent dispatch" suspicion is **not supported** by the 384-cell data — findings are produced with real file:line refs. The defensible read: all harnesses are weaker on Codex; superpowers is weakest, not broken.
- **Model provenance:** API 'opus' = claude-opus-4-5 (pinned); CLI realistic 'opus' resolved to claude-opus-5. API and CLI are never compared head-to-head (SPEC §7 gotcha #9).
- **The SDLC loop (§8.1) is a recommendation derived from the review data, not a measured workflow.** The eval measures single-pass review quality, not the iterative discover→adjudicate→fix→repeat cycle. The loop is the *extrapolation* the data points to; validating it (does iterating the loop actually converge faster / find more bugs than single-pass?) is a Phase-C experiment.

**Pending (will update this doc as it lands):**
- [x] **The 384-cell matrix is complete.** batch_083, 384/384 pass cells, 2026-08-26T05:30Z.
- [ ] **metareview 0.8.2 × GLM** — not yet run; would complete the GLM sidebar's factory comparison.
- [ ] **Phase C** (50 PRs + confidence intervals) — the bar before any final ranking.
- [ ] **OpenEnv Arena** deterministic-grader cross-check (security classes + explicit false-positive control) — not yet in the primary matrix.
- [ ] **SDLC-loop validation** — run the discover→adjudicate→fix→repeat loop end-to-end on a few PRs and measure convergence (does confirmed-bug recall rise per iteration? does the candidate list collapse to hallucinations?). This tests the §8.1 recommendation directly.

---

## 10. Reproducibility

```bash
# Refresh the rolling analysis (writes results/batch_083_ANALYSIS.md + appends history):
cd /Users/dsifry/Developer/harnesseval && uv run python bin/analyze_batch_083.py

# Re-run the interaction analyses (§4.6–4.7: H1/H2a/H2b tests, cost-efficiency, SDLC inputs):
uv run python bin/analyze_083_interactions.py   # -> stdout: 6 analyses on the 384-cell matrix

# Regenerate the full Phase-B analysis (leaderboards, per-lens, adjudication, failure-mode):
uv run python -m harnesseval.analysis      # -> results/ANALYSIS.md + results/*.json
uv run python -m harnesseval.report          # -> results/leaderboard_*.json + pareto_*.png
```

**Pinned versions:**
- Martian Code Review Bench (dataset + grader): `third_party/code-review-benchmark` @ `2b092b670f`
- Superpowers plugin: `third_party/superpowers` @ `b36e0829…` (v6.3.0)
- Compound Engineering plugin: `third_party/compound-engineering-plugin` @ `a32c9474…`
- metareview Go binary: `0.8.0` gates; metareview 0.8.2 slim-orchestration adapter (harnesseval commit `8567d40`)
- Inspect AI: see `pyproject.toml` / `uv.lock`

**Key artifacts:**
- `runs/registry.jsonl` — append-only run registry (the source of truth, 979 runs)
- `runs/<id>/summary.json` — per-run metrics + `per_model_usage` + per-finding adjudication + per-golden matches
- `results/batch_083_ANALYSIS.md` — the rolling analysis this doc cites (refresh with the command above)
- `results/ANALYSIS.md` — the 0.7.0 deep-dive (per-lens, adjudication split, failure-mode)
- `docs/METAREVIEW_IMPROVEMENTS.md` — hypotheses H1–H5b with evidence + confirming experiments
- `docs/SPEC.md`, `docs/PLAN.md`, `docs/HANDOFF.md`, `docs/PARTIAL_RUN_REPORT.md` — design + operational log

**Authors of follow-ups:** re-run `bin/analyze_batch_083.py` after each claude-code fill, then update §4 tables and the "pending" checklist in §9. Do not pool batch_083 with earlier batches without re-checking the cross-batch delta.
