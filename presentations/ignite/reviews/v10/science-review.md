# Scientific and AI-evaluation review, v9 baseline to v10

Reviewed all 20 native Keynote PNGs, the complete spoken script in `work/deck/story.json`, the checked-out primary `REPORT.md`, stored defect metrics, metareview adapter, and the proposed 4-D14 evidence specimen. Read-only review of repository and deck. This does not certify new model runs or re-execute archived tests.

## Verdict

The numerical backbone is sound. The deck already separates the 42-golden reasoning comparison from the 147-bug recall comparison, names the two configurations in the selected economic comparison, acknowledges missed bugs and human checking, and avoids claiming measured production-quality gains. Preserve those distinctions. One factual attribution needs correction; the other recommendations below improve how clearly the audience can interpret the evidence.

## Required factual correction

**Slide 5: do not attribute all 105 additional defects to review outputs.** The script says, “The reviews surfaced another hundred and five verified defects.” `REPORT.md:797–801` says 10967-D05 was discovered by the audit and never reported by any run. The 105 total remains correct, as does fail-on-head/pass-on-own-fix validation (`REPORT.md:422–426`).

Suggested 31-word script:

> After auditing the findings, the answer key grew by a hundred and five verified defects. Each had a test that failed before its fix and passed after. Now we had 147.

Keep the 42 → +105 → 147 visual. The essential distinction is that these are audited defects, not 105 extra allegations or automatically trusted model judgments.

## Strongest improvements, in priority order

1. **Put campaign breadth and primary-sample depth together earlier.** Moving 50 PRs/five codebases from slide 15 to slide 3 is scientifically better. It prevents the late breadth slide from sounding as though the preceding 147-bug results applied to all 50 PRs. Slide 4 must retain the spoken six-PR/two-codebase scope. The source is `REPORT.md:48–51, 139–143, 218–220`. Do not claim a completed 72-configuration grid, 2,416 independent PRs, repeated-run reliability, or evaluation of every possible run. There were 66 complete primary configurations, six partial Fable harness configurations, and one selected run per configuration per PR. The proposed deletion of the 72-cell diagram is a design decision, not a loss of scientific validity if the scoped experiment remains clear in speech and source notes.

2. **Make “evidence” tangible using slide 15.** The exact 4-D14 archived reproduction is stronger than another magnitude statistic. A real defect, failure log, one-line fix and passing test embody the talk’s central idea. It also bridges the 59-misses warning to the developer verification loop without claiming the study measured that loop. See specimen below.

3. **Retain explicit setup framing across slides 11–13.** All three variables change: model, approach and effort, with different serving paths too. These slides show a practically useful configuration comparison, not an isolated causal effect of open weights or low reasoning. “This setup found more” is correctly scoped. Suggested spoken opening: “Here’s one combination worth trying.” A concise transition after the metrics can land the lesson: “Price alone didn’t predict this result. Testing did.” Do not upgrade these slides to “Open models beat closed models” or “Low reasoning works better.” The Opus CE medium configuration still has the highest observed bug recall.

4. **Keep the cost of checking visible in speech.** The draft already says human time counts, which is good. The selected Flash setup has more classified unsupported findings and many unscored groups; cheap API usage is not demonstrated cheap total ownership. This is not a reason to add a complex precision chart in a 15-second slot. It is a reason to keep “check the findings” central and avoid broad “better in every way” copy. `REPORT.md:649–658, 709–715, 1299–1309`.

5. **Name uncertainty in ordinary speech on slide 10.** “No statistically resolved difference” is accurate but stiff. Suggested: “Turning reasoning from medium to high gave no clear answer in seventeen of twenty-two comparisons. Four favored high; one favored medium. On this benchmark, higher effort wasn’t a reliable shortcut.” The small subtitle should retain “benchmark F1” so this cannot be mistaken for the 147-bug recall metric. Do not use “the same,” “equivalent,” or “high doesn’t help.” `REPORT.md:1261–1274`.

## Proposed slide 15: archived evidence, not a simulation

**Visible direction:** “Make it fail. Then pass.” Above or beside two large results, “Before fix: FAIL” and “After fix: PASS.” A modest descriptive line can read “Deleted post → re-import crash.” Use editable typography and shapes, with the literal archived failure excerpt if it stays readable. Do not invent an IDE screen, fictional run timestamps, a production incident, or an automatic repair animation.

**Spoken option (32 words):**

> Here’s one verified defect: importing an embedded post again crashed after that post was deleted. An isolated test reproduced the failure. Add the missing guard, and that test passes. That’s checkable evidence.

**Exact evidence:**

