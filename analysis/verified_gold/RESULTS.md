# Verified hidden gold — final results

Every candidate from the hidden-gold union was executed against the real post-PR code. A candidate is
promoted only when a runnable test FAILS on the pinned post-PR revision and PASSES with a minimal fix
(see `README.md` for the verdict taxonomy and `REPLICATION_KIT.md` for how to re-run any of them).

**99 verified hidden gold** across 6 PRs, versus a 42-comment original golden set — 2.4x as many as the goldens contain.

## Verification outcome by tier

| tier | n | meaning |
|---|---|---|
| `confirmed_regression` | 10 | pre-PR PASS, post-PR FAIL, fixed PASS |
| `behavior_change_not_regression` | 89 | new/changed code path: post-PR FAIL, fixed PASS |
| `defect_present_before_pr` | 46 | real, demonstrable defect that pre-dates the PR |
| `unresolved_file` | 32 | claim could not be pinned to a changed file |
| `inconclusive_env` | 24 | test/fix authoring or environment blocked the proof |
| `not_a_bug` | 5 | two independent tests pass on unmodified code (demotion candidates) |
| `base_not_comparable` | 4 | base run failed for a different reason than the claim |
| `static_text_test` | 1 | invalidated: asserted on source text, not behaviour |
| `golden_duplicate` | 1 | excluded: same defect as a golden comment |

## Per PR

| PR | candidates | verified hidden gold | other tiers |
|---|---|---|---|
| 4 | 70 | **41** | defect_present_before_pr=10, inconclusive_env=8, not_a_bug=1, unresolved_file=10 |
| 8 | 21 | **5** | defect_present_before_pr=12, inconclusive_env=1, not_a_bug=1, unresolved_file=2 |
| 10 | 32 | **17** | defect_present_before_pr=9, not_a_bug=1, unresolved_file=5 |
| 10967 | 31 | **5** | defect_present_before_pr=9, inconclusive_env=14, not_a_bug=1, static_text_test=1, unresolved_file=1 |
| 11059 | 25 | **15** | defect_present_before_pr=2, golden_duplicate=1, unresolved_file=7 |
| 14740 | 33 | **16** | base_not_comparable=4, defect_present_before_pr=4, inconclusive_env=1, not_a_bug=1, unresolved_file=7 |

## How this compares to the earlier figures

| figure | count | ratio to the 42 goldens |
|---|---|---|
| original golden set | 42 | 1.0x |
| raw hidden-gold key-union (before verification) | 359 | 8.5x |
| verified candidates after merge + overlap removal | 211 | 5.0x |
| **verified by execution (this document)** | **99** | **2.4x** |

The intermediate unions overcounted by ~2.1-3.6x: paraphrase splits, then golden overlaps, and finally
claims that could not be demonstrated at all. The executable count is the defensible one.

## Integrity gates (all clean at the end)

- golden-distinctness gate: 0 duplicates among the 99 promoted (judge gpt-5.2; one earlier case excluded)
- base-verdict audit: 0 reclassifications
- no duplicate bug ids; LLM-authored tests that assert on source text are rejected, and demotions require an adversarial second test

