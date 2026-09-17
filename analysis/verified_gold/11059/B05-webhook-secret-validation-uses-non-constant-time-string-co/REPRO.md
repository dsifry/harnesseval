# REPRO — Webhook secret validation uses non-constant-time string comparison (timing side-channel) and fragile header lookup

**Verdict:** `behavior_change_not_regression` · repo suite (vitest)

```bash
cd .cache/verify_repos/cal.com && git checkout -f 9fde0e906897cc0f4f71793f647dd629faba3317
git apply /Users/dsifry/Developer/harnesseval/analysis/verified_gold/11059/webhook-secret-validation-uses-non-constant-time-string-co/test.patch
yarn vitest run apps/web/pages/api/webhook/app-credential.verified.test.ts                       # expected: FAIL
git apply /Users/dsifry/Developer/harnesseval/analysis/verified_gold/11059/webhook-secret-validation-uses-non-constant-time-string-co/fix.patch
yarn vitest run apps/web/pages/api/webhook/app-credential.verified.test.ts                       # expected: PASS
```
