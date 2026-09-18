# EXECUTIVE SUMMARY — automated code review: what to run, what it costs, and how sure we are

**For:** engineering leadership deciding on automated code review · **Data:** 2026-09-16 freeze of
the manifold campaign (50-PR Martian offline benchmark, 8 models × 3 frameworks × 3 efforts;
66 of 72 cells complete on the six severity-hardest PRs) · **Full report:** `REPORT_FINAL.md` ·
**Coverage:** `analysis/COVERAGE_FINAL.md`

## The recommendation

**Run the metareview harness on `glm-5.3-vision-background` at low reasoning effort.**

On the six severity-hardest benchmark PRs it matched the best frontier harness on golden recall —
**0.81 [CI 0.74–0.86] vs opus-5 harness 0.81–0.83** — beat it on F1 (0.73 [0.67–0.80] vs
0.44–0.57) and on precision (adjP 0.67 vs 0.30–0.44), and cost **7.5% [6.7–8.5] of the opus
compound-engineering cell**: **$0.22 vs $2.95 per PR review**, **$0.04 vs $0.52 per golden defect
found** ($0.004 vs $0.048 per real finding incl. beyond-gold), at the same latency (95 s vs 110 s
per PR).

*Lens note:* the figures just quoted are the **benchmark-defined** analysis (the 42 goldens only, scored as
F1). On the **true golden set** — our reported lens — the recommended cell scores **F2′ 0.470 [0.40–0.55]**,
ahead of `glm-flash · MRV · low` (**0.436 [0.39–0.51]**), which costs about a ninth as much per review
(**$0.024 vs $0.222**); the best cell overall is `glm-vis · CE · medium` (**0.494**). Effort-matched claim
soundness agrees at low effort (adjP **0.809 vs 0.703**, vision ahead); at high effort flash is
nominally ahead (0.924 vs 0.916). So the two lenses agree on the harness family and, at low effort, both favor vision
on quality — while flash remains the pick where API budget dominates, and the evidence does not establish
that vision's extra cost buys net developer savings (developer time is unmeasured). §10d. If
noise-tolerance is high and budget dominates, `glm-5.3-flash-background` at low effort delivers recall
0.83 [0.74–0.92] at **0.8% of the opus cost** — but with visibly lower precision (0.54) and fewer real
findings beyond the golden set where that drop is demonstrated (§"where it stops holding").

| option | recall (CI) | F1 (CI) | $/PR | $/golden-defect | s/PR |
|---|---|---|---|---|---|
| **glm-5.3-vision @ mrv, low** *(recommended)* | **0.81 [0.74, 0.86]** | **0.73 [0.67, 0.80]** | **$0.22** | **$0.039** | 95 |
| glm-5.3-flash @ mrv, low *(budget)* | 0.83 [0.74, 0.92] | 0.65 [0.62, 0.69] | $0.02 | $0.004 | 79 |
| opus-5 @ CE, low *(frontier ref)* | 0.81 [0.72, 0.87] | 0.57 [0.47, 0.71] | $2.95 | $0.52 | 110 |
| fable-5.1 @ vanilla, low *(premium single-pass)* | 0.74 [0.67, 0.81] | 0.78 [0.72, 0.81] | $0.90 | $0.17 | 57 |

All CIs are 95% cluster-bootstrap over PRs; quality is All-profile recall/F1 with k=1
adjudication, judge gpt-5.2 for the Anthropic/GLM rows.

## What we can and cannot claim (the honest version)

- **Supported, measured:** the cost ratios above (list prices retrieved 2026-09-16, retrieval-dated
  table in the report); recall parity with frontier harness cells on the hardest PRs; the **F2′** Pareto
  frontier of $-per-real-finding vs quality is entirely GLM cells (the *recall* frontier's expensive end is
  opus · CE · medium — a premium-model cell still buys recall no GLM cell reaches); harnesses raise recall for weak/mid
  models (median +0.12, 17/42 pairs resolved) but add 10× tokens median; **high vs medium effort
  buys nothing measurable in 18/22 model×framework comparisons** while costing 0.96×–4.2× — buy
  effort only where a resolved gain exists (our table lists them).
