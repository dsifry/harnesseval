# Vibes vs. Evidence: design direction

The presentation moves from private doubt to a systematic benchmark experiment, then to evidence-supported development practices. It is designed for an evening conference hall with dimmed lights.

The foundation is the restraint of Keynote's Basic Black widescreen theme, customized with charcoal, warm ivory, and orange. Helvetica Neue carries every slide, including the question change. Its minus/plus signs and contrasting weight preserve the diff idea within a consistent typographic language. Large type carries the opening and closing. Native charts carry the evidence. One generated dial image introduces the reasoning question.

The revised opening is “I thought it was me,” followed by a code diff that changes “Is it me?” to “What works?” The third slide pairs 2,416 reviews with the planned 72 configurations and explicitly reports 66 complete and six partial configurations across the six primary PRs. The matrix graphic is a coverage field; it does not assign named factors to unlabeled row or column positions.

## References and what to learn from them

| Reference | Useful lesson | Application here |
|---|---|---|
| [Jeff Veen, Great Designers Steal](https://www.youtube.com/watch?v=8CtC_qbQ51U) | Carry a single argument through a story, then return to its opening with a changed understanding. | Open with uncertainty about everyone else's advice. Close with a concrete way to decide for yourself. |
| [Mark Selander, Commutapult](https://www.youtube.com/watch?v=S099fdRuRi0) | Familiar frustration sets up increasingly surprising visual reveals. | Introduce one pair of configurations, then reveal bugs found, cost, and speed on three successive slides. |
| [Scott Berkun, How to Give a Great Ignite Talk](https://scottberkun.com/2009/how-to-give-a-great-ignite-talk/) | Leave pauses and create sections that let the speaker recover after a stumble. | Use short passages and a few large-number slides. Slides 15 and 18 provide clear recovery points. |
| [Storytelling with Data, A Quick Presentation Makeover](https://www.storytellingwithdata.com/blog/a-quick-presentation-makeover) | Explain a chart through a sequence of simple views. Separate slides can replace elaborate animation. | The three comparison slides retain the same models, colors, and positions. Only the metric changes. |
| [Jason Grigsby, How to Give a Successful Ignite Presentation](https://gri.gs/328/successful-ignite-presentations/) | Precisely scripted sentences can become brittle; rehearse concepts and recovery. | The separate practice document has a short cue for every slide. Practice complete runs without reading notes. |

The Ignite talk transcripts were read in full; selected video frames were inspected for composition. This was not a continuous audiovisual viewing of each recording. The Storytelling with Data example is a design reference, not an Ignite talk. Older examples' title and contact slides do not override this event's stricter rules.

## Five minutes, fixed

| Slides | Time | Purpose |
|---|---|---|
| 1–3 | 0:00–0:45 | Personal frustration, a brief joke, then the experiment. |
| 4–5 | 0:45–1:15 | The answer key grew from 42 to 147 verified bugs. |
| 6–10 | 1:15–2:30 | Harnesses, their token cost, and the uncertain value of higher reasoning. |
| 11–15 | 2:30–3:45 | The concrete bugs/cost/time comparison, its limits, then full-campaign breadth. |
| 16–20 | 3:45–5:00 | Put review into local development; use a harness; start low and test open weights; follow evidence. |

Exactly twenty static 16:9 slides. Fifteen seconds per slide. No title slide, biography, contact ending, video, audio, or complicated builds. Most slides use a few large words; chart slides include the labels necessary to identify their evidence. Sources and qualifications live in the notes and rehearsal document.

## Images

The final deck retains one original editorial illustration generated with the built-in image-generation tool: assets/reasoning-dial.png. It is a metaphor for the reasoning setting, not a photograph of a real product control. The original prompt remains in Image_Prompts.json.

The loudspeaker scenes, trophies, wands, pennies and quiet-workbench scenes are retired concepts. They are not used in the current deck. The opening uses the speaker's personal admission; the ending gives the final idea the entire frame.

All text, diagrams and chart numbers remain editable. The word-and-symbol question change is native text. Slide 6 contrasts a single prompt with checks, parallel focused reviews and combined findings. Slide 17 turns the developer practice into a review, reproduce, fix and test loop, with an explicit return to review the changed code. Both diagrams use native vector paths and text, without builds. Chart configuration labels use three larger lines and remain in the same positions across the bugs, cost and speed sequence.

## Evidence discipline

The 71 versus 51 bugs, $0.024 versus $1.30, and 79 versus 148 seconds compare the same two specifically identified configurations. They do not isolate the causal effect of model, harness, or reasoning level. Seventy-one and fifty-one are totals across six PRs; costs and times are means per review. The prices are from the study, not a current quote.

The local review/fix/test loop is a practical recommendation. The study did not demonstrate a measured longitudinal improvement in production software quality. Low reasoning and open weights are promising starting points to test, not universal winners.

## Native Keynote verification

The native `.key` file was saved and opened in Keynote. It contains exactly 20 slides at 1200 × 675 points (16:9). All twenty slides were selected together and verified as Automatically, 15.00 seconds, with no transition effect. All twenty PNGs exported by Keynote were visually inspected individually. Charts remain native editable chart objects. Keynote import issues with dot marker fills and numeric labels were repaired before this version was saved. The separate PowerPoint file is an editable interchange backup.

The revised 620-word spoken draft still needs an aloud timed run. The slide timings are configured; actual speaking pace and back-row projection have not been tested.

The v9 changes on slides 2, 6 and 17 were checked in native Keynote exports. Image comparison confirms that the other seventeen slides are pixel-identical to v7. The diagrams were checked for clear arrow direction, legible labels and clipping.
