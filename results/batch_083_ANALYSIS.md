# Batch 083 fullmatrix — rolling analysis · 2026-09-06T16:25:34Z

**Batch:** `20260825-batch-083-fullmatrix` · status: **FINISHED/DEAD**
Matrix: **56 (fw × model × effort) combos × 6 PRs = 336 designed cells** (premium models run {low, high} only) · concurrency=3 · mode=cli (OAuth)
Models: claude-opus-5, gpt-5.6-sol, claude-sonnet-5, gpt-5.6-terra · Efforts: low, medium, high, xhigh · Frameworks: vanilla-engineered, metareview-realistic, compound-realistic, superpowers-realistic

## Progress

- Cells finished in stdout log: **0/336** (fail=0)
- Cells registered (effective, deduped): **336/336**
- In-flight right now: **0** cells
- Avg wall per finished cell: **0s** · remaining 336 cells → ETA **~0 min** (0.0h)
- Log tokens (done cells): 0

  `░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░` 0.0%

## Overall (completed cells so far)

- **Recall** 0.440 · **Precision (raw)** 0.142 · **Adjudicated precision** 0.370 · **Incremental recall** 0.767
- **Hidden gold** 3296 (9.8/cell) · **Hallucinations** 2948 (8.8/cell)
- **Tokens** 577,098,192 (1,717,554/cell)
- **Reported $** $483.16 ($1.44/cell) — real Anthropic billing w/ cache; GPT=$0 via OAuth
- **Implied $ (est.)** $510.17 ($1.52/cell) — adds GPT at estimated per-token rates

## Per framework (completed cells)

| framework | n | TP | FP | FN | recall | prec | adj_p | incr_r | hidden | /cell | hal | /cell | tok | rep$ | imp$ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vanilla-engineered | 72 | 244 | 408 | 260 | 0.48 | 0.37 | 0.71 | 0.67 | 277 | 3.8 | 131 | 1.8 | 10,695,155 | $13.79 | $22.16 |
| metareview-realistic | 72 | 277 | 1966 | 227 | 0.55 | 0.12 | 0.29 | 0.85 | 964 | 13.4 | 1002 | 13.9 | 233,013,031 | $163.09 | $169.74 |
| compound-realistic | 96 | 320 | 2545 | 352 | 0.48 | 0.11 | 0.33 | 0.83 | 1431 | 14.9 | 1114 | 11.6 | 285,846,392 | $252.97 | $261.17 |
| superpowers-realistic | 96 | 195 | 1325 | 477 | 0.29 | 0.13 | 0.22 | 0.63 | 624 | 6.5 | 701 | 7.3 | 47,543,614 | $53.31 | $57.11 |

## Per model (completed cells)

| model | n | TP | FP | FN | recall | prec | adj_p | incr_r | hidden | /cell | hal | /cell | tok | rep$ | imp$ | imp$/cell |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `claude-opus-5` | 72 | 342 | 3378 | 162 | 0.68 | 0.09 | 0.24 | 0.93 | 1761 | 24.5 | 1617 | 22.5 | 184,171,655 | $311.94 | $311.94 | $4.33 |
| `gpt-5.6-sol` | 72 | 186 | 799 | 318 | 0.37 | 0.19 | 0.39 | 0.67 | 456 | 6.3 | 343 | 4.8 | 37,693,701 | $0.0000 | $7.94 | $0.1103 |
| `claude-sonnet-5` | 96 | 285 | 1334 | 387 | 0.42 | 0.18 | 0.36 | 0.71 | 646 | 6.7 | 688 | 7.2 | 315,128,318 | $171.22 | $171.22 | $1.78 |
| `gpt-5.6-terra` | 96 | 223 | 733 | 449 | 0.33 | 0.23 | 0.46 | 0.59 | 433 | 4.5 | 300 | 3.1 | 40,104,518 | $0.0000 | $19.06 | $0.1986 |

## Per effort (completed cells)

