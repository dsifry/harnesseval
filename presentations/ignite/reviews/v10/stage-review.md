# Ignite stage review for v10

Reviewed every v9 native PNG individually, slides 1–20, and all 20 current spoken passages in `work/deck/story.json`. Checked campaign scope, matched comparisons and the reasoning conclusion against the local primary `REPORT.md`. Applied the Dave writing profile; its evidence for contemporary spoken presentations is limited, so recommendations below use his supplied motivation and normal speaking principles rather than pretending to reproduce an authenticated stage voice.

This is a script and visual inspection. I have not heard Dave deliver the talk. Timing estimates are not an aloud rehearsal or a projection test.

## Verdict

The current deck is coherent and legible, but its spoken version still behaves too much like a compressed report. It gets to three compelling results and then briefly turns back into methodology. At 15 seconds per slide, the listener must hear a claim, understand the chart, and notice the qualification at the same time. Several passages spend almost all 15 seconds on words alone.

Keep the emotional opening, the two-stage discovery of 42 becoming 147, the harness mechanism, the selected pair, the admission of misses, and the existing final line. Make the evidence easier to *experience*: enough silence to see a difference, a real failure/fix specimen, and a repeatable action the audience can recall later.

## Highest-priority changes

1. **Buy back listening time.** Current copy is 620 whitespace-counted words. At 135 words per minute, slides 3, 8, 12 and 14 already use roughly 15 seconds before adding pauses or expanding numerals. Slides 6, 10–13 and 17 add visual or conceptual work. A five-minute average conceals these local overruns. The proposed script is 530 spoken-token equivalents after splitting hyphenated terms and expanding AI/API; numerical quantities are already written out. It averages 26.5 per slide. That leaves roughly two to five seconds per slide at an illustrative 135 words per minute, to look, pause, gesture or recover.
2. **Put the campaign breadth with the experiment.** Slide 3 should carry 2,416, 50 PRs and five codebases. Say the eight-model/three-approach/three-setting matrix, but do not also make the audience decode a 72-cell grid and incomplete-coverage legend. Keep full coverage documentation in notes. Slide 4 must then explicitly narrow to the six selected PRs/two-codebase detailed comparison. Breadth and depth must not be allowed to blur.
3. **Replace the late scope recap with proof.** Slide 15 currently breaks the transition from ‘even the best missed bugs’ to ‘here is how you should use this.’ The approved new slot should show a source-verified original-fails/fix-passes specimen. It gives a concrete meaning to evidence, then naturally becomes the developer loop. The specimen belongs to the defect-verification work, not an invented automatic harness-fixing capability.
4. **Remove the accidental concession in the opening.** ‘My friends had better prompts’ states superiority as fact. Dave described hearing confident advice and feeling behind. ‘Everyone seemed to know the perfect way’ preserves his experience without granting the claims.
5. **Name what is being counted before saying 39/42.** The earlier 42 meant bugs. Here it means paired configurations. A listener who misses one noun can misunderstand the main result. Say ‘In matched comparisons’ first and keep a visible comparison label.
6. **Do not make uncertainty sound like a win for low reasoning.** Slide 10 tests high versus medium on the original benchmark score. Seventeen inconclusive comparisons do not establish equality and do not compare low with high. The short spoken end ‘Inconclusive doesn’t mean equal’ deserves its own beat. The low-effort recommendation comes from the practical selected configuration, not this null result alone.
7. **Keep selected-pair continuity unmistakable.** Slides 11–13 must preserve order, color, model, harness and effort identifiers. The listener should spend slides 12 and 13 absorbing new outcomes, not re-identifying the setup. Speak ‘one tested pair’ on 11 and ‘same pair’ on 13; the cost slide can let the unchanged visual pairing carry continuity.
8. **Keep one conclusion per takeaway.** Slide 18 currently promises ‘ways to challenge its own conclusions,’ which is not the process diagram shown. Say focused review jobs and a repeatable process. Slide 19 recommends affordable starting points and measurement, not a permanent model ranking.

## Per-slide stage findings

