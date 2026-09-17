# Verified hidden gold — PR 11059

Candidates: 2 · verdicts: {'behavior_change_not_regression': 2}

| bug id | bug | verdict | head | base | fix | file | tarball sha256 |
|---|---|---|---|---|---|---|---|
| 11059-B04 | B04-parseRefreshTokenResponse-strips-expiry | `behavior_change_not_regression` | FAIL - AssertionError: expected undefined to be 3600 | N/A - module absent on base (vitest: Failed to load url ./parseRefreshTokenResponse) | PASS - 1 passed (1) | `packages/app-store/_utils/oauth/parseRefreshTokenResponse.ts` | `26ecc10cb1db…` |
| 11059-B05 | B05-webhook-secret-validation-uses-non-constant-time-string-co | `behavior_change_not_regression` | FAIL | FAIL | PASS | `apps/web/pages/api/webhook/app-credential.ts` | `1b2534cfc46e…` |