| effort | n | TP | FP | FN | recall | prec | adj_p | incr_r | hidden | /cell | hal | /cell | tok | rep$ | imp$ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| low | 96 | 287 | 1489 | 385 | 0.43 | 0.16 | 0.38 | 0.73 | 766 | 8.0 | 723 | 7.5 | 90,943,440 | $80.73 | $85.85 |
| medium | 72 | 196 | 1228 | 308 | 0.39 | 0.14 | 0.32 | 0.73 | 631 | 8.8 | 597 | 8.3 | 112,601,422 | $77.83 | $82.89 |
| high | 96 | 329 | 1914 | 343 | 0.49 | 0.15 | 0.41 | 0.80 | 1036 | 10.8 | 878 | 9.1 | 183,141,866 | $171.50 | $179.71 |
| xhigh | 72 | 224 | 1613 | 280 | 0.44 | 0.12 | 0.35 | 0.80 | 863 | 12.0 | 750 | 10.4 | 190,411,464 | $153.10 | $161.72 |

## Per framework × model × effort (completed cells)

| fw | model | effort | n/6 | TP | FN | recall | adj_p | incr_r | hidden | hal | tok | imp$ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vanilla-engineered | `claude-opus-5` | low | 6/6 | 28 | 14 | 0.67 | 0.52 | 0.82 | 36 | 28 | 514,806 | $2.80 |
| vanilla-engineered | `claude-opus-5` | high | 6/6 | 29 | 13 | 0.69 | 0.51 | 0.86 | 53 | 30 | 650,984 | $4.04 |
| vanilla-engineered | `gpt-5.6-sol` | low | 6/6 | 22 | 20 | 0.52 | 0.87 | 0.69 | 23 | 4 | 264,356 | $0.3011 |
| vanilla-engineered | `gpt-5.6-sol` | high | 6/6 | 23 | 19 | 0.55 | 0.89 | 0.67 | 15 | 5 | 3,263,021 | $1.36 |
| vanilla-engineered | `claude-sonnet-5` | low | 6/6 | 18 | 24 | 0.43 | 0.44 | 0.61 | 20 | 21 | 636,607 | $1.22 |
| vanilla-engineered | `claude-sonnet-5` | medium | 6/6 | 19 | 23 | 0.45 | 0.55 | 0.61 | 17 | 14 | 649,849 | $1.32 |
| vanilla-engineered | `claude-sonnet-5` | high | 6/6 | 21 | 21 | 0.50 | 0.82 | 0.67 | 22 | 6 | 706,615 | $1.93 |
| vanilla-engineered | `claude-sonnet-5` | xhigh | 6/6 | 16 | 26 | 0.38 | 0.69 | 0.64 | 31 | 9 | 763,270 | $2.47 |
| vanilla-engineered | `gpt-5.6-terra` | low | 6/6 | 17 | 25 | 0.40 | 0.94 | 0.56 | 15 | 1 | 351,765 | $0.8055 |
| vanilla-engineered | `gpt-5.6-terra` | medium | 6/6 | 14 | 28 | 0.33 | 0.70 | 0.46 | 10 | 5 | 380,270 | $0.8191 |
| vanilla-engineered | `gpt-5.6-terra` | high | 6/6 | 18 | 24 | 0.43 | 0.74 | 0.59 | 16 | 3 | 834,533 | $1.68 |
| vanilla-engineered | `gpt-5.6-terra` | xhigh | 6/6 | 19 | 23 | 0.45 | 0.83 | 0.62 | 19 | 5 | 1,679,079 | $3.40 |
| metareview-realistic | `claude-opus-5` | low | 6/6 | 36 | 6 | 0.86 | 0.16 | 0.97 | 174 | 207 | 20,490,753 | $31.13 |
| metareview-realistic | `claude-opus-5` | high | 6/6 | 33 | 9 | 0.79 | 0.12 | 0.97 | 222 | 241 | 33,283,536 | $56.65 |
| metareview-realistic | `gpt-5.6-sol` | low | 6/6 | 21 | 21 | 0.50 | 0.41 | 0.75 | 43 | 31 | 3,392,404 | $0.5865 |
| metareview-realistic | `gpt-5.6-sol` | high | 6/6 | 27 | 15 | 0.64 | 0.39 | 0.87 | 77 | 49 | 4,739,926 | $0.7808 |
| metareview-realistic | `claude-sonnet-5` | low | 6/6 | 25 | 17 | 0.60 | 0.24 | 0.85 | 75 | 82 | 18,260,842 | $9.10 |
| metareview-realistic | `claude-sonnet-5` | medium | 6/6 | 24 | 18 | 0.57 | 0.19 | 0.84 | 72 | 103 | 36,022,584 | $15.73 |
| metareview-realistic | `claude-sonnet-5` | high | 6/6 | 22 | 20 | 0.52 | 0.25 | 0.83 | 76 | 79 | 42,810,210 | $20.78 |
| metareview-realistic | `claude-sonnet-5` | xhigh | 6/6 | 24 | 18 | 0.57 | 0.20 | 0.87 | 95 | 101 | 55,594,700 | $29.70 |
| metareview-realistic | `gpt-5.6-terra` | low | 6/6 | 13 | 29 | 0.31 | 0.37 | 0.55 | 23 | 23 | 3,893,835 | $1.00 |
| metareview-realistic | `gpt-5.6-terra` | medium | 6/6 | 18 | 24 | 0.43 | 0.43 | 0.63 | 23 | 28 | 4,433,944 | $1.35 |
| metareview-realistic | `gpt-5.6-terra` | high | 6/6 | 17 | 25 | 0.40 | 0.36 | 0.70 | 41 | 30 | 4,791,040 | $1.33 |
| metareview-realistic | `gpt-5.6-terra` | xhigh | 6/6 | 17 | 25 | 0.40 | 0.37 | 0.71 | 43 | 28 | 5,299,257 | $1.61 |
| compound-realistic | `claude-opus-5` | low | 6/6 | 28 | 14 | 0.67 | 0.19 | 0.93 | 145 | 138 | 12,180,770 | $20.01 |
| compound-realistic | `claude-opus-5` | medium | 6/6 | 32 | 10 | 0.76 | 0.20 | 0.96 | 219 | 186 | 24,533,263 | $36.87 |
| compound-realistic | `claude-opus-5` | high | 6/6 | 33 | 9 | 0.79 | 0.21 | 0.97 | 260 | 176 | 34,282,671 | $55.96 |
| compound-realistic | `claude-opus-5` | xhigh | 6/6 | 35 | 7 | 0.83 | 0.13 | 0.98 | 314 | 277 | 39,899,882 | $66.58 |
| compound-realistic | `gpt-5.6-sol` | low | 6/6 | 20 | 22 | 0.48 | 0.44 | 0.78 | 58 | 26 | 3,244,030 | $0.5340 |
| compound-realistic | `gpt-5.6-sol` | medium | 6/6 | 17 | 25 | 0.40 | 0.23 | 0.79 | 76 | 38 | 6,216,556 | $0.9403 |
| compound-realistic | `gpt-5.6-sol` | high | 6/6 | 15 | 27 | 0.36 | 0.35 | 0.67 | 39 | 28 | 6,503,903 | $0.8909 |
| compound-realistic | `gpt-5.6-sol` | xhigh | 6/6 | 19 | 23 | 0.45 | 0.55 | 0.70 | 35 | 19 | 6,010,946 | $0.9472 |
| compound-realistic | `claude-sonnet-5` | low | 6/6 | 8 | 34 | 0.19 | 0.20 | 0.43 | 18 | 22 | 17,283,784 | $9.43 |
| compound-realistic | `claude-sonnet-5` | medium | 6/6 | 14 | 28 | 0.33 | 0.30 | 0.58 | 24 | 49 | 27,059,000 | $13.11 |
| compound-realistic | `claude-sonnet-5` | high | 6/6 | 15 | 27 | 0.36 | 0.37 | 0.57 | 21 | 26 | 33,945,220 | $17.10 |
| compound-realistic | `claude-sonnet-5` | xhigh | 6/6 | 13 | 29 | 0.31 | 0.23 | 0.61 | 32 | 40 | 58,558,648 | $33.91 |
| compound-realistic | `gpt-5.6-terra` | low | 6/6 | 17 | 25 | 0.40 | 0.51 | 0.65 | 30 | 22 | 4,056,250 | $1.06 |
| compound-realistic | `gpt-5.6-terra` | medium | 6/6 | 16 | 26 | 0.38 | 0.48 | 0.70 | 44 | 16 | 3,343,133 | $1.01 |
| compound-realistic | `gpt-5.6-terra` | high | 6/6 | 15 | 27 | 0.36 | 0.51 | 0.67 | 41 | 15 | 4,006,130 | $1.22 |
| compound-realistic | `gpt-5.6-terra` | xhigh | 6/6 | 23 | 19 | 0.55 | 0.41 | 0.84 | 75 | 36 | 4,722,206 | $1.59 |
| superpowers-realistic | `claude-opus-5` | low | 6/6 | 17 | 25 | 0.40 | 0.29 | 0.68 | 37 | 36 | 2,007,558 | $4.79 |
| superpowers-realistic | `claude-opus-5` | medium | 6/6 | 18 | 24 | 0.43 | 0.17 | 0.80 | 78 | 72 | 3,517,572 | $7.66 |
| superpowers-realistic | `claude-opus-5` | high | 6/6 | 25 | 17 | 0.60 | 0.22 | 0.86 | 83 | 105 | 5,872,345 | $11.13 |
| superpowers-realistic | `claude-opus-5` | xhigh | 6/6 | 28 | 14 | 0.67 | 0.22 | 0.92 | 140 | 121 | 6,937,515 | $14.32 |
| superpowers-realistic | `gpt-5.6-sol` | low | 6/6 | 7 | 35 | 0.17 | 0.20 | 0.51 | 30 | 28 | 722,343 | $0.3069 |
| superpowers-realistic | `gpt-5.6-sol` | medium | 6/6 | 7 | 35 | 0.17 | 0.14 | 0.48 | 25 | 42 | 1,074,101 | $0.4067 |
| superpowers-realistic | `gpt-5.6-sol` | high | 6/6 | 7 | 35 | 0.17 | 0.16 | 0.43 | 19 | 34 | 1,045,047 | $0.3892 |
| superpowers-realistic | `gpt-5.6-sol` | xhigh | 6/6 | 1 | 41 | 0.02 | 0.02 | 0.29 | 16 | 39 | 1,217,068 | $0.5022 |
| superpowers-realistic | `claude-sonnet-5` | low | 6/6 | 8 | 34 | 0.19 | 0.15 | 0.49 | 25 | 33 | 3,088,332 | $2.26 |
| superpowers-realistic | `claude-sonnet-5` | medium | 6/6 | 13 | 29 | 0.31 | 0.30 | 0.59 | 29 | 26 | 4,811,285 | $3.13 |
| superpowers-realistic | `claude-sonnet-5` | high | 6/6 | 22 | 20 | 0.52 | 0.46 | 0.75 | 37 | 29 | 5,827,761 | $3.90 |
| superpowers-realistic | `claude-sonnet-5` | xhigh | 6/6 | 23 | 19 | 0.55 | 0.42 | 0.80 | 52 | 48 | 9,109,611 | $6.13 |
| superpowers-realistic | `gpt-5.6-terra` | low | 6/6 | 2 | 40 | 0.05 | 0.11 | 0.29 | 14 | 21 | 555,005 | $0.5162 |
| superpowers-realistic | `gpt-5.6-terra` | medium | 6/6 | 4 | 38 | 0.10 | 0.21 | 0.32 | 14 | 18 | 559,865 | $0.5339 |
| superpowers-realistic | `gpt-5.6-terra` | high | 6/6 | 7 | 35 | 0.17 | 0.25 | 0.38 | 14 | 22 | 578,924 | $0.5651 |
| superpowers-realistic | `gpt-5.6-terra` | xhigh | 6/6 | 6 | 36 | 0.14 | 0.12 | 0.32 | 11 | 27 | 619,282 | $0.5708 |

