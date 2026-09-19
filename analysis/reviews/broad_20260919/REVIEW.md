# Broad repository review — 2026-09-19

The numerical and source review is finished. The report and interactive data use the completed six-PR, 403-review policy (advisory credit ≥0.70, penalties ≥0.80). No new adjudication was run and no frozen T/D, bug-only, or legacy scores were changed.

## Findings and changes

1. **Audit binding (P2):** the nonfrozen scoring consumer previously accepted a changed claim-to-group mapping without checking its referenced audit. An in-memory PR10 counterexample collapsed 187 identities to one while the original validator accepted it. The consumer now verifies the audit hash, exact eligible partition and mapping, provenance, and referenced pair checkpoints. Corruption regression tests pass. The frozen runner is unchanged. All 403 evidence-stage score tuples were identical before and after this fix (SHA256 `f6dd7e5d387e6482d2fa9f1de58a536e334bd075b5d993a0e33de4e7f9fdacd5`).
2. **Interval wording (P2):** saying only eight intervals excluded zero omitted the three favoring CE. Report, summary, and table generator now state eight favor MRV, three favor CE, and ten include zero.
3. **Hover terminology:** processed findings below threshold are called classified but unscored, rather than unresolved.
4. **Coverage wording:** Fable's incomplete original harness PR coverage is distinguished from completed advisory adjudication.
5. **Navigation:** T11/T13 anchors and collapsed sections now wrap their intended tables. Fifteen collapsed sections are balanced; eleven table anchor/fold/heading triples agree.
6. **Frozen baseline disclosure:** three historical verified assignments never entered the frozen TP text inventory: a7f53199a759/10967-D03 and 6de9765d8a56/14740-D05,14740-D01. They receive neither new TP nor advisory credit. This is now disclosed; changing T would violate the requested frozen baseline.

## Numerical evidence

- Independently reproduced all 216 cell scores and F2′ bootstrap intervals, and all 63 MRV–CE paired intervals.
- Matched comparison uses 21 identical model/effort cohorts, 126 reviews per framework. Mean F2′: MRV 0.443647789, CE 0.399140307, vanilla 0.265355601. MRV wins 18/21 point comparisons; eight paired 95% intervals favor MRV, three favor CE, ten include zero.
- CE retains the highest individual cell (Opus medium, 0.641092328). A higher MRV matched average does not imply it wins every configuration.
- Threshold sensitivity uses identical validated ≥0.70 advisory identities and fixed H/T/D for both thresholds.
- Checked 13,333 base input hashes, 42 frozen source hashes, all six policy audits/checkpoint bindings, and 1,501 retained within-group pairs. The policy contains 1,501 eligible advisory claims grouped into 888 PR-scoped identities.
- All 72 Pareto points match metrics. All 17 embedded report chart datasets match generated fragments. REPORT.html and EXECUTIVE_SUMMARY.html were regenerated from Markdown.

## Source review and tests

The original working tree includes hundreds of megabytes of generated/history files. Its initial gate could not ingest complete context. A temporary Git snapshot covered all 47 changed source, test, and documentation files named and SHA256-bound in snapshot_manifest.json; the original repository was not committed or staged. Generated evidence was audited separately as described above.

The final plan has 21 reviewed shards plus a cross-shard review, all passing with zero open findings in their receipts. All 47 source hashes matched the project at archival time. The full unittest suite passed **156 tests** (tests.log). No new numerical drift was found.

**Procedural limitation:** the aggregate metareview gate still returns NEEDS_REVISION because it carries forward the initial context-risk finding claiming zero of 21 shards, even though the same final gate report records 21/21 covered and a passing cross-shard receipt. This is an outstanding gate-state inconsistency, not a passing aggregate gate. No override or manual finding-state change was made. See aggregate_gate.md and receipts/. The substantive review is complete; formal gate closure remains pending correction of that inconsistency.

**Visual limitation:** exported chart PNGs were inspected, and HTML/data consistency was checked programmatically. Browser URL policy blocked opening the local report; live interactive behavior was not verified.

## Reproduction

Run `.venv/bin/python -m unittest discover -s tests` from the project root. The final source diff, exact review plan, current-hash receipts, manifest, aggregate gate/context, and test output are archived alongside this document. Numerical regeneration provenance is in `analysis/verified_gold/advisory_readjudication/scoring_policies/advisory070_penalty080_v1/final_calculation_validation.json`; report artifact hashes are in the adjacent report_validation.json.
