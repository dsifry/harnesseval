# Verified hidden gold — evidence bundles

Each bug has a browsable directory and an attachable tarball, per PR:

- unpacked bundle: `analysis/verified_gold/<pr>/<bug-id>-<slug>/` (meta.json, test.patch, fix.patch, logs/, REPRO.md)
- attachable tarball: `analysis/verified_gold/bundles/<pr>/<bug-id>-<slug>.tar.gz` (+ `.sha256`)
- per-PR bundle: `analysis/verified_gold/bundles/verified_gold_<pr>.tar.gz` (all bugs + MANIFEST + SUMMARY)
- roll-up: `analysis/verified_gold/bundles/verified_gold_all.tar.gz`

Every attempted candidate produces a bundle whatever the verdict; `not_a_bug` and
`inconclusive_env` are the demotion-review queue (`DEMOTION_REVIEW.md`).

Generated 2026-09-18T00:31:28Z · verdicts: {'unresolved_file': 28, 'confirmed_regression': 8, 'behavior_change_not_regression': 69, 'inconclusive_env': 43, 'defect_present_before_pr': 20, 'not_a_bug': 3, 'static_text_test': 1, 'golden_duplicate': 1, 'base_not_comparable': 4}

## PR 10 — 20 candidates · {'unresolved_file': 3, 'confirmed_regression': 1, 'behavior_change_not_regression': 8, 'inconclusive_env': 3, 'defect_present_before_pr': 4, 'not_a_bug': 1}
- per-bug tarballs: `bundles/10/`
- PR bundle: `bundles/verified_gold_10.tar.gz` · sha256 `9f87a3c13dbb8bca…` · 83 KiB
- table: `bundles/10/SUMMARY.md` · machine index: `bundles/10/MANIFEST.json`

## PR 10967 — 31 candidates · {'inconclusive_env': 19, 'static_text_test': 1, 'confirmed_regression': 4, 'defect_present_before_pr': 5, 'not_a_bug': 1, 'unresolved_file': 1}
- per-bug tarballs: `bundles/10967/`
- PR bundle: `bundles/verified_gold_10967.tar.gz` · sha256 `ed4aef48c02fa3a6…` · 162 KiB
- table: `bundles/10967/SUMMARY.md` · machine index: `bundles/10967/MANIFEST.json`

## PR 11059 — 23 candidates · {'golden_duplicate': 1, 'behavior_change_not_regression': 13, 'defect_present_before_pr': 2, 'unresolved_file': 7}
- per-bug tarballs: `bundles/11059/`
- PR bundle: `bundles/verified_gold_11059.tar.gz` · sha256 `6e47fb9a721e5604…` · 107 KiB
- table: `bundles/11059/SUMMARY.md` · machine index: `bundles/11059/MANIFEST.json`

## PR 14740 — 33 candidates · {'inconclusive_env': 6, 'unresolved_file': 7, 'behavior_change_not_regression': 14, 'base_not_comparable': 4, 'defect_present_before_pr': 2}
- per-bug tarballs: `bundles/14740/`
- PR bundle: `bundles/verified_gold_14740.tar.gz` · sha256 `52ee99ae079244f7…` · 152 KiB
- table: `bundles/14740/SUMMARY.md` · machine index: `bundles/14740/MANIFEST.json`

## PR 4 — 70 candidates · {'behavior_change_not_regression': 34, 'confirmed_regression': 3, 'inconclusive_env': 15, 'defect_present_before_pr': 7, 'unresolved_file': 10, 'not_a_bug': 1}
- per-bug tarballs: `bundles/4/`
- PR bundle: `bundles/verified_gold_4.tar.gz` · sha256 `b54007e5c132dc1f…` · 281 KiB
- table: `bundles/4/SUMMARY.md` · machine index: `bundles/4/MANIFEST.json`

## Roll-up
- `bundles/verified_gold_all.tar.gz` · sha256 `fe0f2c2e58a05f9a…` · 786 KiB

