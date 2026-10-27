# Vibes vs. Evidence: current rehearsal draft

Dave Sifry. Exactly 20 widescreen slides, automatically advancing every 15 seconds. Five minutes total. No title, résumé or contact slide, audio, video or builds. A brief personal introduction is folded into slide 3.

This is a practice aid. Learn the point of each slide and use the image as your stage cue. The current draft is 544 whitespace-counted words, including Dave’s latest direct edits and slide order. The fixed 15-second advances require an aloud rehearsal to check each passage. Word counts alone do not verify stage pacing. Dave's actual aloud pace and back-row projection have not been tested.

The source is the [corrected report](https://github.com/dsifry/harnesseval/blob/8f634b68664751527a9ad0123d1a082dd70a0931/REPORT.md). The full campaign covered 50 PRs; the detailed 147-bug comparison covered six selected PRs. Preserve that distinction. The GLM comparison used hosted inference, even though the recommended review workflow runs during local development.

## How to rehearse

Run the entire deck with its automatic timings. Keep going after a stumble. If a slide changes before you finish, move to the new slide's cue rather than chasing unused words. Keep the essential qualifications: six-PR scope, one selected configuration pair, high-versus-medium on the original benchmark, inconclusive does not mean equal, and API cost excludes your checking time.

On the next run, speak from the cue sheet rather than reading this draft. Use the short passages to look at the audience. Finish the final line before the last two seconds, then hold. Do not add a biography, URL or product pitch at the end.

## 1. My secret fear: Is it me? (0:00 to 0:15)

**Cue:** Their confidence, my doubt

Everyone seemed to know the perfect way to use AI. Better prompts. Better tools. Better systems. The more confident the advice got, the less confident I felt.

*Delivery:* Address the room, not the slide. Give the final sentence space. AI adds an extra spoken syllable, not a pause.

*Evidence boundary:* Proposed first-person wording based on Dave's account of his motivation, supplied in this conversation. Typographic opening; no staged portrait or claim about a photographed event.

## 2. Is it me? / What works? (0:15 to 0:30)

**Cue:** Ask what actually works

Buy the course. Comment ‘AI agents.’ Get the perfect system. I was comparing myself to everybody else’s claims. So I changed the question: what actually works?

*Delivery:* Treat the first three clauses as familiar examples, not impressions of a specific vendor. Small pause before the new question.

*Evidence boundary:* Dave's account. The wording is a general illustration of the pattern he described, not an attributed quotation from an identified person.

## 3. Dave Sifry / 2,416 reviews (0:30 to 0:45)

**Cue:** Introduce myself, then experiment

BTW, I’m Dave Sifry. I founded Technorati and co-founded Linuxcare. I got pissed with all those vibes. So I ran the tests. two thousand four hundred sixteen AI code reviews, across fifty pull requests and five mature open source codebases.

*Delivery:* Briefly introduce yourself after the two opening emotional beats. Then move directly to the study. The small generated waving portrait is based on Dave’s supplied photograph. Do not add a career list or extra statistics.

*Evidence boundary:* Biographical facts supplied by Dave in the organizer’s accepted speaker description: founder of Technorati and co-founder of Linuxcare.
REPORT.md, campaign overview and §2.2. 2,416 healthy runs across the campaign, not 2,416 independent pull requests. The planned matrix has 72 configurations; 66 have complete coverage of the six primary PRs. Primary analysis selects one run per configuration per PR; it does not measure repeat-run variance. The original benchmark and executed hidden-defect validation supply distinct parts of the answer key.

## 4. The comparison manifold (0:45 to 1:00)

**Cue:** Model, method, reasoning

Which model? One prompt or a harness? How much reasoning? Could China’s open-weight GLM models compete? I tested eight models, three review methods, and low, medium and high reasoning.

*Delivery:* Give each question a beat. The family names support the question, not a roster to read aloud. Do not say all 72 configurations were complete.

*Evidence boundary:* REPORT.md §2.2. Eight tested models: Claude Fable 5.1, Opus 5, Sonnet 5; GPT-5.6 Sol, GPT-5.6 Terra, GPT-6 Astra; GLM-5.3 and GLM-5.3-Flash. Three methods: an engineered single prompt, Compound Engineering, and metareview. Three effort levels: low, medium, high. The planned 72-cell matrix has 66 complete cells on the primary six-PR sample; six Fable harness cells have partial coverage. The open-weight comparison covers these two GLM deployments, not every Chinese or emerging model. GLM-5.3 used a hosted 4-bit quantized build; the Flash serving build was not documented. Geographic background for GLM: Z.ai/Zhipu official company page, https://www.zhipuai.cn/en/about .

## 5. 42 known bugs (1:00 to 1:15)

**Cue:** Six PRs, 42 known bugs

For the detailed comparison: I whittled it down to the six most knotty pull requests, Forty-two bugs humans had found. That gave me part of the answer. But the answer key was incomplete.

*Delivery:* Preserve the six-PR scope. The answer key was incomplete; that is not a measured comparison of human reviewer performance.

*Evidence boundary:* REPORT.md §§2.2 and 3.1. Six severity-selected PRs. Forty-two original benchmark goldens.

## 6. 105 more (1:15 to 1:30)

**Cue:** Verify the additional defects

After the audit: a hundred and five more verified defects. Each test failed before the fix and passed after. One hundred forty-seven bugs in the answer key.

*Delivery:* One gesture from the original ivory bug icons to the added orange bug icons. Do not enumerate both the arithmetic and the total twice.

*Evidence boundary:* REPORT.md corrected hidden-defect audit. 105 retained hidden defects plus 42 benchmark goldens. Audit removed unsupported claims and duplicates. The universe is campaign-discovered and not exhaustive. Attribution correction: REPORT.md lines 797–801 identifies 10967-D05 as audit-discovered and never reported by a run; the 105 total must not all be attributed to AI review findings.

## 7. Evidence you can rerun (1:30 to 1:45)

**Cue:** Reproduce, fix, test again

Here’s one verified defect: re-importing a deleted post crashed. An isolated test reproduced it. Add the missing guard, and the test passes. Evidence you can check.

*Delivery:* Name the defect in ordinary language. Indicate the failing result, then the passing result. Do not read code or a stack trace. This is evaluator verification, not an automatic repair demo.

*Evidence boundary:* Verified defect 4-D14. Original isolated reproduction log: RESULT: FAIL: NoMethodError: undefined method `raw' for nil:NilClass. Fixed log: RESULT: PASS. The minimal patch adds return if post.nil? after post = embed.post in the real app/models/topic_embed.rb. The isolated Ruby test stubs surrounding dependencies, so this is not a full Rails integration run or proof of a new PR regression. The audit explicitly retained it. Primary artifacts at https://github.com/dsifry/harnesseval/tree/8f634b68664751527a9ad0123d1a082dd70a0931/analysis/verified_gold/4/B08-topicembed-re-import-crashes-when-the-embedded-post-was-/defects/4-D14 . See also analysis/verified_gold/WITHDRAWALS_AND_DEDUP_2026-09-18.md, line 47. The benchmarked harness did not perform this evaluator verification automatically.

## 8. Inside a review harness (1:45 to 2:00)

**Cue:** Same model, focused jobs

A harness runs checks, assigns focused reviews in parallel, then combines findings. Same model, different jobs. I maintain metareview, one of the harnesses tested.

*Delivery:* Use the three active verbs to walk left to right once. Do not read every lens label. The maintainer disclosure is essential and this is the only spoken product mention.

*Evidence boundary:* Illustrative architecture based on REPORT.md §2.2 and the pinned metareview_realistic.py adapter. Security, Architecture and Testing-quality are examples of actual reviewer lenses, not the full roster. The adapter runs its deterministic command and context scaffold before dispatching reviewers, then combines per-lens outputs. The report says eight lenses and synthesis; the pinned CLI prompt says nine and explicitly concatenates the findings. This diagram deliberately does not assert an exact lens count or a separate judgment step. No automatic fixing is depicted. The evaluator and its ground-truth adjudication are separate from the review harness.

## 9. The harness found more (2:00 to 2:15)

**Cue:** 39 of 42 matched comparisons

In matched comparisons, the harness found more verified bugs thirty-nine times out of forty-two. Same model. Same reasoning setting. The review process mattered.

*Delivery:* Say ‘comparisons’ before introducing the count; forty-two earlier meant bugs. Leave a beat after the result. Display a noun with the number, not only 39/42.

*Evidence boundary:* REPORT.md matched true-gold recall comparison. Seven models, three efforts, two harness versus vanilla pairs. Observed direction, not 39 individually statistically significant effects.

## 10. 10× the tokens (2:15 to 2:30)

**Cue:** More review uses more tokens

Those extra passes used about ten times the tokens, at the median. More review has a price. Did that work also need an expensive model at high reasoning?

*Delivery:* Let the excessive paper trail set up the cost question. Say "at the median" aloud; keep the slide itself spare. The photograph is a generated visual metaphor, not a measured bill.

*Evidence boundary:* REPORT.md median token multiple 10.1 across 42 matched comparisons. Token consumption is distinct from dollar cost.

## 11. More thinking? (2:30 to 2:45)

**Cue:** Test the reasoning dial

The reasoning dial is tempting. Turn it up, get a better review. But that’s an assumption. I tested low, medium and high to see what the extra thinking bought.

*Delivery:* Let the photograph be understood before speaking. A small turning gesture is enough; no acting routine.

*Evidence boundary:* REPORT.md effort sweep. Only low, medium, high were tested. Generated rotary-control illustration is a metaphor, not a real product control.

## 12. Often, no clear difference (2:45 to 3:00)

**Cue:** Inconclusive doesn’t mean equal

Of twenty-two high-versus-medium comparisons, seventeen were inconclusive on the original benchmark score. Four favored high; one favored medium. Inconclusive doesn’t mean equal.

*Delivery:* This is the densest concept. Point to the large inconclusive group, then briefly the other two. End on the uncertainty, not a claim that high cannot help.

*Evidence boundary:* REPORT.md effort comparison on the 42-golden benchmark F1, not the 147-bug composite score. 17 unresolved, 4 favor high, 1 favor medium. Unresolved does not establish equivalence.

## 13. 20 more bugs (3:00 to 3:15)

**Cue:** One pair, 20 more bugs

One tested pair. Fable, high reasoning, one prompt: fifty-one bugs. Open-weight G L M Flash, low reasoning, a harness: seventy-one. Twenty more.

*Delivery:* Treat each horizontal row as a complete setup. Upper row first, lower row second, then return to the audience for “Twenty more.” G L M is spaced in the draft to show the spoken load.

*Evidence boundary:* REPORT.md 147-bug primary results: Fable 5.1 vanilla high 51/147, GLM-5.3-Flash metareview low 71/147. Selected configuration comparison, not an isolated model or effort causal effect. GLM ran through hosted inference.

## 14. 1/55 the API cost (3:15 to 3:30)

**Cue:** Same pair, lower API cost

About a dollar thirty versus two point four cents per review. API costs, at study prices. Checking the findings still takes your time.

*Delivery:* Pause after “cents.” The fraction is already on screen. Keep upper and lower configuration identities fixed from the previous slide.

*Evidence boundary:* REPORT.md exact means: Fable vanilla high $1.29594/PR; GLM Flash metareview low $0.02354/PR. Ratio 55.05. Published September 16 list prices applied to metered usage, not actual gateway invoice. Excludes human time and failed-call overhead.

## 15. Nearly twice as fast (3:30 to 3:45)

**Cue:** Same pair, less waiting

Same pair: about two and a half minutes versus eighty seconds, on average. Less waiting. More bugs found. A combination worth testing in your development loop.

*Delivery:* Read the upper configuration first, then the lower one. Rounded spoken durations correspond to 148s and 79s on the slide. Leave room after “Less waiting.”

*Evidence boundary:* REPORT.md exact means: 78.54169 seconds versus 147.69631 seconds per review. Selected configuration comparison includes different model, harness, effort, and provider paths. Not universal speed superiority.

## 16. 59 bugs still missed (3:45 to 4:00)

**Cue:** 59 bugs still missed

Even the highest-recall setup missed fifty-nine verified bugs. A clean review doesn’t prove the code is correct. Useful help. We still have to check.

*Delivery:* Stop looking at the chart after the first sentence. The warning belongs to the audience. Do not call this the previous GLM/Fable pair.

*Evidence boundary:* REPORT.md Opus 5 + Compound Engineering medium: 88/147, the highest recall among complete single configurations. Mean API cost $6.12246. Misses 147-88=59. Union of configurations is a different procedure.

## 17. Before you commit (4:00 to 4:15)

**Cue:** Review before you commit

Review before you commit. Reproduce the failure. Fix it. Run the test. Then review the fix, too. Check the findings yourself. Find bugs before your users do.

*Delivery:* Follow the loop once, then return to the audience. Finding bugs before users is the goal, not a measured production outcome.

*Evidence boundary:* Recommended developer workflow, not a measured autonomous fixing loop. The developer uses the harness for review, reproduces and verifies findings, fixes and tests the code, then re-reviews the changed code. FURTHER-RESEARCH.md treats iterative development-loop outcomes as further work. Local development describes the workflow, not local model inference. Finding bugs before users is a goal, not a production outcome measured by this study.

## 18. Use a harness (4:15 to 4:30)

**Cue:** Give reviewers focused jobs

Use a harness. Give the model focused review jobs and a repeatable process. In this study, that usually found more verified bugs than asking the same model once.

*Delivery:* Keep this as the first clear takeaway. Avoid saying the harness challenges its own conclusions unless the illustrated process actually includes that separate stage.

*Evidence boundary:* Recommendation supported by 39/42 positive matched recall differences. It does not establish that every harness implementation helps every task.

## 19. Use /low effort (4:30 to 4:45)

**Cue:** Start low, try open weights

Start with low reasoning. Try open-weight models. Compare what they catch, what they miss, the cost and the wait. Then choose based on evidence from your code.

*Delivery:* Distinct imperatives. This is a starting recommendation, not a universal ranking or a claim that low beat high in the high-versus-medium comparison.

*Evidence boundary:* Recommendation from the selected GLM Flash metareview low configuration. 71 bugs is total across six PRs; cost and latency are per-review means. Other configurations can have higher recall. Open weights does not imply local inference.

## 20. Follow the evidence (4:45 to 5:00)

**Cue:** Follow the evidence

I started with doubt. Now I have evidence I can check. Demand that from AI advice, including mine. You don’t have to trust the vibes. Follow the evidence. All free, all open source. 

*Delivery:* Finish on "Follow the evidence." The QR is an optional route to the full report; allow the audience to scan without reading the URL aloud.

*Evidence boundary:* Dave's requested conclusion. Typographic close. End on the idea, with no contact, biography, or promotional slide.
