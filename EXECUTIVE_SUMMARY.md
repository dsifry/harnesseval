# EXECUTIVE SUMMARY — Harnesses find more verified bugs, and open-weight models make them cheap: a systematic evaluation of AI code review (September 2026)

**For:** engineering leadership choosing a code-review pilot · **Data:** 2026-09-16 campaign freeze,
2026-09-18 evidence audit and 2026-09-19 advisory policy · **Full report:** `REPORT.md` · **Coverage:** `analysis/COVERAGE.md`

## What we evaluated

We measured whether extra model passes find more defects, how much review noise they add, and what they
cost. Eight models × three frameworks × three effort settings produced 2,416 healthy runs across a public
50-PR benchmark spanning five codebases. The primary analysis covers **six severity-selected PRs from two
codebases**, with 66 of 72 configurations complete. It does not establish production readiness or quality
equivalence on other repositories.

Our primary ground truth contains **147 distinct bugs: 42 benchmark goldens plus 105 verified hidden defects
with archived reproduction/fix-test evidence**. The 2026-09-18 audit withdrew three unsupported defect claims and merged
two duplicates. The benchmark's original 42-golden analysis is retained as a separately labelled lens.

## The recommendation

**Pilot the low-effort MRV options, GLM vision and GLM flash, on your own reviews.** Flash is the
lower-API-cost choice; accepted advisory usefulness and unsupported output must be assessed separately.
Vision has the lower scored unsupported count; developer time saved is unmeasured.

| MRV low-effort model | bugs / 147 | accepted A | unsupported H | below cutoff | F2′ | $/review | seconds/review |
|---|---|---|---|---|---|---|---|
| vision | 72 | 40 | 5 | 139 | 0.567 | $0.222 | 95 |
| flash | 71 | 50 | 19 | 148 | 0.556 | $0.024 | 79 |

Vision costs about **9.4×** as much and finds one additional distinct bug, with **14 fewer scored
unsupported findings**; flash receives **10 more accepted advisories**. Vision’s F2′ interval is
0.567 [0.490, 0.673], versus 0.556 [0.462, 0.712] for flash. These marginal intervals alone
cannot resolve a paired difference or establish equivalence. Medium/high GLM effort can be much slower;
this pilot recommendation is specifically for low effort.

## What the primary results support

- **Harnesses improve recall in 39/42 own-model comparisons** (mean Δrecall +0.135): seven models ×
  two harnesses × three efforts, excluding Fable for incomplete harness coverage.
- **MRV usually scores higher than CE:** 18/21 positive F2′ point differences;
  95% paired intervals favor MRV in 8 cases and CE in 3; 10 include zero. This is not a uniform win.
- **The highest F2′ point estimate is Opus · CE · medium (0.641)**. The best eligible vanilla cell
  is Fable · vanilla · medium (0.427). Their paired difference is 0.214 [0.116, 0.275]; the
  ratio is 1.502 [1.215, 1.819]×. Selecting both after observing the results makes the comparison optimistic.
- **The score rewards useful advisories, not just bug discovery.** Report §3.1 gives α = 0.5/1/2
  sensitivity and separate T/A/H/below-cutoff counts. Historical F1′ and adjP′ are burden-based metrics,
  so their rankings answer a different question.
- **Configurations complement one another.** The highest-recall cell finds 88/147 and misses 59.
  Other complete configurations recover 52 of those misses; the union covers 140/147. Repeat-run
  variance was not measured.

## The separate 42-golden benchmark lens

These figures use **only the original 42 goldens**, not the primary 147-bug universe:

| option | golden recall (95% CI) | F1 (95% CI) | $/PR | $/golden defect | seconds/PR |
|---|---|---|---|---|---|
| vision · MRV · low | 0.81 [0.74, 0.86] | 0.73 [0.67, 0.80] | $0.22 | $0.039 | 95 |
| flash · MRV · low | 0.83 [0.74, 0.92] | 0.65 [0.62, 0.69] | $0.024 | $0.004 | 79 |
| opus · CE · low | 0.81 [0.72, 0.87] | 0.57 [0.47, 0.71] | $2.95 | $0.52 | 110 |
| fable · vanilla · low | 0.74 [0.67, 0.81] | 0.78 [0.72, 0.81] | $0.90 | $0.17 | 57 |

Vision MRV-low costs 7.5% [6.7–8.5%] of opus CE-low, with a golden-recall ratio of
1.00 [0.91, 1.09]. The interval does not prove parity. Under this benchmark lens, **17/22**
high-versus-medium effort comparisons have unresolved F1 differences, four improve and one worsens.
High effort costs 0.96×–4.2× as much; those results do not directly describe true-gold F2′.

The full-50 selection check is also **benchmark-golden-only**: across 33 cells with ≥40 PRs,
mean top-six minus full-set recall is +0.006, while harness F1 is higher by +0.084 on average.
Rankings mostly agree, with CE-low a notable exception. This is an observed selection check, not evidence
that the six-PR true-gold results generalize to all 50 PRs or to production.

## Costs, evidence and limits

Metered costs use published list prices retrieved 2026-09-16, including cache pricing; the campaign
itself used a flat-fee gateway. Flash MRV-low costs **1/57 per blended token and 1/38 per task** versus
Fable vanilla-low, and **1/26 per token and 1/17 per task** versus Opus vanilla-low. The proposed
“1/200th per token, 1/10th per task” shorthand is unsupported. Against commercial harnesses, flash's
savings come from both lower token volume and lower per-token prices. Vision MRV-low is also cheaper
than the low-effort vanilla references: about 25% of Fable, 55% of Opus and 54% of Astra cost.

