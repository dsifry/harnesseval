# Adjudicator inter-rater reliability study (2026-09-09)

**Question.** Are newer models (gpt-5.6-gen, gpt-6-astra) actually better judges than gpt-5.2,
with our 61% "self-agreement" measuring an old model's inconsistency? Or do they merely
disagree differently?

**Method.** 90 findings (stratified 30/30/30 bug/hallucination/important vs the gpt-5.2 k=3
reference from the 0.11.1 flash batch), seed-0 sample via `tools/eval_adjudicator.py --k 1`.
Seven raters each judged all 90 independently; per-finding verdicts saved to
`analysis/adjudicator_verdicts/`. Premium raters (gpt-6-astra, claude-opus-4.5) ran via
OAuth CLI (`tools/eval_adjudicator_oauth.py`, codex exec / claude -p) at $0 API cost — note
these carry the CLI scaffolding wrapper, a transport difference flagged for interpretation.

## Agreement vs reference (30/30/30 balanced)

| rater | agreement | bug calls | hal | imp |
|---|---:|---:|---:|---:|
| gpt-5.2 (rerun, k=1 low) | 0.544–0.611 (run-to-run) | 54–56 | 15–18 | 14–16 |
| claude-opus-4.5 (oauth) | 0.589 | 40 | 22 | 28 |
| glm-5.3-background:xhigh | 0.567 | 50 | 24 | 12 |
| gpt-5.6-luna | 0.511 | 64 | 18 | 4 |
| gpt-5.6-sol | 0.511 | 51 | 25 | 4 |
| gpt-6-astra (oauth) | 0.467 | 69 | 20 | 1 |
| gpt-5.6-terra | 0.433 | 60 | 20 | 1 |

## Pairwise matrix (key structure)

Intra-5.6-generation agreement is high: luna-astra 0.833, luna-terra 0.822, sol-terra 0.800,
terra-astra 0.800, luna-sol 0.756, sol-astra 0.767 (mean ≈ 0.80). gpt-5.2 sits outside the
cluster (0.66–0.72); claude-opus is furthest from everyone (0.51–0.60).

## Manual audit of contested cases (decisive)

22 findings had ≥3/4 5.6-gen agreement against both the reference and opus. Audited against
the actual diffs:

- **cook_method cluster (5 findings)**: all four 5.6-gen models unanimously called a mass
  misclassification "bug". The diff shows `Enum.new(:regular, :raw_html)` — regular=1 — so
  `default: 1` is the *correct* default. **Shared family hallucination**: identical enum
  inversion across all four models. gpt-5.2 + opus both correct (hallucination).
- **#2 (force:true on shipped migration)**: real change, but migrations don't silently
  re-execute; impact inflated. important_non_bug (ref+opus right).
- **#33 (spec xhr :put routes to add_members, not remove_member)**: verifiably present in
  diff; minor coverage gap. 5.6-gen called it *hallucination* — wrong in the opposite
  direction (dismissed a real observation).
- **#5, #44**: 5.6-gen returned unresolved (3/4) where ref ruled bug/important.

Score: 7 audited, 7 losses for the 5.6-generation.

## Conclusions

1. **High inter-rater agreement between same-generation models is a trap** — it measures
   shared training, not correctness. The 0.80 intra-gen agreement here is substantially
   convergence on shared errors (same inverted enum, same impact inflation, same dismissals).
2. **The newer generation is worse as judges**, not differently-right: bug-overcalling on
   borderline findings (60–69 vs gpt-5.2's 54–56), plus shared factual hallucinations.
3. **gpt-5.2's ~55–61% run-to-run agreement is churn on genuinely borderline cases**, not
   error: on every fact-checkable audited case gpt-5.2 was correct.
4. **claude-opus-4.5 is the only near-balanced rater** (40/28/22) and was correct on all
   audited cases; it is the leading candidate for precision-sensitive judgment layers
   (metareview production advisory gates) and as an independent-family cross-check.
5. Cross-family agreement (opus 0.589 vs gpt-5.2) is the honest noise level for independent
   judges on borderline findings; same-family agreement should not be read as quality.

**Production decisions.** harnesseval adjudicator stays gpt-5.2 k=3 medium (frozen; also
now audit-validated). metareview production judge: stay on gpt-5.2; consider claude-opus
where precision matters; do not adopt 5.6-generation judges.
