# Campaign Glossary — definitions that are NOT up for reinterpretation

## "top-6" / "top N" (BANKED 2026-09-13, user directive)
**top-N means the HARNESS ordering: severity weight descending, then comment count descending**
(sum of golden-comment severities per PR: Critical=4, High=3, Medium=2, Low=1 — identical to
run_model_matrix's `--prs N` selection). "Top 6" = the six HARDEST PRs.
It does NOT mean lexicographic URL order, dataset file order, or any other arbitrary subset.
The severity-weight top-6 of this campaign's dataset:
  1. calcom/cal.com/pull/11059   (sev 26, 9 comments)
  2. discourse-graphite/pull/4    (sev 21, 8)
  3. discourse-graphite/pull/10   (sev 21, 7)
  4. calcom/cal.com/pull/14740    (sev 14, 6)
  5. discourse-graphite/pull/8    (sev 14, 6)
  6. calcom/cal.com/pull/10967    (sev 13, 6)
Authoritative artifact: manifold_top6_hitlist.csv (regenerated against this ordering).
Verifier: .venv/bin/python tools/verify_hitlist.py --verbose
