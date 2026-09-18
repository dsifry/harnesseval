# Verified hidden gold — evidence bundles

Each bug has a browsable directory and an attachable tarball, per PR:

- unpacked bundle: `analysis/verified_gold/<pr>/<bug-id>-<slug>/` (meta.json, test.patch, fix.patch, logs/, REPRO.md)
- attachable tarball: `analysis/verified_gold/bundles/<pr>/<bug-id>-<slug>.tar.gz` (+ `.sha256`)
- per-PR bundle: `analysis/verified_gold/bundles/verified_gold_<pr>.tar.gz` (all bugs + MANIFEST + SUMMARY)
- roll-up: `analysis/verified_gold/bundles/verified_gold_all.tar.gz`

Every attempted candidate produces a bundle whatever the verdict; `not_a_bug` and
`inconclusive_env` are the demotion-review queue (`DEMOTION_REVIEW.md`).

Generated 2026-09-18T04:41:58Z · verdicts: {'unresolved_file': 32, 'confirmed_regression': 11, 'behavior_change_not_regression': 90, 'defect_present_before_pr': 46, 'inconclusive_env': 24, 'static_text_test': 1, 'not_a_bug': 2, 'golden_duplicate': 1, 'base_not_comparable': 4, 'test_quality_verified': 1}

## PR 10 — 32 candidates · {'unresolved_file': 5, 'confirmed_regression': 2, 'behavior_change_not_regression': 16, 'defect_present_before_pr': 9}
- per-bug tarballs: `bundles/10/`
- PR bundle: `bundles/verified_gold_10.tar.gz` · sha256 `f436a7a130cd3974…` · 134 KiB
- table: `bundles/10/SUMMARY.md` · machine index: `bundles/10/MANIFEST.json`

## PR 10967 — 31 candidates · {'inconclusive_env': 14, 'static_text_test': 1, 'confirmed_regression': 5, 'defect_present_before_pr': 9, 'not_a_bug': 1, 'unresolved_file': 1}
- per-bug tarballs: `bundles/10967/`
- PR bundle: `bundles/verified_gold_10967.tar.gz` · sha256 `c774887896afd69b…` · 172 KiB
- table: `bundles/10967/SUMMARY.md` · machine index: `bundles/10967/MANIFEST.json`

## PR 11059 — 25 candidates · {'golden_duplicate': 1, 'behavior_change_not_regression': 15, 'defect_present_before_pr': 2, 'unresolved_file': 7}
- per-bug tarballs: `bundles/11059/`
- PR bundle: `bundles/verified_gold_11059.tar.gz` · sha256 `51900d97f98d5a7e…` · 117 KiB
- table: `bundles/11059/SUMMARY.md` · machine index: `bundles/11059/MANIFEST.json`

## PR 14740 — 33 candidates · {'inconclusive_env': 1, 'unresolved_file': 7, 'behavior_change_not_regression': 16, 'base_not_comparable': 4, 'not_a_bug': 1, 'defect_present_before_pr': 4}
- per-bug tarballs: `bundles/14740/`
- PR bundle: `bundles/verified_gold_14740.tar.gz` · sha256 `776e5b5ff93ffa22…` · 156 KiB
- table: `bundles/14740/SUMMARY.md` · machine index: `bundles/14740/MANIFEST.json`

## PR 4 — 70 candidates · {'behavior_change_not_regression': 38, 'confirmed_regression': 3, 'inconclusive_env': 8, 'defect_present_before_pr': 10, 'unresolved_file': 10, 'test_quality_verified': 1}
- per-bug tarballs: `bundles/4/`
- PR bundle: `bundles/verified_gold_4.tar.gz` · sha256 `904ec024d805582a…` · 288 KiB
- table: `bundles/4/SUMMARY.md` · machine index: `bundles/4/MANIFEST.json`

## PR 8 — 21 candidates · {'confirmed_regression': 1, 'defect_present_before_pr': 12, 'behavior_change_not_regression': 5, 'unresolved_file': 2, 'inconclusive_env': 1}
- per-bug tarballs: `bundles/8/`
- PR bundle: `bundles/verified_gold_8.tar.gz` · sha256 `d29b0ccbb2bb4157…` · 89 KiB
- table: `bundles/8/SUMMARY.md` · machine index: `bundles/8/MANIFEST.json`

## Roll-up
- `bundles/verified_gold_all.tar.gz` · sha256 `d1250858959723db…` · 958 KiB

