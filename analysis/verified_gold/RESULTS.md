> **SUPERSEDED (2026-09-18) — kept as the audit record of that stage.** The numbers below (100 verified
> bundles, "up to 145") predate the defect-level deduplication, the under-count recovery and the
> container-test normalisation. **Current canonical state: 42 goldens + 110 individually test-validated
> defects = 152 true bugs**, in `GOLD_DEFECT_CATALOG.md` / `DEFECT_REGISTRY.json` (`_final`). See
> also `DUP_REVIEW_2026-09-18.md` and `UNDERCOUNT_2026-09-18.md`.

# Verified hidden gold — final results

Every candidate from the hidden-gold union was executed against the real post-PR code. A candidate is
promoted only when a runnable test FAILS on the pinned post-PR revision and PASSES with a minimal fix.

**100 verified hidden gold** across 6 PRs, versus a 42-comment original golden set — 2.4x as many. *(Final count after deduplication and under-count recovery: 110.)*

Those 100 bundles contain **45 additional distinct defects** (merge audit below), so the number of
distinct real bugs present is up to **145**, of which 100 are individually verified.

## Verification outcome by tier

| tier | n | meaning |
|---|---|---|
| `confirmed_regression` | 10 | pre-PR PASS, post-PR FAIL, fixed PASS |
| `behavior_change_not_regression` | 90 | new code path: post-PR FAIL, fixed PASS |
| `defect_present_before_pr` | 46 | real, demonstrable defect that pre-dates the PR |
| `unresolved_file` | 32 | claim could not be pinned to a changed file |
| `inconclusive_env` | 24 | proof blocked, not disproven (floor on the true count) |
| `base_not_comparable` | 4 | base failed for a different reason than the claim |
| `not_a_bug` | 2 | confirmed demotion: two independent tests pass on unmodified code |
| `not_a_bug_unconfirmed` | 1 | one passing test; adversarial confirmation not run |
| `claim_supported_source_only` | 1 | source analysis supports it; runtime promotion pending |
| `static_text_test` | 1 | invalidated: asserted on source text, not behaviour |
| `golden_duplicate` | 1 | excluded: same defect as a golden comment |

## Instruments (a claim decides which evidence type can prove it)

| instrument | what it proves | bundles |
|---|---|---|
| `repo_suite` / `repo_suite_harness_config` | the repository's own vitest, real module graph | most cal.com bundles |
| `standalone_real_code` | real post-PR file with visible stubs (Rails 4.2 era) | most discourse bundles |
| `db_migration` | the REAL migration run up/down against Docker Postgres with ActiveRecord 4.2 | 10-B11 |
| `typecheck` | tsc compile-time assertions (runtime tests cannot evaluate types) | 10967-B18 |
| `source_analysis` | reading the real code path (weakest; used only where the app cannot run) | 4-B75 |

## Merge audit — how honest is the count?

`tools/verified_gold_merge_audit.py` asked the judge, per promoted bundle, whether its members really
describe ONE defect. **28 of 100 are multi-defect** (18 bundles with 2 defects, 3 with 3, 7 with 4),
i.e. **45 extra distinct defects** are sitting inside bundles whose test verifies only one of them.
Each affected bundle carries a `multi_defect` field naming the defects. Consequences:

- the verified count **100 is a lower bound** on distinct defects (up to 145);
- a mis-merge can also fabricate a demotion or hide a candidate — `8-B00` merged 94 pagination + 30 API-contract
  + 13 param findings, so its single passing test demoted nothing; that demotion is voided and the pagination
  sub-claim is a new candidate.

## How this compares to the earlier figures

| figure | count | ratio to the 42 goldens |
|---|---|---|
| original golden set | 42 | 1.0x |
| raw hidden-gold key-union | 359 | 8.5x |
| verified candidates after merge + overlap removal | 211 | 5.0x |
| **verified by execution** | **100** | **2.4x** |
| verified + multi-defect extras (unverified) | up to 145 | 3.5x |

## Demotion review (all five resolved)

| candidate | outcome |
|---|---|
| `14740-B11` (team-notification branch unreachable) | **demotion confirmed** (two independent tests); caveat: proves the callee is reachable, not that callers populate `team` |
| `10967-B18` (credentialId not enforced) | **demotion confirmed** with the right instrument: tsc shows the interface requires `(event, credentialId)` and rejects a legacy one-arg implementation |
| `10-B11` (irreversible migration) | **REVERSED — it is a real bug.** Real migration vs real Postgres: up destroys the settings, rollback raises IrreversibleMigration; a `reversible` fix restores them |
| `8-B00` (visible param flips to false) | **demotion voided** — merged artefact (see merge audit); split recorded, pagination sub-claim now a candidate |
| `4-B75` (spec false positive) | **demotion withdrawn** — source analysis supports the claim (`ensure_embeddable` rejects before `params.require`); needs the Rails spec env to promote |

## Integrity gates

- golden-distinctness gate: 0 duplicates among the promoted set
- base-verdict audit: 0 reclassifications
- duplicate bug ids: none; source-text tests rejected; demotions require an adversarial second test

