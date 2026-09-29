# Vibes vs. Evidence: Ignite presentation

Dave Sifry's approved presentation checkpoint, revision v9, prepared September 28, 2026.

- [Native Keynote master](DaveSifry_VibesVsEvidence.key): 20 widescreen slides, automatic 15-second advances, no transition effects.
- [PowerPoint backup](DaveSifry_VibesVsEvidence.pptx): editable interchange copy.
- [Slide overview](Ignite_Preview.png) and [20 native Keynote PNG exports](Keynote_Slides/).
- [Rehearsal draft](Ignite_Rehearsal.md): spoken copy, cues and evidence boundaries.
- [Design direction](Ignite_Design_Direction.md), [image decisions](Image_Direction.md) and [creative review record](Creative_Review_Final.md).

This revision unifies slide 2's typography, explains a review harness on slide 6, and shows the developer review/reproduce/fix/test loop on slide 17. Exactly 20 slides at 15 seconds each make a five-minute talk. The spoken draft is 620 words; an aloud timed rehearsal and back-row projection check remain outstanding.

Research is pinned to [harnesseval commit 8f634b6](https://github.com/dsifry/harnesseval/tree/8f634b68664751527a9ad0123d1a082dd70a0931). The full campaign and the detailed six-PR comparison have different scopes, explained in the rehearsal document and slide source notes.

The retained generated image is [the reasoning dial](assets/reasoning-dial.png). [Image_Prompts.json](Image_Prompts.json) also records retired image concepts; those images are not included in this checkpoint.

## Source and verification

`source/` contains the current builder, Keynote compatibility patch, finalizer and story. These are snapshots of the working tools, with absolute paths to the original Codex workspace and runtime. Regeneration on another machine requires those dependencies and path adjustments. Native Keynote timing configuration and PNG export were performed separately after importing the generated PowerPoint deck.

`validation/` contains the original verification receipts and a SHA-256 manifest for the copied files. The native verification receipt also names a ZIP used for delivery in the original workspace; that duplicate bundle is omitted here because all 20 PNGs are stored individually.

Superseded concepts, previous deck revisions and scratch files are excluded. This checkpoint does not change the evaluation code or results.
