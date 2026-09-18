## True-gold headline (deduplicated verified hidden-gold set)

Denominator (the true golden set): **152** = 42 Martian goldens + 110 verified hidden-gold defects. TP counts are per cell over the campaign's 6 PRs; `totals.TP/den` (2789/10246) sums findings across cells and is not the gold-set ratio.

| | cell | recall | F1′ | adjusted precision |
|---|---|---|---|---|
| best harness recall | `claude-opus-5|compound-realistic|medium` | 0.487 | 0.292 | 0.474 |
| best harness F1′ | `gpt-6-astra|metareview-realistic|high` | 0.289 | 0.415 | 0.846 |
| best vanilla recall | `claude-fable-5-1|vanilla-engineered|high` | 0.322 | 0.441 | 0.700 |
| best vanilla F1′ | `claude-fable-5-1|vanilla-engineered|high` | 0.322 | 0.441 | 0.700 |

- peak-recall ratio, harness ÷ vanilla: **1.51×**
- best-F1′ ratio, harness ÷ vanilla: **0.94×** (vanilla ahead)
