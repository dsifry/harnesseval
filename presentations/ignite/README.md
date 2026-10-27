# Vibes vs. Evidence: Ignite presentation

Dave Sifry's revised Ignite presentation, v10. The preceding approved checkpoint is commit `6daf0c18`.

- [Native Keynote master](DaveSifry_VibesVsEvidence.key): 20 widescreen slides, automatic 15-second advances, no transition effects.
- [PowerPoint backup](DaveSifry_VibesVsEvidence.pptx): editable interchange copy.
- [Slide overview](Ignite_Preview.png) and [20 native Keynote PNG exports](Keynote_Slides/).
- [Rehearsal draft](Ignite_Rehearsal.md) and [cue sheet](Ignite_Cue_Sheet.md).
- Presenter notes on every slide: a 3–5-word cue in 36-point bold, followed by the exact rehearsal passage in 24-point type. Sources follow in smaller text.
- [Design direction](Ignite_Design_Direction.md), [image decisions](Image_Direction.md) and [creative review record](Creative_Review_Final.md).

This revision gives the harness diagram more room, makes the bug/cost/speed comparisons a consistent three-slide sequence, and adds a real isolated failing/passing test specimen. Campaign breadth appears early. The ending preserves the practical takeaways: use a harness, start low and try open weights, verify findings in the development loop, and follow evidence.

Exactly 20 slides at 15 seconds each make a five-minute talk. The current spoken draft is 539 whitespace-counted words after Dave’s direct edits and the current sequence changes. An aloud timed rehearsal and back-row projection check remain outstanding.

Research is pinned to [harnesseval commit 8f634b6](https://github.com/dsifry/harnesseval/tree/8f634b68664751527a9ad0123d1a082dd70a0931). The full campaign covered 50 PRs from five codebases. The detailed 147-bug comparison covers six severity-selected PRs from two codebases. The selected configuration pair does not isolate a model, harness or reasoning effect. API costs use the study's list prices and exclude human checking time. The developer loop is a recommendation, not a measured production-quality result.

The generated images are [the reasoning dial](assets/reasoning-dial.png) and a small [waving portrait of Dave](assets/Dave_Sifry_Waving.png) on slide 3. The portrait was generated from his supplied photograph; its [prompt](assets/Dave_Sifry_Waving_Prompt.txt) is retained. [Image_Prompts.json](Image_Prompts.json) also records retired image concepts, which are not included in this deck.

## Source and verification

`source/` contains the current builder, Keynote compatibility patch, finalizer and story. These are snapshots of the working tools with absolute paths to the original Codex workspace and runtime. Regeneration on another machine requires those dependencies and path adjustments. Native Keynote timing configuration and PNG export were performed separately after importing the generated PowerPoint deck.

Three independent AI reviewers covered design/art direction/copy, computer science/AI evaluation, and Ignite presentation/speaking. All returned PASS for their inspected content and artifacts. The parent and creative reviewer each inspected all 20 native Keynote exports individually. The detailed review records are in `reviews/v10/`.

`validation/` contains the v9 and v10 receipts, speaking-load estimates and SHA-256 manifests. The old checkpoint manifest is retained as `checkpoint-v9-sha256.json`; `checkpoint-sha256.json` describes the current files. Some receipts name original-workspace deliverable paths and ZIP bundles omitted here because the deck and all PNGs are stored directly.

The isolated 4-D14 reproduction logs were inspected, not re-executed during presentation preparation. No evaluation code or results are changed by this revision.

The September 29 slide 3 introduction adds Dave’s name, the requested portrait and a brief spoken Technorati/Linuxcare introduction after the opening two slides. Its validation receipt is `validation/introduction-validation.json`. The earlier independent v10 reviews predate this narrow addition. The primary agent inspected the changed native slide; the other 19 native PNGs remain pixel-identical.

## Current authoring baseline

The native Keynote master and PowerPoint backup include Dave’s latest direct edits. Bug-count circles, now on slides 5, 6 and 16, have been replaced with editable native pictograms, preserving their counts, colors and positions. The current rehearsal document and `source/story.json` match the current native presenter notes.

`source/bug-icons/latest-before-bugs.pptx` preserves the direct-edit baseline. The bug-icon builder and grouped interchange shapes are in `source/bug-icons/`; these scripts retain original-workspace paths. The older `source/build.mjs` is the pre-direct-edit v10 builder and should not be used to overwrite the current master. Current native text is captured in `source/bug-icons/current-native-content.json`. The current slides and notes, including the user’s recent copy changes, have not received another independent full editorial or science review.

## Current sequence update

The comparison manifold is slide 4, preserving Dave’s native edits to the heading and model/method labels. The isolated failing/passing verification is slide 7, where Dave moved it to explain the answer key. The two development-workflow beats are combined into slide 17. The deck remains exactly twenty widescreen slides with automatic fifteen-second advances. `source/experiment-map/current-native-content.json` captures the current slide text and notes; the canonical Keynote and PowerPoint are authoritative. `source/experiment-map/user-edited-insert.pptx` preserves Dave’s edited insertion source. The generator in that folder predates those direct label edits and must not overwrite them. The targeted science and art-direction review is recorded in `Creative_Review_Final.md`; the earlier full-deck review still predates recent user edits.

## Verified token-image and report-QR snapshot

The current repository deck is the verified ReportQR snapshot: twenty widescreen slides, automatic fifteen-second advances, restored token slide 10 with the approved paper-trail image and no footer, and a tighter closing slide with a QR to https://dsifry.github.io/harnesseval. The code was independently decoded from the native closing PNG. The script is 544 whitespace-counted words. Dave continued editing the open canonical Keynote after this snapshot; those subsequent live edits are not claimed to be included in this backup. The source and validation receipts are under `source/restore-token-qr` and `validation/report-qr-*`. Earlier 19-slide native copies had diverged from the prior 20-slide PowerPoint export; this snapshot recovers the missing slide and verifies native/export consistency. No new commit, push, full-deck independent review, or aloud rehearsal is claimed.
