# Scientific recheck of rebuilt candidate

**Disposition: PASS. No material factual errors or misleading scientific implications found in the reviewed candidate.**

Reviewed every rendered slide individually (`previews/slide-01.png` through `slide-20.png`), all 20 spoken passages and source notes in `story.json`, and the chart/diagram values and axes in `build.mjs`. This is a content and visual-claim review, not certification of native Keynote rendering, automatic timing, aloud delivery, or fresh execution of archived defect tests.

## Resolved findings

- Slide 5 now attributes the 105 additional defects to the audit rather than saying all were found by AI reviews. This fixes the 10967-D05 exception.
- Campaign breadth appears on slide 3. Slide 4 immediately scopes the detailed comparison to six severity-selected PRs from two codebases. The presentation no longer gives late campaign breadth a chance to imply that all 147-bug results generalize across 50 PRs.
- Slide 10 explicitly labels the 17 cases “Unresolved.” Speech says inconclusive does not mean equal. The original benchmark F1 lens remains visible.
- Slides 11–13 preserve the complete configuration identities in fixed rows. “One tested pair” and “same pair” prevent the economic comparison from being presented as an isolated model or reasoning effect.
- Slide 15 shows the retained 4-D14 archived result as an isolated reproduction. The script and notes do not claim full Rails integration, a newly introduced regression, or automatic fixing by the benchmarked review harness.
- Slide 18 uses focused review jobs and repeatable process. It no longer implies a separately measured self-verification stage.

## Data and encoding checks

- Slides 4 and 5 encode 42 original bugs and 105 additional verified defects, totaling 147.
- Slide 7 encodes 39 positive point-estimate comparisons and three without a recall increase. The script says “found more,” not “39 significant wins.”
- Slide 8 rounds median 10.1× token overhead to approximately 10×, with the median specified.
- Slide 10 encodes 17, 4 and 1 with common zero-based scaling.
- Slide 11 encodes 51 versus 71 verified bugs with a common zero-based scale. The caption states the six-PR/147-bug denominator.
- Slide 12 encodes $1.29594 versus $0.02354 mean API cost per review. Its 1/55 headline and rounded $1.30/$0.024 labels are consistent. Study list prices are visible and human checking time is acknowledged.
- Slide 13 encodes 147.69631 versus 78.54169 seconds with a common zero-based scale. 148s/79s labels, “nearly twice,” and spoken approximately two-and-a-half minutes/eighty seconds are consistent.
- Slide 14 encodes 88 found and 59 missed, with hollow markers making the misses distinct. “Highest recall” avoids attributing those counts to the preceding selected pair.

The values agree with `REPORT.md` and `analysis/verified_gold/DEFECT_METRICS.json` / `analysis/final_report_metrics.json` reviewed in the first pass. Exact source lines and specimen provenance remain in `science-review.md`.

## Conclusion and scientific tone

Slides 18–20 preserve Dave’s practical enthusiasm without changing an empirical result into a universal guarantee. “Use a harness” is immediately grounded in “In this study.” “Start low. Try open weights” is a starting recommendation, followed by testing on the audience’s own code. This is stronger and more defensible than “you never need high reasoning” or “open weights are always better.” Keep the current wording.

Slides 16–17 correctly present a recommended development loop rather than a measured production outcome. The slide 15 specimen supports the idea of checking evidence while keeping the evaluator separate from the harness. The final invitation to demand evidence “including mine” is scientifically appropriate and gives the talk confidence without overclaiming.

No additional scientific correction is required before native verification. Preserve these distinctions during final editing; an aesthetic edit does not need another science review unless it changes a claim, qualifier, denominator, diagram meaning or configuration label.
