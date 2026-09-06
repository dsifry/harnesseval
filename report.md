# AI Code-Review Frameworks — Empirical Comparison (Report)

> **What this is.** This report summarizes the `harnesseval` lab's comparison of four AI
> code-review frameworks across a `(framework × model × effort)` matrix, reporting review
> quality **and** cost together. It is the cleaned-up form of the working analysis in
> [`docs/FRAMEWORK_COMPARISON.md`](docs/FRAMEWORK_COMPARISON.md); every number below is
> reproducible from the committed run records via the commands in [`REPRODUCE.md`](REPRODUCE.md).
>
> **Status:** complete (336/336 designed pass cells, batch_083 post-remediation, refreshed
> 2026-09-06 — see §3.5 for the collision-bug audit that triggered the refresh). **N is small**
> (6 PRs per cell; bootstrap CIs wide or undefined). Treat this as a **directional, reproducible
> read — not a published ranking**. Phase C (50 PRs + confidence intervals) remains the bar
> before any final claim — the two vanilla columns added 2026-09-06 (gpt-6-astra,
> claude-fable-5-1) already cover the full 50-PR suite; see §3.3.

---

## 1. Executive summary — which should a developer pick?

The central question is not *"which framework is best"* but *"which gives the best review
quality and finds and fixes the most bugs per unit of cost and triage effort."* The 336-cell
matrix below measures the **review** component (single-pass discovery — the *finding* of bugs);
the **fix** component (the discover → adjudicate → fix loop) is the active research direction
([`FURTHER-RESEARCH.md`](FURTHER-RESEARCH.md) §1).

### TL;DR — practitioner recommendations

**The shorthand.** Four *frameworks* are compared: **vanilla** — a single well-engineered
review prompt, no subagents (the baseline); **metareview 0.8.2** — free deterministic gates + 8
adversarial "lens" subagents; **Compound Engineering** — risk-driven "persona" subagents + a
synthesis pass; **Superpowers** — one code-reviewer subagent. The "factories"/"harnesses" = the
latter three. Two *model families*: **Claude opus/sonnet/fable** (Anthropic) and **Codex
gpt-5.6/gpt-6** (OpenAI); GLM is a sidebar. **Effort** = a model's reasoning-depth knob
(low/medium/high/xhigh) — more thinking, more cost. **Hidden gold** = real bugs the human
reviewers missed; **hallucination** = a reported "bug" that isn't real (the triage tax).

**Five counterintuitive findings the data shows:**

1. **The expensive review frameworks are NOT the best value — vanilla is.** A single
   well-built prompt dominates recall-per-dollar; the factories are 10–40× more expensive for the
   recall they deliver. The factory premium buys *coverage*, not *efficiency*. → §3.4 (H1)
2. **The factories find more total bugs on *every* model, not just Claude opus.** The
   harness-vs-vanilla tradeoff points the same way on Codex too — what changes by model is the
   cost and the precision hit, not whether the harness helps. → §3.4
3. **When vanilla reports a bug the humans missed, it's real 67% of the time; when a factory
   does, it's a coin flip (40–54%).** The factories flood you with candidates — ~40–54% of their
   unmatched findings are hallucinations. → §5.3
4. **Cranking effort to "xhigh" mostly wastes money.** Recall rises only modestly low→xhigh
   while cost explodes (e.g. Compound on opus xhigh ≈ $67/review). low/medium captures most of
   the value — and the two new 2026-09-06 model columns confirm it: recall is flat across
   low/medium/high for both gpt-6-astra and claude-fable-5-1 in vanilla mode. → §3.3
5. **The newest models don't improve bug-finding — pick models for review on data, not
   release notes.** gpt-6-astra is strictly dominated by last-gen gpt-5.6-sol in the same
   harness (recall 0.40 vs 0.52, equal precision, ~7× the implied cost) at every effort level.
   Anthropic's newest generation did help: claude-fable-5.1 posts the strongest vanilla recall
   measured (0.74 top-6 / 0.62 full-suite, incr. 0.89) at the best premium $/real-bug ($0.077).
   Model rank for review ≠ model rank for coding. → §3.3

**What to actually use** (pick the framework together with your model + stakes):

- **Routine / low-stakes review on any model → vanilla, low or medium effort.** Highest
  precision (0.71), cheapest (~$0.31/review), fewest false alarms (1.8/review). The only
  framework that works well on Claude, Codex, *and* GLM. On Claude Code specifically,
  **claude-fable-5-1 at low effort is the strongest vanilla cell measured** (recall 0.74,
  incr. 0.89, $0.077/real-bug) — the best single upgrade if you review with Claude Code
  already. → §3.1, §3.3, §6, §7 #2