- `analysis/verified_gold/GOLD_DEFECT_CATALOG.md:90–95`: 4-D14, TopicEmbed re-import after deletion; `own_executed` evidence.
- `analysis/verified_gold/4/B08-topicembed-re-import-crashes-when-the-embedded-post-was-/meta.json:15–39`: model-reported discovery, including GLM Flash MRV low. `DEFECT_ASSIGN.json` currently maps 70 finding identities to 4-D14. The older bundle candidate lists 68 findings/24 cells; avoid displaying these incidental counts.
- Same bundle `defects/4-D14/logs/head.log`: `RESULT: FAIL: NoMethodError: undefined method \`raw' for nil:NilClass`.
- Same bundle `defects/4-D14/logs/fixed.log`: `RESULT: PASS`.
- Same bundle `defects/4-D14/fix.patch`: adds `return if post.nil?` immediately after `post = embed.post` in the real `app/models/topic_embed.rb`.
- `analysis/verified_gold/WITHDRAWALS_AND_DEDUP_2026-09-18.md:47`: audit explicitly kept this defect because the failure originates from the real unstubbed file and its nil-guard fix.

**Boundary:** the isolated Ruby test stubs ActiveRecord, translation and PostRevisor dependencies. It executes the real TopicEmbed file; it is not a full Rails integration run. Bundle metadata says `standalone_real_code`, `behavior_change_not_regression`, with base `ERROR:LoadError`. Say “verified defect” or “isolated reproduction,” not “proved this PR introduced a production regression.” The test/fix pipeline is the evaluator’s ground-truth work, not proof that the benchmarked harness autonomously fixed code.

## Verified numerical spine

| Claim | Supported value and exact source |
|---|---|
| Campaign size and scope | 2,416 healthy runs; public 50-PR benchmark/five codebases. `REPORT.md:48–51, 139–143` |
| Primary matrix | Eight models × three frameworks × three effort settings; 66/72 complete on six PRs, 396 selected primary runs. `REPORT.md:139–143` |
| Audited bug set | 42 original goldens + 105 verified additional defects = 147. `REPORT.md:422–426, 753–761` |
| Harness direction | Higher observed recall in 39/42 matched same-model/same-effort pairs; mean recall increase 0.135. These are positive point estimates, not 39 statistically significant wins. `REPORT.md:723–726, 1883` |
| Harness token overhead | Median 10.1× for 42 matched pairs. `REPORT.md:1210–1217` |
| High vs medium | 22 benchmark-F1 comparisons: 17 unresolved, four favor high, one favors medium. `REPORT.md:1263–1274` |
| Selected pair, bugs | Fable 5.1 vanilla high: 51/147; GLM 5.3 Flash MRV low: 71/147. `analysis/verified_gold/DEFECT_METRICS.json` → `verified.cells` for the two exact configuration keys; Flash also in `REPORT.md:657` |
| Selected pair, API cost | $1.29594 vs $0.02354 mean/PR; ratio 55.05. `REPORT.md:994, 1061`. Study list-price accounting; not invoice, human time, or failed-call overhead (`REPORT.md:1425–1428`) |
| Selected pair, latency | Report-rounded 148 vs 79 mean seconds/PR. `REPORT.md:994, 1061`; exact means in saved metrics 147.69631 and 78.54169. Approximately 1.88× speed ratio, not a universal provider/model claim |
| Best observed recall | Opus CE medium 88/147, hence 59 misses, among complete configurations. `REPORT.md:651, 660–662, 745–749` |

## Harness and workflow guardrails

- Slide 6’s focused-review branches are accurate examples. Security, Architecture and Testing-quality are actual reviewer focuses in `harnesseval/adapters/metareview_realistic.py`.
- Keep “Combine,” not “Verify,” at the output stage. Adapter lines 305–307 explicitly concatenate rather than independently synthesize or reverify outputs. The report says eight lenses; the adapter prompt says nine. The current diagram wisely gives examples and an ellipsis instead of an exact count.
- Deterministic checks exist in this workflow, but their findings are filtered from the evaluated judged stream (`metareview_realistic.py:397, 522`). Do not say the measured recall gain proves the deterministic checks caused it.
- Slide 17 should remain a recommended developer loop. The study did not measure production bug reduction, autonomous fix-loop quality, or developer time saved (`REPORT.md:48–51`). “Use locally in development” must not become “all inference ran locally.” GLM used hosted gateway inference (`REPORT.md:156–166`).
- Slide 18’s “ways to challenge its own conclusions” is plausible advice, but a clearer and directly tested wording is “Give reviewers different jobs, combine their findings, then check them.”

## Whole-deck disposition

Slides 1–2: user-provided motivation, no fabricated external claims. Slide 3: correct numbers, improve scope order. Slide 4: accurate sample and original answer key. Slide 5: correction required above. Slides 6–8: sound with the workflow/evaluation distinction preserved. Slide 9: a labeled conceptual metaphor, no data claim. Slide 10: sound uncertainty, improve spoken simplicity. Slides 11–13: verified selected-pair evidence, preserve labels and scope. Slide 14: correct misses, retain “highest-recall configuration” in speech. Slide 15: replace repeated breadth with literal evidence after moving breadth to 3. Slides 16–17: recommendations, not measured production outcomes. Slides 18–19: useful starting choices; do not turn them into universal guarantees. Slide 20: strong and appropriate, including the invitation to question Dave’s own conclusions.

Exactly 20 slides and 15 seconds per slide can be preserved with these substitutions. No recommendation here requires an extra slide, a product pitch, or an additional technical metric.