## Spend breakdown by provider model (per_model_usage, completed cells)

| provider model | n_cells | input tok | cache_read | cache_write | output tok | reasoning | reported $ | implied $ |
|---|---|---|---|---|---|---|---|---|
| claude-opus-5 Anthropic (real) | 72 | 10,314 | 162,812,924 | 16,282,673 | 4,719,425 | 0 | $311.59 | $311.59 |
| claude-sonnet-5 Anthropic (real) | 96 | 13,506 | 290,088,982 | 18,389,033 | 5,961,800 | 0 | $170.52 | $170.52 |
| claude-haiku-4-5-20251001 Anthropic (real) | 168 | 1,016,847 | 0 | 0 | 4,469 | 0 | $1.05 | $1.05 |
| gpt-5.6-terra GPT (est.) | 96 | 3,235,157 | 36,320,512 | 0 | 377,843 | 171,006 | $0.0000 | $19.06 |
| gpt-5.6-sol GPT (est.) | 72 | 3,176,242 | 34,120,320 | 0 | 309,581 | 87,558 | $0.0000 | $7.94 |
| **TOTAL** | — | — | — | — | — | — | **$483.16** | **$510.17** |

> **Reported $** = real Anthropic `cost_usd` (cache-discounted billing); GPT models report **$0** via OAuth/subscription so reported $ **understates** true cost. **Implied $** adds GPT at *estimated* per-token rates (pinned 2026-08-22, **unverified**): gpt-5.6-sol in $1.25/out $10.0 per 1M; gpt-5.6-terra in $2.5/out $20.0 per 1M; gpt-5.2 in $1.25/out $10.0 per 1M; gpt-6-astra in $10.0/out $12.5 per 1M.