The hidden-defect evidence includes fail-on-head/pass-on-fix tests, duplicate audits and finding-to-defect
assignments (`analysis/verified_gold/GOLD_DEFECT_CATALOG.md`). The universe was discovered largely from
this campaign's own findings and then audited, so it is not an independent, exhaustive bug census.

Quality metrics pool PR-level counts into ratios; they are not means of the six PR scores. The 95%
cluster-bootstrap intervals resample observed PRs and recompute metrics. They are not prediction
intervals for new PR sets, do not remove selection bias, and omit run-to-run model variation and
unmeasured judge error. Overlap of marginal intervals is not a paired test.

The revised F2′ rewards **accepted useful advisories** rather than treating every important non-bug
as noise: **(5T + αA)/(4D + T + αA + H)**, with D = 147 and α = 1. T counts distinct verified bugs,
A counts accepted useful advisories and H counts unsupported findings. False claims, style-only comments
and vague speculation carry the same unit penalty. α = 0.5 and 2 provide preference sensitivity;
none of these weights measures developer time or economic value. Bug-only F2 and recall are unchanged.
F1′, adjP′ and `F2p_legacy` retain the historical non-bug-burden definitions.

**Revised F2′ has no penalty merely for reporting a non-bug.** A useful advisory classified at
confidence ≥0.70 earns credit; one below 0.70 receives neither credit nor a penalty. Penalties apply
only to the current classifier's `hallucination` category at confidence ≥0.80, which includes false
claims, style-only nitpicks and vague, non-actionable speculation. Such findings below 0.80 are also
unscored. These are model-reported confidence judgments, not calibrated probabilities. Frozen
verified-bug assignments take precedence, and below-threshold findings retain their classifications.

The selected common pass is **`glm-5.3-background`, low effort, k=1, initially four concurrent calls**, processing
the six PRs one at a time. All six PRs and **403 reviews** have validated base and selected-policy outputs; **1,501 eligible
advisory claims form 888 validated identities**, and all 66 complete cells are eligible for F2′. New judgments
earn advisory credit at **confidence ≥0.70** or an unsupported/style penalty at **confidence ≥0.80**.
An advisory at 0.75 earns credit; an unsupported finding at 0.75 receives no penalty. Classified findings
below their category’s cutoff remain unscored, with raw categories and responses retained. The frozen
0.80 base export is preserved; the selected scoring policy uses completed advisory duplicate checks. On identical advisory identities, raising
the A cutoff to 0.80 changes matched-cohort mean F2′ from 0.4436 to 0.4316 (MRV), 0.3991 to 0.3860
(CE), and 0.2654 to 0.2627 (vanilla); H remains fixed. These are descriptive sensitivities. Exact cleaned claims preserve case and receive separate judgments;
semantic duplicate counting does not transfer one claim's verdict to another. Admitted verified-defect
identities reuse audited truth per member without another model call or fabricated confidence.
A recorded six-call duplicate-validation trial completed 100 comparisons/minute versus 168 at four
in separate five-minute windows. The model, prompts and scoring rules were unchanged; the comparison
is observational and six recovered late in its window. Four remains the selected default.
Policy-specific deduplication now bounds each router call to 120 seconds, with at most three
attempts and saved-checkpoint reuse. Timeouts are processing failures, never finding classifications;
the separate execution extension preserves model, prompts, thinking and scoring rules.

Old semantic groups and votes are candidate evidence. Validated files/intervals prioritize comparison;
full mechanism, trigger and consequence must agree in a separate pair check, uncertain claims stay
separate, and counting groups are split by effective classification. The common prompt explicitly uses
the staff advisory bar and concrete maintainer benefit. Matched pilots are documented in
`analysis/verified_gold/advisory_readjudication/MODEL_PILOT_COMPARISON.md`; they do not establish
calibrated confidence or equivalent intelligence. Earlier Vision-classifier passes are not the current
instrument. The selected policy and its ≥0.80 advisory sensitivity use the same ≥0.70 identities.

This is model adjudication, not human validation; same-family judging may favor GLM outputs, and
confidence is not a calibrated correctness probability. Unassigned classifier `bug` groups receive no
new bug/advisory credit or penalty and are counted separately, so false claims can still be under-penalized.
The two low-effort options also have 139/148 below-cutoff groups and 82/81 uncredited bug groups
(vision/flash); these receive no credit or penalty. Uncredited bug groups are outside the extreme
below-cutoff sensitivity bounds. The reference advisory set covers only two of six PRs, so advisory recall is unmeasured. Original verified
bug credit remains unchanged. Relative to legacy scores, both the formula and judging/deduplication
instrument change; the entire score movement is not an advisory-bonus effect. See `REPORT.md` §2.6.

All headline GLM harness cells contain runs preceding the September 15 gateway/SDK fixes. Medium/high
effort ran 4–12× slower than same-effort commercial cells in this campaign; failed gateway calls are
excluded from per-review costs. Fable's full harness grid was omitted for budget, Opus/Sonnet vanilla
coverage is top-six-only, and GLM full-set fills stopped at the freeze. These gaps and the two-codebase
primary sample limit adoption claims. The evidence supports testing the two low-effort MRV options on
your own reviews and measuring developer triage time before choosing between them.

---

**Disclosure:** the author maintains **metareview** (MRV), one of the harnesses evaluated in this
report. It is open source, MIT licensed, and available free of charge at
<https://github.com/dsifry/metareview>.
