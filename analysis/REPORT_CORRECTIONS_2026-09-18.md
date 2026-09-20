# September report corrections

This edition corrects the working source based on commit `8f7b8f9c` (the historical
`report-2026-09-18` tag). That tag still identifies the pre-correction edition; it
has not been moved. Reproducing this edition requires the corrected source snapshot,
including any uncommitted changes, and its matching output-checksum manifest.

## Changes

- Corrected metric-axis indexing in both historical semantic paired bootstraps.
- Made historical harness-versus-vanilla bootstrap draws pool PR counts, matching
  their point estimators instead of averaging individual PR recalls.
- Corrected the GLM MRV-low / Opus MRV-medium cost comparison and its display precision.
- Made catalog provenance and withdrawal labels reflect recorded evidence; missing
  cross-fix evidence no longer becomes a claim of proven orthogonality.
- Corrected the 39/42 comparison population, missing-bug arithmetic, CI interpretation,
  adjudication-instrument caveats, and distinction between API cost and developer utility.
- Made the recommendation explicitly distinguish lower noise (Vision) from lower
  API cost (Flash), on the primary 147-defect set. Moved superseded framework analysis
  into Appendix A and labeled benchmark-only comparisons.
- Fixed Markdown table delimiters, generated F2′ columns and universe labels, chart
  reference-line orientation, CI clipping, and frontier-label placement.
- Expanded the documented presentation rebuild to include chart fragments, dashboard
  snapshots, and both HTML reports. HTML is rendered from Markdown, not edited separately.

## Validation commands

```sh
MPLCONFIGDIR=/private/tmp/harnesseval-mpl .venv/bin/python -W ignore::ResourceWarning -m unittest discover -s tests -p 'test_report_*.py'
.venv/bin/python -W ignore::ResourceWarning -m unittest discover -s tests -p 'test_dashboard_export.py'
.venv/bin/python tools/final_report_compute.py
.venv/bin/python tools/gold_defect_catalog.py
.venv/bin/python tools/final_report_tables.py
MPLCONFIGDIR=/private/tmp/harnesseval-mpl .venv/bin/python tools/final_report_figures.py
MPLCONFIGDIR=/private/tmp/harnesseval-mpl .venv/bin/python tools/final_report_figures_true_gold.py
.venv/bin/python tools/final_report_html.py
.venv/bin/python tools/report_interactive_charts.py
node tools/export_dashboard_panels.js --ci
.venv/bin/python tools/dashboard_panel_snapshots.py
.venv/bin/python tools/report_to_html.py
shasum -a 256 -c analysis/verified_gold/OUTPUT_SHA256SUMS
git diff --check
```

`final_report_tables.py` writes `/tmp/final_report_tables.md`. The affected evidence
tables and checksum values in the authored Markdown must be synchronized from these
outputs before the final HTML render. The original run registry, defect registry,
finding assignments and saved execution logs are unchanged by this correction.

The archived fresh-clone test in `REPLICATION_TEST_2026-09-18.md` describes the earlier
edition. It must not be cited as a fresh-clone test of these later corrections.

## Results

- 17 regression tests passed: 8 calculation/provenance, 3 chart, 3 table and
  3 real Node dashboard-export checks.
- The full metrics computation completed. Compared with base commit `8f7b8f9c`,
  `true_gold_defects` is unchanged in its entirety. Only `cost_structure_ratios`,
  `expanded_gold_semantic` and `expanded_gold_verified` changed.
- The corrected historical semantic paired intervals resolve as follows: recall
  6 positive / 2 negative / 13 unresolved; F1 7 / 2 / 12; F1′ 9 / 0 / 12.
  Historical harness-versus-vanilla recall intervals resolve 39 / 0 / 4.
- The corrected GLM MRV-low / Opus MRV-medium ratios are 0.9800 per token,
  0.0462 tokens per task and 0.0453 dollars per task.
- All five artifacts pass the updated SHA-256 manifest.
- Rebuilt static figures, the dashboard, 19 interactive fragments (including CI
  variants), all 10 dashboard PNG snapshots, and both HTML documents from Markdown.
- Browser inspection confirmed 66 complete-cell points and unclipped confidence
  intervals in the headline chart.

This was a recomputation and presentation correction using saved inputs. It did not
rerun model reviews, adjudication, or the archived defect tests. It was not a new
fresh-clone replication. Generated SVG trailing whitespace was normalized after export.
