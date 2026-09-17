# EXECUTIVE SUMMARY — automated code review: what to run, what it costs, and how sure we are

**For:** engineering leadership deciding on automated code review · **Data:** 2026-09-16 freeze of
the manifold campaign (50-PR Martian offline benchmark, 8 models × 3 frameworks × 3 efforts;
66 of 72 cells complete on the six hardest PRs) · **Full report:** `REPORT_FINAL.md` ·
**Coverage:** `analysis/COVERAGE_FINAL.md`

## The recommendation

**Run the metareview harness on `glm-5.3-vision-background` at low reasoning effort.**

On the six hardest benchmark PRs it matched the best frontier harness on golden recall —
**0.81 [CI 0.74–0.86] vs opus-5 harness 0.81–0.83** — beat it on F1 (0.73 [0.67–0.80] vs
0.44–0.57) and on precision (adjP 0.67 vs 0.30–0.44), and cost **7.5% [6.7–8.5] of the opus
compound-engineering cell**: **$0.22 vs $2.95 per PR review**, **$0.04 vs $0.52 per golden defect
found** ($0.004 vs $0.048 per real finding incl. beyond-gold), at the same latency (95 s vs 110 s
per PR). If noise-tolerance is high and budget dominates, `glm-5.3-flash-background` at low effort
delivers recall 0.83 [0.74–0.92] at **0.8% of the opus cost** — but with visibly lower precision
(0.54) and far fewer real findings beyond the golden set (§"where it stops holding").

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
  table in the report); recall parity with frontier harness cells on the hardest PRs; the Pareto
  frontier of $-per-real-finding vs F1 is entirely GLM cells; harnesses raise recall for weak/mid
  models (median +0.12, 17/42 pairs resolved) but add 10× tokens median; **high vs medium effort
  buys nothing measurable in 18/22 model×framework comparisons** while costing 1.1–4.2× — buy
  effort only where a resolved gain exists (our table lists them).
- **Not supported — do not repeat:** the operator's "~1/200th per token, ~1/10th per task".
  Measured: flash is **1/57 per blended token and 1/38 per task** vs fable-5.1 vanilla; vs opus-5
  vanilla it is 1/26 per token and 1/17 per task. Vision tier is only ~1/3 of opus per token.
  Cheap per-token rates are partly eaten by the harness's 10–20× token overhead — always quote
  both ratios.
- **Where it stops holding:** (1) at medium/high effort the GLM lane was 12–30× slower
  (gateway-throughput-limited) — this is a **low-effort** recommendation, and the Sep-14/15
  provider incident showed the cheap lane's capacity limits (an operational issue, not quality,
  but it is your operational issue if you adopt it); (2) every headline GLM cell predates the
  Sep-15 gateway/SDK fixes — quality direction unknown, likely operational; (3) flash (not vision)
  drops 39–201 real beyond-gold findings per cell — use vision if breadth matters; (4) the numbers
  are for the six *hardest* PRs — recall generalises to the full 50 (mean gap +0.006, model
  rankings mostly preserved) but harness F1 on the top-6 overstates full-set F1 by ~+0.08
  (e.g. glm-vis mrv-low F1: 0.73 top-6 vs 0.57 full-50; the *ranking* survives, the level does
  not); (5) n = 1 run per cell×PR — CIs cover PR-sampling noise, not run-to-run noise.

## Our results are the expanded (real-world) numbers; the strict benchmark is the artificial lens kept for comparison

We report the **true-golden-set analysis** (REPORT_FINAL §10b) as our results throughout; the strict benchmark (goldens only) and the earlier key-union expansion (§5b) are kept for comparison/provenance.

The benchmark's golden set is a floor, not a ceiling. We rebuilt the hidden-gold set by
LLM semantic merge: every confirmed bug found across all 2,416 healthy runs
(hallucinations and nitpicks excluded at the adjudication gate) was clustered into
**distinct real bugs** — 42 goldens + **359 additional true bugs** across the six PRs,
each with a human-verifiable evidence card (location, why-real, replication steps,
found-by list) in `analysis/TRUE_GOLDEN_EVIDENCE.md`. Two construction defects were
found and fixed en route: the earlier key-union overcounted distinct bugs ~17×
(paraphrase splits), and an extract bug had silently dropped 706 rj3-confirmed bugs
(disproportionately vanilla cells). Under the honest denominators: **the
harness-vs-vanilla comparison holds decisively** — 39/43 paired recall deltas resolve
positive — and the recommendation cell carries **~1.9× fable vanilla's real-bug recall**
at the same fraction of the cost (0.339 vs 0.177; not the 9× the inflated union
suggested). **MRV beats CE overall** on real-world F1 (mean ΔF1 +0.036 [+0.012,
+0.064], 21 matched pairs) and the gap widens under the user lens that charges nitpicks
against precision (adjP′): CE's findings are filtered as nitpicks at 29% vs MRV's 25%.

## Gaps we will not paper over

Fable-5.1's harness cells don't exist (account rate-capped ~3 days) — 29 of 111 hitlist rows;
opus/sonnet vanilla and metareview cells are top-6-only (operator decision + era rule); GLM
full-50 fills were stopped at the data freeze (~2/3 done, resumable); sonnet-5's compound cells
*lose* recall because Claude-Code-style routing sends reviewer subagents to haiku — a harness is
only as good as the models it actually calls.

**Bottom line:** near-frontier defect-finding quality on the hardest PRs at ~1/13 the golden-defect
cost of the frontier harness, same latency at low effort — adopt at low effort on the vision tier,
keep flash for budget-only lanes, don't pay for high effort without a measured gain, and treat the
GLM numbers as carrying a disclosed provider-infrastructure caveat until a post-fix replication
lands.