- **Not supported — do not repeat:** the operator's "~1/200th per token, ~1/10th per task".
  Measured: flash is **1/57 per blended token and 1/38 per task** vs fable-5.1 vanilla; vs opus-5
  vanilla it is 1/26 per token and 1/17 per task. Vision tier is only ~1/3 of opus per token.
  Cheap per-token rates are partly eaten by the harness's 10–20× token overhead — always quote
  both ratios.
- **Where it stops holding:** (1) at medium/high effort the GLM lane ran 4–12× slower than same-effort frontier cells (up to ~30× against
the fastest frontier low-effort cell)
  (gateway-throughput-limited) — this is a **low-effort** recommendation, and the Sep-14/15
  provider incident showed the cheap lane's capacity limits (an operational issue, not quality,
  but it is your operational issue if you adopt it); (2) every headline GLM cell predates the
  Sep-15 gateway/SDK fixes — quality direction unknown, likely operational; (3) the beyond-gold
  breadth drop is flash's where it is demonstrated: −39 [−62, −16] (CE low), −104 [−179, −45]
  (CE medium), −201 [−266, −141] (MRV medium) per cell — but at the recommended MRV-low cell
  the delta is +3 [−56, +64], i.e. **no demonstrated drop there** (§7.4 T6); prefer vision for
  breadth on the cells where the drop is shown, not as a blanket rule; (4) the numbers
  are for the six *hardest* PRs — recall generalises to the full 50 (mean gap +0.006, model
  rankings mostly preserved) but harness F1 on the top-6 overstates full-set F1 by ~+0.08
  (e.g. glm-vis mrv-low F1: 0.73 top-6 vs 0.57 full-50; the *ranking* survives, the level does
  not); (5) n = 1 run per cell×PR — CIs cover PR-sampling noise, not run-to-run noise.

## Our results are the expanded (real-world) numbers; the strict benchmark is the artificial lens kept for comparison

We report the **verified true-golden-set analysis** (REPORT_FINAL §10d) as our results throughout; the strict benchmark (goldens only) and the earlier unions (§5b, §10b, §10c) are kept for provenance.

The benchmark's golden set is a floor, not a ceiling. We rebuilt the hidden-gold set from every
confirmed-bug finding across all 2,416 healthy runs (hallucinations and nitpicks excluded at the
adjudication gate), then **executed** it: for every candidate, a test that fails on the PR head, a
minimal fix that makes it pass, and — where a sibling defect shares the site — an orthogonality
check that the bundle's fix leaves it red. Independent duplicate passes (six reviewers, then a
fix-location adjudication) removed 23 restatements and container folding removed 17 more, while a
walk of the audits' own label lists surfaced 13 candidate claims that had been dropped, of which 10 turned
out to be distinct defects (3 merged into the container's claim). A **2026-09-18 post-publication audit**
(triggered by external review; `analysis/verified_gold/WITHDRAWALS_AND_DEDUP_2026-09-18.md`) re-read every
defect's failure logs, **withdrew 3** whose tests did not demonstrate the claim (mock-manufactured or
stub-artifact failures), and **merged 2 duplicates** (including one already described by the original
golden). The verified universe is **42 goldens + 105 individually test-validated defects = 147 distinct
bugs**, every one owning its own test, fix and logs (`analysis/verified_gold/GOLD_DEFECT_CATALOG.md`).

Under those honest denominators: **harnesses still find more real bugs** — Δrecall > 0 in **39/42**
matched model·effort pairs (mean **+0.135**; peak-recall ratio **1.63×** versus the best vanilla cell,
0.599 vs 0.367) — and that advantage survives our evaluator as a point estimate: on **F2′ the best harness
cell leads the best vanilla cell 0.494 to 0.406 (1.22×)**, a paired difference whose 95% CI (−0.007 to
+0.169) **crosses zero** — a higher point estimate, not an established win (and selecting the best
configurations after observing their results is a disclosed, favorable caveat). The equal-weight **F1′**
lens ranks a vanilla cell first (0.482 vs 0.451); it is reported as a **legitimate alternative
preference**, not an artifact, for the volume-sensitivity and instrument reasons set out below.
**MRV is ahead of CE on average, not uniformly** (ΔF2′ point estimate +17/−4 over 21 matched pairs,
7/21 resolving at 95%).