| Slide | Current stage issue | Recommended treatment |
|---|---|---|
| 1 | Strong emotional entry; script mistakenly asserts friends really had better prompts. | Keep the slide. Root the speech in perceived confidence and Dave’s stated self-doubt. |
| 2 | Strong turn in the story; most of the speech repeats the overload. | Keep the three recognizable claims, then stop at ‘what actually works?’ Give the question room. |
| 3 | Four competing numerical tasks plus a coverage footnote. Very little time left for the promise of the experiment. | Large campaign count and breadth. Say the matrix once; remove the mini-legend from stage. |
| 4 | Useful narrowing and strong answer-key setup. | Keep the six-PR/two-codebase scope in the speech. ‘Except it was incomplete’ should land near the change. |
| 5 | One of the strongest visual transitions. Too many audiences will remember only ‘more bugs’ unless verification is plain. | Say fail on original, pass with fix. One gesture to the added dots. Do not narrate arithmetic twice. |
| 6 | Good explanation but the existing 32-word speech and maintainer disclosure leave little time to trace two lanes. | About 22 words. Explain the three actions; do not read all labels. Keep the disclosure. |
| 7 | 42 risks being confused with original bugs. The dot field cannot carry the noun alone. | Say comparisons first. The speaker can then look back to the audience while the scale stays visible. |
| 8 | Honest tradeoff; existing speech is long and repeats the next question. | Keep median and token unit. End on the cost of maximum settings as the transition to the dial. |
| 9 | Photo is the one sensory release in the evidence block. | Allow a brief visual beat. One small turning gesture if natural; no acted routine. |
| 10 | Most technical spoken sentence, with high-versus-medium, significance and benchmark scope competing. | Simplify to inconclusive/favored. Retain original benchmark qualifier and explicit non-equivalence. |
| 11 | The listener has two models, two efforts, two processes and two counts to attach. | Name one selected pair. Treat each column as a whole unit; do not say full version numbers. |
| 12 | Oral fraction, prices and cost caveat exhaust the time. | Let the title carry 1/55. Speak dollar thirty versus two point four cents, then the API/human-time qualification. |
| 13 | Raw second counts make an easy idea harder to hear. | Speak about eighty seconds versus two and a half minutes; show rounded 79s/148s on the chart. |
| 14 | An important reversal can lose its force in four numbers and a long guarantee sentence. | Speak the missed count only. Show 88/147. Make clear this is the highest-recall setup, not the selected pair. |
| 15 | Current broad-campaign recap feels like a methods appendix before the close. | Real test specimen, source verified. The original fails, the fix passes. No full log screenshot. |
| 16 | Strong public benefit but long existing speech. | Put the review before commit. State this as the goal, not measured production improvement. |
| 17 | Good diagram; repetition in the speech can force rushing through the return arrow. | Name each action once. The key extra thought is ‘review the fix, too.’ |
| 18 | Useful recap; unsupported challenge-its-own-conclusions clause is dispensable. | Focused jobs, repeatable process, observed advantage in this study. |
| 19 | Correct practical recommendation; avoid making it sound like ‘low is always best.’ | Start low, try open weights, compare catches/misses/cost/wait on your code. |
| 20 | Current ending is already strong. | Keep it. Pause after ‘including mine.’ Finish the final line, then stop. |

## Proposed complete script

`script-proposal.json` contains all 20 passages, one recovery cue per slide, delivery suggestions and the qualifications that must survive any final edit. It retains the current slide sequence except the agreed early-breadth/slide-15-specimen change. It does not invent a bug-specific story for slide 15 pending science review.

Speaking-load proxy after spelled-out numerals and acronym expansion:

| Slide | Spoken-token equivalents | Illustrative words-only time at 135/min |
|---|---:|---:|
| 1 | 28 | 12.4s |
| 2 | 27 | 12.0s |
| 3 | 25 | 11.1s |
| 4 | 28 | 12.4s |
| 5 | 27 | 12.0s |
| 6 | 22 | 9.8s |
| 7 | 25 | 11.1s |
| 8 | 28 | 12.4s |
| 9 | 29 | 12.9s |
| 10 | 25 | 11.1s |
| 11 | 25 | 11.1s |
| 12 | 25 | 11.1s |
| 13 | 25 | 11.1s |
| 14 | 26 | 11.6s |
| 15 | 27 | 12.0s |
| 16 | 26 | 11.6s |
| 17 | 27 | 12.0s |
| 18 | 28 | 12.4s |
| 19 | 28 | 12.4s |
| 20 | 29 | 12.9s |

These are planning estimates, not recommended metronomic delivery. Use shorter beats as room for looking at the diagram or hearing the result, not as empty time to fill.

## Rehearsal and recovery

- Rehearse against actual automatic 15-second changes, with no pausing or rewinding. One complete run reveals more than perfecting individual sentences without the clock.
- Learn the one-sentence job of each slide before memorizing exact wording. The on-screen claim is the recovery cue.
- If a slide advances early, finish the current sentence and move to the new slide’s claim. Do not chase the prior slide’s unused tail.
- Do not sacrifice essential qualifiers to catch up: detailed six-PR scope, selected pair, original benchmark metric, inconclusive versus equal, and API cost scope need to remain intact.
- Keep gaze with the audience for the opening, the warning about missed bugs and the closing. Look at the diagrams only enough to synchronize one gesture. Narrating the entire visual while turned away weakens the story.
- On slide 20, aim to finish the last line before the final two seconds and hold. Do not add an improvised thank-you, URL, product pitch or credential summary over the transition.

## Remaining verification

The revised deck needs a fresh native-Keynote visual pass, especially the slide-15 specimen and any remade charts. Final performance readiness requires Dave’s complete aloud run with automatic timing. A script-length calculation cannot certify that run.
