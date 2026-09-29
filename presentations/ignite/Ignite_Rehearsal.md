# Vibes vs. Evidence: rehearsal draft

Dave Sifry. Exactly 20 slides, 15 seconds each, 5 minutes total. Widescreen 16:9. No title, biography, or contact slide.

This is a practice aid, not something to read on stage. Learn the point and use each slide as the cue. The draft is 620 words. It has not yet been tested in an aloud rehearsal.

The primary research is the [corrected report](https://github.com/dsifry/harnesseval/blob/8f634b68664751527a9ad0123d1a082dd70a0931/REPORT.md). Model comparisons are specific configurations; they do not establish a universal ordering.

## 1. I thought it was me. (0:00 to 0:15)

**Cue:** Everybody else seemed to have it figured out.

Everybody seemed to have AI figured out. My friends had better prompts. Vendors had better tools. And somehow, all that confidence was making me less confident. What was I missing?

*Evidence boundary:* Proposed first-person wording based on Dave's account of his motivation, supplied in this conversation. Typographic opening; no staged portrait or claim about a photographed event.

## 2. Is it me? / What works? (0:15 to 0:30)

**Cue:** Change the question.

Buy the course. Comment ‘AI agents.’ Get the perfect system. I was comparing myself to everybody else’s claims. So I changed the question: what actually works, when we compare it fairly?

*Evidence boundary:* Dave's account. The wording is a general illustration of the pattern he described, not an attributed quotation from an identified person.

## 3. 2,416 reviews (0:30 to 0:45)

**Cue:** The promise: I did the experiment.

So I ran 2,416 AI code reviews: eight models, three review approaches, three reasoning levels. I compared them systematically against a known benchmark, using the same code and verified bugs as the answer key.

*Evidence boundary:* REPORT.md, campaign overview and §2.2. 2,416 healthy runs across the campaign, not 2,416 independent pull requests. The planned matrix has 72 configurations; 66 have complete coverage of the six primary PRs. Primary analysis selects one run per configuration per PR; it does not measure repeat-run variance. The original benchmark and executed hidden-defect validation supply distinct parts of the answer key.

## 4. 42 known bugs (0:45 to 1:00)

**Cue:** Start with the answer key.

For the deep comparison, I used six difficult pull requests from two codebases. The benchmark listed forty-two bugs. That gave me an answer key. Except the answer key was incomplete.

*Evidence boundary:* REPORT.md §§2.2 and 3.1. Six severity-selected PRs. Forty-two original benchmark goldens.

## 5. 105 more (1:00 to 1:15)

**Cue:** The first surprise. These survived testing.

The reviews surfaced another hundred and five verified defects. Each had a test that failed on the original code and passed with its fix. That brought the total to 147.

*Evidence boundary:* REPORT.md corrected hidden-defect audit. 105 retained hidden defects plus 42 benchmark goldens. Audit removed unsupported claims and duplicates. The universe is campaign-discovered and not exhaustive.

## 6. Same model. Better process. (1:15 to 1:30)

**Cue:** The harness gives reviewers separate jobs.

One prompt gives you one review. A harness runs checks, assigns focused reviews in parallel, and combines the findings. Same model, different review jobs. I maintain metareview, one of the harnesses tested.

*Evidence boundary:* Illustrative architecture based on REPORT.md §2.2 and the pinned metareview_realistic.py adapter. Security, Architecture and Testing-quality are examples of actual reviewer lenses, not the full roster. The adapter runs its deterministic command and context scaffold before dispatching reviewers, then combines per-lens outputs. The report says eight lenses and synthesis; the pinned CLI prompt says nine and explicitly concatenates the findings. This diagram deliberately does not assert an exact lens count or a separate judgment step. No automatic fixing is depicted. The evaluator and its ground-truth adjudication are separate from the review harness.

## 7. 39 of 42 (1:30 to 1:45)

**Cue:** The workflow result.

In thirty-nine of forty-two matched comparisons, the harness found more verified bugs. Same model. Same reasoning setting. The review process mattered. This was something we could measure.

*Evidence boundary:* REPORT.md matched true-gold recall comparison. Seven models, three efforts, two harness versus vanilla pairs. Observed direction, not 39 individually statistically significant effects.

## 8. 10× the tokens (1:45 to 2:00)

**Cue:** More passes aren't free.

There’s a catch: those harnesses used about ten times the tokens, at the median. More passes do more work. So the next question was whether we needed an expensive model doing all that work.

*Evidence boundary:* REPORT.md median token multiple 10.1 across 42 matched comparisons. Token consumption is distinct from dollar cost.

## 9. More thinking? (2:00 to 2:15)

**Cue:** Question the expensive default.

And did we really need to crank the reasoning setting up? It’s an easy assumption: harder thinking must produce better reviews. I tested low, medium, and high instead of assuming the answer.

*Evidence boundary:* REPORT.md effort sweep. Only low, medium, high were tested. Generated rotary-control illustration is a metaphor, not a real product control.

## 10. Often, no clear gain (2:15 to 2:30)

**Cue:** Unresolved means unresolved.

On the original benchmark score, seventeen of twenty-two high-versus-medium comparisons showed no statistically resolved difference. Four favored high; one favored medium. Higher effort wasn’t a dependable shortcut to a better review.

*Evidence boundary:* REPORT.md effort comparison on the 42-golden benchmark F1, not the 147-bug composite score. 17 unresolved, 4 favor high, 1 favor medium. Unresolved does not establish equivalence.

## 11. This setup found more. (2:30 to 2:45)

**Cue:** Introduce this exact pair once.

Here’s one useful comparison. Fable at high effort, with one prompt, found fifty-one bugs. Open-weight GLM Flash, at low effort, inside a harness, found seventy-one. Twenty more bugs.

*Evidence boundary:* REPORT.md 147-bug primary results: Fable 5.1 vanilla high 51/147, GLM-5.3-Flash metareview low 71/147. Selected configuration comparison, not an isolated model or effort causal effect. GLM ran through hosted inference.

## 12. 1/55 the API cost (2:45 to 3:00)

**Cue:** Same pair. Let the price land.

That same comparison cost about a dollar thirty per review versus two point four cents. About one fifty-fifth the API cost. That’s metered API cost, using published prices. Your time checking the findings still counts.

*Evidence boundary:* REPORT.md exact means: Fable vanilla high $1.29594/PR; GLM Flash metareview low $0.02354/PR. Ratio 55.05. Published September 16 list prices applied to metered usage, not actual gateway invoice. Excludes human time and failed-call overhead.

## 13. Nearly twice as fast (3:00 to 3:15)

**Cue:** Same pair. This fits into a workflow.

And it finished in seventy-nine seconds instead of a hundred and forty-eight, on average. More bugs found, less API cost, less waiting. That makes this combination worth testing in an everyday development workflow.

*Evidence boundary:* REPORT.md exact means: 78.54169 seconds versus 147.69631 seconds per review. Selected configuration comparison includes different model, harness, effort, and provider paths. Not universal speed superiority.

## 14. Even the best missed 59 (3:15 to 3:30)

**Cue:** Useful review still needs judgment.

It still isn’t magic. The highest-recall configuration found eighty-eight of the 147 bugs. It missed fifty-nine. These tools can uncover real defects, but a clean review is never a guarantee that your code is correct.

*Evidence boundary:* REPORT.md Opus 5 + Compound Engineering medium: 88/147, the highest recall among complete single configurations. Mean API cost $6.12246. Misses 147-88=59. Union of configurations is a different procedure.

## 15. 50 PRs. Five codebases. (3:30 to 3:45)

**Cue:** The full campaign, then the next step.

The full campaign covered fifty pull requests across five codebases: 2,416 healthy reviews. The detailed 147-bug comparison used six PRs.

*Evidence boundary:* REPORT.md campaign scope: 2,416 healthy runs across a public 50-PR benchmark spanning five codebases. The detailed 147-bug analysis uses six severity-selected PRs from two codebases. Whole-campaign breadth does not extend the 147-bug results to all 50 PRs. Coverage is incomplete for some configurations.

## 16. Find bugs. Before users do. (3:45 to 4:00)

**Cue:** Make review part of writing the code.

Put review into your development loop. Before you commit, have a harness inspect your changes. The goal is to find defects while the code is fresh, and you can reproduce and fix them.

*Evidence boundary:* Practical recommendation informed by measured review cost and latency. The headline is an imperative goal, not a claimed production outcome. Local development describes where review enters the workflow; GLM inference was hosted. The study did not measure production defect reduction.

## 17. Review. Reproduce. Fix. Test. Repeat. (4:00 to 4:15)

**Cue:** A finding becomes evidence when you can check it.

When a review flags something, reproduce the failure. Fix it. Run the test. Then review the change again, including the fix. You stay responsible for checking the findings. The harness makes review repeatable.

*Evidence boundary:* Recommended developer workflow, not a measured autonomous fixing loop. The developer uses the harness for review, reproduces and verifies findings, fixes and tests the code, then re-reviews the changed code. FURTHER-RESEARCH.md treats iterative development-loop outcomes as further work.

## 18. Use a harness (4:15 to 4:30)

**Cue:** First takeaway: process.

My first takeaway: use a harness. Give the review a repeatable process, multiple passes, and ways to challenge its own conclusions. A single beautiful prompt leaves too much riding on a single pass.

*Evidence boundary:* Recommendation supported by 39/42 positive matched recall differences. It does not establish that every harness implementation helps every task.

## 19. Start low. Try open weights. (4:30 to 4:45)

**Cue:** Second takeaway: test affordable defaults.

Start with low reasoning and test open-weight models. The most expensive option doesn’t have to be your default. Compare what each setup catches, what it misses, and what the review costs.

*Evidence boundary:* Recommendation from the selected GLM Flash metareview low configuration. 71 bugs is total across six PRs; cost and latency are per-review means. Other configurations can have higher recall. Open weights does not imply local inference.

## 20. Follow the evidence (4:45 to 5:00)

**Cue:** Land the final line, then stop.

I started with doubt. Now I have evidence I can check. Demand that from AI advice, including mine. You don’t have to trust the vibes. Follow the evidence.

*Evidence boundary:* Dave's requested conclusion. Typographic close. End on the idea, with no contact, biography, or promotional slide.

## Rehearsal

Run the deck continuously at 15 seconds per slide. Do not restart after a stumble. Jump to the next slide’s cue. In particular, practice a late start after the joke on slide 2, and allow the price on slide 12 to land.

If a passage repeatedly overruns, cut a sentence before increasing speed. The comparison at slides 11–13 keeps the configurations in the same positions and changes just the metric. Slides 15 and 18 are recovery points. Finish the final line before the last slide’s fifteen seconds expire.

The final local-development recommendation is a workflow to try. This study measured review findings, API costs, and latency; it did not measure long-term production defect reduction or an automated fix-loop outcome.