**Our evaluator is F2′, on the full 147-bug true golden set.** The choice is deliberate — a stated
*preference*, not a measurement. Recall alone is half a metric (a tool that comments on everything would
score 1.0 and be useless), so it must be paired with a noise term — and the only free parameter is β, the
ratio at which a missed bug is charged against a false alarm. We *choose* β=2 to weight recall 4:1
because missed bugs matter more to us than false alarms; that is not a measured developer cost, and the
report (§10d) shows a literal 4×FN+noise utility can favor either cell depending on the pair — no economic
claim is safe without an explicit utility model. F1′ (β=1) is a legitimate alternative preference, not an
artifact to be "fixed"; it is reported alongside because adjP′-charged rankings are volume-sensitive — and
comparable only among cells whose adjudicator *measures* nitpicks: the fable vanilla cells run the older
binary instrument, which structurally cannot classify important-non-bugs, so their adjP′ is uncharged and
inflated (the report flags those cells with an instrument caveat; this bias favors vanilla, so the 1.22×
canvas is conservative). On the full true golden set (42 goldens + all 105 verified defects = 147 — we keep
the full set, so the metric leaves room for better agents) the best harness cell (glm-vis · CE · medium)
scores **F2′ 0.494 [0.443, 0.593]** against **0.406** for the best vanilla cell (fable · van · medium) — a
**1.22× point-estimate edge whose paired 95% CI crosses zero** (−0.007 to +0.169). The previously-
published pair (glm-vis · MRV · high 0.488 vs fable · van · high 0.386) resolves at 95% under the repaired
data (Δ +0.102, CI +0.003 to +0.168). `adjP` is reported alongside F2′ so the noise story stays visible,
and F1′ appears as a labelled alternative.

**Why even the best harness misses what it misses.** Three mechanisms, separated: (1) *denominator
inflation* — paraphrase splits and golden duplicates made the universe look ~1.6× bigger than it is:
359 raw pre-merge clusters → 253 after the strict re-merge → 152 candidates → **147** true bugs after the
2026-09-18 audit (3 tests withdrawn, 2 duplicates merged); (2) *configuration complementarity, not
blindness* — the best single cell finds **88 of 147**, and of the 52 it missed that any cell found, **all 52**
were found by a *different configuration* (a different model/framework/effort); the union of all 66
complete cells reaches **140/147 (95%)** (derived block, `final_report_metrics.json`). Repeat-run variance
is **not** measured by this experiment (n = 1 run per cell per PR) — the evidence says configurations
complement each other, not that re-running the same one recovers the misses; (3) a *genuine blind tail of 7
true bugs no complete cell found* (6 defects — three of them in PR 10 — plus 1 golden). The pre-audit class
analysis of the unfound set (`TRUE_GOLDEN_EVIDENCE.md`) found it overwhelmingly outside the correctness/
security brief the lenses are built for (performance/N+1/eager-loading, test-quality gaps, framework
idioms, migration-lock semantics). A scope explanation was tested and rejected: anchored findings are 227
in-diff vs 1 out-of-diff.

## Gaps we will not paper over

Fable-5.1's harness cells don't exist (account rate-capped ~3 days) — 29 of 111 hitlist rows;
opus/sonnet vanilla cells are top-6-only by operator decision; some metareview cells needed era-rule re-runs; GLM
full-50 fills were stopped at the data freeze (~40% of the planned fills done, resumable); sonnet-5's compound cells
*lose* recall because Claude-Code-style routing sends reviewer subagents to haiku — a harness is
only as good as the models it actually calls.

**Bottom line:** near-frontier defect-finding quality on the hardest PRs at ~1/13 the golden-defect
cost of the frontier harness, same latency at low effort — adopt at low effort on the vision tier for
lower-noise review, keep flash as the low-API-cost candidate where budget dominates (its low-effort
quality gap is a point estimate that our CIs do not resolve into a win for either), don't pay for high
effort without a measured gain, and treat the
GLM numbers as carrying a disclosed provider-infrastructure caveat until a post-fix replication
lands.