## Per-PR coverage (completed cells)

| PR | label | cells done | TP | FN | FP | hidden | hal | recall | tok | imp$ |
|---|---|---|---|---|---|---|---|---|---|---|
| 11059 | calcom/cal.com#11059 | 56/64 | 283 | 221 | 1039 | 452 | 587 | 0.56 | 108,753,936 | $91.90 |
| 4 | discourse-graphite#4 | 56/64 | 132 | 316 | 1457 | 866 | 591 | 0.29 | 74,956,968 | $76.31 |
| 10 | discourse-graphite#10 | 56/64 | 179 | 213 | 733 | 415 | 318 | 0.46 | 75,303,147 | $78.86 |
| 14740 | calcom/cal.com#14740 | 56/64 | 145 | 191 | 882 | 544 | 338 | 0.43 | 75,160,230 | $69.40 |
| 8 | discourse-graphite#8 | 56/64 | 164 | 172 | 1037 | 543 | 494 | 0.49 | 100,246,803 | $85.05 |
| 10967 | calcom/cal.com#10967 | 56/64 | 133 | 203 | 1096 | 476 | 620 | 0.40 | 142,677,108 | $108.65 |

## Cross-batch comparison (matched cells on framework×model×effort×PR)

Each earlier batch is compared to 083 **only on cells present in both** (matched keys). Deltas are 083 − earlier; positive recall Δ = 083 improved. `vanilla-engineered` is the control arm — if 083 vanilla recall ≈ earlier vanilla recall on matched cells, the other frameworks are comparable.

