# Verified hidden gold — evidence bundles

Each bug has a browsable directory and an attachable tarball, per PR:

- unpacked bundle: `analysis/verified_gold/<pr>/<bug-id>-<slug>/` (meta.json, test.patch, fix.patch, logs/, REPRO.md)
- attachable tarball: `analysis/verified_gold/bundles/<pr>/<bug-id>-<slug>.tar.gz` (+ `.sha256`)
- per-PR bundle: `analysis/verified_gold/bundles/verified_gold_<pr>.tar.gz` (all bugs + MANIFEST + SUMMARY)
- roll-up: `analysis/verified_gold/bundles/verified_gold_all.tar.gz`

Every attempted candidate produces a bundle whatever the verdict; `not_a_bug` and
`inconclusive_env` are the demotion-review queue (`DEMOTION_REVIEW.md`).

Generated 2026-09-18T00:07:15Z · verdicts: {'inconclusive_env': 37, 'static_text_test': 1, 'confirmed_regression': 7, 'defect_present_before_pr': 19, 'not_a_bug': 1, 'unresolved_file': 23, 'behavior_change_not_regression': 61}

## PR 10967 — 28 candidates · {'inconclusive_env': 16, 'static_text_test': 1, 'confirmed_regression': 4, 'defect_present_before_pr': 5, 'not_a_bug': 1, 'unresolved_file': 1}
- per-bug tarballs: `bundles/10967/`
- PR bundle: `bundles/verified_gold_10967.tar.gz` · sha256 `0217d71cb702d38b…` · 148 KiB
- table: `bundles/10967/SUMMARY.md` · machine index: `bundles/10967/MANIFEST.json`

## PR 11059 — 23 candidates · {'behavior_change_not_regression': 14, 'defect_present_before_pr': 2, 'unresolved_file': 7}
- per-bug tarballs: `bundles/11059/`
- PR bundle: `bundles/verified_gold_11059.tar.gz` · sha256 `8b752fdf02a592f8…` · 107 KiB
- table: `bundles/11059/SUMMARY.md` · machine index: `bundles/11059/MANIFEST.json`

## PR 14740 — 33 candidates · {'inconclusive_env': 6, 'unresolved_file': 7, 'behavior_change_not_regression': 14, 'defect_present_before_pr': 6}
- per-bug tarballs: `bundles/14740/`
- PR bundle: `bundles/verified_gold_14740.tar.gz` · sha256 `1f149ac0110caedf…` · 152 KiB
- table: `bundles/14740/SUMMARY.md` · machine index: `bundles/14740/MANIFEST.json`

## PR 4 — 65 candidates · {'behavior_change_not_regression': 33, 'confirmed_regression': 3, 'inconclusive_env': 15, 'defect_present_before_pr': 6, 'unresolved_file': 8}
- per-bug tarballs: `bundles/4/`
- PR bundle: `bundles/verified_gold_4.tar.gz` · sha256 `35801bcbfeed1b77…` · 265 KiB
- table: `bundles/4/SUMMARY.md` · machine index: `bundles/4/MANIFEST.json`

## Roll-up
- `bundles/verified_gold_all.tar.gz` · sha256 `d982e91b0cdc32ec…` · 671 KiB

