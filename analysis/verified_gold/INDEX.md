# Verified hidden gold — evidence bundles

Each bug has a browsable directory and an attachable tarball, per PR:

- unpacked bundle: `analysis/verified_gold/<pr>/<bug-id>-<slug>/` (meta.json, test.patch, fix.patch, logs/, REPRO.md)
- attachable tarball: `analysis/verified_gold/bundles/<pr>/<bug-id>-<slug>.tar.gz` (+ `.sha256`)
- per-PR bundle: `analysis/verified_gold/bundles/verified_gold_<pr>.tar.gz` (all bugs + MANIFEST + SUMMARY)
- roll-up: `analysis/verified_gold/bundles/verified_gold_all.tar.gz`

Every attempted candidate produces a bundle whatever the verdict; `not_a_bug` and
`inconclusive_env` are the demotion-review queue (`DEMOTION_REVIEW.md`).

Generated 2026-09-18T04:09:58Z · verdicts: {'unresolved_file': 32, 'confirmed_regression': 10, 'behavior_change_not_regression': 90, 'defect_present_before_pr': 46, 'inconclusive_env': 24, 'static_text_test': 1, 'not_a_bug': 2, 'golden_duplicate': 1, 'base_not_comparable': 4, 'not_a_bug_unconfirmed': 2}

## PR 10 — 32 candidates · {'unresolved_file': 5, 'confirmed_regression': 2, 'behavior_change_not_regression': 16, 'defect_present_before_pr': 9}
- per-bug tarballs: `bundles/10/`
- PR bundle: `bundles/verified_gold_10.tar.gz` · sha256 `e9d519704156f14d…` · 133 KiB
- table: `bundles/10/SUMMARY.md` · machine index: `bundles/10/MANIFEST.json`

## PR 10967 — 31 candidates · {'inconclusive_env': 14, 'static_text_test': 1, 'confirmed_regression': 5, 'defect_present_before_pr': 9, 'not_a_bug': 1, 'unresolved_file': 1}
- per-bug tarballs: `bundles/10967/`
- PR bundle: `bundles/verified_gold_10967.tar.gz` · sha256 `4e5a61cd5f1e40be…` · 172 KiB
- table: `bundles/10967/SUMMARY.md` · machine index: `bundles/10967/MANIFEST.json`

## PR 11059 — 25 candidates · {'golden_duplicate': 1, 'behavior_change_not_regression': 15, 'defect_present_before_pr': 2, 'unresolved_file': 7}
- per-bug tarballs: `bundles/11059/`
- PR bundle: `bundles/verified_gold_11059.tar.gz` · sha256 `6c2210aed2326137…` · 115 KiB
- table: `bundles/11059/SUMMARY.md` · machine index: `bundles/11059/MANIFEST.json`

## PR 14740 — 33 candidates · {'inconclusive_env': 1, 'unresolved_file': 7, 'behavior_change_not_regression': 16, 'base_not_comparable': 4, 'not_a_bug': 1, 'defect_present_before_pr': 4}
- per-bug tarballs: `bundles/14740/`
- PR bundle: `bundles/verified_gold_14740.tar.gz` · sha256 `660aaac306c5b184…` · 155 KiB
- table: `bundles/14740/SUMMARY.md` · machine index: `bundles/14740/MANIFEST.json`

## PR 4 — 70 candidates · {'behavior_change_not_regression': 38, 'confirmed_regression': 3, 'inconclusive_env': 8, 'defect_present_before_pr': 10, 'unresolved_file': 10, 'not_a_bug_unconfirmed': 1}
- per-bug tarballs: `bundles/4/`
- PR bundle: `bundles/verified_gold_4.tar.gz` · sha256 `e7560227503dce2c…` · 285 KiB
- table: `bundles/4/SUMMARY.md` · machine index: `bundles/4/MANIFEST.json`

## PR 8 — 21 candidates · {'not_a_bug_unconfirmed': 1, 'defect_present_before_pr': 12, 'behavior_change_not_regression': 5, 'unresolved_file': 2, 'inconclusive_env': 1}
- per-bug tarballs: `bundles/8/`
- PR bundle: `bundles/verified_gold_8.tar.gz` · sha256 `2ef33f7d828f940c…` · 87 KiB
- table: `bundles/8/SUMMARY.md` · machine index: `bundles/8/MANIFEST.json`

## Roll-up
- `bundles/verified_gold_all.tar.gz` · sha256 `2d77dc61e4443dfe…` · 947 KiB

