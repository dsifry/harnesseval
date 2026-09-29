# Full-deck adversarial review

Three independent AI reviewers applied documented principles from David Ogilvy, Luke Sullivan and Edward Boches, and James Webb Young. These are principles-based assessments, not reviews or quotations by the authors themselves.

Each reviewer individually inspected all 20 native Keynote PNGs, numbered 001 through 020, and read all 20 spoken passages and evidence boundaries. This complete review covered the deck before the revision described below. Earlier rounds had covered concepts and selected slides only.

## Findings applied

| Finding | Revision |
|---|---|
| Slide 15 made the entire campaign sound like six PRs from two codebases. | Headline: **50 PRs. Five codebases.** Supporting line: **Full campaign: 2,416 healthy reviews.** The speech explicitly identifies the six-PR scope of the detailed 147-bug comparison. |
| Slide 16 described a step without a compelling reason to care. | **Find bugs. Before users do.** The speech places harness review before committing changes and frames earlier detection as the goal. |
| Slide 7 reused the bug-dot visual language for matched comparisons. | Comparison marks are squares. **Matched comparisons** is larger and bold. The unmeasured comparison with advice in Dave's feed is removed from the speech. |
| Slide 17 skipped reproduction in the visible sequence. | **Reproduce. Fix. Test. Repeat.** Reproduction connects everyday review to the study's verification method. The new three-line layout breaks the repeated two-line treatment. |
| Slide 19 repeated three already-presented numerical results. | The speech now recommends affordable starting settings and comparing findings, misses and costs. |
| Slide 20 summarized methodology without resolving the opening's personal tension. | The speech returns to doubt, evidence Dave can check, and demanding evidence from advice “including mine.” The final visible words remain **Follow the evidence.** |
| “Fifty-five times less” was needlessly ambiguous. | The spoken cost comparison is now **one fifty-fifth the API cost**. |

All three supported the proposed replacements for slides 15 and 16. Their shared recommendation was a bounded revision to scope, unit clarity, verification and the ending, while preserving the evidence sequence.

## Decisions retained

The configuration field remains on slide 3. One reviewer proposed removing it to reduce numerical load; the other two valued its role in making the defined experimental matrix visible. It directly serves Dave's emphasis on systematic comparisons. Its six-PR coverage caption remains scoped to that subset. This slide needs particular attention during rehearsal.

The reasoning dial remains on slide 9. It is a generic metaphor, but provides a useful visual pause. The reviewers did not identify a material reason for another image-generation round.

“Use a harness” remains an explicit takeaway, as Dave requested. Low reasoning and open weights remain starting configurations to test, not universal winners. The selected comparison continues to identify both model, process and reasoning settings.

One reviewer initially flagged slide 19's word spacing, then withdrew that as a rendering defect after re-examination. No repair was warranted.

## Evidence and delivery boundaries

The full campaign covers 50 PRs across five codebases and 2,416 healthy review runs. The detailed 147-bug comparison covers six severity-selected PRs from two codebases. Expanding the campaign description does not expand the denominator of those results.

“Find bugs. Before users do.” is the goal of the proposed development practice. The experiment measured findings, API cost and latency, not a reduction in production incidents. Local development does not imply local model inference.

The revised spoken draft is 620 words. Word counts and reading judgments are not a timed aloud rehearsal. Back-row projection has also not been tested.

## Revision recheck

All three reviewers subsequently inspected the four changed native Keynote exports (7, 15, 16 and 17) and the revised spoken passages (7, 12, 15–17, 19–20). They found the substantive issues addressed, with no new material visual or meaning problem. The art-direction reviewer flagged remaining speaking-room risk, so the optional final clauses on slides 7 and 15 were removed. This is a review of content and rendered slides, not a timed aloud delivery.

Native image comparison confirms that only slides 7, 15, 16 and 17 changed visually. The other sixteen exports are pixel-identical to the previously reviewed deck. Exactly twenty slides remain, and all have been verified in Keynote as Automatically, 15.00 seconds, with no transition effect.

## Typography and diagram revision (v9)

All three reviewers recommended restraint about adding photography. The evidence charts and the speaker already carry the story; another metaphor image would need to explain something the current slides cannot. Dave approved diagrams on slides 6 and 17.

Slide 2 now uses Helvetica Neue, preserving the minus/plus contrast and bold new question. Slide 6 contrasts a single prompt with deterministic checks, parallel focused reviews and combined findings. Security, architecture and tests are illustrative review lenses, not a complete roster. Slide 17 shows Review, Reproduce, Fix and Test, with an explicit return to Review.

All three reviewers inspected the rendered v9 diagram previews and the revised spoken passages. They reported no material issues. The Ogilvy-principles reviewer also checked slide 2 for typographic consistency. These reviews used toolkit previews; the primary agent separately inspected the native Keynote exports. Neither the diagram nor the script claims automatic fixing or that findings have already been independently verified.

Native export comparison confirms that only slides 2, 6 and 17 changed visually from v7. The other seventeen exports are pixel-identical. All twenty slides remain set to Automatically, 15.00 seconds, with no transition effect. The current spoken draft is 620 words. Aloud delivery and back-row projection remain untested.
