# Image and diagram direction, v10

Keep the single photographic illustration on slide 9. The latest independent creative review again recommended against adding photographs merely to increase the image count. The visual work belongs to the bug fields, comparative charts, process diagrams and one real test specimen.

## Explanatory visuals

**Slide 6: what a code review harness does.** Two aligned lanes share Change and Findings endpoints. The first has one Review stage. The second adds Checks, parallel Focused reviews and Combine. Security, Architecture and Tests are illustrative review perspectives; the ellipsis indicates additional lenses. The diagram explains coordination. It does not claim different models, independent verification of findings, or automatic fixing.

**Slide 15: evidence you can rerun.** The retained defect 4-D14 concerns re-importing a deleted Discourse post. The archived isolated reproduction failed before the nil guard and passed after it. Large FAIL and PASS labels express the result without fabricated terminal output or decorative chrome. Coral and mint echo the old/new question on slide 2. The visible caption identifies an isolated reproduction, not a full Rails integration test. The artifacts were inspected, not re-executed in this presentation session.

**Slide 17: how a developer uses review.** Review, Reproduce, Fix, Test, with a return path labeled Repeat. The narration places responsibility for checking findings with the developer and makes reviewing the fix explicit. This is a recommended workflow, not a measured production-quality improvement or a benchmarked autonomous fix loop.

The campaign breadth now appears on slide 3, leaving slide 15 for the concrete specimen. Exactly 20 static slides remain.

## Deliberately omitted

- A worried-developer photo would compete with Dave's real admission on stage.
- A lab or machinery metaphor would obscure the actual experiment.
- Extra imagery between slides 4 and 5 would interrupt the growth from 42 to 147.
- Images in the comparison sequence would disrupt its stable rows and direct labels.
- An unhappy customer would invent an incident and could imply measured production effects.
- A closing photograph would compete with the final idea and Dave's delivery.

## Sources and precision

The harness diagram is based on the [study report](https://github.com/dsifry/harnesseval/blob/8f634b68664751527a9ad0123d1a082dd70a0931/REPORT.md) and its [pinned metareview adapter](https://github.com/dsifry/harnesseval/blob/8f634b68664751527a9ad0123d1a082dd70a0931/harnesseval/adapters/metareview_realistic.py). The report describes eight lenses and synthesis; the adapter's CLI prompt specifies nine and concatenation of per-lens output. The slide uses example perspectives and combining findings without an exact count or an unsupported adjudication step. Benchmark judging and ground-truth verification are distinct from the harness itself.

The isolated specimen is retained in the pinned repository under `analysis/verified_gold/4/B08-topicembed-re-import-crashes-when-the-embedded-post-was-/defects/4-D14/`. The source notes identify its archived logs, patch and scope.

The entire deck uses Helvetica Neue. Circles represent defects; squares represent matched comparisons. The parent and independent creative reviewer inspected all 20 native Keynote exports. No aloud rehearsal or back-row projection test has been performed.

## Slide 3 portrait, September 29

Added at Dave’s request: a small anime-inspired portrait of Dave waving, generated from his supplied photograph using the built-in image-generation tool. The transparent PNG is embedded in the upper-right corner at 240 × 200 points on a 1200 × 675-point slide, positioned at (880, 50). It introduces the speaker after the two opening emotional beats. Full prompt: assets/Dave_Sifry_Waving_Prompt.txt. Asset: assets/Dave_Sifry_Waving.png.
