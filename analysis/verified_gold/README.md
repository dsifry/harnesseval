# Verified Hidden Gold — evidence bundles

A candidate from the verified true-golden set (`analysis/TRUE_GOLDEN_EVIDENCE.md`) is promoted to
**verified hidden gold** only when this directory contains an executable evidence bundle proving it,
on the real PR code. Judge opinion alone is not sufficient.

## Bundle layout

```
analysis/verified_gold/<pr_slug>/<class_slug>/
  meta.json          candidate id, PR, file:line, claim, base/head SHAs, toolchain, commands,
                     timestamps, verdict, sibling instances (unverified), provenance hashes
  test.patch         the added test (applies to the PR head tree)
  fix.patch          the minimal fix that makes the test pass
  logs/base.log      test run on the PRE-PR commit          (expected: PASS, or N/A for new files)
  logs/head.log      test run on the PR head                 (expected: FAIL — the regression)
  logs/fixed.log     test run on PR head + fix.patch         (expected: PASS)
  REPRO.md           one-command reproduction for a human
```

## Verdict taxonomy

| verdict | base | head | head+fix | meaning |
|---|---|---|---|---|
| `confirmed_regression` | PASS | FAIL | PASS | the PR introduced a testable behavior regression |
| `behavior_change_not_regression` | N/A or PASS | FAIL | PASS | new/one-way code path added by the PR behaves wrongly |
| `not_a_bug` | — | PASS | — | no observable behavior change → demote to quality/ops finding |
| `defect_present_before_pr` | FAIL | FAIL | PASS | the behavior was already wrong before the PR (pre-existing, not introduced here) |
| `inconclusive_env` | — | — | — | environment blocked the run (recorded, not counted) |
| `flaky` | — | mixed | — | nondeterministic — must be re-run and recorded |

Only `confirmed_regression` and `behavior_change_not_regression` qualify as verified hidden gold.
Everything else is excluded from verified metrics and **never deleted**:

- `not_a_bug` (test passes on head → no observable behavior change) is a **candidate for demotion**.
  Its full bundle is kept and indexed in `analysis/verified_gold/DEMOTION_REVIEW.md` so the claims can
  be reviewed together afterwards and either demoted permanently or re-argued with a sharper test.
- `inconclusive_env` / `flaky` bundles are kept and indexed the same way, with the blocking reason
  recorded in `meta.json.blocker`.
- Every candidate therefore produces a bundle regardless of outcome; absence of a bundle means the
  candidate was not yet attempted, never that it was discarded.

## Acceptance rules (checked mechanically)

1. `test.patch` applies cleanly to the head tree; `fix.patch` applies cleanly after it.
2. `logs/head.log` shows a failing assertion or non-zero exit caused by the claim (not by a
   missing dependency); the failure message must name the asserted behavior.
3. `logs/fixed.log` shows the same test passing, with the fix applied and nothing else changed.
4. `logs/base.log` exists (PASS, or a recorded "file absent on base" for new-file candidates).
5. `meta.json` records: PR, base SHA, head SHA, exact commands, toolchain versions, UTC timestamps,
   and the SHA-256 of each artifact.
6. The fix is the **minimal change for the demonstrated instance**; other instances of the same
   class are listed in `meta.json.sibling_instances` as unverified, never silently fixed.

## Deliberate limitations (disclosed, not hidden)

- Full-fidelity bundles run the repository's own test framework at the PR commit. Where the era
  toolchain cannot be brought up (2013-era Rails), a bundle may instead run the **real post-PR file**
  in a standalone runner with stubbed dependencies; `meta.json.fidelity` records
  `repo_suite` vs `standalone_real_code`, and the bundle is labelled accordingly wherever cited.
- The test proves the behavior change for the argued mechanism; it does not prove severity or
  business impact.
- LLM-written tests/fixes are artifacts like any other: they are saved, versioned, and re-runnable.
