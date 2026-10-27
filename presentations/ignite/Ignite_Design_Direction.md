# Vibes vs. Evidence: design direction, v10

The story moves from other people's confidence making Dave doubt himself, to systematic testing, to a development practice the audience can try and judge. Every slide has 15 seconds. Visuals must make the claim graspable while leaving room to hear Dave.

Near-black, warm ivory and orange suit the dim conference hall. Helvetica Neue supplies the entire typographic system. Orange directs attention, and direct labels explain each chart. Coral and mint pair the old/new question with the later failing/passing test. The defect grid keeps its coordinates across 42 known bugs, 105 verified additions and 59 misses. Bug pictograms count defects; squares count matched comparisons.

The opening and ending are deliberately typographic. A single generated rotary-control image on slide 9 gives the middle of the talk a change in texture. The harness and development-loop diagrams explain relationships. The real test specimen supplies concrete evidence instead of decorative metaphor.

Slides 11–13 form one comparison sequence. Fable stays in the upper row and GLM in the lower row. Labels, chart origins and value positions stay fixed while the metric changes. Every pair uses the same zero-based scale within its slide. Costs and elapsed times are means per review. The 51 and 71 bug counts are totals across six PRs, out of the audited set of 147.

The final actions remain explicit: use a harness, start with low reasoning and test open weights, verify the findings in your development loop, and follow the evidence. These are recommendations grounded in this study, not universal model rankings or measured production-quality gains.

Exactly 20 static widescreen slides, 15 seconds each. No title, resume, contact ending, complicated animation, product pitch, audio or video. Chart and diagram labels provide necessary context; other slides stay sparse. All text, diagrams and charts are native editable objects. Sources live in slide notes and the rehearsal draft.

The v10 native Keynote exports have been inspected individually. The 515-word draft leaves more room for pauses than v9. Aloud timing and projection remain to be tested with Dave and the room.

## Slide 3 introduction update

The first two emotional beats stay intact. Slide 3 adds Dave’s name, a small anime-inspired waving portrait in the upper right, and a brief spoken introduction through Technorati and Linuxcare before the campaign scale. The portrait was generated from Dave’s supplied photograph with real transparency; it is separate from the editable text and is not a documentary photograph. The deck remains 20 slides at 15 seconds each.

## Bug pictograms

Slides 4, 5 and 14 use editable six-legged bug silhouettes in the existing grid positions. Ivory and orange retain their existing meanings. The 59 misses remain orange outlines. Each icon represents one defect. Direct edits made by Dave to the open Keynote are preserved.

## September 29: comparison and sequence

Slide 4 uses a three-column 8 × 3 × 3 experiment map. Dave’s edited heading and model/method labels are retained. The isolated failing/passing reproduction is now slide 7, immediately after the verified-defect answer key. The combined before-commit workflow is slide 17. The deck remains twenty slides, each advancing automatically after fifteen seconds. The bug-icon slides are now 5, 6 and 16; the token-cost setup is slide 10.

## September 29: restored token slide and report QR

The native Keynote had lost slide 10 while the previous verified PowerPoint still contained it. That mismatch was recovered from the intact export. Slide 10 now combines the approved generated paper-trail photograph with editable Helvetica Neue typography. The visible median footer is removed; the median qualification remains in the spoken notes. The closing typography uses equal type sizes and tighter spacing, with a functional QR to https://dsifry.github.io/harnesseval. The checked native snapshot stayed byte-identical across export; Dave continued editing the live canonical deck afterward. The ReportQR Keynote is the frozen verified snapshot, and its exported twenty slides all advance after fifteen seconds. The other eighteen slide object trees and notes 1 through 19 are unchanged from the recovered live baseline; Dave’s closing-script addition "All free, all open source" is retained. Final native PNGs 10 and 20 were visually inspected, and Apple Vision decoded the QR from the exported closing slide. No new independent full-deck review or aloud rehearsal is claimed.