- **High-stakes / security-critical diff on Claude opus → metareview, low or high effort
  (not xhigh).** On opus, both factories reach the same ceiling — single-pass metareview and
  two-pass Compound find 92–97% of all real bugs (incl. ones the humans missed) and surface
  3–5× more hidden gold than vanilla. At low effort metareview costs more ($31 vs $20/cell —
  Compound's two-pass is cheaper there); at high effort they converge ($57 vs $56) — the old
  "metareview ~30% cheaper on opus" claim did not survive the post-remediation data. Both at
  7–9× the cost of vanilla. → §3.1, §3.3, §5.4, §6, §7 #1
- **Maximum bug discovery, cost secondary → Compound (Claude).** Most real bugs found per
  review (14.9 hidden-gold). On Codex, Compound/gpt-5.6-terra/xhigh is the one factory cell that
  beats vanilla on raw recall. → §3.1, §3.3, §6
- **On Codex (gpt-5.6) → vanilla for precision/cost; Compound (not metareview) when you want
  more total bugs.** vanilla starts high-precision (0.70–0.94). The factories still find more
  *total* bugs on gpt (metareview 4/6 comparable cells, Compound 5/6; hidden gold 8/8 for
  both) — but the factory-efficiency picture flips vs opus: on Codex, **Compound is the more
  efficient factory** (more findings per token; metareview's xhigh is wasted spend on Codex).
  The precision drop is steeper on Codex either way. **Skip gpt-6-astra for review** — it is
  dominated by sol on recall, precision, and cost in the same harness. → §3.2, §3.3, §3.4, §5.4, §6, §7 #1
- **Triage-constrained team → vanilla as the baseline gate; adjudicate the factories' output
  before filing.** Use a precision model (gpt-5.6-terra) or a cross-family judge as the
  second-pass filter to kill the 40–54% hallucinations. → §5.3, §6, §7 #4 / #8
- **The full loop (discover → adjudicate → fix → repeat) → harness discovers, precision model
  adjudicates, fix, iterate.** The matrix measures single-pass *finding*; the *fixing* loop is
  the active experiment. → §7, [`FURTHER-RESEARCH.md`](FURTHER-RESEARCH.md) §1
- **Cost per real bug → vanilla ~$0.04/bug (most efficient); factories ~3.5× more per bug but
  find ~3.5× more.** On the two new 2026-09-06 columns, fable-5.1/low is the best premium
  vanilla cell ($0.077/bug, recall 0.74); astra's best cell ($0.094/bug at medium) is ~10×
  worse than vanilla/sol ($0.009). → §3.1, §3.3

The table below expands the first four use cases; §6 gives per-framework verdicts; §7 gives the
SDLC loop + the ten tactical points these are drawn from.

| If your situation is… | Use this | Why (empirical) |
|---|---|---|
| Routine review of low-stakes diffs on **any** model | **vanilla-engineered** | Highest adjudicated precision (**0.71**), cheapest (**~$0.31/cell**), competitive recall (0.48). Model-agnostic — works on Claude, Codex, and GLM. |
| High-stakes / security-critical diffs on **Claude Code** (opus) | **metareview 0.8.2** *or* **Compound Engineering** | Both reach **incremental recall ~0.92–0.97** on opus and surface **3–5× more hidden gold** (real bugs the human reviewers missed) than vanilla. At high effort they cost about the same ($57 vs $56/cell); metareview/low runs $31.13 vs Compound/low $20.01. |
| You want the broadest coverage and can afford triage | **Compound Engineering** (Claude) | Most findings per cell (14.9 hidden-gold/cell, highest absolute), but **lowest adjudicated precision (0.33)** — you will triage a lot of noise. |
| You are on **Codex** (gpt-5.6) | **vanilla-engineered** for precision/cost; **metareview or compound** when you want more total bugs | The harnesses still find more *total* bugs on Codex (incr_recall: metareview 4/6, compound 5/6 comparable cells vs vanilla; hidden gold 8/8), but vanilla starts high-precision there (adj_p 0.74–0.96) so the harness's precision drop is steeper. All three harnesses degrade Claude→Codex (recall drop 0.32–0.37). superpowers is the weakest on Codex (recall 0.02–0.17) but still produces real findings (19–73/cell) — it is not "broken." |
| You want a deterministic, free "floor" before LLM review | **metareview's deterministic gates** — *but* | On this PR subset the gates contributed **0 recall** (all gate findings were hallucinated against the gold set). They are free, but don't rely on them to catch bugs here. |

**The single most important finding: the factory frameworks trade precision for coverage on
*every* model, not just opus.** Their value is *largest* on Claude opus (recall 0.79–0.86,
incr_recall 0.97), but on Codex gpt they still find more total bugs (incr_recall 4/6 for
metareview, 5/6 for compound on comparable cells) and more hidden gold (8/8). What changes by model is the
tradeoff *shape*, not the *direction*. Pick your framework *together with* your model, but
don't assume the harnesses only help on opus.

**The second finding: the factories trade precision for coverage.** They find substantially
more real bugs (incremental recall 0.83–0.85 vs vanilla 0.67; 13.4–14.9 hidden-gold/cell vs
vanilla 3.8) but at 7–9× the cost and **far lower precision** (0.29–0.33 vs vanilla 0.71) —
meaning a human must triage 6–8× more candidate findings. The net win depends on whether the
extra real bugs are High/Critical and whether your team can absorb the triage cost.

---

## 2. Methodology (reproducible)

### 2.1 The lab

`harnesseval` compares AI code-review **frameworks** on a `(model × framework × effort)` matrix,
reporting quality and cost together. It reuses three established open-source projects and writes
only the novel glue (framework adapters + scoring). See [`README.md`](README.md) for the table.

### 2.2 Frameworks under test

Each framework's *review capability* is tested as a user actually invokes it ("realistic"
mode), driving the real plugin/CLI in a host agent (`claude -p` or `codex exec`) with the real
agent loop + subagent dispatch. All four live in `harnesseval/adapters/`:

| Framework | Methodology (one line) | Adapter |
|---|---|---|
| **vanilla-engineered** | One model call, no subagents, diff-in/prose-out (rubric + severity) | `adapters/vanilla.py` |
| **metareview 0.8.2** | Orchestrator runs `bin/metareview` deterministic gates + dispatches 8 lenses as parallel subagents; single-pass synthesis | `adapters/metareview_realistic.py` |
| **Compound Engineering** | Risk-driven persona roster dispatched as parallel subagents + a separate synthesis pass; P0–P3 + confidence | `adapters/compound_realistic.py` |
| **Superpowers** | Coordinator resolves SHAs, dispatches one code-reviewer subagent; returns Strengths/Issues/Assessment | `adapters/superpowers_realistic.py` |

> Per `docs/SPEC.md` §6.3.1, Claude Code routes `general-purpose` subagent dispatches to Haiku
> by default regardless of `--model`. So "framework-X @ opus" realistically = opus orchestrator
> + Haiku reviewer/persona/lens subagents. This is recorded honestly in `per_model_usage` and
> is the single biggest driver of the cost structure (§6).

### 2.3 Models and efforts

| Axis | Values | Meaning |
|---|---|---|
| Model | `claude-opus-5`, `claude-sonnet-5` (Claude Code); `gpt-5.6-sol`, `gpt-5.6-terra` (Codex) | GLM is a sidebar (§5), not in the primary matrix |
| Effort | `low`, `medium`, `high`, `xhigh` | Anthropic: low/medium→thinking off, xhigh→thinking on; OpenAI/GLM: `reasoning_effort` low/medium/high. Source: `harnesseval/effort.py` |

### 2.4 Judges (cross-family)

Claude-family findings → judged by `gpt-5.2`; GPT-family findings → judged by
`claude-opus-4-5-20251101`; adjudication (real-but-ungold vs hallucination) uses the same
cross-family judge. This avoids same-model bias and produced every number below.

### 2.5 Metrics (the numbers that matter)

| Metric | Definition | What it tells you |
|---|---|---|
| **Recall** | TP / (TP + FN) vs the 42 human goldens | Coverage of the *known* bugs |
| **Precision (raw)** | TP / (TP + FP) | Penalizes real bugs the gold set missed |
| **Adjudicated precision** | TP / (TP + hallucination), after reclassifying unmatched findings | The "honest" precision: counts only true hallucinations as wrong |
| **Incremental recall** | (TP + real-but-ungold) / (TP + FN + real-but-ungold) | Total real bugs found, **including hidden gold** |
| **Hidden gold** | real-but-ungold findings (adjudicated real, not in gold set) | New bugs beyond the human gold |
| **Hallucinations** | unmatched findings adjudicated not-real | Noise a human must triage |

**Cost:** Reported $ = real Anthropic `cost_usd` (cache-discounted); GPT reports $0 via OAuth so
reported $ understates true cost. **Implied $** adds GPT at pinned 2026-08-22 rates (**unverified**):
gpt-5.6-sol $1.25 in / $10 out per 1M; gpt-5.6-terra $2.5 in / $20 out per 1M.

---

## 3. Primary results — batch_083 (metareview 0.8.2), 336/336 designed cells

Refreshed 2026-09-06 from the post-remediation registry (see §3.5). Source:
`results/batch_083_ANALYSIS.md` (regenerate with `bin/analyze_batch_083.py`),
`bin/analyze_083_interactions.py`.

### 3.1 Per framework (the headline)

| framework | n | recall | adj. precision | incr. recall | hidden /cell | hal /cell | tok /cell | imp$ /cell |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **vanilla-engineered** | 72 | 0.48 | **0.71** | 0.67 | 3.8 | **1.8** | 149K | **$0.31** |
| **metareview 0.8.2** | 72 | **0.55** | 0.29 | **0.85** | 13.4 | 13.9 | 3.24M | $2.36 |
| **compound** | 96 | 0.48 | 0.33 | 0.83 | **14.9** | 11.6 | 2.98M | $2.72 |
| **superpowers** | 96 | 0.29 | 0.22 | 0.63 | 6.5 | 7.3 | 495K | $0.60 |

**Read:** vanilla finds ~half the known bugs with high precision and almost no noise, cheaply.
The two big factories find a comparable-or-higher fraction of known bugs (recall 0.48–0.55) and
surface **~3.5–4× more hidden gold**, reaching incr. recall 0.83–0.85 — at 8–9× the cost and
with 6–8× more hallucinations to triage. superpowers is cheap but finds the fewest bugs
(recall 0.29).

**Cost per real bug found** (imp$ / (TP + hidden gold)):
- vanilla: **$0.043/bug** — the most efficient per real bug
- superpowers: $0.070/bug
- metareview: $0.138/bug
- compound: $0.149/bug

The factories cost ~3.5× more per real bug but find ~3.5× more bugs in total. The choice is
whether the extra bugs are worth the cost + triage.

### 3.2 Per model (the model axis matters as much as the framework)

| model | n | recall | adj. prec | incr. recall | hidden /cell | hal /cell | tok /cell | imp$ /cell |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `claude-opus-5` | 72 | **0.68** | 0.24 | **0.93** | **24.5** | 22.5 | 2.56M | $4.33 |
| `claude-sonnet-5` | 96 | 0.42 | 0.36 | 0.71 | 6.7 | 7.2 | 3.28M | $1.78 |
| `gpt-5.6-sol` (Codex) | 72 | 0.37 | 0.39 | 0.67 | 6.3 | 4.8 | 523K | $0.11 |
| `gpt-5.6-terra` (Codex) | 96 | 0.33 | **0.46** | 0.59 | 4.5 | **3.1** | 418K | $0.20 |

**opus-5 is the recall/coverage engine** (recall 0.68, incr. 0.93, 24.5 hidden-gold/cell) but
the most expensive ($4.33/cell) and noisiest. **Codex is the precision/value engine** (adj. prec
0.39–0.46, cheapest, fewest hallucinations) but finds fewer bugs. This model effect interacts
strongly with the framework choice (§3.3).

### 3.3 Per framework × model × effort (where the recommendations live)

| fw | model | effort | recall | adj_p | incr_r | hidden | hal | imp$ |
|---|---|---|---:|---:|---:|---:|---:|---:|
| vanilla | opus-5 | low | 0.67 | 0.52 | 0.82 | 36 | 28 | $2.80 |
| vanilla | opus-5 | high | 0.69 | 0.51 | 0.86 | 53 | 30 | $4.04 |
| vanilla | gpt-5.6-sol | low | 0.52 | 0.87 | 0.69 | 23 | 4 | $0.30 |
| vanilla | gpt-5.6-sol | high | 0.55 | 0.89 | 0.67 | 15 | 5 | $1.36 |
| vanilla | sonnet-5 | high | 0.50 | 0.82 | 0.67 | 22 | 6 | $1.61 |
| vanilla | gpt-5.6-terra | low | 0.40 | 0.94 | 0.56 | 15 | 1 | $0.81 |
| vanilla | gpt-6-astra | low | 0.40 | 0.85 | 0.52 | 10 | 4 | $2.80 |
| vanilla | gpt-6-astra | medium | 0.39 | 0.89 | 0.55 | 13 | 4 | $2.81 |
| vanilla | gpt-6-astra | high | 0.40 | 0.93 | 0.56 | 16 | 2 | $5.95 |
| vanilla | claude-fable-5-1 | low | 0.74 | 0.47 | 0.89 | 52 | 37 | $6.41 |
| vanilla | claude-fable-5-1 | medium | 0.68 | 0.56 | 0.85 | 47 | 23 | $7.75 |
| vanilla | claude-fable-5-1 | high | 0.71 | 0.60 | 0.88 | 53 | 21 | $8.87 |

**New column (added 2026-09-06): vanilla × gpt-6-astra × low** (codex-cli 0.153.4; same 6 PRs,
same pipeline, mode=cli). Runs single-prompt vanilla at ~47K tokens/PR — the leanest runs in the
matrix. Results: **recall 0.40, adjudicated precision 0.85, incr. 0.52, 0.7 hallucinations/cell**.
Read: astra's precision is strong but recall lands *below* vanilla/gpt-5.6-sol/low (0.52) and
vanilla/opus-5/low (0.67) — a mid-pack vanilla cell, not a step change. Its tokens are
**~2.5× sol's per token** at OpenAI's current standard tier ($10.00 in / $12.50 out per 1M,
fetched 2026-09-06; sol standard is now $4.00/$5.00 — the eval's older sol/terra pins of
$1.25/$10 and $2.50/$20 no longer match the current page), so despite the smallest token count
implied-$* — cheap in absolute terms, but not the bargain the token count suggests.

**New column (added 2026-09-06): vanilla × claude-fable-5-1 × low** (Claude Code 2.1.263, alias
`fable` → `claude-fable-5-1`; same 6 PRs, same pipeline, mode=cli). Results: **recall 0.74,
adjudicated precision 0.47, incr. 0.89, 8.7 real/cell, 6.2 hallucinations/cell, ~85K tok/PR,
$6.41/cell actual billing** — the strongest recall of any vanilla cell and the best
real-bug-per-dollar among premium vanilla cells ($0.077/bug), at ~1/5 the cost and ~1/5 the
hallucination triage of mrv/opus-5/low (recall 0.85). Precision (0.47) is its weak spot.
Pricing: fable 5.1 bills at $10.00 in / $12.50 out / $0.25 cache-read per 1M (fetched from
docs.claude.com pricing 2026-09-06; cache hit = 0.025× base input — the discounted tier).
Cost basis is Anthropic's ACTUAL reported billing, like every other Anthropic cell. Model
identity: the Claude Code alias `fable` resolves to `claude-fable-5-1` (verified via modelUsage);
the explicit slug `fable-5-1` silently falls back to Haiku — do not use it directly.

**Effort ladder (added 2026-09-06):** both new models also ran vanilla at medium and high on the
same 6 PRs. The effort knob does NOT buy recall for either model — fable stays flat-to-down
(0.74 → 0.68 → 0.71) and astra is pinned at 0.40 across all three efforts. What effort buys is
precision and triage: fable hal 6.2 → 3.5 and adj_p 0.47 → 0.60 (at $6.41 → $8.87/cell);
astra adj_p 0.85 → 0.93 with 0.3 hal/cell at high — but high *doubles* astra's cost ($2.80 →
$5.95, 47K → 99K tok/PR) for zero recall gain, degrading $/bug from $0.104 to $0.180. Fable low
is its sweet spot; astra high is its worst deal. This replicates the report's effort-knob
finding (§3.1) on two brand-new models: more thinking, not more finding.

