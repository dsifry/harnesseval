# Verified hidden gold — evidence bundles

Each bug has a browsable directory and an attachable tarball, per PR:

- unpacked bundle: `analysis/verified_gold/<pr>/<bug-id>-<slug>/` (meta.json, test.patch, fix.patch, logs/, REPRO.md)
- attachable tarball: `analysis/verified_gold/bundles/<pr>/<bug-id>-<slug>.tar.gz` (+ `.sha256`)
- per-PR bundle: `analysis/verified_gold/bundles/verified_gold_<pr>.tar.gz` (all bugs + MANIFEST + SUMMARY)
- roll-up: `analysis/verified_gold/bundles/verified_gold_all.tar.gz`

Every attempted candidate produces a bundle whatever the verdict; `not_a_bug` and
`inconclusive_env` are the demotion-review queue (`DEMOTION_REVIEW.md`).

Generated 2026-09-17T20:26:08Z · verdicts: {'behavior_change_not_regression': 2}

## PR 11059 — 2 candidates · {'behavior_change_not_regression': 2}
- per-bug tarballs: `bundles/11059/`
- PR bundle: `bundles/verified_gold_11059.tar.gz` · sha256 `0badf7f7ff662125…` · 17 KiB
- table: `bundles/11059/SUMMARY.md` · machine index: `bundles/11059/MANIFEST.json`

## Roll-up
- `bundles/verified_gold_all.tar.gz` · sha256 `0badf7f7ff662125…` · 17 KiB

