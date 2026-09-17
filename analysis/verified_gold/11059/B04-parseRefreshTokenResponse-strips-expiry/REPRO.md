# REPRO — [11059] parseRefreshTokenResponse strips expiry / refresh_token (credential-sync path)

**Verdict:** `behavior_change_not_regression` · **Fidelity:** repo suite (vitest) · **Base:** `bc89fe00ea` · **Head:** `9fde0e9068`

```bash
cd .cache/verify_repos/cal.com && git checkout verify/11059
git apply $BUNDLE/test.patch
yarn vitest run packages/app-store/_utils/oauth/parseRefreshTokenResponse.verified.test.ts   # FAIL
git apply $BUNDLE/fix.patch
yarn vitest run packages/app-store/_utils/oauth/parseRefreshTokenResponse.verified.test.ts   # PASS
```

Expected: pre-fix failure is `expected undefined to be 3600` (expiry stripped by the minimum sync
schema); post-fix run is green. `git checkout bc89fe00ea` shows the module did not exist before the PR
(new credential-sync feature), so no pre-PR baseline applies.
