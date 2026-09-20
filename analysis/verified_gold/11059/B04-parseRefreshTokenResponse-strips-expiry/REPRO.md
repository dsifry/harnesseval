# Replication — B04-parseRefreshTokenResponse-strips-expiry (11059-B04)

**Claim.** None

**Verdict in this bundle:** `golden_duplicate` ({'base': 'N/A - module absent on base (vitest: Failed to load url ./parseRefreshTokenResponse)', 'head': 'FAIL - AssertionError: expected undefined to be 3600', 'fixed': 'PASS - 1 passed (1)'})
**Fidelity:** `repo_suite`  ·  **Authoring model:** `not recorded (bundle predates model recording; cal.com bundles of this era were authored with gpt-5.2)`

Everything needed to check this yourself is in this directory:
`test.diff` (the test, applies cleanly), `fix.patch` (the minimal fix), `logs/` (raw runs),
`meta.json` (SHAs, toolchain, hashes).

## Reproduce it

```bash
git clone https://github.com/calcom/cal.com && cd cal.com
git checkout 9fde0e906897cc0f4f71793f647dd629faba3317          # the post-PR revision this bundle was verified against

yarn install            # yarn 3.4.1 (corepack prepare yarn@3.4.1 --activate); ~2 min, ~2 GB

git apply test.diff          # adds the test file (must not already exist — a fresh clone is clean)
yarn vitest run <see meta.json: test_path> --reporter=basic                        # -> 1 failed : the claimed defect is present

git apply fix.patch          # the minimal fix
yarn vitest run <see meta.json: test_path> --reporter=basic                        # -> 1 passed : defect gone
```

## What the two runs mean

| run | expected | why it matters |
|---|---|---|
| post-PR, unmodified | **FAIL** | the behaviour the campaign claims is demonstrably wrong here |
| post-PR + `fix.patch` | **PASS** | the claim is fixable, and the fix is real (not just a green test) |

Pre-PR revision `bc89fe00ea84d20bedcec782f0701b9711dc8201` is only informative: for `behavior_change_not_regression` the code path did
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
