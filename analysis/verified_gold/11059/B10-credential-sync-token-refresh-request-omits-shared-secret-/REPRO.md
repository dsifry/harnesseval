# REPRO — Credential-sync token refresh request omits shared secret/Authorization header

**Verdict:** `behavior_change_not_regression` · repo suite (vitest)

```bash
cd .cache/verify_repos/cal.com && git checkout -f 9fde0e906897cc0f4f71793f647dd629faba3317
git apply /Users/dsifry/Developer/harnesseval/analysis/verified_gold/11059/B10-credential-sync-token-refresh-request-omits-shared-secret-/test.patch
yarn vitest run packages/app-store/_utils/oauth/refreshOAuthTokens.verified.test.ts                       # expected: FAIL
git apply /Users/dsifry/Developer/harnesseval/analysis/verified_gold/11059/B10-credential-sync-token-refresh-request-omits-shared-secret-/fix.patch
yarn vitest run packages/app-store/_utils/oauth/refreshOAuthTokens.verified.test.ts                       # expected: PASS
```
