# Why CE still finds more hidden gold than the upgraded mrv — decomposition

**Cell:** glm-5.3-background × low, all under the same v3 adjudicator (k=1 quick pass).
CE: hid 39.0/PR (imp 21.8, hal 4.3, 77.8 findings/PR) · mrv 9-lens: hid 31.7 (imp 1.2,
hal 3.8, 65.2/PR) · old mrv 8-lens: hid 21.0. Gap: 7.3/PR. (CE under v3 is *higher* than
its v2 number — 36.8 → 39.0 — so the gap was previously understated, not overstated.)

Per-PR hid (mrv vs CE v3): 10: 23/38 · 4: 28/39 · 8: 14/24 · 10967: **40/35 (mrv ahead)** ·
11059: 51/55 · 14740: 34/43.

## Decomposition of the 7.3/PR gap

All 221 CE confirmed bugs were semantic-matched against the new mrv run's findings
(`analysis/residue_tasks.json`, `analysis/residue_results_*.json`): 194 matched (88%),
27 unmatched. The matched set was then checked against the mrv run's own verdicts.

| component | size | what it is |
|---|---:|---|
| Golden-absorbed | ~7/PR | CE hidden-gold bugs whose mrv counterpart was matched to a **golden** in mrv's judging — counted as recall, not hidden gold. **Not a discovery gap** (mrv incr-recall 0.96 vs CE 0.97). A metric-partition artifact: same issue, TP in one run, hidden gold in the other. |
| Never reported | ~4.5/PR raw, ~3/PR unique | 27 findings; CE restates the same issue 2–3× (isInvalidEmail ×3, findFirstOrThrow ×2, protocol-relative ×2 in the residue itself) |
| Reported, not confirmed | ~1.5/PR | mrv's phrasing of the same issue got important/hallucination/unresolved in the mrv run — the hedged-phrasing class from the flip analysis, again |

## The never-reported residue (27), clustered

**A. Pattern in the brief, didn't fire (~10).** The taxonomy has these; glm-5.3 at low
effort didn't apply them: whitespace/strip on username split (FORMAT-DRIFT family — the
PR8 run has 14 username findings, zero mention stripping; the earlier "acceptance 8/8" was
a false pass on this one), protocol-relative `//` URLs in `absolutize_urls`, non-atomic
setnx/expire throttle, negative/huge offset validation, missing params envelope → 500,
`findFirstOrThrow` with `userId || 0`.

**B. Genuinely new patterns (~6).** Not in any brief: client/server Zod schema divergence
(two copies drifting apart — the server copy lacks the uniqueness refinement), stale-field-
on-update (webhook update never sets `type`), missing `include: {app}` changing service
resolution, unbounded reply-to header growth, default-page-size change silently truncating
membership lists (200→50), fan-out N×M duplicate event creation (partially caught).

## What CE structurally does that mrv doesn't

1. **Redundant restatement = adjudication retry lottery.** CE's personas restate the same
   issue 2–3×; assertive phrasings get confirmed, hedged ones don't. mrv states each issue
   once. Evidence mrv benefits from the same effect when it happens: the PR8 run restated
   the silent-skip issue 4–5× across lenses and all instances confirmed.
2. **Broader claim spectrum.** CE's 21.8 important/PR vs mrv's 1.2 — CE emits
   maintainability/design observations v3 counts as real; mrv's lenses emit almost only
   defect claims. More surface area → more confirmed bugs at every threshold.
3. **Focused context per persona** vs mrv's 9 long briefs — attention dilution per pattern
   on a weak model at low effort. (The 8/8 acceptance pass proves the patterns fire; the
   residue proves they fire inconsistently.)

## Recommendations

1. **Phrasing discipline in LENS_SYSTEM** — require assertive defect-claim phrasing with
   the concrete failure mode; hedging is the judge's job. Worth ~1–2/PR per the flip data.
2. **k=3 majority for the formal numbers** (this was the k=1 quick pass) — recovers part of
   the reported-not-confirmed class.
3. **Cheap restatement pass**: each lens restates its P0/P1 findings as one-line assertive
   claims — mimics CE's redundancy at near-zero cost.
4. **Add the ~6 new patterns** (schema divergence, stale-field-on-update, missing-include,
   unbounded header growth, default-value behavior change, fan-out multiplication).
5. **Re-measure at high effort / on flash** — the in-brief-pattern-didn't-fire class should
   shrink with a stronger executor; taxonomy is near saturation, returns are now in
   execution and phrasing, not more lenses.
