# October report correction: Codex reasoning tokens

This correction recomputes the metered cost and token figures for every Codex cell
(`gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-6-astra`). It is based on commit `88048a09`, which
contains the code fixes from harnesseval#21, #22 and #23. The stored run summaries in
`runs/` are unchanged.

## The defect

Codex CLI reports `output_tokens` with reasoning tokens already included: its own
`total_tokens` equals `input_tokens + output_tokens`. `from_codex_cli` stored that
`output_tokens` unchanged and also stored `reasoning_output_tokens`, and every consumer
treats the two as separate. The metered-cost formula in report §3.4.1,
`(output + reasoning) · out`, therefore priced Codex reasoning twice, at the output rate
(harnesseval#19, reported by Jesse Robbins).

## Changes

- `from_codex_cli` subtracts reasoning from `output_tokens` (#21). New summaries are
  stamped `usage_convention: 2` (#23).
- Stored summaries are not rewritten. 162 of the 1,562 Codex summaries are pinned by sha256
  in the active readjudication pass. Instead, `harnesseval.usage.corrected_per_model_usage`
  applies the same subtraction when an unstamped summary registered before the fix is read.
  `tools/final_report_extract.py` and `harnesseval/analysis.py` use it (#23).
- `tools/codex_reasoning_correction.py` measures the correction without writing anything:
  1,562 legacy Codex summaries, 1,559 with reasoning, and 2,391,684 double-counted tokens
  removed from `total_tokens`.
- `tokens_in` / `tokens_out` now split per-model usage cleanly (#22). This affects only new
  runs; the report chain derives its token figures from per-model usage, not these fields.
- REPORT.md: the affected rows of Tables T2, T4, T5, T7 and T8 (63 rows) were replaced
  from the regenerated `/tmp/final_report_tables.md`. Two prose figures changed: the T4
  cost-multiple range (0.6×–20× → 0.7×–20×), and vision MRV-low's per-task cost relative
  to Astra vanilla-low (54% → 55%, also in EXECUTIVE_SUMMARY.md). A correction note was
  added to §3.4.1 and to "About this revision". The §5.3 checksum table and
  `analysis/verified_gold/OUTPUT_SHA256SUMS` were updated for the two regenerated artifacts.

## Effect

In `final_report_dataset.json` the run selection is identical in all three run lists
(2,234 selected, 2,416 healthy, 54 legacy). The only field that changes is `out_tok`.
`top6`, `pr_golden` and both coverage tables are byte-equal.

In `final_report_metrics.json` only `matrix`, `pareto`, `token_multiple`, `effort_ladder`,
`cost_structure_ratios` and `recommendation_ratios` change. Every quality section is
unchanged: `true_gold_defects`, `rank_agreement`, `framework_delta`, `monotonicity`,
`selection_effect`, `tier_flash_vs_vision`, the `expanded_gold*` appendices, and
`pareto_frontier` membership.

| Codex cells (27) | change |
|---|---|
| metered cost per run and $/real finding, vanilla | −2.1% to −25.9% |
| metered cost per run and $/real finding, CE | −0.2% to −5.4% |
| metered cost per run and $/real finding, MRV | −0.3% to −3.9% |
| tokens per run | −0.01% to −2.2% |

The largest change is `gpt-5.6-terra · vanilla · high`: $0.275 → $0.204 per run. Vanilla
cells move most because their token bill is mostly fresh input and output; harness cells
are dominated by cached input. On $/real finding, neighboring cells swap rank in 30 places.
High/medium effort cost ratios move by up to 10%, but the T5 ranges quoted in the prose are
unchanged (unresolved pairs 0.96×–3.0×; overall 0.96×–4.2×). GLM-versus-Codex
recommendation ratios move by at most 1.9%. One T4 pair changes interpretation:
Sol · CE · high costs 0.66× [0.46, 1.07] of Sol vanilla-high, so its interval now includes
1×. The old interval, 0.59× [0.42, 0.86], said the harness was measurably cheaper. No prose
relied on that.

## Frozen advisory passes

The frozen pass and policy manifests (`passes/glm_base_claim_v3`, `passes/reuse_v2`,
`scoring_policies/advisory070_penalty080_v1`) pin `analysis/final_report_dataset.json`,
and the active pass and policy also pin `harnesseval/model_router.py`. Both files changed.
The manifests are not edited. Model-calling re-execution (`tools/advisory_timeout.py`,
`tools/advisory_policy_dedup.py`, `tools/advisory_resume.py`) must run from commit
`ca3eed9e`, the last commit whose sources match the active pass and policy. The offline
refresh (`verified_gold_defect_metrics.py`, `final_report_true_gold.py`,
`-m tools.advisory_framework_comparison`) does not check those pins. It was run on the
corrected source and succeeded.

## Validation

- Determinism: the full §5.2 chain (steps 1–5) was run twice in separate clean worktrees,
  both on the pre-correction source and on the corrected source. On the pre-correction
  source both runs reproduced every committed artifact byte-for-byte (clean `git status`,
  no ignored outputs). On the corrected source the two runs were byte-identical to each
  other, including every PNG, SVG, interactive fragment, dashboard and HTML file, and
  `/tmp/final_report_tables.md`.
- `shasum -a 256 -c analysis/verified_gold/OUTPUT_SHA256SUMS` passes for all five artifacts.
- Code: 225 tests pass. Mutation testing of the changed code kills every non-equivalent
  mutant.

This was a recomputation from saved inputs. No model reviews, adjudications or defect tests
were re-run.
