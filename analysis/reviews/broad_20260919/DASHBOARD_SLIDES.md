# Dashboard and slides follow-up

Both requested pages have been reviewed and updated. Sol reviewed the slides; Terra independently reviewed the dashboard; the parent verified final data and corrected remaining unsupported outcome claims.

## Changes

- Dashboard numbers were current, but methodology omitted the selected confidence cutoffs. It now states A ≥0.70, H ≥0.80, and classified-but-unscored treatment below cutoff, and displays the matched framework comparison prominently.
- Corrected the campaign-finding versus distinct-bug cost ratio from approximately 6× to 5× (360/72). Scoped latency comparisons to specific cells and removed causal claims about effort and gateway throughput. Removed wording suggesting human verification where archived evidence is the basis.
- Slides were stale. Replaced all 66 complete-cell data rows, including F2′, intervals, costs, latency, recall, tokens, and bug counts. Updated annotations, recommendations, and best-vs-best comparison. Added matched MRV/CE results and threshold policy.
- Raised both slide score axes to 0.8 so the highest point (0.641) and interval upper bound (0.747) fit. Distinguished the historical benchmark-F1 effort result from revised F2′. Replaced unsupported “frontier-grade” equivalence and increased shipping claims with a low-cost pilot recommendation and measurable developer outcomes.
- SLIDES.html is its own source; no Markdown deck source exists. Dashboard changes are in its Python generator and regenerated HTML. REPORT.html and EXECUTIVE_SUMMARY.html were regenerated from unchanged Markdown.

## Validation

All 66 slide rows match the dashboard data exactly across eight numeric fields. All 66 dashboard quality scores match current verified metrics within the generator's five-decimal truncation. Matched averages are MRV 0.444, CE 0.399, vanilla 0.265; MRV leads CE in 18/21 point comparisons, with paired intervals favoring MRV in eight, CE in three, and including zero in ten. Both pages' inline JavaScript passes Node syntax checking. The full suite passes 158 tests; dashboard-specific tests also check current scoring and matched policy results. Final calculation output hashes are unchanged.

File hashes are in dashboard_slides_validation.json; test output is dashboard_slides_tests.log. This supplement records subsequent edits to the earlier broad-review snapshot. It does not clear the previously documented aggregate metareview gate-state issue. Live browser rendering and interaction remain unverified because of the local-browser restriction.

Reproduce dashboard generation with `.venv/bin/python tools/final_report_html.py`, then `node tools/export_dashboard_panels.js --ci`. Verify with `.venv/bin/python -m unittest tests.test_dashboard_export`. The slides' `const D` rows come from `analysis/figures/interactive/dash_chart1a.json` customdata; the eight numeric columns are cost_run, F2p_sem, F2p_sem_lo, F2p_sem_hi, recall_sem, TP_sem, tok_run, and wall_run, preceded by model/framework/effort labels (F2′ interval contains the point plus two bounds).
