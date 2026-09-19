## True-gold headline (deduplicated verified hidden-gold set)

Denominator (the true golden set): **147** = 42 Martian goldens + 105 verified hidden-gold defects. TP counts are per cell over the campaign's 6 PRs; `totals.TP/den` (3124/9914) sums findings across cells and is not the gold-set ratio.

| | cell | recall | **F2′** | adjusted precision (adjP) |
|---|---|---|---|---|
| best harness recall | `claude-opus-5|compound-realistic|medium` | 0.599 | 0.641 | 0.518 |
| **best harness F2′ (bug quality + advisory credit)** | `claude-opus-5|compound-realistic|medium` | 0.599 | 0.641 | 0.518 |
| best vanilla recall | `claude-fable-5-1|vanilla-engineered|medium` | 0.367 | 0.427 | 0.701 |
| best vanilla F2′ | `claude-fable-5-1|vanilla-engineered|medium` | 0.367 | 0.427 | 0.701 |

- **harness ÷ vanilla on F2′: 1.50×**
- peak-recall ratio, harness ÷ vanilla: 1.63×
- (F1′, the equal-weight lens, for reference: 0.98×)

**Partial-coverage cells** (1–2 PRs only; drawn with open markers in the figures and never cited as a best cell):
`fable CE high` (1 PR), `fable CE low` (2 PR), `fable CE medium` (1 PR), `fable MRV high` (1 PR), `fable MRV low` (1 PR), `fable MRV medium` (1 PR).
