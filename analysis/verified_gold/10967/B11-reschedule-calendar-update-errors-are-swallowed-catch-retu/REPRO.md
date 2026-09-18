# Replication — B11-reschedule-calendar-update-errors-are-swallowed-catch-retu (10967-B11)

**Claim.** Reschedule calendar update errors are swallowed: catch returns [] when calendarReference is unset and logs were removed

**Verdict in this bundle:** `confirmed_regression` ({'base': 'PASS', 'head': 'FAIL', 'fixed': 'PASS'})
**Fidelity:** `repo_suite`  ·  **Authoring model:** `deepseek-4.1-flash`

Everything needed to check this yourself is in this directory:
`test.diff` (the test, applies cleanly), `fix.patch` (the minimal fix), `logs/` (raw runs),
`meta.json` (SHAs, toolchain, hashes).

## Reproduce it

```bash
git clone https://github.com/calcom/cal.com && cd cal.com
git checkout de628295646d0848226618108a52f2f1e5d04ac0          # the post-PR revision this bundle was verified against

yarn install            # yarn 3.4.1 (corepack prepare yarn@3.4.1 --activate); ~2 min, ~2 GB

git apply test.diff          # adds the test file (must not already exist — a fresh clone is clean)
yarn vitest run packages/core/EventManager.verified.test.ts --reporter=basic                        # -> 1 failed : the claimed defect is present

git apply fix.patch          # the minimal fix
yarn vitest run packages/core/EventManager.verified.test.ts --reporter=basic                        # -> 1 passed : defect gone
```

## What the two runs mean

| run | expected | why it matters |
|---|---|---|
| post-PR, unmodified | **FAIL** | the behaviour the campaign claims is demonstrably wrong here |
| post-PR + `fix.patch` | **PASS** | the claim is fixable, and the fix is real (not just a green test) |

Pre-PR revision `a308075bc39b77ed7059b0cae9d443d669a7bf98` is only informative: for `behavior_change_not_regression` the code path did
not exist yet, and for `confirmed_regression` the test passes there too.

## Honest limits (please read)

- The test and fix were authored by an LLM and then **executed**; they are artifacts, not a proof of
  severity or business impact. Read the test before trusting the conclusion — one early candidate was
  rejected precisely because its test asserted on source text rather than behaviour.
- `fix.patch` addresses the **demonstrated instance only**; other instances of the same class are
  listed as unverified siblings in `meta.json`.
- Toolchain matters. TS bundles: node 22 + yarn 3.4.1 + the repo's own vitest. If a `.tsx` bundle
  says `repo_suite_harness_config`, the test ran under a minimal harness config (the repo's workspace
  glob excludes `.tsx` and its tsconfig sets `jsx: preserve`); the test file is identical either way.
- Ruby bundles (`standalone_real_code`) stub collaborators (ActiveRecord, I18n, …). The **file under
  test is the real post-PR file**; the stubs are visible at the top of the test.
