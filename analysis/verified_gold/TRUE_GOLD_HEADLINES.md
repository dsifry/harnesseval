## True-gold headline (deduplicated verified hidden-gold set)

Denominator (the true golden set): **152** = 42 Martian goldens + 110 verified hidden-gold defects. TP counts are per cell over the campaign's 6 PRs; `totals.TP/den` (2789/10246) sums findings across cells and is not the gold-set ratio.

| | cell | recall | **F2′** | adjusted precision (adjP) |
|---|---|---|---|---|
| best harness recall | `claude-opus-5|compound-realistic|medium` | 0.487 | 0.385 | 0.474 |
| **best harness F2′ (our evaluator)** | `glm-5.3-vision-background|metareview-realistic|high` | 0.454 | 0.436 | 0.908 |
| best vanilla recall | `claude-fable-5-1|vanilla-engineered|high` | 0.322 | 0.361 | 0.700 |
| best vanilla F2′ | `claude-fable-5-1|vanilla-engineered|high` | 0.322 | 0.361 | 0.700 |

- **harness ÷ vanilla on F2′: 1.21×**
- peak-recall ratio, harness ÷ vanilla: 1.51×
- (F1′, the equal-weight lens, for reference: 0.94×)