| earlier batch | matched | earlier recall | 083 recall | Δrec | earlier adj_p | 083 adj_p | Δadj_p | earlier hidden/cell | 083 hidden/cell | earlier hal/cell | 083 hal/cell | earlier imp$/cell | 083 imp$/cell |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 082-v2 (48c, direct predecessor) | 0 | — | — | — | — | — | — | — | — | — | — | — | — |
| 0824-1019 (144c) | 46 | 0.548 | 0.452 | -0.096 | 0.242 | 0.209 | -0.033 | 12.0 | 17.4 | 12.7 | 15.7 | $3.16 | $2.32 |
| 0824-0728 (144c) | 13 | 0.473 | 0.455 | -0.018 | 0.269 | 0.215 | -0.054 | 8.5 | 18.3 | 9.0 | 16.8 | $2.36 | $1.89 |

## Spend extrapolation (linear, to the full 336-cell designed matrix)

- Completed 336/336 cells (100.0%). At current per-cell rates:
- Projected **tokens** (all 384): 577,098,192
- Projected **reported $** (all 384): $483.16 — Anthropic real billing; GPT $0
- Projected **implied $** (all 384): $510.17 — incl. GPT at estimated rates
- Spend rate so far: $510.17 implied over 336 cells

> ⚠ Extrapolation is linear and early (N small). Frameworks with heavy orchestrator+cache (metareview-realistic, compound-realistic on claude-opus-5) dominate cost; if those cells are under-represented in the completed set, the projection underestimates; if over-represented, it overestimates.

## Notes & anomalies

- 🔧 241 cell(s) originally errored, now FILLED IN (latest wins).
- 💸 highest-token cells so far: claude-sonnet-5/xhigh/compound-realistic 21,083,894tok $9.41, claude-sonnet-5/high/compound-realistic 12,261,047tok $5.47, claude-opus-5/xhigh/compound-realistic 11,906,084tok $13.82

---
_Generated by `bin/analyze_batch_083.py` at 2026-09-06T16:25:34Z._