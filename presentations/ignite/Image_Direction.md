# Image and diagram direction

Keep the single photographic illustration on slide 9. All three creative reviewers advised against adding stock or generated photographs merely to increase the image count. The deck already has substantial visual material in its configuration matrix, bug fields and comparative charts.

The reviewers applied Ogilvy, Sullivan/Boches and Young principles. They did not impersonate the authors. Their shared test was whether a visual adds a relationship or understanding that the words alone do not supply.

## Approved additions

**Slide 6: what a code review harness does.** Two aligned lanes share Change and Findings endpoints. The first has one Review stage. The second adds Checks, parallel Focused reviews and Combine. Security, Architecture and Tests are illustrative review perspectives; the ellipsis indicates additional lenses. The branching shows how the harness coordinates work. The diagram does not suggest that the models are different, that findings have been proven correct by synthesis, or that the harness automatically fixes code.

**Slide 17: how a developer uses review.** Review, Reproduce, Fix, Test, with a large return path labeled Repeat. This makes reviewing the fix visible. The narration places responsibility for checking findings with the developer. It depicts a recommended workflow, not a measured production-quality improvement or a benchmarked autonomous fix loop.

Both diagrams replace existing treatments. The deck remains exactly 20 static slides at 15 seconds each.

## Images deliberately omitted

- Slide 1: a worried developer would compete with Dave's real admission on stage.
- Slide 3: a lab or machinery metaphor would be less precise than the actual experimental matrix.
- Slides 4–5: preserve the growth from 42 to 147 instead of interrupting it with a specimen.
- Slides 11–13: preserve the consistent positions and labels across bugs, cost and speed.
- Slide 16: an unhappy customer would invent an incident and could imply measured production effects.
- Slide 20: leave the closing idea and Dave's delivery the full frame.

Two reviewers initially proposed a conditional real fail/pass specimen on slide 17; one preferred a process diagram. An authentic retained specimen, defect 4-D14, was located. Dave then requested and approved diagrams explaining the harness and the development loop. The two approved diagrams are the implemented direction; the specimen is not added as a third visual.

## Sources and precision

The harness diagram is based on the [study report](https://github.com/dsifry/harnesseval/blob/8f634b68664751527a9ad0123d1a082dd70a0931/REPORT.md) and its [pinned metareview adapter](https://github.com/dsifry/harnesseval/blob/8f634b68664751527a9ad0123d1a082dd70a0931/harnesseval/adapters/metareview_realistic.py). The report describes eight lenses and synthesis; the adapter's CLI prompt specifies nine and concatenation of per-lens output. The slide therefore illustrates named example perspectives and combining findings, without an exact count or an unsupported adjudication step. The benchmark's later judging and ground-truth verification are distinct from the harness itself.

Slide 2 now uses Helvetica Neue, with the old question subdued and the new question bold. Plus/minus symbols carry the edit metaphor without a second type family.

All three reviewers inspected the new diagram previews and spoken passages and found no material correction needed. Native conversion, slide timing settings and unchanged-slide comparisons are checked separately. No aloud rehearsal or back-row projection test has been performed.
