# Replication — B26-admin-group-template-bypasses-usercountdisplay-and-rende (8-B26)

**Claim.** Admin group template bypasses userCountDisplay and renders raw zero user_count

**Verdict in this bundle:** `defect_present_before_pr` ({'base': 'FAIL', 'head': 'FAIL', 'fixed': 'PASS'})
**Fidelity:** `standalone_real_code`  ·  **Authoring model:** `deepseek-4.1-flash-background`

Everything needed to check this yourself is in this directory:
`test.diff` (the test, applies cleanly), `fix.patch` (the minimal fix), `logs/` (raw runs),
`meta.json` (SHAs, toolchain, hashes).

## Reproduce it

```bash
git clone https://github.com/ai-code-review-evaluation/discourse-graphite && cd discourse-graphite
git checkout 060cda77729cb1c4a827560e09e89a7b22078ba9          # the post-PR revision this bundle was verified against

# no dependency install needed: the test stubs its collaborators and runs on system ruby
# (verified with ruby 2.6.10; ActiveRecord 4.1.16 is what the era repo expects)

git apply test.diff          # adds the test file (must not already exist — a fresh clone is clean)
ruby -I. spec/verify/group_verify.rb                        # -> RESULT: FAIL : the claimed defect is present

git apply fix.patch          # the minimal fix
ruby -I. spec/verify/group_verify.rb                        # -> RESULT: PASS : defect gone
```

## What the two runs mean

| run | expected | why it matters |
|---|---|---|
| post-PR, unmodified | **FAIL** | the behaviour the campaign claims is demonstrably wrong here |
| post-PR + `fix.patch` | **PASS** | the claim is fixable, and the fix is real (not just a green test) |

Pre-PR revision `4975fc28903a84418f546b2809370f19abf10e08` is only informative: for `behavior_change_not_regression` the code path did
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
