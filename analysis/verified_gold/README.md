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
| `unresolved_file` | — | — | — | the finding could not be pinned to a changed file; manual triage queue |
| `inconsistent_evidence` | — | — | — | the test file differed between the head/fixed/base runs; bundle void |
| `static_text_test` | — | — | — | the test asserted on source text rather than executing code; no behaviour demonstrated |
| `not_a_bug_unconfirmed` | — | PASS | — | a test passed on head but the adversarial confirmation could not be produced; treat as triage, not demotion |

Only `confirmed_regression` and `behavior_change_not_regression` qualify as verified hidden gold, and
**tests that read the source file as text are rejected**: asserting on a source string (e.g.
`readFileSync(...).includes("?.push")`) "reproduces" head-FAIL/fix-PASS as a *textual* difference while
demonstrating no runtime behaviour. Authoring now rejects such tests, and the audit flagged one
pre-existing bundle as `static_text_test`.
Everything else is excluded from verified metrics and **never deleted**:

- `not_a_bug` (TWO independent tests pass on unmodified head — the first, and an adversarial second
  written specifically to fail if the claim is true) is a **candidate for demotion**. Requiring the
  second test exists because a single passing test can pass for the wrong reason: our first demotion
  candidate asserted only `safeParse().success === false` while sending an invalid `guests` payload,
  so the failure came from an unrelated field and the claim was in fact true.
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

## Known causes of `inconclusive_env` (disclosed)

- **Fix targeting across modules.** The candidate's resolved file (from the findings' own anchors) is
  sometimes the *caller* while the defect lives in a *callee* (e.g. a tRPC router vs the zod schema it
  imports). The fix author then guesses a file and its `find` string matches nothing, so no fix is
  produced. The fix prompt now accepts `fix_file_path`, which reduces but does not eliminate this.
- **Very large files.** Authoring against `handleNewBooking.ts` / `EventManager.ts` (40-90k chars)
  takes 5-8 minutes and sometimes still fails.
- These bundles are kept with their logs and blockers for the `standalone_real_code` pass or manual
  triage; they are never silently dropped.

## Deliberate limitations (disclosed, not hidden)

- Full-fidelity bundles run the repository's own test framework at the PR commit. Where the era
  toolchain cannot be brought up (2013-era Rails), a bundle may instead run the **real post-PR file**
  in a standalone runner with stubbed dependencies; `meta.json.fidelity` records
  `repo_suite` vs `standalone_real_code`, and the bundle is labelled accordingly wherever cited.
- The test proves the behavior change for the argued mechanism; it does not prove severity or
  business impact.
- LLM-written tests/fixes are artifacts like any other: they are saved, versioned, and re-runnable.

## The catalogue (start here)

`GOLD_DEFECT_CATALOG.md` (also `.json` / `.csv`) is the canonical, deduplicated list of the verified
hidden-gold defects — one entry per defect with its id, PR, label, `file:line` location, the exact test
artifact that demonstrates it, its minimal fix, its logs, its evidence level, its orthogonality result and
its provenance (merged duplicate / restored / corrected label). Rebuild with
`python tools/gold_defect_catalog.py`.

Evidence levels per defect:

| level | count | meaning |
|---|---|---|
| defect-authored test | 34 | the verifier wrote a test for this defect alone: it fails on the PR head, its own minimal fix makes it pass, and the bundle's fix leaves it red (orthogonality proven) |
| container test authored for this claim | 76 | the defect **is** its execution container's own claim, so the container's executed test is its own exact test (mechanically checked: in every multi-concern container the only test-less defects were the container's own `labels[0]`, token overlap 1.00) |

**110/110 defects own `defects/<id>/{test.diff,fix.patch,logs/,meta.json}`** — no defect's evidence is a
container test it shares with another defect. `meta.json` records `evidence_provenance`. The canonical list,
with each defect's test, fix, location and provenance, is `GOLD_DEFECT_CATALOG.md`; `DEFECT_REGISTRY.json`
carries `_final` (goldens 42, defects 110, total gold 152).

## Terminology (these mean the same thing)

| term used elsewhere | term used here | meaning |
|---|---|---|
| framework, fw | **harness** | the wrapper around a model: `vanilla-engineered` (van), `compound-realistic` (CE), `metareview-realistic` (MRV) |
| effort | **effort level** | low / medium / high reasoning effort |
| bundle | **execution container** | one candidate finding with one executed test+fix; containers are provenance, defects are the unit |
| claim, label | **defect claim** | a distinct root cause asserted by the merge audit |
| true golden set, true gold, verified hidden gold | same | 42 Martian goldens + 110 verified defects = **152** |
| expanded gold, verified union (§10b/§10c) | *superseded* | the earlier key-union sets (359 → 253); keep for provenance only |
| coverage ceiling | — | a cell's reachable maximum (goldens + defects in the PRs it covered); **not** the same as `reachable` |
| reachable denominator | — | 42 + the 97 defects some run actually reported (139), used only as a disclosed sensitivity variant |