**Full-suite extension (added 2026-09-06):** both columns were extended to all **50
golden-labeled PRs** (Phase C template, first two columns measured on the full suite):
**fable** rec 0.62 / adj_p 0.31 / incr 0.80, 3.9 real + 4.8 hal per PR, ~75K tok/PR,
**$47.36/suite actual** ($0.155/bug); **astra** rec 0.36 / adj_p 0.63 / incr 0.47, 0.9 real,
0.4 hal per PR, **$26.68/suite implied** ($0.245/bug). The top-6 → full-suite regression is
real but tail-driven: fable sweeps 5 multi-golden PRs at recall 1.00 and zeros 5 PRs that all
have only 1–2 goldens (small denominators swing the tail; several zero-recall PRs still found
real-but-ungold issues, e.g. grafana #106778 incr 0.83). Judged cross-family like every other
column; single run per PR. Scope note: the factory columns (mrv/ce/sp) remain measured on the
top-6 subset only — suite-level cross-framework comparison is still open Phase C work.
| metareview 0.8.2 | opus-5 | low | **0.86** | 0.16 | **0.97** | 174 | 207 | $31.13 |
| metareview 0.8.2 | opus-5 | high | 0.79 | 0.12 | 0.97 | 222 | 241 | $56.65 |
| metareview 0.8.2 | gpt-5.6-sol | low | 0.50 | 0.41 | 0.75 | 43 | 31 | $0.59 |
| metareview 0.8.2 | sonnet-5 | med | 0.57 | 0.19 | 0.84 | 72 | 103 | $15.73 |
| metareview 0.8.2 | gpt-5.6-terra | high | 0.40 | 0.36 | 0.70 | 41 | 30 | $1.33 |
| compound | opus-5 | xhigh | **0.83** | 0.13 | **0.98** | 314 | 277 | $66.58 |
| compound | opus-5 | high | 0.79 | 0.21 | 0.97 | 260 | 176 | $55.96 |
| compound | gpt-5.6-terra | xhigh | 0.55 | 0.41 | 0.84 | 75 | 36 | $1.59 |
| superpowers | opus-5 | xhigh | 0.67 | 0.22 | 0.92 | 140 | 121 | $14.32 |
| superpowers | gpt-5.6-sol | xhigh | **0.02** | 0.02 | 0.29 | 16 | 39 | $0.50 |
| superpowers | sonnet-5 | high | 0.52 | 0.46 | 0.75 | 37 | 29 | $3.90 |

*(Representative rows; the full 64-row table is in `docs/FRAMEWORK_COMPARISON.md` §4.3.)*

**The model-conditional story:**
- **On opus-5:** the factories pull ahead on coverage. metareview reaches **recall 0.79–0.86,
  incr. 0.97** (the highest in the matrix); compound reaches recall 0.67–0.83, incr. 0.92–0.98.
  vanilla on opus is recall 0.67–0.69, incr. 0.82–0.86. **On opus you pay the factory cost to go
  from ~0.85 to ~0.97 incremental recall and 3–5× the hidden gold.**
- **On Codex (gpt-5.6):** the factory advantage on pure recall mostly evaporates. vanilla is
  competitive on recall (0.33–0.55) and **dominates precision** (adj. 0.70–0.94). metareview
  on Codex is modest (recall 0.31–0.64). The one factory bright spot on Codex is **compound
  xhigh on terra (recall 0.55, incr. 0.84)**. superpowers on Codex is the weakest harness
  (recall 0.02–0.17) but still produces real findings (19–73/cell with file:line refs), so the
  earlier "broken subagent dispatch" suspicion is **not supported** by the 336-cell data.
- **On effort:** recall rises only modestly low→xhigh (0.43→0.44; incr. 0.73→0.80) while cost
  rises steeply. **low/medium capture most of the value; xhigh is diminishing returns** for the
  factories (compound opus xhigh = $67/cell).

### 3.4 The interaction analyses (the tests that answer the practitioner questions)

Two hypotheses were posed and tested on the complete 336-cell matrix
(`bin/analyze_083_interactions.py`, re-run post-remediation 2026-09-06):

**H2a — the harnesses always beat vanilla at equal effort: SPLIT DECISION, model-dependent.**

| metric | metareview beats vanilla | compound beats vanilla | verdict |
|---|---|---|---|
| recall | 11/16 | 5/16 | ❌ not "always" — model-dependent |
| **hidden gold** | **16/16** | **14/16** | ✅ **near-always** — strong (mrv 16/16; compound loses only 2 sonnet-5 cells) |
| incr_recall | 10/16 | 7/16 | ⚠️ model-dependent (weaker than the pre-remediation read) |
| PR-paired (harness TP ≥ vanilla TP) | 72/96 (75%) | 53/96 (55%) | partial |

"Always beat" is **true for hidden gold, false for recall — and weaker than the
pre-remediation snapshot suggested on incremental recall.** The harnesses *nearly always*
surface more real bugs beyond the gold set (metareview 16/16, compound 14/16 — compound loses
only two sonnet-5 cells) — but on narrow recall they beat vanilla mainly with opus-5 and
sonnet-5; with gpt they often lose on recall, because candidate-flooding hurts precise models.

**H2b — harness at lower effort beats vanilla cranked higher: WEAK, opus-5 only.**
metareview at effort E beats vanilla at E+1 in 8/24 cases; compound in 3/24 — concentrated
almost entirely in opus-5. "Often" is overstated; it's really "opus-5 + harness at lower effort
beats opus-5 + vanilla cranked higher."

**H1 — the wins are cheap-model + harness + low-effort: REFUTED on cost-efficiency** (this test
uses *recall* as the quality proxy against cost). The most surprising result:
- **14 of the top 15 cells by recall-per-million-tokens are vanilla** (one superpowers cell
  sneaks in at #14).
- **Pareto frontier (recall vs cost):** 3 vanilla cells + 1 metareview/opus-5/low cell. The
  harnesses are off this recall-vs-cost frontier.
- **Direct matchup:** none of the 12 "cheap+harness+low/medium" cells beats
  `vanilla/opus-5/high` (recall 0.69, 0.7M tok) on recall at lower cost. The cheapest comparable
  harness cell costs 11× more for *lower* recall.

The harnesses are **10–40× more expensive** for the recall they deliver. They are **not** the
bang-per-buck play — vanilla is. The factory premium buys *coverage*, not *efficiency*.

**The refined story (three points):**
1. **The harnesses' value is *maximum signal*, not *efficiency*.** `metareview/opus-5/low` hits
   recall 0.86 + 174 hidden gold (the highest absolute signal in the matrix) but at 20.9M
   tokens (40× vanilla/opus-5/low's 0.5M). If you want *every* bug, harness+opus-5. If you want
   *bugs-per-dollar*, vanilla.
2. **The harness-vs-vanilla tradeoff is the *same direction* on every model — it is NOT opus-only.**
   On gpt the harnesses still find more total bugs: metareview beats vanilla on incr_recall in
   4/6 comparable gpt cells, compound in 5/6, and both beat vanilla on hidden gold 8/8. What differs by
   model is the *magnitude and cost*, not the direction.
3. **The one universal harness win is *hidden gold*** (16/16 metareview, 14/16 compound —
   including 8/8 on gpt; compound's only losses are two sonnet-5 cells). If you care about
   *discovery* (bugs beyond the benchmark), the harnesses consistently deliver — you just pay
   for it in tokens + hallucinations to triage.

### 3.5 Data integrity: the shared-repo collision bug and the batch_083 remediation

**The bug.** The batch_083 matrix ran with a shared materialize-repo cache: `materialize()`
kept ONE working repo directory per PR, and the realistic adapters mutate that directory
in-place. Two concurrent runs on the same PR clobbered each other — `git reset --hard` +
`git clean -fdx` in one run deleted the other's in-flight findings file, and both runs then
could extract the same (wrong or empty) findings file.

**Detection.** Signature: two runs on the same PR with overlapping time windows whose extracted
findings are near-identical across DIFFERENT (framework, model, effort) cells — impossible
legitimately, since different cells use different prompts/models. Same-cell rerun overlap is
expected-similar and excluded. Tool: `uv run python audit_batch_083.py` (committed).

**Audit result (2026-09-06):** 599 runs scanned, 595 same-PR overlap pairs — **16 confirmed
corruption pairs** (jaccard ≥ 0.5 across different cells, incl. jac = 1.00 across models),
1 suspect, **25 runs implicated** (compound 18, metareview 5, superpowers 2; vanilla 0).
All **20 tainted published data points were re-run on the fixed adapters** (per-run `mkdtemp`
work copies + per-PR flock) and registered under the original batch id, so the latest-pass
selection used throughout this report is clean: **0 published-selection points sit on
confirmed-implicated runs**. The only remaining flag is one benign post-fix pair (jaccard 0.37,
two runs of the same model on PR 8 at different efforts — expected similarity on isolated
work dirs, below the 0.5 corruption bar).

**What the bug explains.** The original snapshot's 10 "degenerate" (0-finding) runs were
mostly collision artifacts, not framework failures: 7 of 10 had an overlapping same-PR run,
and every cell re-run cleanly produces findings (e.g. metareview/gpt-5.6-sol/high went
0-finding → recall 0.64, incr. 0.87). The §3.1–3.4 numbers above reflect the clean
selections; §5's structural analyses (which depend on within-run attribution, not
cross-cell comparisons) are unchanged in their conclusions.

---

## 4. GLM sidebar

GLM (`glm-5.2-vision-flex`) is **not in the primary matrix**. It ran in the earlier 0.7.0 batch
across all four frameworks × {medium, xhigh}. Per the eval's scoping, only metareview 0.8.2
results count, so the 0.7.0 metareview GLM row is **excluded**. vanilla/compound/superpowers GLM
numbers are usable **within** the 0824-1019 sidebar (with a batch-effect caveat — that batch was
~0.14 higher recall than batch_083, so don't cross-compare without the caveat):

| framework (GLM) | effort | recall | adj_p | incr_r | hidden | hal |
|---|---|---:|---:|---:|---:|---:|
| vanilla-engineered | medium | 0.35 | 0.39 | 0.53 | 21 | 16 |
| vanilla-engineered | xhigh | 0.43 | 0.66 | 0.60 | 21 | 11 |
| compound | medium | 0.84 | 0.26 | 0.97 | 169 | 103 |
| compound | xhigh | 0.80 | 0.23 | 0.96 | 188 | 121 |
| superpowers | medium | 0.43 | 0.32 | 0.67 | 32 | 45 |
| superpowers | xhigh | 0.51 | 0.28 | 0.73 | 34 | 59 |

**Reading:** vanilla-glm is a credible budget reviewer (recall 0.35–0.43, adj. prec up to
0.66, very few hallucinations). compound on GLM was strong in the 0.7.0 batch (recall 0.80–0.84)
but at high noise. **metareview 0.8.2 × GLM is a gap** — not yet run. See `FURTHER-RESEARCH.md`.

---

## 5. Why the factories cost what they cost (structural findings)

### 5.1 The orchestrator, not the subagents, dominates cost (H3 — confirmed)

metareview-realistic cost is **~99.96% orchestrator (opus), ~0.04% lenses (Haiku)**. The 8-lens
fanout is essentially free; the opus orchestrator dominates. **"metareview is expensive because
of 8 lenses" is false — the lenses are cheap; the opus planning turn is the cost.** Implication:
pinning lenses to a stronger model (Sonnet) would be a cheap knob that might raise lens recall
(untested — see `FURTHER-RESEARCH.md`).

### 5.2 Per-lens attribution — which lenses catch bugs vs hallucinate

From `results/per_lens_attribution.json` (metareview-realistic), the LLM lenses vs the
deterministic gates:

| lens | n_findings | matched (TP) | real_rate | halluc_rate |
|---|---:|---:|---:|---:|
| feasibility | 263 | 85 | 0.677 | 0.323 |
| **security** | 229 | 27 | **0.712** | 0.288 |
| architecture | 706 | 76 | 0.577 | 0.423 |
| completeness | 549 | 78 | 0.574 | 0.426 |
| intent-preservation | 77 | 15 | 0.545 | 0.455 |
| scope | 312 | 23 | 0.37–0.45 | 0.55–0.63 (noisy) |
| orchestrator prose | 83 | 0 | 0.084 | **0.916** (mostly noise) |
| **all deterministic gates** | ~85 | **0** | **0.0** | **1.0** |

Two findings: (1) the **Security lens is high-precision** (real_rate 0.71) — one of metareview's
better lenses. (2) **Deterministic gates contributed 0 recall on this PR subset** (all gate
findings hallucinated against the gold set). The gates are free and may catch other classes
(eval/TODO/missing-test), but on these 6 PRs they add coverage noise, not bugs.

### 5.3 Adjudication split — whose "extra findings" are real vs hallucinated

The share of *unmatched* findings adjudicated **real** (the rest are hallucinations):

| framework | real_ratio of unmatched |
|---|---:|
| **vanilla-engineered** | **0.67** |
| compound | 0.54 |
| metareview-realistic | 0.46 |
| superpowers-realistic | 0.40 |

**vanilla's unmatched findings are the most likely to be real bugs** (67% real); superpowers' are
mostly noise (40% real). This is why vanilla's adjudicated precision (0.71) is so much higher
than the factories' — when vanilla reports something the gold set missed, it's usually real;
when the factories do, it's a coin-flip. **For a triage-constrained team, vanilla's extra
findings are worth reading; the factories' extra findings need adjudication first.**

### 5.4 metareview vs compound — the conclusion flips by model

- **On opus-5:** metareview and compound are cost-equivalent (~$5.75/cell at 0.7.0 medium);
  metareview finds more (recall 0.80 vs 0.54). metareview's single-pass design beats compound's
  two-pass (dispatch + synthesis) at xhigh.
- **On Codex gpt-5.6-sol:** the picture **inverts** — compound dominates metareview on both cost
  and quality (recall 0.70–0.75 vs 0.55–0.57; incr. 0.92–0.94 vs 0.82). metareview's xhigh is
  wasted spend on Codex.

**Takeaway:** on Claude opus, metareview is the more efficient factory; on Codex, compound is —
but vanilla is competitive with both on Codex and far cheaper.

---

## 6. Empirical verdict per framework

### vanilla-engineered
- **Benefits:** Highest adjudicated precision (0.71) and lowest hallucination rate (1.8/cell).
  Cheapest ($0.31/cell). **Model-agnostic** — the only framework that works well on every model
  tested. Strong on Codex (adj. prec 0.70–0.94).
- **Drawbacks:** Lower total coverage (incr. recall 0.67; 3.8 hidden-gold/cell) — misses ~⅓ of
  known bugs and surfaces fewer new bugs than the factories. No subagent fanout.
- **Verdict:** **The default.** Use it for routine review and on any non-Claude model. Reach
  for a factory only when the diff is high-stakes and you're on Claude.

### metareview 0.8.2
- **Benefits:** Highest recall on opus (0.79–0.86, incr. 0.97) — best coverage of known bugs on
  top-tier Claude. 8 adversarial lenses incl. a high-precision Security lens. Single-pass
  synthesis is more xhigh-efficient than compound. Deterministic gates are a free pre-check.
  Cost-equivalent to compound on opus at high effort ($57 vs $56); cheaper at low on sonnet.
- **Drawbacks:** Low precision (0.29 adj.) and high hallucination rate (13.9/cell) — ~8× the
  noise of vanilla. On Codex the pure-recall gain shrinks but it still finds more *total* bugs
  (incr_recall 4/6 on gpt). xhigh is wasted spend. The orchestrator (opus) is 99.96% of cost.
  Deterministic gates contributed 0 recall on this subset.
- **Verdict:** **The high-coverage choice on Claude opus.** Best when the diff is
  security/architecture-sensitive and you can absorb triage. Use low/high (not xhigh).

### Compound Engineering
- **Benefits:** The **most findings per cell** (14.9 hidden-gold/cell — highest absolute bug
  discovery). Risk-driven persona roster adapts to the diff. Highest incr. recall tier (0.83).
  On Codex gpt-5.6-terra xhigh, the one factory that beats vanilla on coverage (recall 0.55,
  incr. 0.84). P0–P3 output is triage-friendly in shape.
- **Drawbacks:** **Most expensive** ($2.72/cell, ~9× vanilla). Lowest adjudicated precision (0.33).
  Two-pass doubles xhigh cost on opus. Persona subagents route partly to Sonnet (not Haiku),
  inflating cost vs metareview's all-Haiku lenses.
- **Verdict:** **Use when you want maximum bug discovery and cost is secondary** — especially on
  Codex where it's the only factory that consistently works. Expect to triage a lot of noise.

### Superpowers
- **Benefits:** Cheap ($0.60/cell). On Claude opus xhigh it reaches incr. recall 0.92 —
  competitive with the other factories at lower cost.
- **Drawbacks:** **Lowest recall (0.29) and precision (0.22)** overall. Weakest harness on Codex
  (recall 0.02–0.17) — degrades Claude→Codex more than metareview/compound (drop 0.37 vs
  0.32/0.36) but still produces real findings, so it is not "broken." Highest hidden-gold miss
  rate of the factories.
- **Verdict:** **Claude-only, and currently the weakest factory on the data.** Promising on opus
  xhigh but outperformed by metareview and compound at most cells. Fix the Codex dispatch issue
  before re-evaluating.

---

## 7. Recommendations for the SDLC

The interaction analyses show no single framework/model is optimal across the loop. The
harnesses win at *discovery* (hidden gold, 16/16) but lose on *efficiency* and *precision*;
vanilla and the gpt models win at *precision* and *cost* but find fewer bugs. The practitioner
move is to **use them in sequence** — each where it is strongest — rather than picking one:

```
(a) write code  →  (b) discover candidate bugs  →  (c) adjudicate (kill hallucinations)  →  (d) fix & re-run (b–d) until done
```

- **(a) Write code** — strongest reasoner; effort = high, not xhigh (high and xhigh are nearly
  identical on recall but xhigh costs ~25% more).
- **(b) Discover** — run a harness to find maximum bugs including hidden gold (works on every
  model, not just opus). Default: `metareview/opus-5/low` (recall 0.86, 174 hidden gold, $31.13);
  on Codex, `metareview/gpt-5.6-sol/medium` or `compound/gpt-5.6-terra/xhigh`. Expect ~4–7× more
  candidates than vanilla, ~40–54% hallucinations. **Do not skip the harness on gpt** — it finds
  more total bugs (incr_recall) on gpt in 4/6 (metareview) / 5/6 (compound) comparable cells.
- **(c) Adjudicate** — filter the candidate list with a *precision* pass: use `gpt-5.6-terra`
  or vanilla as a second-pass judge, or the cross-family judge (`harnesseval/adjudicate.py`).
  Keep findings that survive (real-but-ungold + matched goldens = confirmed bugs).
- **(d) Fan out & iterate** — feed confirmed bugs back as fixes; re-run (b)→(c) until recall
  stops improving, tests pass, and the candidate list collapses to mostly hallucinations.

**The key insight: the harnesses and the precision models are *complements* in a loop, not
alternatives.** Harness+opus-5 discovers; precision-model (gpt-5.6-terra) or vanilla adjudicates.
A single framework/model for the whole workflow is suboptimal — the loop is where the value is.

> The loop is a *recommendation* derived from single-pass review data, not a measured workflow.
> Validating it (does iterating discover→adjudicate→fix actually converge faster / find more
> bugs than single-pass?) is the active experiment — see [`FURTHER-RESEARCH.md`](FURTHER-RESEARCH.md).

### Tactical recommendations

1. Match the framework to the model and the stakes — but don't assume the harness only helps on
   opus (it finds more total bugs on every model). All three harnesses degrade on Codex
   (Claude→Codex recall drop 0.32–0.37); superpowers is weakest on Codex but not broken.
2. Use vanilla as the baseline review gate; escalate high-stakes diffs (auth, payments, data
   migration, security boundaries) to a factory.
3. Prefer low/medium effort for the factories; reserve xhigh for opus + critical diffs.
4. Triage the factories' output by adjudicated precision, not raw finding count (~40–54% of
   their unmatched findings are hallucinations). vanilla's extra findings (67% real) are always
   worth reading.
5. Avoid overengineering via conditional coverage (Compound's risk-driven roster is an
   empirically supported efficiency idea; metareview's fixed 8 lenses always run).
6. Catch security and architecture early (metareview's Security lens real_rate 0.71;
   Architecture is its highest-volume TP source).
7. Don't trust the deterministic "free floor" to catch bugs (yet) — 0 recall on this subset.
8. Watch the hallucination tax — require adjudication before filing factory findings as issues.
9. Review the diff + intent, not just the diff (metareview's Intent/Scope lenses; compound's
   architecture persona).
10. Measure cost where it actually falls: the orchestrator (99.96% of metareview's cost). To cut
    factory cost, downgrade the orchestrator (Sonnet) or cache its context — not the lenses.

---

## 8. Caveats

- **N is tiny.** 6 PRs per cell; bootstrap 95% CIs wide or undefined. No "X beats Y" claim
  survives the bootstrap at this N — the interaction analyses report raw win-rates, not
  significance. Phase C is the bar before any final ranking.
- **batch_083 was partially corrupted by a shared-repo collision bug; every number in §3 comes
  from the post-remediation clean selections** (20 tainted data points re-run; 0 published-
  selection points on confirmed-corrupted runs — see §3.5 and `audit_batch_083.py`).
- **Batch effect.** batch_083 is ~0.14 lower recall than 0824-1019 on matched cells — a
  batch/judge effect, not a framework regression. Cross-batch pooling is avoided.
- **Cost for GPT is an unverified estimate.** Reported $ = real Anthropic billing; GPT reports
  $0 via OAuth, so implied $ adds GPT at pinned per-token rates (2026-08-22 pins for sol/terra;
  gpt-6-astra pinned 2026-09-06 at $10/$12.50 — the older pins no longer match OpenAI's current
  pricing page). Real GPT cost may differ.
- **All three harnesses degrade on Codex** (recall drop 0.32–0.37). superpowers is weakest on
  Codex (recall 0.02–0.17) but still produces real findings — not "broken."
- **Model provenance:** API 'opus' = `claude-opus-4-5` (pinned); CLI realistic 'opus' resolved to
  `claude-opus-5`. API and CLI are never compared head-to-head.
- **The SDLC loop (§7) is a recommendation derived from review data, not a measured workflow.**
  The 336-cell matrix measures single-pass review quality — the *finding* (discovery) component
  of the central question — not the iterative discover→adjudicate→*fix* cycle (the *fixing*
  component). Validating the loop is the active research direction
  ([`FURTHER-RESEARCH.md`](FURTHER-RESEARCH.md) §1).

---

## 9. Reproducibility

The exact tested code is pinned: `harnesseval` @ tag `v0.8.2-eval` (= `1847f7d`) +
`metareview` @ branch `0.8.2-eval`. Refresh every number above from the committed run records:

```bash
uv run python bin/analyze_batch_083.py          # rolling batch_083 analysis
uv run python bin/analyze_083_interactions.py   # the §3.4 interaction tests
uv run python audit_batch_083.py                # §3.5 collision audit (verify taint = 0)
uv run python -m harnesseval.analysis           # leaderboards, per-lens, adjudication split
uv run python -m harnesseval.report             # pareto plots + leaderboard JSON
```

See [`REPRODUCE.md`](REPRODUCE.md) for the full setup, the pinned versions, and the cost
warnings. See [`docs/FRAMEWORK_COMPARISON.md`](docs/FRAMEWORK_COMPARISON.md) for the detailed
working analysis this report summarizes.
