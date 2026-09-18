# Finding -> defect assignment

Every finding in every verified bundle is considered. Multi-defect bundles are judged in 50-finding calls (the pre-2026-09-18 version dropped texts past the first 60); findings that describe no listed defect are recorded as `null` and skipped by the scorer, never silently dropped. Low word-overlap assignments are re-checked by a verification judge pass.

Judge calls: 29 assignment + 1 verification (unparseable-after-retry chunks: 0).

Findings considered: 2923; mapped: 2852; null (no clear match): 71.

Verification corrections: 0 (see DEFECT_ASSIGN_AUDIT.json).

| PR | considered | mapped | null |
|---|---|---|---|
| 10 | 619 | 600 | 19 |
| 10967 | 139 | 138 | 1 |
| 11059 | 311 | 289 | 22 |
| 14740 | 511 | 511 | 0 |
| 4 | 987 | 958 | 29 |
| 8 | 356 | 356 | 0 |

Per-bundle detail (chunks, nulls, suspects, corrections): DEFECT_ASSIGN_AUDIT.json

Note: 73 of the 2,852 mapped findings are assigned to withdrawn- or duplicate-tier defect ids
(4-D04: 50, 4-D29: 12, 11059-D14: 9, 11059-D28: 1, 11059-D32: 1) — kept as historical record; the
scorer filters these tiers, so they are effectively nulls for all published metrics (effective
mapped count for scoring: 2,779).

