# Verified hidden gold — PR 11059

Candidates: 25 · verdicts: {'golden_duplicate': 1, 'behavior_change_not_regression': 14, 'defect_present_before_pr': 2, 'unresolved_file': 7, 'duplicate_of': 1}

| bug id | bug | verdict | head | base | fix | file | tarball sha256 |
|---|---|---|---|---|---|---|---|
| 11059-B05 | B05-webhook-secret-validation-uses-non-constant-time-string-co | `behavior_change_not_regression` | FAIL | FAIL | PASS | `apps/web/pages/api/webhook/app-credential.ts` | `6a71e1b702cf…` |
| 11059-B07 | B07-non-atomic-findfirst-then-create-in-webhook-can-create-dup | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `apps/web/pages/api/webhook/app-credential.ts` | `70e06d7f9d3c…` |
| 11059-B09 | B09-webhook-api-handler-performs-credential-create-update-with | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `apps/web/pages/api/webhooks/app-credential.ts` | `0f7a6645c445…` |
| 11059-B10 | B10-credential-sync-token-refresh-request-omits-shared-secret- | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/app-store/utils/oauth/refreshoauthtokens.ts` | `fa18b5763d67…` |
| 11059-B13 | B13-webhook-persists-decrypted-credential-keys-without-validat | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `apps/web/pages/api/webhook/app-credential.ts` | `dab6340bcee1…` |
| 11059-B14 | B14-webhook-updates-an-arbitrary-credential-when-user-has-mult | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `apps/web/pages/api/webhook/app-credential.ts` | `b8607569d968…` |
| 11059-B19 | B19-webhook-secret-header-lookup-uses-raw-env-header-name-brea | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `apps/web/pages/api/webhooks/app-credential.ts` | `203ef79216c9…` |
| 11059-B21 | B21-webhook-auth-fails-open-when-calcomwebhooksecret-is-unset- | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `apps/web/pages/api/webhook/app-credential.ts` | `08980ecac900…` |
| 11059-B22 | B22-instance-wide-shared-webhook-secret-allows-overwriting-any | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `apps/web/pages/api/webhook/app-credential.ts` | `969e9541af4b…` |
| 11059-B23 | B23-parserefreshtokenresponse-throws-on-schema-mismatch-and-ca | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/app-store/utils/oauth/parseRefreshTokenResponse.ts` | `9feebae3922e…` |
| 11059-B24 | B24-webhook-credential-sync-updates-key-but-does-not-clear-pre | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `apps/web/pages/api/webhook/app-credential.ts` | `9961492c3cd9…` |
| 11059-B26 | B26-parserefreshtokenresponse-now-throws-on-zod-safeparse-fail | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/lib/integrations/oauth/parseRefreshTokenResponse.ts` | `0241c0b57089…` |
| 11059-B31 | B31-api-route-default-imports-zod-making-z-undefined-and-cras | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `apps/web/pages/api/webhook/app-credential.ts` | `0574c6601804…` |
| 11059-B32 | B32-webhook-secret-check-has-no-rate-limiting-enabling-unlimit | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `apps/web/pages/api/webhook/app-credential.ts` | `4e821f1ca226…` |
| 11059-B12 | B12-salesforce-calendarservice-references-prisma-without-impor | `defect_present_before_pr` | FAIL | FAIL | PASS | `packages/app-store/salesforce/lib/calendarservice.ts` | `2f61518d5685…` |
| 11059-B17 | B17-envexample-suggests-wrong-length-aes-256-encryption-key-ge | `defect_present_before_pr` | ? | ? | ? | `.env.example` | `d26e0d430757…` |
| 11059-B33 | B33-webhook-app-credential-sync-updates-keys-but-leaves-creden | `duplicate_of` | FAIL | N/A_module_absent | PASS | `apps/web/pages/api/webhook/app-credential.ts` | `c8e53b59200b…` |
| 11059-B04 | B04-parseRefreshTokenResponse-strips-expiry | `golden_duplicate` | FAIL - AssertionError: expected undefined to be 3600 | N/A - module absent on base (vitest: Failed to load url ./parseRefreshTokenResponse) | PASS - 1 passed (1) | `packages/app-store/_utils/oauth/parseRefreshTokenResponse.ts` | `026b19f728b0…` |
| 11059-B20 | B20-feature-flag-constant-evaluates-to-raw-encryption-key-stri | `unresolved_file` | — | — | — | `packages/lib/constants.ts` | `dd720cd0db53…` |
| 11059-B25 | B25-some-oauth-integrations-refresh-via-refreshoauthtokens-but | `unresolved_file` | — | — | — | `packages/app-store/lark/lib/getAccessToken.ts` | `090e767f9d09…` |
| 11059-B27 | B27-google-oauth-refresh-persists-unvalidated-credentialkey-sc | `unresolved_file` | — | — | — | `unknown (not in PR diff); search in Google OAuth refresh/credential update code for `parseRefreshTokenResponse(` and `credential.update({ data: { key: ... } })`` | `b2229161b4cf…` |
| 11059-B28 | B28-zoho-crm-token-expiry-adds-3600ms-instead-of-1-hour-causin | `unresolved_file` | — | — | — | `packages/app-store/zoho-crm/lib/credentials.ts` | `cc6e8e7c49e0…` |
| 11059-B29 | B29-cross-instance-credential-sync-incorrectly-trusts-reqbodyu | `unresolved_file` | — | — | — | `UNKNOWN (not in PR diff) — locate the sync handler that reads req.body.userId and queries the local User table` | `d7bd79fe9b70…` |
| 11059-B30 | B30-sync-endpoint-fetch-has-no-timeout-abort-and-no-fallback-a | `unresolved_file` | — | — | — | `UNKNOWN (sync-endpoint fetch call site not included in PR #11059 diff; reports provided no file/line refs)` | `8635141d9e63…` |
| 11059-B34 | B34-office365video-sends-appslug-msteams-which-doesnt-match- | `unresolved_file` | — | — | — | `None` | `56354ff9be76…` |
