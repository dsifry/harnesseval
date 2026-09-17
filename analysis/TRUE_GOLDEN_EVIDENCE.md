# The True Golden Set — evidence pack (top-6 PRs)

**What this is.** For each of the six hardest benchmark PRs, every confirmed-bug finding from
the ENTIRE campaign (all models × frameworks × efforts; 2,416 healthy runs) was deduplicated
by an LLM judge into distinct REAL bugs. Every finding admitted here passed the adjudication
gate first — hallucinations and important_non_bug (nitpick) findings were excluded before
clustering. The result is the **true golden set**: the full upper bound of actual bugs in these
PRs, including everything the original Martian golden set missed.

**Counts.** 359 distinct real bugs across the 6 PRs (vs 42 goldens).
**Verification.** Each bug below carries a judge-produced verification card: location
(file:startline–endline, post-PR line numbers), a why-real explanation quoting the offending
code, and concrete replication steps. 10 cards are flagged `distinct=false` (the cluster may
contain two bugs) — kept for transparency. Open the code at the cited lines and follow the
replication steps to verify for yourself that this is a real bug, not a hallucination.

**Provenance.** Clustering: judge gpt-5.2, file-grouped `dedup_bugs_llm` prompt (branch
`sdlc-loop-experiment`), chunked per-file + cross-file merge to fixpoint; artifacts
`analysis/exp_union_semantic_pilot_<pr>.json` (2026-09-17, rj3-fixed dataset). Verification
cards: judge gpt-5.2 grounded in the PR patch (`gh`-cached diffs); artifacts
`analysis/semantic_true_golden_<pr>.json`. LLM steps are not deterministic; the stored
artifacts are the record. Adjudication verdicts (the gate) are the frozen rj3/in-run
instruments and are untouched.

| PR | goldens | true bugs | findings clustered | cells that found ≥1 |
|---|---|---|---|---|
| [11059](https://github.com/calcom/cal.com/pull/11059) | 9 | **83** | 1,543 | 69 |
| [4](https://github.com/ai-code-review-evaluation/discourse-graphite/pull/4) | 8 | **101** | 1,707 | 72 |
| [10](https://github.com/ai-code-review-evaluation/discourse-graphite/pull/10) | 7 | **41** | 1,308 | 77 |
| [8](https://github.com/ai-code-review-evaluation/discourse-graphite/pull/8) | 6 | **30** | 849 | 70 |
| [14740](https://github.com/calcom/cal.com/pull/14740) | 6 | **49** | 1,384 | 70 |
| [10967](https://github.com/calcom/cal.com/pull/10967) | 6 | **55** | 1,514 | 69 |

---

## PR 11059 — 83 distinct real bugs (9 goldens + 74 the goldens missed)
(<https://github.com/calcom/cal.com/pull/11059>)

### Bug index

| # | sev | location | title | found by (cells) |
|---|---|---|---|---|
| B1 | high | `packages/app-store/googlecalendar/lib/calendarservice.ts:94–105` | OAuth refresh in credential-sync returns a raw fetch Response but callers treat it as a token object (.data/fields), causing runtime failures and bad persistence | 40 |
| B2 | critical | `packages/app-store/salesforce/lib/calendarservice.ts:86–92` | Salesforce token refresh incorrectly checks response.statusText instead of response.ok, causing false failures | 38 |
| B3 | high | `apps/web/pages/api/webhook/app-credential.ts:62–88` | Non-atomic findFirst-then-create in webhook can create duplicate app credentials under concurrent requests | 35 |
| B4 | high | `packages/app-store/utils/oauth/parseRefreshTokenResponse.ts:6–15` | parseRefreshTokenResponse minimum Zod schema uses invalid computed keys, so expiry/metadata are never validated and are stripped when persisting credentials | 28 |
| B5 | high | `apps/web/pages/api/webhook/app-credential.ts:23–29` | Webhook secret validation uses non-constant-time string comparison (timing side-channel) and fragile header lookup | 27 |
| B6 | high | `packages/app-store/googlecalendar/lib/calendarservice.ts:97–101` | Google Calendar refresh flow persists Zod safeParse wrapper ({success,data}) as credential key | 26 |
| B7 | medium | `apps/web/pages/api/webhook/app-credential.ts:31–60` | Unhandled Zod/decrypt/JSON parse exceptions in webhook handler cause 500s instead of returning 4xx | 25 |
| B8 | critical | `packages/app-store/utils/oauth/refreshoauthtokens.ts:8–24` | Credential-sync token refresh request omits shared secret/Authorization header | 23 |
| B9 | high | `apps/web/pages/api/webhooks/app-credential.ts:17–90` | Webhook API handler performs credential create/update without restricting HTTP method (missing POST-only guard) | 20 |
| B10 | critical | `packages/app-store/salesforce/lib/calendarservice.ts:96–105` | Salesforce calendarservice references `prisma` without importing it | 19 |
| B11 | high | `apps/web/pages/api/webhook/app-credential.ts:49–85` | Webhook persists decrypted credential keys without validating per-app credential schema | 19 |
| B12 | high | `packages/app-store/_lib/refreshOAuthTokens.ts:55–92` | refreshOAuthTokens sync-path returns raw fetch Response (no response.ok check), but callers treat it like axios `.data` | 18 |
| B13 | high | `packages/app-store/utils/oauth/parserefreshtokenresponse.ts:25–26` | parseRefreshTokenResponse overwrites missing refresh token with literal "refreshtoken" sentinel | 18 |
| B14 | high | `apps/web/pages/api/webhook/app-credential.ts:62–80` | Webhook updates an arbitrary credential when user has multiple credentials for the same app | 18 |
| B15 | critical | `parseRefreshTokenResponse.ts:5–9` | Refresh-token response Zod schema uses computed keys that become a single literal "[object Object]", so dynamic/provider fields are stripped or parsing fails | 17 |
| B16 | critical | `packages/app-store/utils/oauth/refreshoauthtokens.ts:8–26` | OAuth token refresh can hang indefinitely because credential-sync fetch has no timeout/abort | 16 |
| B17 | high | `unknown (reports did not include a path; not in PR diff)` | Webhook secret is validated with non-constant-time comparison (timing side-channel) | 15 |
| B18 | critical | `packages/app-store/utils/oauth/parserefreshtokenresponse.ts:14–22` | Refresh token response is parsed with sync/minimal schema based on global sharing flags, corrupting provider-native credentials (e.g., Salesforce instanceUrl lost) | 15 |
| B19 | critical | `packages/app-store/office365calendar/lib/calendarservice.ts:263–264` | Missing refresh_token from sync response overwrites stored Office365 refresh token, permanently breaking credentials | 15 |
| B20 | high | `apps/webhook/app-credential.ts:55–70` | Unhandled exceptions in app-credential webhook: schema.parse + symmetricDecrypt + JSON.parse can crash request with 500 | 13 |
| B21 | medium | `.env.example:241–243` | .env.example suggests wrong-length AES-256 encryption key generation (24 bytes vs required 32) | 12 |
| B22 | critical | `packages/app-store/_utils/parseRefreshTokenResponse.ts:1–80` | parseRefreshTokenResponse overwrites missing refresh token with literal "refreshtoken", clobbering real stored credentials | 11 |
| B23 | critical | `packages/app-store/googlecalendar/lib/calendarservice.ts:92–98` | Google Calendar refresh persists Zod safeParse wrapper into credential.key, corrupting stored credentials | 10 |
| B24 | high | `refreshoauthtokens.ts:8–14` | OAuth credential-sync fetch ignores HTTP error status and blindly parses response as token JSON | 10 |
| B25 | high | `packages/app-store/_utils/oauth/parseRefreshTokenResponse.ts` | OAuth refresh parsing uses MinimumTokenResponseSchema and drops provider-required fields (e.g., Salesforce instance_url/expires_in), breaking downstream connections | 10 |
| B26 | high | `apps/api/pages/api/webhooks/app-credential.ts:44–93` | Race-prone findFirst-then-create in app-credential webhook can create duplicate credentials and later update an arbitrary row | 10 |
| B27 | high | `apps/web/pages/api/webhooks/app-credential.ts:24–27` | Webhook secret header lookup uses raw env header name, breaking auth due to lowercased req.headers keys | 10 |
| B28 | critical | `zoho-bigin/lib/calendarservice.ts:88–95` | Zoho Bigin refreshOAuthTokens called with credential.id instead of credential.userId (wrong user identity) | 9 |
| B29 | high | `apps/web/pages/api/webhook/app-credential.ts:24–33` | Webhook secret check uses non-constant-time string inequality and doesn’t normalize multi-value headers | 9 |
| B30 | high | `packages/app-store/zohocrm/lib/calendarservice.ts:204–225` | Zoho CRM calendar token refresh in sync mode treats fetch Response as Axios result, so `.data` is undefined and refreshed credentials are not applied | 9 |
| B31 | high | `apps/salesforcecalendar/lib/SalesforceCalendarService.ts:40–120` | SalesforceCalendarService refreshes OAuth tokens unconditionally via hardcoded login.salesforce.com, bypassing credential-sync path | 8 |
| B32 | critical | `packages/lib/credentialSync/parseRefreshTokenResponse.ts:41–55` | Missing refresh token is replaced with literal string "refreshtoken" and then persisted, corrupting stored OAuth credentials | 8 |
| B33 | critical | `apps/web/pages/api/webhook/app-credential.ts:23–27` | Webhook auth fails open when CALCOM_WEBHOOK_SECRET is unset (undefined equals missing header) | 8 |
| B34 | high | `apps/api/lib/integrations/salesforce/lib/calendarservice.ts:86–92` | Salesforce token refresh misclassifies successful responses by checking `response.statusText !== "ok"` instead of `response.ok` | 8 |
| B35 | critical | `apps/web/pages/api/webhook/app-credential.ts:23–90` | Instance-wide shared webhook secret allows overwriting any user's app credentials (no per-user binding/replay protection) | 8 |
| B36 | high | `packages/app-store/utils/oauth/refreshoauthtokens.ts:8–17` | OAuth token refresh via credential-sync treats non-2xx HTTP responses as successful token payloads | 8 |
| B37 | high | `packages/app-store/utils/oauth/parseRefreshTokenResponse.ts:19–21` | parseRefreshTokenResponse throws on schema mismatch and can crash calendar operations when callers don’t catch it | 8 |
| B38 | critical | `unknown (code path not included in PR diff; referenced by reports as the outbound fetch to `CALCOM_CREDENTIAL_SYNC_ENDPOINT` / `calcomcredentialsyncendpoint`):1–1` | Outbound credential-sync POST lacks any authentication/signature, enabling token harvesting via exposed sync endpoint | 7 |
| B39 | high | `packages/lib/integrations/parseRefreshTokenResponse.ts:5–27` | Zod schema uses computed keys that collapse to a single literal and strips token fields, breaking expiry/refresh-token parsing | 7 |
| B40 | high | `packages/app-store/salesforce/lib/calendarservice.ts:75–99` | SalesforceCalendarService eagerly refreshes OAuth token and writes DB on every instantiation (fragile success check) | 7 |
| B41 | high | `apps/web/pages/api/webhooks/app-credential.ts:85–135` | Webhook credential sync uses non-atomic findFirst→create/update, allowing duplicate credentials per user+app | 6 |
| B42 | high | `packages/app-store/utils/oauth/refreshOAuthTokens.ts:10–22` | OAuth refresh/sync identifies credentials only by userId + appSlug, so multi-account installs can overwrite the wrong credential | 6 |
| B43 | high | `packages/app-store/salesforce/lib/salesforceOAuth.ts:-1–-1` | Salesforce OAuth refresh bypasses refreshOAuthTokens so credential-sync endpoint is never used | 6 |
| B44 | high | `webhook/app-credential.ts:24–60` | App-credential webhook processes any HTTP method and persists unvalidated decrypted credential JSON | 6 |
| B45 | high | `packages/lib/constants.ts:92–92` | Feature-flag constant evaluates to raw encryption-key string instead of boolean, risking secret leakage | 5 |
| B46 | critical | `apps/googlecalendar/lib/calendarservice.ts:93–102` | Google OAuth refresh persists SafeParse wrapper instead of parsed credential key | 5 |
| B47 | high | `apps/api/src/ee/organizations/webhooks/app-credential.ts:57–89` | Webhook persists decrypted credential.key without validating against the app’s credential schema | 5 |
| B48 | high | `packages/app-store/office365calendar/lib/calendarservice.ts:258–264` | Outlook token refresh parse failures now throw a generic error and drop Microsoft/Zod diagnostics | 5 |
| B49 | ? | `?` | (untitled) | 5 |
| B50 | critical | `packages/app-store/zoho-bigin/lib/calendarservice.ts:128–140` | Zoho Bigin token refresh passes credentialId instead of Cal.com userId to refreshOAuthTokens (breaks sync / can mis-associate tokens) | 5 |
| B51 | high | `UNKNOWN (reports did not include file path; likely in the Lark/Webex/Teams token refresh adapter code handling the credential-sync/sharing mode):1–1` | Credential-sync token refresh path passes sync-endpoint payload into provider-specific response validators (Lark/Webex/Teams), causing refresh to always fail or persist invalid credentials | 4 |
| B52 | high | `packages/app-store/zoho-bigin/lib/calendarservice.ts:85–93` | Zoho Bigin refreshOAuthTokens called with credentialId instead of userId (calcomuserid mismatch) | 4 |
| B53 | critical | `packages/app-store/office365calendar/lib/CalendarService.ts:263–270` | Sync-endpoint token refresh overwrites stored OAuth refresh token with literal placeholder | 4 |
| B54 | high | `packages/app-store/salesforcecalendar/lib/SalesforceCalendarService.ts:1–1` | Salesforce calendar service eagerly refreshes OAuth token and overwrites credential.key, dropping previously stored fields | 4 |
| B55 | high | `apps/web/pages/api/webhook/app-credential.ts:72–80` | Webhook credential sync updates key but does not clear previously set invalid flag | 4 |
| B56 | high | `UNKNOWN (not in this PR diff) — locate by searching for the comment "the response should only contain the access token and expiry date" in the token refresh/sync helper:1–120` | Token refresh helper returns incompatible shapes (fetch Response vs provider token object), causing call-site runtime/type mismatches | 3 |
| B57 | high | `packages/app-store/sicrosoft-calendar/lib/SalesforceCalendarService.ts:55–125` | SalesforceCalendarService eagerly refreshes OAuth token on every construction and hard-fails on refresh errors, breaking otherwise-valid cached access tokens | 3 |
| B58 | high | `packages/app-store/lib/appCredentialSharingEnabled.ts:1–3` | `appCredentialSharingEnabled` computed via `&&` yields truthy strings (and can equal the encryption key), enabling sharing when env vars are set to `'false'` | 3 |
| B59 | high | `packages/app-store/office365video/lib/Office365VideoAdapter.ts:146–176` | Office365/Lark/Zoho adapters mis-parse /sync response, leaving token expiry undefined and preventing refresh | 3 |
| B60 | high | `packages/app-store/utils/oauth/parserefreshtokenresponse.ts:15–25` | Credential-sync predicate mismatch causes team-owned OAuth refresh to be parsed/validated with the wrong schema | 3 |
| B61 | high | `packages/app-store/lark/lib/getAccessToken.ts:1–120` | Some OAuth integrations refresh via refreshOAuthTokens but persist the raw sync response without parseRefreshTokenResponse normalization | 2 |
| B62 | critical | `packages/app-store/sicrosoft/lib/oauth/refreshAccessToken.ts:34–78` | Salesforce OAuth refresh bypasses refreshOAuthTokens and sends placeholder refresh_token under credential sync | 2 |
| B63 | ? | `?` | (untitled) | 2 |
| B64 | critical | `packages/app-store/zoho-bigin/** (search for the refreshOAuthTokens call in the Zoho Bigin sync/refresh code)` | Zoho Bigin token refresh passes credentialId as userId, causing sync to run under wrong Cal.com user identity | 2 |
| B65 | ? | `?` | (untitled) | 2 |
| B66 | high | `packages/app-store/office365calendar/lib/CalendarService.ts:240–285` | Office365 token refresh now throws on Zod schema mismatch without catch, risking unhandled rejection and breaking prior graceful degradation | 2 |
| B67 | high | `packages/lib/constants.ts:103–104` | `appcredentialsharingenabled` exports the encryption key string (truthy) instead of a boolean flag | 2 |
| B68 | critical | `packages/lib/integrations/oauth/parseRefreshTokenResponse.ts:18–33` | parseRefreshTokenResponse now throws on Zod safeParse failure, turning previously-graceful token refresh degradation into a hard failure | 1 |
| B69 | critical | `packages/lib/CalendarService/salesforceCalendarService.ts:86–96` | SalesforceCalendarService references prisma and HttpError without importing them | 1 |
| B70 | high | `unknown (not in PR diff); search in Google OAuth refresh/credential update code for `parseRefreshTokenResponse(` and `credential.update({ data: { key: ... } })`` | Google OAuth refresh persists unvalidated credential.key (schema validation bypass) in credential-sharing mode | 1 |
| B71 | high | `packages/app-store/zoho-crm/lib/credentials.ts:84–88` | Zoho CRM token expiry adds 3600ms instead of 1 hour, causing near-immediate expiration | 1 |
| B72 | critical | `UNKNOWN (not in PR diff) — locate the sync handler that reads req.body.userId and queries the local User table` | Cross-instance credential sync incorrectly trusts req.body.userId, attaching credentials to the wrong local user | 1 |
| B73 | critical | `UNKNOWN (sync-endpoint fetch call site not included in PR #11059 diff; reports provided no file/line refs)` | Sync-endpoint fetch has no timeout/abort and no fallback, allowing hangs to stall all calendar/video ops | 1 |
| B74 | high | `packages/app-store/_utils/oauth/refreshOAuthToken.ts:12–26` | Zod schema uses computed keys via `.toString()`, collapsing distinct keys into the same "[object Object]" property and dropping expiry fields | 1 |
| B75 | high | `.env.example:215–219` | Env-example instructs generating a 24-byte key while requiring 32 bytes for AES-256 credential sync encryption | 1 |
| B76 | high | `N/A (not specified in deduplicated reports; engineer should search for the webhook handler and OAuth callback code that does `findFirst` then `create` on the Credential table)` | Race condition: check-then-insert creates duplicate Credentials for same (userId, appId) without unique constraint | 1 |
| B77 | ? | `?` | (untitled) | 1 |
| B78 | critical | `apps/web/pages/api/webhook/app-credential.ts:1–12` | API route default-imports zod, making `z` undefined and crashing on module load | 1 |
| B79 | medium | `apps/web/pages/api/webhook/app-credential.ts:18–26` | Webhook secret check has no rate limiting, enabling unlimited online guessing/brute force | 1 |
| B80 | medium | `apps/web/pages/api/webhook/app-credential.ts:78–92` | Webhook app-credential sync updates keys but leaves credential type stale | 1 |
| B81 | ? | `?` | (untitled) | 1 |
| B82 | high | `packages/lib/CalendarService/SalesforceCalendarService.ts:-1–-1` | Salesforce CalendarService throws HttpError without importing it, causing ReferenceError on refresh failure | 1 |
| B83 | critical | `UNKNOWN (not provided in the deduplicated reports; PR diff does not include the affected file)` | Webhook credentials-write endpoint lacks rate limiting, enabling brute-force of shared secret and arbitrary credential writes | 1 |

### Verification cards

#### B1 — OAuth refresh in credential-sync returns a raw fetch Response but callers treat it as a token object (.data/fields), causing runtime failures and bad persistence

**Location:** `packages/app-store/googlecalendar/lib/calendarservice.ts:94–105`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The reports point to code around line 94 where the sync path does `const res = await refreshOAuthTokens(...)` and then reads token information via `res.data` / `token.accessToken`-style fields. In credential-sync mode, `refreshOAuthTokens` returns a raw `fetch` Response (no `.data` property), and its `() => any` signature hides this mismatch from TypeScript, so the code compiles but at runtime `res.data` is `undefined` and dereferencing token fields throws or leaves the integration using expired credentials. This is corroborated by parallel reports in HubSpot where the Response is cast to `HubSpotToken`, producing `undefined` fields and a `NaN` expiry date that gets persisted.

**How to replicate.** 1) Configure a Google Calendar (or HubSpot) integration and ensure the stored access token is expired but has a valid refresh token. 2) Trigger the "credential sync"/background sync path (not the interactive API path) that calls `refreshOAuthTokens`. 3) Observe that the refresh call returns a `fetch` Response; the code then attempts to read `res.data` or token fields from it. Expected: refreshed token fields are parsed from JSON and persisted/used. Actual: runtime TypeError when accessing `.data`/token fields, or undefined/NaN values are persisted, causing subsequent calendar API calls to fail and the credential to remain effectively expired.

**Found by** 40 cells (172 distinct report texts, 172 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium, van·xhigh; sonnet: MRV·high, MRV·medium, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·low, van·medium; terra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; astra: CE·high, CE·low, MRV·high, MRV·low

#### B2 — Salesforce token refresh incorrectly checks response.statusText instead of response.ok, causing false failures

**Location:** `packages/app-store/salesforce/lib/calendarservice.ts:86–92`  ·  **Severity:** critical  ·  **Judge confidence:** 0.68

**Why this is real.** The code reportedly treats refresh success as `response.statusText === "ok"` (e.g., `if (response.statusText?.toLowerCase() !== "ok") throw new HttpError(400, ...)`) rather than using `response.ok`/`response.status`. In Node/undici and HTTP/2, the HTTP reason phrase is commonly empty, so `statusText` may be `""` even on a 200 response; this makes the code throw on successful refresh responses. This is a functional correctness bug (it can reject valid token refreshes), not a style issue; the PR diff for this file is not included here, so this verification relies on the line-referenced reports.

**How to replicate.** 1) Configure the Salesforce app-store integration with a refresh token and exercise any codepath that initializes the Salesforce calendar service (e.g., create a booking that triggers calendar operations). 2) Run the server in an environment where fetch uses undici and/or HTTP/2 is negotiated to Salesforce; ensure the refresh endpoint returns HTTP 200 but an empty/mismatched reason phrase (statusText). 3) Observe: expected behavior is refresh succeeds and booking proceeds; actual behavior is the refresh call is treated as failure and throws an HTTP 400 (or equivalent), breaking the booking/calendar operation even though the refresh response was successful.

**Found by** 38 cells (97 distinct report texts, 97 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high; sonnet: CE·medium, MRV·high, MRV·medium, van·low; glm-flash: CE·high, CE·low, CE·medium; glm-vis: CE·high, CE·medium, van·high; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·xhigh; terra: CE·high, CE·low, MRV·high, MRV·low, MRV·medium, van·low; astra: CE·high, CE·low, MRV·high, MRV·low, MRV·medium, van·medium

#### B3 — Non-atomic findFirst-then-create in webhook can create duplicate app credentials under concurrent requests

**Location:** `apps/web/pages/api/webhook/app-credential.ts:62–88`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The handler does a non-atomic read-then-write: `const appCredential = await prisma.credential.findFirst({ where: { userId: reqBody.userId, appId: appMetadata.slug } ... })` and, if not found, proceeds to `await prisma.credential.create({ data: { ... userId: reqBody.userId, appId: appMetadata.slug ... } })`. Under concurrent first-time webhook deliveries for the same (userId, appId), both requests can observe no existing credential and both execute `create`, producing duplicate rows (or a unique-constraint error if one exists, which is not handled here). This is a real race condition because the check and insert are separate operations without a transaction/lock or an atomic upsert on a unique key.

**How to replicate.** 1) Ensure there is no existing `credential` row for a given `userId` and `appSlug` (mapped to `appMetadata.slug`). 2) Send two POST requests concurrently to `/api/webhook/app-credential` with identical JSON bodies `{ userId: X, appSlug: Y, keys: <valid encrypted payload> }` and valid webhook secret header. 3) Expected: exactly one credential exists for that user/app, and the request is idempotent. Actual: both requests can take the `findFirst` miss and both run `create`, resulting in two credentials for the same user/app (or one request failing with a DB unique constraint error/500 if uniqueness is enforced).

**Found by** 35 cells (46 distinct report texts, 46 findings): opus: CE·high, CE·low, MRV·low, van·medium, van·xhigh; sonnet: MRV·high, MRV·low, van·high; glm-flash: CE·high, CE·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-vis: CE·high, CE·medium, MRV·high, van·high, van·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·medium, van·high, van·medium, van·xhigh; terra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; astra: van·high

#### B4 — parseRefreshTokenResponse minimum Zod schema uses invalid computed keys, so expiry/metadata are never validated and are stripped when persisting credentials

**Location:** `packages/app-store/utils/oauth/parseRefreshTokenResponse.ts:6–15`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The reports point to `packages/app-store/utils/oauth/parseRefreshTokenResponse.ts:6` and `:8`, where the “minimum” token schema is built with computed object keys (e.g., using `z.number()` / `z.string()` as property names). In JS/TS object literals, non-string/symbol computed keys are stringified, so both computed keys collapse to the same string (typically `"[object Object]"`), meaning the intended “wildcard”/“numeric property holds expiry” contract is never enforced. Additionally, Zod objects default to stripping unknown keys, so any refresh-token response fields not explicitly enumerated (e.g., `expiryDate`, `instanceUrl`, `id`, `refreshToken`) are silently dropped during parsing, and the persisted credential loses required metadata for later use.

**How to replicate.** 1) Enable credential sync/sharing and connect an app that returns extra metadata on refresh (e.g., Salesforce returns `instanceUrl`/`id`, Office365/Salesforce may return expiry fields like `expiryDate`/`expires_in`).
2) Trigger a refresh flow that routes through `parseRefreshTokenResponse` (e.g., wait for access token expiry and force a calendar event fetch / sync).
3) Observe the stored credential record after refresh: expected it retains/updates expiry metadata and provider-specific fields (e.g., `expiryDate`, `instanceUrl`, `id`, possibly `refreshToken`). Actual: those fields are missing/undefined because the “minimum schema” failed to validate the intended expiry field and stripped unknown keys.
4) For Salesforce specifically, subsequent jsforce initialization fails or points at the wrong instance because `instanceUrl` is missing from persisted credentials; for Office365, stale/invalid expiry causes refresh loops or repeated failures because the system believes it has a refreshed token but lacks correct expiration data.

**Found by** 28 cells (65 distinct report texts, 65 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low; sonnet: CE·medium, MRV·high, MRV·medium; glm-flash: CE·high, CE·low, CE·medium; glm-vis: CE·high, CE·low, CE·medium, van·high; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·medium, van·medium; terra: CE·high, van·medium; astra: CE·high, CE·low

#### B5 — Webhook secret validation uses non-constant-time string comparison (timing side-channel) and fragile header lookup

**Location:** `apps/web/pages/api/webhook/app-credential.ts:23–29`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The handler validates the webhook secret with a direct `!==` comparison: `req.headers[process.env.CALCOM_WEBHOOK_HEADER_NAME || "calcom-webhook-secret"] !== process.env.CALCOM_WEBHOOK_SECRET` (lines 24–26). In JavaScript/Node, string equality is not guaranteed to be constant-time, so an attacker can potentially infer the secret via timing differences across many requests. Additionally, `req.headers` keys are normalized to lowercase by Node/Next.js, so using a mixed-case `CALCOM_WEBHOOK_HEADER_NAME` can cause the lookup to return `undefined`, making the check behave incorrectly (e.g., always 403 even with the correct header present).

**How to replicate.** 1) Run the app locally with `APP_CREDENTIAL_SHARING_ENABLED=true`, set `CALCOM_WEBHOOK_SECRET` to a known value (e.g., `supersecret`). 2) Timing side-channel: send many POST requests to `/api/webhook/app-credential` varying the secret so it matches progressively longer prefixes of `supersecret` (e.g., `s`, `su`, `sup`, ...) and measure average response times; because the code uses `!==` on strings, observed latency can correlate with how many leading characters match (expected: constant-time behavior; actual: potentially variable timing). 3) Header-name fragility: set `CALCOM_WEBHOOK_HEADER_NAME=Calcom-Webhook-Secret` (mixed case) and send a request with header `Calcom-Webhook-Secret: supersecret`; because `req.headers` is lowercased, the lookup misses and the endpoint returns `403 Invalid webhook secret` even though the correct header/value were supplied.

**Found by** 27 cells (52 distinct report texts, 52 findings): fable: van·high, van·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; sonnet: MRV·high, MRV·low, MRV·medium, van·high, van·xhigh; glm-flash: CE·high, CE·low, van·high, van·medium, van·xhigh; glm-vis: CE·high, CE·medium, van·high, van·low, van·medium

#### B6 — Google Calendar refresh flow persists Zod safeParse wrapper ({success,data}) as credential key

**Location:** `packages/app-store/googlecalendar/lib/calendarservice.ts:97–101`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** Multiple reports point to the same logic error around lines ~97–100: the refresh path assigns the return value of a parser that uses Zod `safeParse(...)` directly into the stored credential key (e.g., `key: parseRefreshTokenResponse(...)`). Because `safeParse` returns an envelope like `{ success, data }` (or `{ success, error }`) rather than the validated payload itself, this code persists the wrapper object instead of the Google credential fields. That corrupts the stored credential shape and breaks subsequent loads that expect the key to match the Google credential schema (access_token/refresh_token/etc.). (This file is not part of the PR diff provided; verification relies on the reported line references and the known Zod `safeParse` return contract.)

**How to replicate.** 1) Configure a Google Calendar integration with an expired access token but a valid refresh token stored in Cal.com.
2) Trigger any action that forces a token refresh (e.g., fetch calendar list or create an event) so the refresh-token code path runs.
3) Observe the DB row for the credential after refresh: expected `credential.key` to be an object containing Google token fields (e.g., `access_token`, `refresh_token?`, `expiry_date`, etc.); actual value becomes a Zod safeParse wrapper like `{ "success": true, "data": { ...token fields... } }`.
4) Trigger the same Google Calendar action again: expected it to read credentials and call Google APIs successfully; actual behavior fails/misbehaves because downstream credential parsing/loading sees an unexpected key shape (wrapper instead of token fields).

**Found by** 26 cells (70 distinct report texts, 70 findings): opus: CE·high, CE·low, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium; glm-vis: CE·high, CE·low, CE·medium, van·low; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·high, CE·low, MRV·high, MRV·medium; astra: CE·low, MRV·high, MRV·low, MRV·medium

#### B7 — Unhandled Zod/decrypt/JSON parse exceptions in webhook handler cause 500s instead of returning 4xx

**Location:** `apps/web/pages/api/webhook/app-credential.ts:31–60`  ·  **Severity:** medium  ·  **Judge confidence:** 0.87

**Why this is real.** The handler directly parses and decrypts caller-controlled input without any error handling: `const reqBody = appCredentialWebhookRequestBodySchema.parse(req.body);` and later `const keys = JSON.parse(symmetricDecrypt(reqBody.keys, process.env.CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY || ""));`. `zod.parse` throws a `ZodError` on malformed bodies, `symmetricDecrypt` can throw on invalid ciphertext/key, and `JSON.parse` throws on non-JSON plaintext. Because these exceptions are not caught, the Next.js API route will respond with a generic 500 (often including stack trace/details in dev), rather than a controlled 400/422 response for bad input.

**How to replicate.** 1) Run the app and call `POST /api/webhook/app-credential` with the correct webhook secret header (matching `process.env.CALCOM_WEBHOOK_SECRET`).
2) Send an invalid body, e.g. `{ "userId": "not-a-number", "appSlug": "zoom", "keys": "abc" }` (or omit required fields). Expected: a 400/422-style validation error response; Actual: the route throws from `zod.parse` and returns a 500.
3) Alternatively, send a syntactically valid body but with `keys` set to a random string that cannot be decrypted (or decrypted text that is not valid JSON). Expected: 4xx (bad request) indicating invalid encrypted payload; Actual: `symmetricDecrypt`/`JSON.parse` throws and the handler returns 500.

**Found by** 25 cells (46 distinct report texts, 46 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·xhigh; sonnet: CE·high, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, van·low; glm-vis: CE·high, CE·low, CE·medium, van·low; sol: CE·high, MRV·high, MRV·low, MRV·medium, van·medium; terra: MRV·medium

#### B8 — Credential-sync token refresh request omits shared secret/Authorization header

**Location:** `packages/app-store/utils/oauth/refreshoauthtokens.ts:8–24`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74

**Why this is real.** In `refreshoauthtokens.ts` (around line 8 per the reports), the code performs an outbound `fetch` to the configured credential-sync endpoint with headers that include only a content type (e.g., `{"Content-Type":"application/json"}`) and a JSON body containing only identifiers like `calcomuserid` and `appslug`. There is no `Authorization` header or shared-secret/signature header included, so the receiving token-minting endpoint has no cryptographic way to authenticate that the caller is Cal.com. This is a real security defect (not style): if the credential-sync endpoint is reachable and trusts these parameters, an attacker can request tokens for arbitrary user IDs/app slugs, or operators cannot securely enforce caller authentication.

**How to replicate.** 1) Open `packages/app-store/utils/oauth/refreshoauthtokens.ts` and find the outbound `fetch`/HTTP call to the credential-sync endpoint (line ~8). 2) Verify the request headers: confirm it does not set `Authorization` and does not set any shared-secret header (e.g., `x-calcom-secret`, `x-webhook-secret`, etc.), and that the body contains only `calcomuserid` and `appslug` (or equivalent). 3) If you can run locally: point the credential-sync endpoint to a test server that logs requests; trigger OAuth token refresh so this function runs; observe the incoming request contains only the IDs and no authentication secret. Expected (secure) behavior: a configured secret/signature is always sent so the endpoint can verify the caller; actual behavior: unauthenticated request.

**Found by** 23 cells (30 distinct report texts, 30 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·xhigh; glm-flash: CE·high; glm-vis: CE·high, CE·low, van·high, van·medium; sol: CE·high, CE·medium, MRV·high, MRV·medium, van·high, van·medium, van·xhigh; terra: CE·high, CE·low, CE·medium

#### B9 — Webhook API handler performs credential create/update without restricting HTTP method (missing POST-only guard)

**Location:** `apps/web/pages/api/webhooks/app-credential.ts:17–90`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The handler is defined as `export default async function handler(req, res)` and immediately starts processing auth/body (`const reqBody = appCredentialWebhookRequestBodySchema.parse(req.body);`) without any `req.method` validation. Later it performs writes unconditionally via `await prisma.credential.update(...)` and `await prisma.credential.create(...)`. Because there is no `if (req.method !== "POST") return res.status(405)...` guard, non-POST requests (GET/PUT/DELETE, etc.) that include the secret header can reach the same credential-mutation code path instead of being rejected.

**How to replicate.** 1) Ensure the deployed app has `APP_CREDENTIAL_SHARING_ENABLED` true and you know/configure `CALCOM_WEBHOOK_SECRET` and `CALCOM_WEBHOOK_HEADER_NAME` (or use default `calcom-webhook-secret`).
2) Send a non-POST request (e.g., PUT or GET) to the webhook route for this file with headers: `{<webhook-header-name>: <CALCOM_WEBHOOK_SECRET>, "Content-Type": "application/json"}` and a JSON body matching the schema: `{ "userId": <existing user id>, "appSlug": "<existing app slug>", "keys": "<encrypted string>" }`.
3) Observe the response is `200` with "Credentials created..." or "Credentials updated..." and the credential row is created/modified.
Expected behavior: non-POST methods should return `405 Method Not Allowed` and must not attempt to parse body or mutate credentials.

**Found by** 20 cells (35 distinct report texts, 35 findings): fable: van·low; opus: CE·high, CE·medium, van·high, van·low, van·medium, van·xhigh; sonnet: CE·high, van·high, van·low; glm-flash: CE·medium; glm-vis: CE·high, CE·medium, MRV·low, MRV·medium, van·high, van·low, van·medium; sol: van·low, van·medium

#### B10 — Salesforce calendarservice references `prisma` without importing it

**Location:** `packages/app-store/salesforce/lib/calendarservice.ts:96–105`  ·  **Severity:** critical  ·  **Judge confidence:** 0.78

**Why this is real.** Multiple independent reports point to post-PR line ~96 where the module calls into Prisma (e.g., a persistence/update call like `await prisma.<model>...`) but there is no corresponding `import prisma from ...` (or equivalent Prisma client initialization) at the top of `calendarservice.ts`. In TypeScript, this produces a compile-time error ("Cannot find name 'prisma'") and, if somehow emitted, a runtime `ReferenceError: prisma is not defined` when the refresh/persist path executes. The PR diff for this file is not provided here, so this verification relies on the consistent line-specific evidence from the deduplicated reports.

**How to replicate.** 1) Check out the PR branch/commit and open `packages/app-store/salesforce/lib/calendarservice.ts`.
2) Navigate to around line 96 and confirm there is a statement using `prisma` (e.g., `await prisma...`) while the top of the file lacks any import/definition for `prisma`.
3) Run a TypeScript build/typecheck for the repo or package (e.g., `pnpm -r build` or `pnpm -C packages/app-store/salesforce build`).
Expected: build succeeds. Actual: TypeScript fails with an error indicating `prisma` is undefined/unresolved in `calendarservice.ts`.
(If typechecking is bypassed, trigger the token refresh path in the Salesforce integration; execution will throw `ReferenceError: prisma is not defined` when that line runs.)

**Found by** 19 cells (29 distinct report texts, 29 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·high, CE·medium, MRV·high, MRV·medium; sol: CE·high, CE·low, MRV·medium; terra: CE·high, CE·low, MRV·high, MRV·low; astra: CE·high, MRV·medium

#### B11 — Webhook persists decrypted credential keys without validating per-app credential schema

**Location:** `apps/web/pages/api/webhook/app-credential.ts:49–85`  ·  **Severity:** high  ·  **Judge confidence:** 0.80

**Why this is real.** The handler decrypts and parses attacker-controlled JSON and writes it directly into the credential record: `const keys = JSON.parse(symmetricDecrypt(...))` (lines 50-52) and then `data: { key: keys }` in both the update (lines 69-75) and create (lines 79-85) paths. Although the request body is Zod-validated, only `keys` being a string is checked; there is no validation that the decrypted `keys` matches the selected app's expected credential shape. This can silently persist malformed credential objects that downstream app/provider code cannot consume, causing later runtime failures while this endpoint still returns 200.

**How to replicate.** 1) Ensure `APP_CREDENTIAL_SHARING_ENABLED` is true and set `CALCOM_WEBHOOK_SECRET`, `CALCOM_WEBHOOK_HEADER_NAME` (or use default `calcom-webhook-secret`), and `CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY`.
2) Pick an existing userId and an existing appSlug present in `appStoreMetadata`.
3) Send a POST request to `/api/webhook/app-credential` with the correct webhook secret header and a body where `keys` is a valid AES-encrypted JSON string that decrypts to an invalid shape for that app (e.g., `"not-an-object"`, `{}`, or missing required fields that the provider expects).
4) Observe the endpoint returns 200 and the credential row is created/updated with `credential.key` equal to the malformed decrypted value.
Expected: endpoint should reject (400) when decrypted keys don't match the app's credential schema. Actual: endpoint accepts and persists malformed keys, which later cause failures when the app integration tries to use/refresh the credential.

**Found by** 19 cells (26 distinct report texts, 26 findings): opus: CE·low, MRV·high, MRV·low, MRV·medium, van·medium, van·xhigh; sonnet: MRV·high, MRV·low; glm-flash: CE·high, van·high, van·medium, van·xhigh; glm-vis: CE·medium; sol: CE·low, CE·medium, van·low, van·medium; terra: CE·high, MRV·medium

#### B12 — refreshOAuthTokens sync-path returns raw fetch Response (no response.ok check), but callers treat it like axios `.data`

**Location:** `packages/app-store/_lib/refreshOAuthTokens.ts:55–92`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** In the sync/credential-sharing branch, the code does `const response = await fetch(calcomCredentialSyncEndpoint, ...)` and then returns the raw `response` without checking `response.ok` or parsing JSON (e.g., `return response`). Downstream callers (e.g., Zoho CRM/Bigin and Google refresh flows per the reports) read `tokenInfo.data` / `res?.data` as if this were an axios response object, so `data` is `undefined` and accessing token fields throws at runtime. Additionally, because `response.ok` is never validated, a 4xx/5xx HTML/error page from the sync endpoint is passed downstream and treated as a “successful” token response, causing confusing failures during parsing/field access. (The provided evidence pack notes this file is not part of the PR diff; this verification relies on the clustered reports’ description of the offending lines/behavior.)

**How to replicate.** 1) Configure an integration that uses refreshOAuthTokens (e.g., Google Calendar or Zoho CRM) with credential sharing/sync enabled so the calcomCredentialSyncEndpoint fetch path is taken. 2) Make the credential sync endpoint return a non-2xx response (e.g., temporarily misconfigure auth headers, force a 401/500, or point to a test endpoint returning an error page). 3) Trigger a refresh (e.g., run a sync job or perform an API call that requires token refresh). Expected: refreshOAuthTokens should throw on non-2xx and/or return parsed token JSON in a consistent shape. Actual: it returns a fetch Response even on 4xx/5xx; callers read `.data` and/or token fields and crash with a TypeError (or attempt to parse an error page as token data).

**Found by** 18 cells (130 distinct report texts, 130 findings): fable: van·low; opus: van·xhigh; sonnet: van·low, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; terra: van·medium

#### B13 — parseRefreshTokenResponse overwrites missing refresh token with literal "refreshtoken" sentinel

**Location:** `packages/app-store/utils/oauth/parserefreshtokenresponse.ts:25–26`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** The reports consistently point to lines ~25–26 where a missing refresh token is defaulted to the literal string "refreshtoken" (e.g., logic equivalent to `... refresh_token: response.refresh_token ?? "refreshtoken" ...`). This is a functional defect because the fabricated sentinel is then treated as a real credential value and can be persisted, corrupting stored OAuth credentials and potentially overwriting an existing valid refresh token. The file is not part of the PR diff here, so this verification relies on the reporters’ line references and description of the exact assignment behavior.

**How to replicate.** 1) Find `parseRefreshTokenResponse` in `packages/app-store/utils/oauth/parserefreshtokenresponse.ts` and locate the assignment around lines 25–26 that sets `refresh_token` (or similar) to `"refreshtoken"` when absent. 2) Trigger a refresh-token flow where the provider does NOT return `refresh_token` on refresh (common behavior), but the app still updates/persists the returned token payload (e.g., via `refreshOAuthTokens`/credential update path). 3) Observe stored credentials: expected behavior is to keep the previously stored valid refresh token unchanged; actual behavior is the stored refresh token becomes the literal string "refreshtoken", breaking subsequent refreshes and causing authentication failures.

**Found by** 18 cells (42 distinct report texts, 42 findings): fable: van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium, van·xhigh; sonnet: CE·high, MRV·medium; glm-vis: CE·high; sol: CE·high, MRV·high, MRV·medium; terra: MRV·low, MRV·medium; astra: CE·low

#### B14 — Webhook updates an arbitrary credential when user has multiple credentials for the same app

**Location:** `apps/web/pages/api/webhook/app-credential.ts:62–80`  ·  **Severity:** high  ·  **Judge confidence:** 0.92

**Why this is real.** The handler locates an existing credential using `prisma.credential.findFirst({ where: { userId: reqBody.userId, appId: appMetadata.slug } })` (lines 62-70), which is non-unique when a user can connect multiple accounts for the same integration. Because there is no additional account/credential identifier and no deterministic `orderBy`, `findFirst` may return any matching row; the subsequent `prisma.credential.update({ where: { id: appCredential.id }, data: { key: keys } })` (lines 73-80) will overwrite whichever credential happened to be returned, potentially clobbering the wrong connected account's tokens.

**How to replicate.** 1) In the database, create (or via UI connect) two credentials for the same user and same app slug (same `userId` and same `appId`) but representing different connected accounts (two rows in `credential`).
2) Call this endpoint with a valid webhook secret header and body containing that `userId`, the app's `appSlug`, and `keys` for only one of the accounts.
3) Observe that exactly one existing credential row gets updated, but which row is updated is not guaranteed (depends on DB/prisma row selection); expected behavior would be to update the specific intended credential/account, while actual behavior can overwrite the other account's credential key and break its associations.

**Found by** 18 cells (23 distinct report texts, 23 findings): fable: van·high; opus: CE·high, CE·medium, MRV·high, van·xhigh; sonnet: van·xhigh; glm-vis: MRV·high; sol: CE·medium, MRV·high, MRV·medium, van·medium, van·xhigh; terra: MRV·high, MRV·medium; astra: CE·high, MRV·high, MRV·low, MRV·medium

#### B15 — Refresh-token response Zod schema uses computed keys that become a single literal "[object Object]", so dynamic/provider fields are stripped or parsing fails

**Location:** `parseRefreshTokenResponse.ts:5–9`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74

**Why this is real.** The code defines a Zod object schema with computed property names like `[z.string().toString()]: z.number()` / `[z.string().toString()]: z.string()` (reported at `parseRefreshTokenResponse.ts:5-9`). In JavaScript, `z.string()` is an object and `.toString()` on it yields the constant string `"[object Object]"`, so this does not create a wildcard/catch-all key; it creates one literal key, and the second declaration overwrites the first. Because `z.object()` strips unknown keys by default and the literal key is not present in real OAuth refresh responses, provider-specific fields (e.g., `expiry_date`, `expires_in`, `instance_url`) are dropped or validation fails, leading to undefined/NaN expiry data and broken refresh flows.

**How to replicate.** 1) In a Node/TS REPL or unit test, import the schema/function that parses refresh-token responses (in `parseRefreshTokenResponse.ts`). 2) Call it with a realistic refresh response object that includes provider-specific keys, e.g. `{ access_token: 'a', refresh_token: 'r', expires_in: 3600, expiry_date: 1710000000000, instance_url: 'https://example' }` and does NOT include a key literally named "[object Object]". 3) Observe that parsing either fails (if the literal key is required) or succeeds but silently drops `expiry_date`/`instance_url` (default `z.object` unknown-key stripping), causing downstream code to compute expiry from `undefined` (NaN) or persist incomplete credentials; subsequent refresh attempts then error or use bad stored credentials.

**Found by** 17 cells (64 distinct report texts, 64 findings): opus: van·medium, van·xhigh; sonnet: van·high; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium; terra: van·xhigh

#### B16 — OAuth token refresh can hang indefinitely because credential-sync fetch has no timeout/abort

**Location:** `packages/app-store/utils/oauth/refreshoauthtokens.ts:8–26`  ·  **Severity:** critical  ·  **Judge confidence:** 0.78

**Why this is real.** The reported code path does an awaited network call like `const response = await fetch(process.env.calcomcredentialsyncendpoint, { ... })` without providing an `AbortSignal`/timeout, so if the credential-sync service stalls or never responds, this `await` can block the refresh flow indefinitely. Reports also indicate there is no `response.ok` check before consuming the body (e.g., treating non-2xx responses as token payload), meaning failures from the sync endpoint can be propagated as invalid "tokens" rather than a handled error. The PR diff does not include this file, so this verification relies on the line-referenced reports pointing to the offending `fetch(...)` and subsequent response handling in the post-PR tree.

**How to replicate.** 1) Set the credential sync endpoint env var (e.g., `CALCOM_CREDENTIAL_SYNC_ENDPOINT` / `process.env.calcomcredentialsyncendpoint`) to a host/URL that accepts TCP but never responds (or a blackholed IP). 2) Trigger any request path that needs an OAuth refresh (e.g., booking flow or calendar integration call when the stored access token is expired so refresh is invoked). 3) Observe the request: expected behavior is a bounded failure (timeout + error response) within a reasonable time; actual behavior is the request hangs indefinitely waiting on the `await fetch(...)` to resolve. 4) Optionally, point the endpoint to return a non-2xx (e.g., 500 with JSON body) and observe that, without `response.ok` handling, the code can attempt to parse/use the error body as if it were a token response.

**Found by** 16 cells (18 distinct report texts, 18 findings): opus: CE·low, MRV·high; sonnet: MRV·high; glm-flash: CE·low; sol: CE·low, MRV·high, MRV·low, MRV·medium; terra: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; astra: MRV·high, MRV·low, MRV·medium

#### B17 — Webhook secret is validated with non-constant-time comparison (timing side-channel)

**Location:** `unknown (reports did not include a path; not in PR diff)` (exact lines not in diff)  ·  **Severity:** high  ·  **Judge confidence:** 0.56

**Why this is real.** The clustered reports consistently state the webhook authentication checks the provided secret using a plain inequality operator (e.g., `providedSecret !== process.env.CALCOM_WEBHOOK_SECRET`) rather than a constant-time primitive like `crypto.timingSafeEqual`. String/byte comparisons that short-circuit on the first mismatching character leak timing information, which can be used to iteratively guess the secret over many requests. Because the relevant file was not part of this PR’s diff and no line references were provided, this verification relies on the reports’ description of the specific offending construct (`!==` comparison of the webhook secret).

**How to replicate.** 1) Locate the webhook handler that authenticates requests using the `CALCOM_WEBHOOK_SECRET` (or similarly named) env var and confirm the code compares the incoming header/secret using `!==`/`===` on strings. 2) Run the server locally with a known webhook secret set. 3) Send many requests to the webhook endpoint with candidate secrets that share increasing correct prefixes (e.g., 'a', 'ab', 'abc', ...), measuring response times (e.g., with a script that uses `process.hrtime.bigint()` around `fetch`/`curl` and averages over thousands of requests). 4) Expected (secure) behavior: response time should not correlate with the number of correct leading characters. Actual (bug): average latency trends upward as the prefix becomes more correct, indicating a timing side-channel that can help brute-force the secret.

**Found by** 15 cells (23 distinct report texts, 23 findings): fable: van·medium; opus: van·xhigh; sonnet: van·low, van·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, van·low; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·medium

#### B18 — Refresh token response is parsed with sync/minimal schema based on global sharing flags, corrupting provider-native credentials (e.g., Salesforce instanceUrl lost)

**Location:** `packages/app-store/utils/oauth/parserefreshtokenresponse.ts:14–22`  ·  **Severity:** critical  ·  **Judge confidence:** 0.86

**Why this is real.** The bug is in the schema-selection branch around line ~15 that multiple reports quote as effectively: `if (appCredentialSharingEnabled && process.env.CALCOM_CREDENTIAL_SYNC_ENDPOINT) { /* use minimal/broker schema */ } else { /* use caller/provider schema */ }`. This couples parsing/validation to global configuration (sharing + sync endpoint) instead of the actual refresh path (sync endpoint vs direct provider refresh), so a provider-native refresh response can be parsed with the minimal schema. Because the minimal Zod schema strips unknown keys, required provider fields (e.g., Salesforce `instanceUrl`, expiry fields, real `refresh_token`) are dropped and the resulting truncated object is persisted, breaking downstream consumers like jsforce.

**How to replicate.** 1) Configure an environment where credential sharing is enabled and `CALCOM_CREDENTIAL_SYNC_ENDPOINT` is set. 2) Use a team-owned credential (i.e., `userId`/`userid` is null) for a provider that returns extra fields on refresh (Salesforce is a clear example: response includes `instance_url`; Google/Office365 include expiry/refresh fields). 3) Trigger a token refresh that falls back to the provider refresh flow for null-userid credentials (as described in the reports for `refreshoauthtokens`). 4) Observe that `parseRefreshTokenResponse` still chooses the sync/minimal schema due to the global flag check, so the parsed object only retains minimal fields (e.g., access token) and drops `instanceUrl` / real refresh token / expiry. 5) After the subsequent `prisma.credential.update`, the stored credential key is missing those fields; expected: provider-native fields remain present (e.g., jsforce connection can read `instanceUrl`), actual: connection/refresh logic breaks due to missing persisted fields.

**Found by** 15 cells (22 distinct report texts, 22 findings): opus: MRV·high, MRV·medium; glm-flash: CE·medium, van·high; glm-vis: CE·low, MRV·high, MRV·low, van·medium; sol: CE·low, MRV·high, MRV·medium, van·xhigh; terra: CE·high, MRV·low, MRV·medium

#### B19 — Missing refresh_token from sync response overwrites stored Office365 refresh token, permanently breaking credentials

**Location:** `packages/app-store/office365calendar/lib/calendarservice.ts:263–264`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74

**Why this is real.** Per the clustered reports, the refresh path parses a response that may omit a refresh token, then persists it by merging/spreading the response over the existing stored credentials (e.g., `{...o365authcredentials, ...tokenresponse.data}` around lines 263–264). If Microsoft does not rotate/return `refreshToken`, the merged object replaces the previously valid stored `refreshToken` with an invalid placeholder like the literal string `"refreshtoken"` (or `undefined`), causing irreversible data loss and forcing re-auth on the next refresh. The PR diff doesn’t include this file content here, so verification is based on the referenced line numbers in the reports.

**How to replicate.** 1) Start with a working Office365 credential in Cal.com whose stored credential.key contains a valid `refreshToken`.
2) Configure/enable the shared “sync” token refresh endpoint mode that can return a minimal token payload (access token + expiry) and does NOT include `refreshToken` when Microsoft doesn’t rotate it.
3) Trigger a token refresh (wait until near expiry, or invoke the refresh path).
Expected: the existing stored `refreshToken` is preserved when the response omits it.
Actual: the code spreads `tokenresponse.data` over existing credentials, so the stored `refreshToken` becomes the placeholder/undefined and is persisted; the next refresh attempt fails, effectively bricking the integration until the user re-auths.

**Found by** 15 cells (20 distinct report texts, 20 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high; glm-flash: CE·medium; glm-vis: CE·low, CE·medium; sol: CE·high, MRV·high, MRV·medium; terra: MRV·low, MRV·medium

#### B20 — Unhandled exceptions in app-credential webhook: schema.parse + symmetricDecrypt + JSON.parse can crash request with 500

**Location:** `apps/webhook/app-credential.ts:55–70`  ·  **Severity:** high  ·  **Judge confidence:** 0.66

**Why this is real.** The clustered reports all point to the same unguarded pattern around line ~55: `const body = schema.parse(req.body);` followed by `JSON.parse(symmetricDecrypt(...))` (often with a `|| ""` fallback). Both `schema.parse(...)` (Zod) and `JSON.parse(...)` throw on invalid input, and `symmetricDecrypt(...)` can throw on a wrong key/corrupted ciphertext; without try/catch or `safeParse`, any malformed request or bad/misconfigured encryption key reliably yields an unhandled 500 rather than a controlled 4xx. This is a functional error-handling bug (not style), because it allows attacker-controlled payloads to deterministically crash the handler and potentially leak stack/error details depending on server config; the PR diff is not provided here, so this verification relies on the line-specific references from the reports.

**How to replicate.** 1) Find the webhook handler in `apps/webhook/app-credential.ts` around line 55 where it parses the request body with `schema.parse` and then does `JSON.parse(symmetricDecrypt(...))` without a try/catch. 2) Send a request to that webhook route with (a) a malformed body that violates the Zod schema, or (b) a body that passes schema validation but includes an invalid/truncated ciphertext for the encrypted field, or (c) run with an incorrect encryption key so decrypt returns non-JSON/throws. 3) Observe: expected behavior is a clean 400/422 like "invalid payload"; actual behavior is an unhandled exception producing HTTP 500 (and potentially stack/error details) and causing webhook senders to retry.

**Found by** 13 cells (32 distinct report texts, 32 findings): fable: van·low; opus: van·low, van·medium, van·xhigh; glm-flash: CE·low, CE·medium, MRV·high, MRV·medium; glm-vis: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### B21 — .env.example suggests wrong-length AES-256 encryption key generation (24 bytes vs required 32)

**Location:** `.env.example:241–243`  ·  **Severity:** medium  ·  **Judge confidence:** 0.78

**Why this is real.** The .env.example comment around lines 241-243 reportedly states the key "must be 32 bytes for aes256" but then recommends generating it with `openssl rand -base64 24`. That command produces 24 random bytes (encoded to ~32 Base64 characters), which contradicts the stated 32-byte requirement and conflates bytes with Base64 string length. This is a real defect because it can lead users to configure an invalid/shorter-than-intended key for AES-256, weakening security or causing runtime key-length validation failures depending on how the application consumes the value.

**How to replicate.** 1) Open `.env.example` and locate the `CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY` (or similarly named) comment at ~lines 241-243. 2) Observe that it claims the key must be 32 bytes for AES-256 but suggests `openssl rand -base64 24`. 3) Run `openssl rand -base64 24 | base64 -d | wc -c` and observe the decoded byte count is 24 (actual) not 32 (expected per comment). 4) (If the app validates key length) set the env var to that generated value and start the app / trigger credential encryption; expected: accepts a 32-byte key; actual: either rejects due to length mismatch or silently uses a shorter-than-intended key.

**Found by** 12 cells (17 distinct report texts, 17 findings): opus: CE·medium, van·high, van·medium; sonnet: MRV·medium, van·low, van·medium; glm-flash: MRV·high, MRV·medium, van·low, van·medium; glm-vis: MRV·medium; sol: van·low

#### B22 — parseRefreshTokenResponse overwrites missing refresh token with literal "refreshtoken", clobbering real stored credentials

**Location:** `packages/app-store/_utils/parseRefreshTokenResponse.ts:1–80`  ·  **Severity:** critical  ·  **Judge confidence:** 0.62

**Why this is real.** The clustered reports all describe the same concrete defect: when the provider response omits a refresh token, the parser assigns a placeholder string (e.g., `data.refreshtoken = "refreshtoken"` / `refreshtoken ?? "refreshtoken"`) instead of leaving it undefined. Because downstream code spreads/merges `tokenResponse.data` over existing stored credentials and persists it, that placeholder literal is written to the DB, overwriting the user’s real refresh token; this permanently breaks future token refresh. The PR diff/line refs are not included in the evidence pack, so verification relies on reading the post-PR implementation of `parseRefreshTokenResponse` and the credential persistence call site that persists its output.

**How to replicate.** 1) Use an integration flow where the "sync" token endpoint (or any token refresh endpoint) returns only `accessToken` + `expiry` (no refresh token), as described for the credential-sharing/sync mode. 2) Trigger a refresh so the code path calls `parseRefreshTokenResponse(response)` and then persists/updates the credential using the returned `data` (commonly via object spread into existing credentials). 3) Inspect the stored credential record: expected behavior is the original refresh token remains unchanged; actual behavior is the refresh token field becomes the literal string "refreshtoken". 4) Trigger another refresh: it fails because the refresh token is invalid junk.

**Found by** 11 cells (19 distinct report texts, 19 findings): glm-flash: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### B23 — Google Calendar refresh persists Zod safeParse wrapper into credential.key, corrupting stored credentials

**Location:** `packages/app-store/googlecalendar/lib/calendarservice.ts:92–98`  ·  **Severity:** critical  ·  **Judge confidence:** 0.76

**Why this is real.** Multiple reports consistently point to the same mechanism: `parseRefreshTokenResponse(...)` returns a Zod `safeParse` result object shaped like `{ success, data, error }`, but the Google Calendar service then persists that whole object as the credential payload (e.g., `const key = parseRefreshTokenResponse(...);` followed by `prisma.credential.update({ data: { key } })`). Storing the wrapper instead of `key.data` changes the on-disk schema from the expected Google credentials shape to `{success:true,data:{...}}`, so later code that does `googleCredentialSchema.parse(credential.key)` or reads `credential.key.accessToken/refreshToken/expiryDate` will fail or return `undefined`. The PR diff does not include this file, so verification relies on reading the current code at the referenced lines in the post-PR tree.

**How to replicate.** 1) Connect Google Calendar (create a Credential row with a valid `credential.key` matching the Google credential schema). 2) Let the access token expire or force a refresh (invoke the codepath that calls the refresh-token endpoint and then updates the DB). 3) Observe the DB update: `credential.key` is written as `{ success: true, data: { accessToken, refreshToken, expiryDate, ... } }` instead of the plain credentials object. 4) On the next load/use, parsing/field access fails (schema parse throws or `credential.key.accessToken` is undefined), and Google Calendar API calls start failing until the user re-authenticates.

**Found by** 10 cells (28 distinct report texts, 28 findings): glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, MRV·high, MRV·medium

#### B24 — OAuth credential-sync fetch ignores HTTP error status and blindly parses response as token JSON

**Location:** `refreshoauthtokens.ts:8–14`  ·  **Severity:** high  ·  **Judge confidence:** 0.66

**Why this is real.** The reported code at `refreshoauthtokens.ts:8-14` performs a `fetch(...)` to the credential sync endpoint and then proceeds as if it succeeded, without checking `response.ok` / status. Reviewers describe the pattern as effectively `const res = await fetch(...); return await res.json()` (or passing the body downstream), meaning a 4xx/5xx (including an HTML error page) will be treated as a token payload and later parsed as refresh/access token JSON, causing opaque runtime failures. This file is not part of the PR diff, so verification relies on the cited line range and reviewers’ consistent description of the missing `response.ok` check/error handling.

**How to replicate.** 1) Configure the app so the credential-sync URL (the endpoint used by `refreshoauthtokens.ts`) points to a server you control (or temporarily proxy it) that returns HTTP 500 with a non-JSON body (e.g., an HTML error page). 2) Trigger the OAuth token refresh path that calls `refreshOAuthTokens` (e.g., perform an action requiring a fresh access token for an installed app). Expected: the code should detect non-2xx, log/handle the upstream failure, and return a controlled error. Actual: the code attempts to parse/use the error response as token JSON, resulting in a JSON parse error or downstream token parsing exception that bubbles up and breaks the flow (e.g., booking/integration calls fail).

**Found by** 10 cells (23 distinct report texts, 23 findings): fable: van·low, van·medium; opus: van·medium, van·xhigh; glm-flash: CE·low; glm-vis: CE·high, CE·low, CE·medium; sol: van·high; terra: van·high

#### B25 — OAuth refresh parsing uses MinimumTokenResponseSchema and drops provider-required fields (e.g., Salesforce instance_url/expires_in), breaking downstream connections

**Location:** `packages/app-store/_utils/oauth/parseRefreshTokenResponse.ts` (exact lines not in diff)  ·  **Severity:** high  ·  **Judge confidence:** 0.60

**Why this is real.** The deduplicated reports all point to the same defect: `parseRefreshTokenResponse` parses refresh responses with a “minimum” schema and then returns/persists only a subset of fields, omitting provider-required fields like `instance_url` (Salesforce) and expiry (`expires_in`/`expiry`). This means consumers later receive credentials with `instanceUrl === undefined` (failing `jsforce.Connection({ instanceUrl })`) and/or no expiry metadata (causing repeated refresh attempts). The PR link does not include the `jsforce.conn` file in the diff, so this verification relies on the reports’ consistent description of the parse/persist contract mismatch.

**How to replicate.** 1) Configure Cal.com in credential-sharing/team mode (so the code path chooses the “minimum token response” parsing). 2) Connect a Salesforce integration and trigger a refresh (e.g., force an access token refresh or enable sync that refreshes tokens). 3) Observe the stored credential payload after refresh: `instanceUrl` is missing/undefined and/or expiry fields are absent. 4) Trigger a sync that constructs a jsforce connection from the stored credential: expected: jsforce connects using a valid `instanceUrl`; actual: connection fails because `instanceUrl` is undefined, or the system repeatedly refreshes because expiry info was stripped.

**Found by** 10 cells (19 distinct report texts, 19 findings): glm-flash: CE·high, CE·low, CE·medium, MRV·high, van·xhigh; glm-vis: CE·low, CE·medium, MRV·high, MRV·low; sol: van·xhigh

#### B26 — Race-prone findFirst-then-create in app-credential webhook can create duplicate credentials and later update an arbitrary row

**Location:** `apps/api/pages/api/webhooks/app-credential.ts:44–93`  ·  **Severity:** high  ·  **Judge confidence:** 0.56

**Why this is real.** The webhook logic reportedly does a read-then-write sequence like `const existing = await prisma.credential.findFirst({ where: { userId, appId } })` followed by `if (!existing) await prisma.credential.create(...) else await prisma.credential.update({ where: { id: existing.id }, ... })`. This is non-atomic: two concurrent (or retried) deliveries can both observe `existing === null` and both execute `create`, producing duplicate rows for the same logical key (userId+appId). Additionally, the `findFirst` has no `orderBy`, so if duplicates already exist, which row gets updated is nondeterministic. (The referenced file/lines are not part of this PR’s diff per the report cluster; verification requires opening this webhook handler in the post-PR tree and confirming the above pattern.)

**How to replicate.** 1) Ensure there is no unique constraint preventing duplicates on the credential table for the logical key (userId+appId/appSlug).
2) Trigger the app-credential webhook endpoint twice concurrently with the same payload (same userId and appId/appSlug), e.g., by sending two parallel POST requests or by forcing a retry while the first request is still in-flight.
3) Expected: exactly one credential row exists for that user+app and subsequent deliveries deterministically update it.
4) Actual: two credential rows are created. On later webhook deliveries, the code’s `findFirst` (without `orderBy`) may pick either duplicate row to update, causing inconsistent state.

**Found by** 10 cells (19 distinct report texts, 19 findings): fable: van·medium; glm-flash: CE·low, CE·medium; glm-vis: CE·high, CE·low, CE·medium; sol: van·medium, van·xhigh; terra: van·high, van·xhigh

#### B27 — Webhook secret header lookup uses raw env header name, breaking auth due to lowercased req.headers keys

**Location:** `apps/web/pages/api/webhooks/app-credential.ts:24–27`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** In `app-credential.ts` (not touched in this PR’s diff; verification relies on the clustered reports), the code indexes the header map with the raw environment value, e.g. `req.headers[process.env.calcomwebhookheadername]`, and then compares it directly to the configured secret. In Node/Next.js, incoming header names are normalized to lowercase in `req.headers`, so if `process.env.calcomwebhookheadername` contains any uppercase characters, the lookup always returns `undefined` and the handler always responds 403 even for valid requests. Additionally, `req.headers[...]` can be `string | string[]`, so repeated headers yield an array that will never strictly equal the secret string.

**How to replicate.** 1) Configure env: set `calcomwebhookheadername=CalCom-Webhook-Secret` (any mixed/upper-case) and `calcomwebhooksecret=shh123`.
2) Send a webhook request to the app-credential webhook endpoint with header `CalCom-Webhook-Secret: shh123`.
3) Observe: the handler reads `req.headers` keys lowercased (e.g. `calcom-webhook-secret`), so `req.headers['CalCom-Webhook-Secret']` is `undefined` and the endpoint returns 403 "invalid webhook secret".
4) Variant: send the same header twice so it becomes an array (e.g. via proxy); `req.headers[...]` becomes `string[]` and the strict comparison fails, also producing 403.
Expected behavior: correct secret in the configured header should authenticate; Actual: valid requests are rejected.

**Found by** 10 cells (13 distinct report texts, 13 findings): glm-flash: CE·low, MRV·high, MRV·low, van·medium, van·xhigh; glm-vis: CE·high, MRV·high, MRV·low, MRV·medium, van·medium

#### B28 — Zoho Bigin refreshOAuthTokens called with credential.id instead of credential.userId (wrong user identity)

**Location:** `zoho-bigin/lib/calendarservice.ts:88–95`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74

**Why this is real.** In `zoho-bigin/lib/calendarservice.ts` (reported around line 91), the Zoho Bigin calendar service calls `refreshOAuthTokens(...)` using the credential’s primary key (e.g., `credential.id`) as the user identifier argument (commonly named `userId`/`calcomUserId`). The `refreshOAuthTokens` API is reported (and consistent with other call sites) to expect `credential.userId` (the Cal.com user id) and forwards it as `calcomUserId` to the sync endpoint; passing `credential.id` makes the sync endpoint look up tokens for a nonexistent/wrong user, leading to missing tokens or cross-user credential mixups. The PR diff is not provided here, so this verification relies on the consistent multi-reviewer line-level reports pointing to this exact call site and argument mismatch.

**How to replicate.** 1) Create two Cal.com users (A and B) and connect Zoho Bigin for each so each gets a distinct `credential.id` and `credential.userId`.
2) Trigger the Zoho Bigin calendar sync/refresh flow (the code path that hits `zoho-bigin/lib/calendarservice.ts` and calls `refreshOAuthTokens`).
3) Observe the request body to the sync endpoint (or logs): it will send `calcomUserId=<credential.id>` rather than `calcomUserId=<credential.userId>`.
Expected: tokens are refreshed for the owner user of the credential (`credential.userId`). Actual: refresh fails to find a user (no tokens) or, if an unrelated user happens to have an id equal to that credential id, tokens may be fetched/overwritten for the wrong user (cross-user contamination).

**Found by** 9 cells (29 distinct report texts, 29 findings): glm-flash: CE·medium, MRV·high, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### B29 — Webhook secret check uses non-constant-time string inequality and doesn’t normalize multi-value headers

**Location:** `apps/web/pages/api/webhook/app-credential.ts:24–33`  ·  **Severity:** high  ·  **Judge confidence:** 0.67

**Why this is real.** The handler reportedly guards the endpoint with a direct inequality check like `if (req.headers["calcom-webhook-secret"] !== process.env.CALCOM_WEBHOOK_SECRET) return res.status(403)`. In Next.js/Node, `req.headers[name]` is typed `string | string[] | undefined`, so a duplicated header becomes a `string[]` and will never equal the expected string, causing false 403s even when one value is correct. Separately, `!==` is not a constant-time comparison, so the endpoint leaks timing signal about the shared secret; this is a genuine security defect (not style) because it’s an unauthenticated, network-reachable credential-writing webhook. This file was not changed in the PR diff, so verification requires reading the current file at the path above and confirming the quoted comparison exists.

**How to replicate.** 1) Run the app with `CALCOM_WEBHOOK_SECRET=secret123` and hit `POST /api/webhook/app-credential` with the correct single header `calcom-webhook-secret: secret123` → expect not-403 (passes auth). 2) Send the same request but with two headers of the same name (e.g., using curl: `-H 'calcom-webhook-secret: secret123' -H 'calcom-webhook-secret: secret123'`) → Node may present this as `string[]`, and the current `!==` comparison will fail, returning 403 unexpectedly. 3) (Security observation) Send many requests varying the prefix of the secret and measure response times; because `!==` is not constant-time, average latency can correlate with the number of matching leading bytes, indicating a timing side channel.

**Found by** 9 cells (16 distinct report texts, 16 findings): glm-flash: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·low, MRV·high, MRV·low, MRV·medium

#### B30 — Zoho CRM calendar token refresh in sync mode treats fetch Response as Axios result, so `.data` is undefined and refreshed credentials are not applied

**Location:** `packages/app-store/zohocrm/lib/calendarservice.ts:204–225`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** In the sync-enabled branch, the helper returns a native `fetch` `Response`, but the downstream refresh logic continues to access it like an Axios response (e.g., `tokenInfo.data...`). A `fetch` `Response` does not have a `.data` property (its body must be read via `await res.json()`), so `tokenInfo.data` is `undefined`, making all token field reads (`access_token`, `refresh_token`, expiry) evaluate to `undefined` and preventing correct persistence of refreshed credentials. This is a runtime behavior mismatch (not a typing/style issue) and will deterministically break refresh handling whenever the sync branch is used.

**How to replicate.** 1) Configure a Zoho CRM calendar integration in a setup where the "sync" path is used (credential sharing / sync-enabled mode as described by the PR reports). 2) Force a token refresh (wait for token expiry or revoke/expire the access token, then trigger any API call that refreshes OAuth tokens). 3) Observe the refresh handler reading `tokenInfo.data` and producing undefined token fields; expected: refreshed access/refresh token values are extracted and stored; actual: refreshed token fields are undefined, resulting in failed subsequent API calls and/or persisted broken credentials.

**Found by** 9 cells (12 distinct report texts, 12 findings): opus: van·medium; glm-flash: CE·high, CE·medium, MRV·high, MRV·low; glm-vis: MRV·high; sol: van·xhigh; terra: van·low, van·medium

#### B31 — SalesforceCalendarService refreshes OAuth tokens unconditionally via hardcoded login.salesforce.com, bypassing credential-sync path

**Location:** `apps/salesforcecalendar/lib/SalesforceCalendarService.ts:40–120`  ·  **Severity:** high  ·  **Judge confidence:** 0.63

**Why this is real.** The clustered reports consistently describe new code in the Salesforce service constructor that (a) always POSTs directly to `https://login.salesforce.com/services/oauth2/token` and (b) immediately persists the refreshed credentials back to the DB, instead of using the shared `refreshOAuthTokens`/credential-sync mechanism used by other apps. Because this refresh happens eagerly on every service construction, any transient failure reaching the token endpoint (or a deployment relying on `CALCOM_CREDENTIAL_SYNC_ENDPOINT` / rotated secrets) causes all Salesforce operations to fail even when the cached access token is still valid, and it creates unnecessary round-trips + DB writes. The evidence pack notes the relevant code is not included in this PR diff, so verification requires reading the post-PR file to confirm the constructor contains the hardcoded `login.salesforce.com` fetch and unconditional credential rewrite.

**How to replicate.** 1) Configure a Cal.com instance with a valid Salesforce credential (stored access token + refresh token) and ensure the access token is still unexpired/valid. 2) Trigger any flow that constructs the Salesforce calendar service repeatedly (e.g., availability checks or booking flows that instantiate the service per request). 3) Observe: each instantiation performs an outbound POST to `login.salesforce.com/services/oauth2/token` and then updates the credential row (DB write) even though the token is still valid. 4) Failure mode: block egress to `login.salesforce.com` (or misconfigure local consumer key/secret in a credential-sync deployment) and observe Salesforce operations fail immediately on service construction instead of continuing to work with the cached access token (or delegating refresh to the sync endpoint).

**Found by** 8 cells (21 distinct report texts, 21 findings): glm-flash: CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·medium, MRV·high, MRV·low, MRV·medium

#### B32 — Missing refresh token is replaced with literal string "refreshtoken" and then persisted, corrupting stored OAuth credentials

**Location:** `packages/lib/credentialSync/parseRefreshTokenResponse.ts:41–55`  ·  **Severity:** critical  ·  **Judge confidence:** 0.66

**Why this is real.** The bug is that the parser mutates the token payload by injecting a sentinel value as real data: `refreshTokenResponse.data.refreshtoken = "refreshtoken"` when the parsed response does not include a refresh token. Because the schema used in this flow strips unknown keys (so `data.refreshtoken` is often undefined), callers that later persist `refreshTokenResponse.data` (often via object-spread updates into `credential.key`) overwrite the real stored refresh token with the literal string "refreshtoken", permanently breaking future refreshes. The PR diff for the persistence site is not included here, so this verification relies on the clustered reports’ description of the downstream `prisma.credential.update({ data: { key: ... } })` behavior.

**How to replicate.** 1) Use an OAuth provider/integration whose refresh response legitimately omits `refresh_token` on subsequent refreshes (common for Google/Microsoft/Zoom after the first grant).
2) Trigger a token refresh in the "credential sync/sharing" path so the response is passed through `parseRefreshTokenResponse`.
3) Observe that the parsed object now contains `refreshtoken: "refreshtoken"` even though the provider did not return one.
4) Let the integration code persist the parsed object back to `prisma.credential.key` (as described in the reports for Google CalendarService/O365/Zoom).
Expected: the existing stored refresh token remains unchanged when the provider omits it. Actual: the stored refresh token is overwritten with the literal string "refreshtoken", and the next direct refresh attempt fails (irrecoverable without re-auth).

**Found by** 8 cells (19 distinct report texts, 19 findings): glm-flash: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: MRV·high, MRV·low, MRV·medium

#### B33 — Webhook auth fails open when CALCOM_WEBHOOK_SECRET is unset (undefined equals missing header)

**Location:** `apps/web/pages/api/webhook/app-credential.ts:23–27`  ·  **Severity:** critical  ·  **Judge confidence:** 0.92

**Why this is real.** The authentication check compares the incoming header directly to the env secret: `req.headers[process.env.CALCOM_WEBHOOK_HEADER_NAME || "calcom-webhook-secret"] !== process.env.CALCOM_WEBHOOK_SECRET`. If `process.env.CALCOM_WEBHOOK_SECRET` is unset (i.e., `undefined`) and the request omits the header, then `req.headers[...]` is also `undefined`, making the comparison `undefined !== undefined` false, so the code does NOT return 403 and proceeds to write credentials. This is a real authorization bypass triggered by a configuration edge case.

**How to replicate.** 1) Configure the app so `APP_CREDENTIAL_SHARING_ENABLED` is true. 2) Ensure `CALCOM_WEBHOOK_SECRET` is NOT set in the environment (unset/empty so it becomes `undefined` at runtime). 3) Send a POST request to `/api/webhook/app-credential` with a valid JSON body (userId/appSlug/keys) but do NOT include the `calcom-webhook-secret` header (or whatever `CALCOM_WEBHOOK_HEADER_NAME` would be). Expected: request should be rejected with 403 due to missing/invalid secret. Actual: the secret check passes (undefined equals undefined) and the handler continues, allowing credential create/update for the specified userId.

**Found by** 8 cells (14 distinct report texts, 14 findings): sol: CE·high, CE·low, CE·medium, MRV·low, MRV·medium; terra: CE·high, CE·low, CE·medium

#### B34 — Salesforce token refresh misclassifies successful responses by checking `response.statusText !== "ok"` instead of `response.ok`

**Location:** `apps/api/lib/integrations/salesforce/lib/calendarservice.ts:86–92`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple reports point to `salesforce/lib/calendarservice.ts:86` using a success gate like `if (response.statusText !== "ok") { throw ... }` (or equivalent). This is a functional bug because HTTP reason phrases are optional and commonly empty for HTTP/2 in fetch implementations (e.g., undici), so a valid `200`/`2xx` response can have `statusText === ""` and be incorrectly treated as a failure. The correct success check is `response.ok` (or `response.status` range), not comparing `statusText` to a literal string. The PR diff does not include this file, so this verification relies on the clustered reports’ specific file/line reference.

**How to replicate.** 1) Locate `apps/api/lib/integrations/salesforce/lib/calendarservice.ts` around line ~86 and confirm the refresh/token call checks `response.statusText !== "ok"` (or `=== "ok"`) to decide success.
2) Run the API with a fetch implementation that returns an empty reason phrase on HTTP/2 (e.g., Node/undici with an upstream/proxy negotiating HTTP/2).
3) Trigger a Salesforce token refresh (e.g., let an access token expire, then make a calendar sync request that forces refresh).
Expected: refresh succeeds on HTTP 200/2xx.
Actual: despite a 200 response, `statusText` is empty/not "ok", so the code throws an HTTP error (reported as spurious 400) and the integration fails.

**Found by** 8 cells (13 distinct report texts, 13 findings): glm-flash: CE·high, CE·medium, MRV·high; glm-vis: CE·high, CE·low, CE·medium, MRV·low, MRV·medium

#### B35 — Instance-wide shared webhook secret allows overwriting any user's app credentials (no per-user binding/replay protection)

**Location:** `apps/web/pages/api/webhook/app-credential.ts:23–90`  ·  **Severity:** critical  ·  **Judge confidence:** 0.93

**Why this is real.** Authorization is only `req.headers[... ] !== process.env.CALCOM_WEBHOOK_SECRET` (lines 24-29), i.e., a single instance-wide shared secret. The target `userId` is taken directly from the request body (`const reqBody = ...parse(req.body)` then `where: { id: reqBody.userId }` and later `where: { userId: reqBody.userId, appId: ... }`) and is used to update/create credentials, so any caller who knows/leaks the shared secret can choose an arbitrary userId and overwrite that user's stored OAuth/app keys. There is also no nonce/timestamp/event-id/revision check, so a captured valid request can be replayed to roll credentials back to older keys.

**How to replicate.** 1) Ensure `APP_CREDENTIAL_SHARING_ENABLED` is true and the server has `CALCOM_WEBHOOK_SECRET` configured. 2) Send a POST request to `/api/webhook/app-credential` with header `calcom-webhook-secret: <CALCOM_WEBHOOK_SECRET>` (or the name in `CALCOM_WEBHOOK_HEADER_NAME`) and JSON body `{ "userId": <victimUserId>, "appSlug": "<existing-app-slug>", "keys": "<valid AES256 encrypted blob>" }`. 3) Observe response `200 Credentials created/updated for userId: <victimUserId>` and that the victim user's `credential` row for that app is created/updated with attacker-supplied `key`. 4) Replay the exact same request later (or after the victim rotates credentials) and observe it still succeeds and overwrites the credential again (no timestamp/nonce/revision guard). Expected: webhook authorization should be scoped to the intended user/app and reject replays/stale updates; actual: any holder of the shared secret can overwrite any user's credentials and replays are accepted indefinitely.

**Found by** 8 cells (11 distinct report texts, 11 findings): opus: CE·medium, MRV·high, MRV·low; sonnet: MRV·high, MRV·medium; glm-vis: CE·low, MRV·low; sol: MRV·high

#### B36 — OAuth token refresh via credential-sync treats non-2xx HTTP responses as successful token payloads

**Location:** `packages/app-store/utils/oauth/refreshoauthtokens.ts:8–17`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple reports point to the sync-endpoint fetch at lines ~8–17 returning/processing the fetch result without checking `response.ok` (e.g., “response.ok is never checked” and “the function returns the raw fetch response”). That means a 4xx/5xx response from the credential-sync endpoint is passed downstream as if it were a valid token response, so callers can parse and persist an error body as tokens or proceed with undefined/invalid token fields. This is a functional correctness bug (error responses are not detected) rather than a style nit; it causes authentication refresh to silently fail in misleading ways.

**How to replicate.** 1) Configure/force the credential-sync endpoint used by `refreshoauthtokens.ts` to return a non-2xx status (e.g., 401 with `{ "error": "invalid_client" }` or 500 with an HTML/text error). 2) Trigger the OAuth refresh flow that calls this sync fetch (e.g., let an integration token expire and invoke the refresh routine). Expected: the refresh function throws/returns a clear failure when `response.ok` is false. Actual: the code treats the response as if it were a token payload (or returns the raw Response), so downstream code attempts to use/deserialize it as tokens, leading to malformed token data or later failures unrelated to the real HTTP error.

**Found by** 8 cells (10 distinct report texts, 10 findings): opus: CE·high, CE·low, CE·medium, MRV·high; sonnet: MRV·high, MRV·low; glm-flash: van·low; sol: van·medium

#### B37 — parseRefreshTokenResponse throws on schema mismatch and can crash calendar operations when callers don’t catch it

**Location:** `packages/app-store/utils/oauth/parseRefreshTokenResponse.ts:19–21`  ·  **Severity:** high  ·  **Judge confidence:** 0.66

**Why this is real.** Post-PR, the helper unconditionally throws on parse failure (reports cite lines 19–21): `throw new Error("invalid refreshed tokens were returned")`. Several callers (notably the Salesforce calendar service connection/client construction path) still treat the function as returning a `{ success: boolean, ... }` result and do not wrap the call in a try/catch, so a non-conforming but otherwise recoverable refresh response (e.g., missing optional fields like `scope`) will now propagate as an unhandled exception/rejection and abort calendar operations. This is a behavioral change from a non-throwing parse-result API and is a functional defect, not a style concern.

**How to replicate.** 1) Set up an integration that refreshes OAuth tokens via this helper (e.g., Salesforce calendar). 2) Force a refresh-token response that fails the Zod schema (common case from reports: Salesforce refresh responses omit `scope` or other fields the schema requires). 3) Trigger any codepath that builds an authed API client/connection and calls `parseRefreshTokenResponse` without a surrounding try/catch (e.g., concurrent booking sync or webhook-driven calendar fetch). Expected: refresh failure is handled (typed error/HTTP error path) and the caller can retry or surface a controlled auth error. Actual: the thrown `Error("invalid refreshed tokens were returned")` bubbles up as an unhandled exception/rejection, causing the calendar operation to fail hard.

**Found by** 8 cells (8 distinct report texts, 8 findings): fable: van·low; opus: CE·low, CE·medium, MRV·high, MRV·low; sonnet: MRV·low; glm-flash: van·low; terra: van·xhigh

#### B38 — Outbound credential-sync POST lacks any authentication/signature, enabling token harvesting via exposed sync endpoint

**Location:** `unknown (code path not included in PR diff; referenced by reports as the outbound fetch to `CALCOM_CREDENTIAL_SYNC_ENDPOINT` / `calcomcredentialsyncendpoint`):1–1`  ·  **Severity:** critical  ·  **Judge confidence:** 0.58

**Why this is real.** The deduplicated reports all describe the same concrete defect: the outbound request Cal.com makes to the configured credential sync endpoint includes only `calcomUserId` and `appSlug` in the POST body and does not include any shared secret, HMAC signature, or authentication header. In contrast, the reverse/inbound webhook flow is described as requiring `calcomWebhookSecret`, indicating the intended trust model relies on a secret but is not applied to this outbound leg. Because the endpoint must return live OAuth access tokens for the requested `calcomUserId`, an unauthenticated request means the endpoint cannot distinguish Cal.com from any other caller who can reach that URL.

**How to replicate.** 1) Configure a self-hosted deployment with `CALCOM_CREDENTIAL_SYNC_ENDPOINT` pointing to a reachable HTTP endpoint you control that logs incoming headers/body and returns a dummy token payload. 2) Trigger whatever code path performs the "outbound credential sync" (e.g., initiating the integration/app flow that fetches fresh OAuth credentials) and observe the request: it contains `calcomUserId` and `appSlug` but no auth material (no secret header/signature). 3) From a separate client (curl/Postman) send a POST directly to the same endpoint with the same JSON shape but a different/guessed `calcomUserId` and `appSlug`; because there is no authentication mechanism, the endpoint cannot reject forged callers (expected: only Cal.com can request tokens; actual: any network peer can submit the request).

**Found by** 7 cells (18 distinct report texts, 18 findings): glm-flash: MRV·high; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### B39 — Zod schema uses computed keys that collapse to a single literal and strips token fields, breaking expiry/refresh-token parsing

**Location:** `packages/lib/integrations/parseRefreshTokenResponse.ts:5–27`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The reports all point to `minimumTokenResponseSchema` being defined with computed keys like `[z.string().toString()]: z.number()` and `[z.string().optional().toString()]: ...` (around lines 5-11). In JavaScript, those expressions are evaluated once at schema construction time and become a single static property name (commonly `"[object Object]"`), so they do not act as a wildcard for “any expiry field”; additionally, `z.object(...)` strips unknown keys by default, so fields like `expires_in`, `refresh_token`, `scope`, `instance_url`, etc. are dropped from the parsed output. The same file is also reported to substitute the literal string `"refreshtoken"` when the parsed object lacks a refresh token (around lines 25-27), which—combined with the stripping behavior—can cause callers to persist a placeholder over the real refresh token and/or miss expiry updates.

**How to replicate.** 1) In code, find `minimumTokenResponseSchema = z.object({ ... [z.string().toString()]: z.number(), ... })` and confirm the computed key evaluates to a fixed string key (not a wildcard) and that `.passthrough()`/`.catchall()` is not used. 2) Run the parser on a typical OAuth refresh response object such as `{ access_token: "A", refresh_token: "R", expires_in: 3600, scope: "...", instance_url: "..." }`. Expected: parsed output retains refresh token and expiry-related fields (or at least correctly extracts expiry) for downstream integrations. Actual: Zod strips unknown keys so `refresh_token`/`expires_in` are removed, expiry validation/extraction is effectively absent, and downstream code may keep an old/expired timestamp or (if the code substitutes a default) persist the literal `"refreshtoken"` string as the refresh token, causing repeated refresh attempts or permanently broken credentials (e.g., Office365/Zoom refresh flows).

**Found by** 7 cells (12 distinct report texts, 12 findings): opus: van·low; sonnet: van·xhigh; glm-flash: van·medium, van·xhigh; glm-vis: CE·high, CE·medium; terra: van·medium

#### B40 — SalesforceCalendarService eagerly refreshes OAuth token and writes DB on every instantiation (fragile success check)

**Location:** `packages/app-store/salesforce/lib/calendarservice.ts:75–99`  ·  **Severity:** high  ·  **Judge confidence:** 0.68

**Why this is real.** The code path that constructs/initializes the Salesforce calendar service performs an unconditional refresh-token POST and then persists the new tokens via `prisma.credential.update(...)` inline (reported at ~75–99), rather than only refreshing when the access token is expired or on an auth failure. It also uses a fragile success guard like `if (response.statusText !== "ok") ...` (or equivalent case-insensitive comparison), which is unreliable under HTTP/2/reason-phrase-stripping proxies where `statusText` may be empty, turning successful responses into thrown errors and masking the real error body/status. This is a behavioral regression: transient network/refresh failures now hard-fail otherwise read-only operations that could have proceeded with the still-valid stored access token.

**How to replicate.** 1) Create a Cal.com user connected to Salesforce (valid stored access/refresh token in Credential). 2) Hit a read-only calendar operation that instantiates the SalesforceCalendarService (e.g., availability/free-busy lookup) multiple times in quick succession; observe each request triggers a POST to `login.salesforce.com` (token endpoint) and a DB write (`credential.update`) even when the stored token is still valid. 3) Simulate a transient refresh failure (block `login.salesforce.com`, force a timeout, or return 5xx) and repeat the same availability call: expected behavior is the operation proceeds using the cached access token until it expires; actual behavior is the request fails immediately (reported as a 400/HttpError) before any API call. 4) (Optional) Route through an HTTP/2 proxy that strips reason phrases so `response.statusText` is empty; expected: refresh succeeds on 200; actual: code treats it as failure and throws.

**Found by** 7 cells (9 distinct report texts, 9 findings): glm-flash: MRV·high, MRV·low; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium

#### B41 — Webhook credential sync uses non-atomic findFirst→create/update, allowing duplicate credentials per user+app

**Location:** `apps/web/pages/api/webhooks/app-credential.ts:85–135`  ·  **Severity:** high  ·  **Judge confidence:** 0.45  ·  ⚠️ `distinct=false` (cluster may span two bugs)

**Why this is real.** The webhook handler reportedly does a read-then-write sequence like `const existing = await prisma.credential.findFirst({ where: { userId, appId } }); if (existing) { await prisma.credential.update(...) } else { await prisma.credential.create(...) }` with no transaction and no uniqueness constraint on `(userId, appId)`.
Under concurrency, two requests can both observe `findFirst` returning null and both execute the `create` branch, persisting two credential rows for the same user+app. Downstream code that later does `findFirst` (without `orderBy`) will pick an arbitrary row, making credential selection nondeterministic and potentially using stale tokens.

**How to replicate.** 1) Ensure there is no existing credential row for a given (userId, appId) targeted by the webhook endpoint.
2) Fire two concurrent POST requests to the app-credential webhook endpoint with identical payload (same userId/appId), e.g., by running two curl requests in parallel or using a load test tool.
3) Observe the database: `Credential` will contain two rows with the same (userId, appId) after both requests succeed (expected: exactly one row).
4) Trigger any code path that resolves credentials using `findFirst` for that user+app (e.g., a booking flow that uses the integration). Actual behavior: which credential is used becomes DB-order-dependent; one duplicate becomes stale/unreachable while the other may be used inconsistently.

**Found by** 6 cells (17 distinct report texts, 17 findings): glm-flash: CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: MRV·high, MRV·medium

#### B42 — OAuth refresh/sync identifies credentials only by userId + appSlug, so multi-account installs can overwrite the wrong credential

**Location:** `packages/app-store/utils/oauth/refreshOAuthTokens.ts:10–22`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** The refresh/sync request is keyed only by the Cal.com user and the app slug (e.g., it sends fields like `calcomUserId: userId.toString()` and `appSlug`), with no `credentialId`/account identifier. For apps that support multiple connected accounts per user (multiple credentials for the same app), that identifier pair is ambiguous, so the server-side handler can only pick an arbitrary matching credential (commonly via an unordered `findFirst({ where: { userId, appId/appSlug } })`) and refresh/update the wrong row. The PR diff does not include this file, so this verification relies on the reported line reference and the described request payload shape.

**How to replicate.** 1) In a dev environment, connect two separate provider accounts for the same OAuth app under one Cal.com user (creating two credentials for the same app).
2) Trigger the token refresh path that calls `refreshOAuthTokens.ts` (e.g., wait for expiry and perform an action that forces refresh, or call the sync/refresh endpoint directly).
3) Observe the outgoing sync/refresh request includes only `calcomUserId` + `appSlug` (no credential/account id).
Expected: only the targeted provider account’s credential gets refreshed/updated.
Actual: the backend cannot disambiguate and may refresh/update an arbitrary credential for that user+app, resulting in the wrong external account being used or a different credential’s token being overwritten.

**Found by** 6 cells (7 distinct report texts, 7 findings): opus: MRV·high; sol: CE·high, CE·medium, van·xhigh; terra: MRV·medium, van·xhigh

#### B43 — Salesforce OAuth refresh bypasses refreshOAuthTokens so credential-sync endpoint is never used

**Location:** `packages/app-store/salesforce/lib/salesforceOAuth.ts:-1–-1`  ·  **Severity:** high  ·  **Judge confidence:** 0.58

**Why this is real.** The issue is that the Salesforce integration performs a direct refresh-token exchange against Salesforce (e.g., a bespoke `fetch`/HTTP POST to Salesforce’s `/services/oauth2/token` with `grant_type=refresh_token`) instead of calling the shared `refreshOAuthTokens(...)` helper that routes refreshes through the configured `CALCOM_CREDENTIAL_SYNC_ENDPOINT`. Because this file is not part of PR #11059’s diff and the reports did not include exact line references, you must confirm by reading the Salesforce integration code: if you find an inline refresh request to Salesforce’s token endpoint and no call-site of `refreshOAuthTokens` in that refresh path, then the credential-sync feature cannot affect Salesforce token refresh and externally-synced refresh tokens will be ignored.

**How to replicate.** 1) Configure a self-hosted instance with credential sharing/sync enabled and set `CALCOM_CREDENTIAL_SYNC_ENDPOINT` to a test endpoint that logs requests. 2) Connect a Salesforce integration and ensure the locally stored access token expires (or force expiry by editing the stored access token/expiry in DB). 3) Trigger any action that requires a valid Salesforce access token (e.g., instantiate the Salesforce client / run a sync). Expected: Cal.com calls the credential-sync endpoint (via `refreshOAuthTokens`) to obtain fresh tokens. Actual (bug): no request hits `CALCOM_CREDENTIAL_SYNC_ENDPOINT`; instead Cal.com posts directly to Salesforce’s OAuth token endpoint using the locally stored refresh token.

**Found by** 6 cells (6 distinct report texts, 6 findings): glm-flash: CE·high; sol: van·medium, van·xhigh; terra: van·high, van·low, van·medium

#### B44 — App-credential webhook processes any HTTP method and persists unvalidated decrypted credential JSON

**Location:** `webhook/app-credential.ts:24–60`  ·  **Severity:** high  ·  **Judge confidence:** 0.66

**Why this is real.** In `webhook/app-credential.ts` around lines 24–27, the handler begins processing the request body without any `req.method` guard (i.e., there is no `if (req.method !== "POST") return res.status(405)`), so non-POST requests are handled the same as POSTs. The same handler path reportedly calls `zodSchema.parse(req.body)` and `JSON.parse(...)` on decrypted credential material without try/catch, and then writes the resulting value directly into `prisma.credential.key` without validating that the decrypted JSON matches the expected credential shape. This is a real correctness/security defect: malformed inputs can trigger unhandled exceptions (500s) or overwrite existing credentials with wrong-shaped data, rather than being rejected with a 4xx response.

**How to replicate.** 1) Locate `webhook/app-credential.ts` and confirm the handler lacks a method check before parsing/processing (no early return for non-POST). 2) Send a non-POST request (e.g., GET) to the app-credential webhook endpoint with a JSON body shaped like a normal request; observe that the handler still attempts to parse/process it (expected: 405 Method Not Allowed; actual: processing occurs). 3) Send a POST with a body that causes decrypted keys to be invalid JSON (or a wrong type like a string/array); observe unhandled `zod.parse`/`JSON.parse` errors leading to a 500 (expected: 400 Bad Request). 4) Send a POST whose decrypted JSON is valid JSON but wrong shape (e.g., `{ "unexpected": true }`); observe that the handler persists it into `credential.key`, potentially breaking previously working credentials (expected: reject with 400 due to schema mismatch).

**Found by** 6 cells (6 distinct report texts, 6 findings): fable: van·medium; sonnet: van·medium; glm-flash: CE·low, CE·medium; glm-vis: CE·low; sol: van·medium

#### B45 — Feature-flag constant evaluates to raw encryption-key string instead of boolean, risking secret leakage

**Location:** `packages/lib/constants.ts:92–92`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The constant is defined using a logical-AND of two environment variables, e.g. `export const appCredentialSharingEnabled = process.env.CALCOM_WEBHOOK_SECRET && process.env.CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY;`. In JavaScript/TypeScript, `a && b` evaluates to the last operand (`b`) when both are truthy, so this “enabled” flag becomes the *raw encryption key string* (or another string) rather than a boolean. This is a functional bug (strict boolean checks like `=== true` fail) and a security footgun because any logging/serialization of the exported flag leaks the encryption key; reports indicate this lives in a shared `constants.ts` module that also exports client-facing constants, increasing the blast radius.

**How to replicate.** 1) Set `CALCOM_WEBHOOK_SECRET=whsec_test` and `CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY=0123456789abcdef...` in the runtime env. 2) Import and print the constant (e.g. `console.log({ appCredentialSharingEnabled })`). 3) Observe actual output is the full encryption key string, not `true`. 4) Additionally, evaluate `appCredentialSharingEnabled === true` (or validate it with a boolean schema): expected `true` when both env vars are set, actual `false` because the value is a string.

**Found by** 5 cells (12 distinct report texts, 12 findings): glm-flash: MRV·low, MRV·medium; glm-vis: MRV·high, MRV·low, MRV·medium

#### B46 — Google OAuth refresh persists SafeParse wrapper instead of parsed credential key

**Location:** `apps/googlecalendar/lib/calendarservice.ts:93–102`  ·  **Severity:** critical  ·  **Judge confidence:** 0.62

**Why this is real.** At the reported location (~line 97), the code stores the result of a Zod/"safeParse" helper directly into `credential.key` (e.g., `key: safeParseResult(...)`) instead of storing the parsed payload (`.data`). `safeParse`-style helpers typically return an envelope like `{ success, data, error }`; persisting that envelope corrupts the credential schema because later code expects token fields (e.g., `refresh_token`, `access_token`) at the top level of `credential.key`, not nested under `data` or guarded by `success`.

**How to replicate.** 1) Enable/trigger the PR's new credential refresh/sync path for the Google Calendar integration (any action that refreshes OAuth tokens and then persists them, such as creating/updating an integration or a background refresh job).
2) Observe the Prisma `Credential` row written by this code path: `credential.key` will contain a wrapper/envelope structure (e.g., `{ success: true, data: {...tokens...} }`) instead of the expected flat token object.
3) Trigger any subsequent request that reads `credential.key.refresh_token` / `credential.key.access_token` expecting them at the top level.
Expected: OAuth continues working and the next refresh succeeds. Actual: runtime failures/missing-token behavior because the tokens are not where callers expect (they are nested or absent), causing refresh to break and bookings/calendar operations to fail.

**Found by** 5 cells (11 distinct report texts, 11 findings): glm-flash: MRV·high, MRV·medium; glm-vis: MRV·high, MRV·low, MRV·medium

#### B47 — Webhook persists decrypted credential.key without validating against the app’s credential schema

**Location:** `apps/api/src/ee/organizations/webhooks/app-credential.ts:57–89`  ·  **Severity:** high  ·  **Judge confidence:** 0.70

**Why this is real.** The handler decrypts and parses the incoming `keys` payload and writes it directly into the DB as `credential.key` (reports cite lines ~57-59 and ~78, e.g. `const decryptedKeys = decrypt(keys, ...)`, `const parsed = JSON.parse(decryptedKeys)`, then `data: { key: parsed }`) with no validation against the target app’s credential Zod schema (unlike OAuth callbacks which run schema validation). Because the only enforced constraint is that the app slug exists and `keys` is an encrypted string, any decryptable JSON value (null/array/wrong object shape/missing required fields) can be persisted and still returns 200, silently corrupting a previously working credential until later runtime usage throws. This file was not part of the PR diff per the prompt, so this verification relies on the reported line references and described code behavior.

**How to replicate.** 1) Pick an app that has a strict credential schema (e.g. Google Calendar) and create a valid working credential for a user.
2) Call the app-credential webhook/endpoint with a valid `appSlug` for that app and a `keys` value that decrypts to malformed-but-JSON, e.g. `{}` or `null` (encrypted with the expected shared secret so decryption succeeds).
3) Observe the endpoint responds 200 (e.g. "credentials updated") and the Credential row’s `key` column is replaced with the malformed value.
4) Trigger any flow that constructs/uses the app’s calendar/service (e.g. booking or checking availability). Expected: the webhook should reject bad keys with a 4xx at ingestion. Actual: runtime fails later (schema parse/field access error), and the original working credential has been overwritten.

**Found by** 5 cells (10 distinct report texts, 10 findings): glm-flash: MRV·high; glm-vis: CE·high, MRV·high, MRV·medium, van·medium

#### B48 — Outlook token refresh parse failures now throw a generic error and drop Microsoft/Zod diagnostics

**Location:** `packages/app-store/office365calendar/lib/calendarservice.ts:258–264`  ·  **Severity:** high  ·  **Judge confidence:** 0.68

**Why this is real.** Per the clustered reports, the post-PR code path around lines ~258–264 removed the only diagnostic logging (a `console.error` that printed the Zod parse error and the raw Microsoft token response) and replaced it with a context-free throw like `throw new Error('invalid refreshed tokens were returned')`. This is a real regression because when Microsoft returns an unexpected/partial payload (schema mismatch), the integration now fails hard with no actionable context, and the previous behavior of preserving the existing credential on parse failure is no longer possible. The reports also note the remaining `tokenResponse.success && tokenResponse.data` guard becomes dead/pointless once the parser throws on failure.

**How to replicate.** 1) Configure an Office365/Outlook calendar connection so the app performs refresh-token flows. 2) Force the Microsoft token endpoint response to be non-conforming to the expected schema (e.g., proxy the request and remove `refresh_token`, or return an error body that previously produced a Zod parse failure). 3) Trigger a refresh (e.g., wait for background refresh or invoke any code path that refreshes tokens). Expected (pre-PR): logs contain Zod error + raw Microsoft response and the system continues using the old credentials (soft failure). Actual (post-PR): refresh throws only "invalid refreshed tokens were returned" with no Microsoft response body / Zod error, making the failure hard to diagnose and potentially breaking the integration flow.

**Found by** 5 cells (10 distinct report texts, 10 findings): fable: van·medium; opus: MRV·high, van·medium, van·xhigh; sonnet: CE·low

#### B49 — (untitled)

**Location:** `?` (exact lines not in diff)  ·  **Severity:** ?  ·  **Judge confidence:** 0.00

**Why this is real.** (missing)

**Found by** 5 cells (8 distinct report texts, 8 findings): glm-flash: CE·high, CE·low, CE·medium; glm-vis: CE·high, CE·low

#### B50 — Zoho Bigin token refresh passes credentialId instead of Cal.com userId to refreshOAuthTokens (breaks sync / can mis-associate tokens)

**Location:** `packages/app-store/zoho-bigin/lib/calendarservice.ts:128–140`  ·  **Severity:** critical  ·  **Judge confidence:** 0.66

**Why this is real.** In the Zoho Bigin calendar service, the refresh call is made like `await refreshOAuthTokens(credentialKey, credential, credentialId)` (per the reports), but the third parameter is treated by the refresh/sync contract as the Cal.com user id (often named/serialized as `calcomuserid`). Every other call site reportedly passes `credential.userId`/`credential.userid`, so sending the credential row id causes the sync endpoint to look up/return tokens for the wrong identity (404/failure at best; cross-user token mixup at worst). The referenced file is not part of this PR’s diff, so this verification relies on the deduplicated reviewer reports describing the exact offending argument at this call site.

**How to replicate.** 1) Enable/trigger the "sync" code path for OAuth refresh (the mode where refreshOAuthTokens forwards a request containing `calcomuserid` to a parent/sync endpoint).
2) Create a Zoho Bigin credential for a user and trigger a refresh (e.g., run the integration sync/refresh flow).
3) Observe the outgoing sync payload/user lookup uses the credential table primary key instead of the Cal.com user id; expected: `calcomuserid` equals `credential.userId`/`credential.userid`, actual: it equals `credentialId`.
4) Result: refresh fails (user not found/404) or returns another user’s tokens, which then get stored under the wrong credential, breaking Zoho Bigin sync and potentially cross-linking access.

**Found by** 5 cells (6 distinct report texts, 6 findings): glm-flash: CE·high, CE·medium, MRV·medium; glm-vis: MRV·low, MRV·medium

#### B51 — Credential-sync token refresh path passes sync-endpoint payload into provider-specific response validators (Lark/Webex/Teams), causing refresh to always fail or persist invalid credentials

**Location:** `UNKNOWN (reports did not include file path; likely in the Lark/Webex/Teams token refresh adapter code handling the credential-sync/sharing mode):1–1`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** The reports consistently describe a concrete schema mismatch: in credential sync/sharing mode the code feeds the sync endpoint’s flat token response (documented as something like `{ accessToken, expiryDate }`) into provider-specific validators/parsers that expect the provider’s native envelope/fields (e.g., Lark `{ code, msg, data }`, Webex `{ refresh_token, expires_in }`, Teams `expires_in/token_type/refresh_token`). In Lark’s case, the validator checks `body.code !== 0` (or equivalent), but the sync payload has no `code`, so `code` becomes `undefined` and the function throws on every refresh attempt; for Webex/Teams, required fields are read as `undefined`, producing invalid persisted credentials (e.g., NaN expiry / missing refresh token) and breaking subsequent operations. This is a functional defect (runtime failure/bad persisted state), not a style or type-nit; however the evidence pack does not include the exact file/line references, so verification must be done by locating the sync-mode branch in each adapter’s refresh-token implementation.

**How to replicate.** 1) Configure Cal.com in a deployment that enables credential sync/sharing (i.e., adapters refresh via the internal sync endpoint rather than directly against the provider).
2) Connect a Lark calendar (and/or Webex/Teams) and trigger a token refresh (wait for expiry or force refresh by calling an API that requires a fresh access token).
3) Observe expected behavior: refresh succeeds and stores a credential with valid access token + expiry (+ refresh token where applicable).
4) Actual behavior per code path: the sync endpoint returns only `{ accessToken, expiryDate }`, but the adapter calls Lark/Webex/Teams response handlers that require `code/msg/data` or `expires_in/refresh_token`; Lark refresh throws immediately, and Webex/Teams persist `undefined` refresh token / NaN expiry, causing failures once the initial access token expires.

**Found by** 4 cells (10 distinct report texts, 10 findings): glm-flash: MRV·high, MRV·medium; glm-vis: MRV·high, MRV·low

#### B52 — Zoho Bigin refreshOAuthTokens called with credentialId instead of userId (calcomuserid mismatch)

**Location:** `packages/app-store/zoho-bigin/lib/calendarservice.ts:85–93`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** Multiple reviewers point to the same call site in `zoho-bigin/lib/calendarservice.ts` (around lines ~85–93) where `refreshOAuthTokens(...)` is invoked with `credentialid` as the third argument. That third parameter is the Cal.com *user id* (serialized as `calcomuserid` to the sync/parent endpoint), but `credentialid` is the credential record’s primary key; other adapters pass `credential.userid`. This breaks the payload contract, so sync mode either fails to find/refresh tokens (silent “sync never used”) or can map tokens to the wrong user on id collisions.

**How to replicate.** 1) Configure a Zoho Bigin credential on an installation that uses the “sync/sharing” token-refresh path (i.e., refreshes via the parent app endpoint that expects `calcomuserid`).
2) Trigger any calendar operation that forces a token refresh (expired access token): e.g., fetch calendars/events.
3) Inspect the outgoing refresh request payload (server logs/network): it will include `calcomuserid: <credentialId>` instead of the owning `userId`.
Expected: the sync endpoint resolves the correct user and returns refreshed tokens.
Actual: the sync endpoint fails to resolve the user (no tokens / refresh fails) or resolves the wrong user and persists wrong tokens to this credential.

**Found by** 4 cells (8 distinct report texts, 8 findings): glm-flash: CE·low; glm-vis: CE·high, CE·low, CE·medium

#### B53 — Sync-endpoint token refresh overwrites stored OAuth refresh token with literal placeholder

**Location:** `packages/app-store/office365calendar/lib/CalendarService.ts:263–270`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74

**Why this is real.** The reported code path merges refreshed token data into the persisted credential key using a spread like `o365AuthCredentials = { ...o365AuthCredentials, ...tokenResponse.data }` and then saves it via `prisma.credential.update({ data: { key: o365AuthCredentials }})`. In “credential sharing / sync-endpoint” mode, the token-response schema omits `refreshtoken`, and a fix-up reportedly injects the sentinel value `refreshtoken: "refreshtoken"`; the subsequent object spread overwrites the user’s *real* stored refresh token with this constant string and persists it. This is a functional data-loss bug (refresh token is destroyed in DB), not a style issue; the PR diff doesn’t include these files, so verification is by reading the existing adapter merge+persist logic described above.

**How to replicate.** 1) Enable credential sharing / credential sync endpoint so refreshes come from the sync endpoint (whose response contains only `accesstoken` + expiry, no `refreshtoken`). 2) Connect an Office365 calendar so a credential row with a valid refresh token is stored. 3) Let the access token expire and trigger a refresh (e.g., run a calendar sync). 4) Observe in the DB that `Credential.key.refreshtoken` becomes the literal string "refreshtoken" after the refresh (due to `{...stored, ...tokenResponse.data}` + prisma update). 5) Disable sharing/sync-endpoint (or hit a code path that uses the stored refresh token directly); subsequent refresh fails because the stored refresh token is now invalid, forcing re-authentication.

**Found by** 4 cells (5 distinct report texts, 5 findings): glm-flash: CE·high, MRV·medium; glm-vis: MRV·high, MRV·low

#### B54 — Salesforce calendar service eagerly refreshes OAuth token and overwrites credential.key, dropping previously stored fields

**Location:** `packages/app-store/salesforcecalendar/lib/SalesforceCalendarService.ts:1–1`  ·  **Severity:** high  ·  **Judge confidence:** 0.60

**Why this is real.** The clustered reports all describe the same concrete behavior change: the Salesforce service constructor/instantiation path now performs a refresh-token OAuth roundtrip unconditionally (no expiry/validity check) and then persists the refresh response back to `credential.key` using a raw spread of the parsed token schema plus `refreshtoken`. Because the persisted object is built only from the schema fields (e.g., access token fields) + refresh token, any additional properties previously present in `credential.key` are silently lost on the first calendar operation after deploy. The PR diff snippet is not available here, so this verification relies on the reviewers’ consistent description of the specific lines/logic (constructor refresh + `prisma.credential.update` replacing the whole JSON key) rather than quoting exact code from the patch.

**How to replicate.** 1) In an environment with the Salesforce calendar app enabled, create a Salesforce credential whose `credential.key` JSON contains the expected OAuth fields plus an extra custom field (e.g., `{"accesstoken":"...","refreshtoken":"...","instanceUrl":"...","customMeta":"KEEP_ME"}`). 2) Trigger any action that instantiates/uses the Salesforce calendar service (e.g., list calendars, create an event). 3) Observe that the service performs a token refresh even if the token is still valid (extra OAuth call per instantiation) and writes back to the DB. 4) Re-check the stored `credential.key`: expected is that `customMeta` remains; actual is that `credential.key` is replaced with only the parsed token-schema fields + `refreshtoken` (extra fields removed). In credential-sharing mode, confirm that the refresh bypasses the usual shared-token refresh indirection (as reported) and can fail or desync shared credentials.

**Found by** 4 cells (4 distinct report texts, 4 findings): glm-flash: MRV·low; glm-vis: CE·low, MRV·low, MRV·medium

#### B55 — Webhook credential sync updates key but does not clear previously set invalid flag

**Location:** `apps/web/pages/api/webhook/app-credential.ts:72–80`  ·  **Severity:** high  ·  **Judge confidence:** 0.80

**Why this is real.** In the update path, the handler only writes the decrypted key back to the existing credential: `data: { key: keys, }` (lines 77-79). If the credential record had previously been marked `invalid=true` (as described by the reports), this endpoint never resets that flag, so even after receiving fresh valid tokens the credential can remain disabled/invalid in the database. This is a functional state bug (missing state transition), not a style issue.

**How to replicate.** 1) In DB, ensure a credential exists for (userId, appId=appMetadata.slug) with `invalid=true` and some old/expired `key` content (or reproduce by letting an integration mark the credential invalid). 2) Send a POST request to `/api/webhook/app-credential` with correct webhook secret header and a body containing the same `userId`, `appSlug`, and `keys` holding newly valid encrypted credentials. 3) Observe the handler returns 200 "Credentials updated" and the `key` field changes, but `invalid` remains true. Expected: a successful credential refresh/sync should also clear `invalid` (and re-enable the integration); actual: integration remains disabled because the invalid flag is never updated.

**Found by** 4 cells (4 distinct report texts, 4 findings): sol: CE·low, van·high; terra: CE·high; astra: MRV·high

#### B56 — Token refresh helper returns incompatible shapes (fetch Response vs provider token object), causing call-site runtime/type mismatches

**Location:** `UNKNOWN (not in this PR diff) — locate by searching for the comment "the response should only contain the access token and expiry date" in the token refresh/sync helper:1–120`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The reported helper has two branches that return different runtime shapes: in “sharing mode” it returns the raw result of `fetch(...)` (a `Response`), while in the non-sharing branch it returns whatever a provider `refreshFunction` returns, with the callback typed as `() => any`. Because the helper’s return type becomes an unsafe union (effectively `Response | any`), TypeScript cannot reliably flag incorrect consumers, and several call sites already consume it as if it were provider-native data (e.g., reading `.data` or flat token fields) which will crash when the helper actually returned a `Response` object. This is a functional contract bug (inconsistent return schema) rather than a style nit; the comment promising “only access token and expiry date” further contradicts consumers that expect provider-specific envelopes.

**How to replicate.** 1) In the codebase, locate the helper that conditionally calls a “sync endpoint” when app sharing is enabled (search for the exact comment string "the response should only contain the access token and expiry date").
2) Observe that the sharing-enabled path returns the raw `fetch(...)` result (a `Response`) without parsing/normalizing, while the other path returns `refreshFunction()` (provider-specific object/axios response), and that `refreshFunction` is typed `() => any`.
3) Enable the “app sharing”/sync-endpoint mode (whatever feature flag/env var gates that branch) and trigger an OAuth token refresh for one of the reported integrations (Google, HubSpot, Zoho Bigin, Zoho CRM).
4) Expected: the call site can reliably read token fields (or `.data`) from a consistent object shape.
5) Actual: the call site receives a `Response` in sharing mode, so property access like `res.data` or `res.access_token` yields `undefined` or throws (e.g., `TypeError: Cannot read properties of undefined`), breaking the integration at runtime.

**Found by** 3 cells (4 distinct report texts, 4 findings): glm-flash: MRV·high; glm-vis: MRV·high, MRV·medium

#### B57 — SalesforceCalendarService eagerly refreshes OAuth token on every construction and hard-fails on refresh errors, breaking otherwise-valid cached access tokens

**Location:** `packages/app-store/sicrosoft-calendar/lib/SalesforceCalendarService.ts:55–125`  ·  **Severity:** high  ·  **Judge confidence:** 0.63

**Why this is real.** According to the clustered reports, the SalesforceCalendarService constructor now performs an unconditional token refresh (an outbound POST to Salesforce) followed by a prisma credential update on every instantiation, and it throws an HttpError(400) if the refresh request fails. This is a real functional regression: any transient refresh failure (rate limit/revocation/misconfig) now aborts service construction even when the currently cached access token is still valid and could have been used (previous behavior via lazy refresh). The reports also note a dead guard like `if (!accessTokenParsed.success)` that can never fire because `parseRefreshTokenResponse(...)` already throws, indicating error-handling is inconsistent and still results in constructor failure; the PR diff itself is not included here, so this verification relies on the reports’ description of the post-PR code.

**How to replicate.** 1) Configure a Salesforce integration with a valid access token stored in DB (not yet expired) and a refresh token. 2) Induce a refresh-token endpoint failure (e.g., block/timeout requests to `login.salesforce.com`, return 429/5xx, revoke refresh token, or remove client keys). 3) Trigger any Cal.com flow that instantiates SalesforceCalendarService (availability lookup, booking creation/update that touches Salesforce). Expected: operations continue using the cached access token until it expires (or at least only fail when token is actually expired). Actual: constructor performs an eager refresh + DB write and throws HttpError(400), causing the entire Salesforce operation to fail immediately; additionally, observe an extra outbound token call and prisma.credential.update on every invocation even when no refresh is needed.

**Found by** 3 cells (3 distinct report texts, 3 findings): glm-flash: MRV·high; glm-vis: CE·high, MRV·low

#### B58 — `appCredentialSharingEnabled` computed via `&&` yields truthy strings (and can equal the encryption key), enabling sharing when env vars are set to `'false'`

**Location:** `packages/app-store/lib/appCredentialSharingEnabled.ts:1–3`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The code reportedly defines the flag as something like: `export const appCredentialSharingEnabled = process.env.CALCOM_CREDENTIAL_SYNC_ENDPOINT && process.env.CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY;`. In JavaScript/TypeScript, `a && b` returns `b` (not a boolean), so the value becomes the raw `CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY` string when both are set; additionally, any non-empty string (including `'false'`) is truthy, so self-hosters setting env vars to `'false'` unintentionally enable the feature. This is a functional bug (incorrect enablement and type/value) rather than a style nit; the file/line is not in this PR’s diff per the report, so verification is by inspecting the post-PR tree directly.

**How to replicate.** 1) In a self-hosted setup, set `CALCOM_CREDENTIAL_SYNC_ENDPOINT=false` and `CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY=false` (or any non-empty strings) and start the server. 2) Trigger an OAuth refresh flow that hits the app-store refresh code paths (e.g., any integration that refreshes tokens, which uses `refreshOAuthTokens.ts` / `parseRefreshTokenResponse.ts`). Expected: sharing should be disabled and no sync/webhook path should run when env vars are set to disable it. Actual: the feature is treated as enabled because `'false'` is truthy, and the "boolean" flag can equal the encryption key string (e.g., `'false'` or the real key), potentially surfacing in logs/serialization and activating sync behavior with an invalid secret.

**Found by** 3 cells (3 distinct report texts, 3 findings): glm-flash: CE·medium; glm-vis: CE·high, CE·low

#### B59 — Office365/Lark/Zoho adapters mis-parse /sync response, leaving token expiry undefined and preventing refresh

**Location:** `packages/app-store/office365video/lib/Office365VideoAdapter.ts:146–176`  ·  **Severity:** high  ·  **Judge confidence:** 0.42

**Why this is real.** The adapters call the OAuth “sync” endpoint (documented to return only an access token + expiry date) but then parse the JSON as if it were the provider’s native token response (e.g., reading fields like `expiresin`/`refreshtoken` after `handleErrorsJson`). With only `{ accessToken, expiryDate }` available, those reads resolve to `undefined`; any subsequent `expiryDate` computation from `undefined` becomes `NaN` (or leaves a stale expiry), so refresh logic stops running and the integration continues using an expired access token. The file was not part of the PR diff; this verification relies on the deduplicated reviewer reports describing the exact field mismatch and its downstream effect.

**How to replicate.** 1) Configure the Office365 Video / MS Teams integration so it uses the shared OAuth sync endpoint for refresh.
2) Ensure the stored access token is near expiry, then trigger a refresh path (e.g., create a Teams meeting/event that forces token refresh).
3) Observe the sync endpoint response body contains only `accessToken` and `expiryDate` (per the endpoint contract).
4) Observe in the adapter code it tries to read provider-token fields like `expiresin`/`refreshtoken` from that response; `expiresin` becomes `undefined`, causing computed expiry to become `NaN` or remain stale.
5) After the original access token actually expires, attempt meeting creation again: expected is a refreshed token and successful meeting creation; actual is continued use of an expired token and a failure from the Microsoft API (401/invalid_token), breaking meeting creation.

**Found by** 3 cells (3 distinct report texts, 3 findings): glm-flash: CE·medium, MRV·high; glm-vis: CE·medium

#### B60 — Credential-sync predicate mismatch causes team-owned OAuth refresh to be parsed/validated with the wrong schema

**Location:** `packages/app-store/utils/oauth/parserefreshtokenresponse.ts:15–25`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The codebase duplicates the "is credential-sync active" check in two places with different predicates. In `refreshOAuthTokens.ts` (reported at line 5) the sync branch is gated on `appCredentialSharingEnabled && process.env.CALCOM_CREDENTIAL_SYNC_ENDPOINT && userId`, but in `parseRefreshTokenResponse.ts` (reported at line 15) it checks only `appCredentialSharingEnabled && process.env.CALCOM_CREDENTIAL_SYNC_ENDPOINT` (missing the `userId` condition). This means team-owned credentials (where `userId` is null) can take the non-sync provider refresh path yet still be parsed as if sync were active, leading to schema mismatch (validated against the stripped/minimum sync schema instead of the app/provider schema) and broken refresh handling.

**How to replicate.** 1) Set `appCredentialSharingEnabled=true` and set `process.env.CALCOM_CREDENTIAL_SYNC_ENDPOINT` to any non-empty value. 2) Create/use a team-owned OAuth credential (no `userId` / `userId` is null) and trigger token refresh (e.g., call the refresh flow that hits `refreshOAuthTokens`). 3) Observe: because `userId` is null, `refreshOAuthTokens` skips the sync endpoint branch and performs a normal provider token refresh, but `parseRefreshTokenResponse` treats sync as active and applies the sync/minimal parsing/validation. Expected: either team creds should sync consistently, or parsing should follow the same predicate and accept the provider refresh schema; actual: refresh fails or drops required fields due to the wrong parsing/validation path.

**Found by** 3 cells (3 distinct report texts, 3 findings): opus: MRV·high; sonnet: MRV·high; sol: MRV·medium

#### B61 — Some OAuth integrations refresh via refreshOAuthTokens but persist the raw sync response without parseRefreshTokenResponse normalization

**Location:** `packages/app-store/lark/lib/getAccessToken.ts:1–120`  ·  **Severity:** high  ·  **Judge confidence:** 0.58

**Why this is real.** The reports describe that certain providers (e.g., lark, hubspot, webex, msteams/office365video) call `refreshOAuthTokens(...)` and then persist the returned JSON directly into `credential.key` without running it through `parseRefreshTokenResponse(...)`, while other providers (google/zoom/office365/salesforce) do apply the parser. This is a real functional defect because the sync endpoint can return provider-specific shapes (e.g., `expiresIn` vs `expires_in`, refresh token placeholders, or extra required fields) and without normalization/validation the app stores an incompatible object verbatim, silently corrupting credentials and breaking future API calls. The PR does not include these files in the diff, so verification is by inspecting the current post-PR tree for the missing `parseRefreshTokenResponse(...)` step after `refreshOAuthTokens(...)` in the affected provider call sites.

**How to replicate.** 1) Enable/force “sync mode” so token refreshes go through the sync endpoint (the code path that uses `refreshOAuthTokens`). 2) Stub/misconfigure the sync endpoint to return a token response missing provider-specific fields (e.g., for Lark omit/rename `refreshToken` and `expire`, or for Webex omit `expiresIn`). 3) Trigger a refresh (wait for expiry or explicitly invoke the provider’s token refresh path). Expected: the response is normalized/validated (via `parseRefreshTokenResponse`) and stored in a consistent schema, preserving required fields/placeholders. Actual: the raw response is saved into `credential.key` as-is, leading to broken subsequent API calls or refresh attempts.

**Found by** 2 cells (2 distinct report texts, 2 findings): glm-flash: MRV·high; glm-vis: MRV·low

#### B62 — Salesforce OAuth refresh bypasses refreshOAuthTokens and sends placeholder refresh_token under credential sync

**Location:** `packages/app-store/sicrosoft/lib/oauth/refreshAccessToken.ts:34–78`  ·  **Severity:** critical  ·  **Judge confidence:** 0.64

**Why this is real.** The reports indicate Salesforce is the only app that refreshes tokens via a hardcoded direct `fetch` using `credentialKey.refreshToken` instead of going through the shared `refreshOAuthTokens(...)` helper that honors `appCredentialSharingEnabled` / `CALCOM_CREDENTIAL_SYNC_ENDPOINT`. Under credential sharing/sync, `parseRefreshTokenResponse` stores a placeholder (literal string like `"refreshToken"`/`"refreshtoken"`) or omits the real refresh token, so this direct refresh path ends up POSTing `refresh_token=refreshtoken` to `https://login.salesforce.com/.../token`, which reliably fails (invalid_grant) and throws. This is a functional defect (broken Salesforce calendar sync) under the exact credential-sync configuration introduced/used by the PR, not a style issue; the prompt notes the offending file is not in the PR diff, so this verification relies on the deduplicated reports describing the post-PR behavior and the known credential-sync contract.

**How to replicate.** 1) Configure Cal.com with credential sharing/sync enabled (set/enable `appCredentialSharingEnabled` and configure `CALCOM_CREDENTIAL_SYNC_ENDPOINT`).
2) Connect the Salesforce app for a user (OAuth completes; refresh token is handled by `parseRefreshTokenResponse` per the PR behavior).
3) Trigger a Salesforce calendar sync or any code path that refreshes the Salesforce access token (wait for token expiry or force refresh).
4) Observe the outgoing request to Salesforce token endpoint: the body contains `grant_type=refresh_token` with `refresh_token` equal to the literal placeholder (e.g., `refreshtoken`/`refreshToken`) or missing.
Expected: refresh should route through `refreshOAuthTokens` so the real refresh token is obtained via the credential sync endpoint and refresh succeeds. Actual: Salesforce refresh fails (e.g., 400 invalid_grant), throws, and Salesforce calendar sync is broken.

**Found by** 2 cells (2 distinct report texts, 2 findings): glm-flash: MRV·medium; glm-vis: MRV·high

#### B63 — (untitled)

**Location:** `?` (exact lines not in diff)  ·  **Severity:** ?  ·  **Judge confidence:** 0.00

**Why this is real.** (missing)

**Found by** 2 cells (2 distinct report texts, 2 findings): glm-vis: MRV·high, MRV·low

#### B64 — Zoho Bigin token refresh passes credentialId as userId, causing sync to run under wrong Cal.com user identity

**Location:** `packages/app-store/zoho-bigin/** (search for the refreshOAuthTokens call in the Zoho Bigin sync/refresh code)` (exact lines not in diff)  ·  **Severity:** critical  ·  **Judge confidence:** 0.60

**Why this is real.** The clustered reports consistently describe that the Zoho Bigin integration calls `refreshOAuthTokens` with `userId` set to the credential row id (e.g., `refreshOAuthTokens({ userId: credentialId, ... })`). That value is then forwarded as `calcomUserId` to the parent/share sync endpoint, which expects an actual Cal.com user id; using a credential id will make the parent look up the wrong user (or none), returning missing/incorrect tokens without an obvious error. This PR does not include the affected file in its diff, so verification must be done by inspecting the current post-PR tree and confirming the parameter mismatch at the `refreshOAuthTokens(...)` call site.

**How to replicate.** 1) In the repo post-PR, locate the Zoho Bigin sync/refresh implementation and find the call to `refreshOAuthTokens`.
2) Confirm whether the argument passed as `userId` is the credential record id (often named `credentialId`) instead of the owning user id.
3) Run in “sharing/parent” mode (where the app calls the parent sync endpoint) and trigger a Zoho Bigin token refresh (e.g., force token expiry or invoke the refresh path).
4) Observe the outbound request to the parent sync endpoint: `calcomUserId` will equal the credential id.
Expected: `calcomUserId` is the actual Cal.com user id and refresh succeeds for that user.
Actual: parent cannot find the user (404) or returns tokens for the wrong identity; refresh/sync fails or syncs against the wrong account.

**Found by** 2 cells (2 distinct report texts, 2 findings): glm-vis: MRV·high, MRV·low

#### B65 — (untitled)

**Location:** `?` (exact lines not in diff)  ·  **Severity:** ?  ·  **Judge confidence:** 0.00

**Why this is real.** (missing)

**Found by** 2 cells (2 distinct report texts, 2 findings): opus: CE·low, van·xhigh

#### B66 — Office365 token refresh now throws on Zod schema mismatch without catch, risking unhandled rejection and breaking prior graceful degradation

**Location:** `packages/app-store/office365calendar/lib/CalendarService.ts:240–285`  ·  **Severity:** high  ·  **Judge confidence:** 0.58

**Why this is real.** Per the clustered reports, the Office365 refresh-token path was changed from logging Zod parse errors (via `console.error(...)`) to calling `parseRefreshTokenResponse(...)` which now uses Zod `.parse(...)` (throwing on schema mismatch). The reported defect is that this new throw is not caught in the surrounding refresh flow, so a malformed/partial Microsoft token response can propagate as an unhandled rejection instead of the previous behavior (log-and-continue with existing credentials). The PR diff itself does not include this file hunk here, so verification relies on confirming in the post-PR tree that `parseRefreshTokenResponse` throws and its caller does not wrap it in try/catch (and the prior `console.error` logging is removed).

**How to replicate.** 1) In a self-hosted instance configured with an Office365 calendar connection, trigger a token refresh (e.g., let the access token expire and perform any action that fetches calendar events).
2) Force the Microsoft token endpoint (or a proxy/mock in front of it) to return JSON missing/renaming a required field in the refresh-token response (e.g., omit `access_token` or return an unexpected type).
3) Expected (pre-change): code logs the Zod error and continues using the last-known stored credentials, avoiding a crash.
4) Actual (post-change): `parseRefreshTokenResponse` throws on schema mismatch and, because the exception is not caught, the refresh call rejects (potentially as an unhandled rejection), breaking calendar sync/requests instead of degrading gracefully.

**Found by** 2 cells (2 distinct report texts, 2 findings): sonnet: van·medium; glm-flash: MRV·medium

#### B67 — `appcredentialsharingenabled` exports the encryption key string (truthy) instead of a boolean flag

**Location:** `packages/lib/constants.ts:103–104`  ·  **Severity:** high  ·  **Judge confidence:** 0.70

**Why this is real.** Multiple reports point to `packages/lib/constants.ts:103-104` where `appcredentialsharingenabled` is derived directly from `process.env.APP_CREDENTIAL_SHARING_ENCRYPTION_KEY` (or equivalent), meaning its value becomes the raw AES/encryption key string when set, not a boolean. That creates two real defects: (1) a public constant with an `...enabled` name becomes a truthy string, causing type/signature drift for consumers expecting `boolean`, and (2) the encryption key is now exposed via a broadly-imported export. The PR diff doesn’t include this file, so verification relies on inspecting the current post-PR code at those lines.

**How to replicate.** 1) In a node environment, set `APP_CREDENTIAL_SHARING_ENCRYPTION_KEY='supersecretkey'`. 2) Import the constant: `import { appcredentialsharingenabled } from '@calcom/lib/constants'` (or the relevant package path). 3) Log/type-check it: `console.log(appcredentialsharingenabled, typeof appcredentialsharingenabled)`. Expected: `true`/`false` boolean indicating whether sharing is enabled; Actual: `'supersecretkey'` (type `string`), which is truthy and also leaks the key to any code that imports the constant.

**Found by** 2 cells (2 distinct report texts, 2 findings): opus: van·high; glm-flash: CE·low

#### B68 — parseRefreshTokenResponse now throws on Zod safeParse failure, turning previously-graceful token refresh degradation into a hard failure

**Location:** `packages/lib/integrations/oauth/parseRefreshTokenResponse.ts:18–33`  ·  **Severity:** critical  ·  **Judge confidence:** 0.60

**Why this is real.** The function reportedly changed from returning/continuing on `schema.safeParse(...)` failure (logging the Zod error + MS response and letting the caller use `tokenResponse.success && tokenResponse.data`) to instead hard-throwing: `if (!tokenResponse.success) throw new Error("invalid refreshed tokens were returned")`. That converts a recoverable/observable parse mismatch (e.g., Office365 returning an unexpected/partial refresh payload) into an exception that aborts `refreshAccessToken`, so any downstream booking flow depending on refresh now fails outright. The evidence pack notes this file is not in the PR diff; verification requires reading post-PR code for this function and confirming the throw replaced the previous non-throwing branch.

**How to replicate.** 1) In an environment with Office365 (or any provider using this shared refresh helper), force a refresh-token response that is missing/renamed fields (e.g., simulate an MS response missing `refresh_token` or with additional/unexpected shape so the strict schema fails). 2) Trigger any code path that calls `refreshAccessToken` during a booking (e.g., attempt to book a meeting that requires creating a calendar event while the access token is expired). Expected (pre-change): the Zod error is logged and the system proceeds with whatever usable fields were present (or at least does not crash the whole request). Actual (post-change): `parseRefreshTokenResponse` throws "invalid refreshed tokens were returned", bubbling up as an unhandled error and the booking/event creation request fails.

**Found by** 1 cells (2 distinct report texts, 2 findings): glm-vis: MRV·low

#### B69 — SalesforceCalendarService references prisma and HttpError without importing them

**Location:** `packages/lib/CalendarService/salesforceCalendarService.ts:86–96`  ·  **Severity:** critical  ·  **Judge confidence:** 0.62

**Why this is real.** The reviewers report that the Salesforce calendar service adds new references to `HttpError` (around line ~86) and `prisma.credential.update` (around line ~96) but the PR does not add corresponding imports. If those identifiers were not already in scope in that file, TypeScript will fail to compile (e.g., "Cannot find name 'prisma'" / "Cannot find name 'HttpError'") or the module will crash at runtime due to missing bindings. The verification relies on the reports because the referenced file is not included in the PR diff snippet provided here.

**How to replicate.** 1) Checkout the PR branch and open `packages/lib/CalendarService/salesforceCalendarService.ts`.
2) Navigate to the reported lines (~86 and ~96) and confirm the code uses `throw new HttpError(...)` and calls `prisma.credential.update(...)`.
3) Check the top of the file for imports: verify there is no import bringing `prisma` into scope (e.g., `import prisma from ...` / `import { prisma } from ...`) and no import for `HttpError`.
4) Run `pnpm -w typecheck` (or the repo's build/CI TypeScript step). Expected: compilation error complaining about undefined `prisma`/`HttpError`; Actual: build fails.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: CE·medium

#### B70 — Google OAuth refresh persists unvalidated credential.key (schema validation bypass) in credential-sharing mode

**Location:** `unknown (not in PR diff); search in Google OAuth refresh/credential update code for `parseRefreshTokenResponse(` and `credential.update({ data: { key: ... } })`` (exact lines not in diff)  ·  **Severity:** high  ·  **Judge confidence:** 0.66

**Why this is real.** The clustered reports indicate the refresh flow now writes `credential.key` using `parseRefreshTokenResponse(googleCredentials, ...)` directly, instead of validating the full stored object via something like `GoogleCredentialSchema.parse(googleCredentials)` before persisting. This is a real behavioral regression because `parseRefreshTokenResponse` is typically a minimal/partial parser for the token response (or a merge helper), not a strict validator of the entire credential key shape, so arbitrary/unvalidated fields present on the mutated `googleCredentials` object (and potentially token-response fields) can be persisted into the database. The file/line numbers are not available in the provided evidence (the affected file is not part of the PR diff), but a reader can confirm by locating where refresh tokens are handled and comparing what expression is assigned to `data: { key: ... }` in the credential update.

**How to replicate.** 1) Enable/enter "credential sharing" mode (shared credential object reused across users/workspaces). 2) Ensure a Google credential exists whose in-memory `googleCredentials` object contains extra/unexpected properties (e.g., inject an additional field via a prior mutation point, or simulate by editing the stored JSON if possible). 3) Trigger a token refresh (e.g., call an endpoint that forces Google access token refresh or wait for expiry and perform an action that refreshes). 4) Inspect the persisted `Credential.key` JSON in the DB: expected behavior is that only fields allowed by the strict Google credential schema remain after refresh; actual behavior is that unvalidated/extra fields survive or new unexpected fields are written because the refresh path persists the merged/minimally-parsed object without strict schema.parse validation.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·low

#### B71 — Zoho CRM token expiry adds 3600ms instead of 1 hour, causing near-immediate expiration

**Location:** `packages/app-store/zoho-crm/lib/credentials.ts:84–88`  ·  **Severity:** high  ·  **Judge confidence:** 0.58

**Why this is real.** The reported code computes expiry as `Math.round(Date.now() + 60 * 60)` (or equivalent `Date.now() + 60 60`), which adds 3600 to a millisecond timestamp—i.e., ~3.6 seconds—not one hour. Because `Date.now()` is in milliseconds, the intended “1 hour” TTL must be `60 * 60 * 1000`. This makes stored Zoho CRM credentials appear expired almost immediately after refresh, forcing a refresh on every subsequent operation. (The file/lines were not part of the PR diff; this verification relies on the aggregated reviewer report snippet.)

**How to replicate.** 1) In the Zoho CRM integration, trigger an access-token refresh (e.g., revoke/expire the token, then perform any calendar/CRM operation that refreshes it). 2) Inspect the persisted credential fields right after refresh (e.g., `expiresAt`/`expiryDate`). Expected: expiry timestamp ~now + 3600000ms (~1 hour). Actual with the bug: expiry ~now + 3600ms (~3.6s). 3) Perform a second operation a few seconds later; observe the integration treats the token as expired and refreshes again every time (extra refresh requests, repeated OAuth calls, potential rate limiting).

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: MRV·high

#### B72 — Cross-instance credential sync incorrectly trusts req.body.userId, attaching credentials to the wrong local user

**Location:** `UNKNOWN (not in PR diff) — locate the sync handler that reads req.body.userId and queries the local User table` (exact lines not in diff)  ·  **Severity:** critical  ·  **Judge confidence:** 0.60

**Why this is real.** The reported handler "resolves reqbody.userid — the calling instance's user id — directly against the local user table" (e.g., a lookup like `where: { id: req.body.userId }`) with no cross-instance identity mapping/scoping beyond a shared secret. In a multi-instance setup where local DB user IDs do not match the parent instance’s ID space, this causes the synced calendar/video credentials to be persisted under whatever local user happens to have that numeric ID. This is a functional mis-association bug (not a style issue): credentials can be silently linked to an unrelated local account, routing meetings/bookings through the wrong external calendar/video provider.

**How to replicate.** 1) Set up two Cal.com instances (Parent and Child) that share the credential-sync shared secret but have different user-id spaces (e.g., on Child, create a user so that local `id=1` belongs to Alice; on Parent, `userId=1` is Bob).
2) From Parent, trigger the credential-sync request to Child with `req.body.userId` set to Parent's user id (e.g., 1) and include valid credential payload.
3) Observe in Child DB that the new credential row is attached to local `userId=1` (Alice) rather than to a mapped identity for Bob.
Expected: Child should map Parent user identity to the correct local user (or reject if unmapped). Actual: Child attaches credentials to the local user with the same numeric ID, causing calendar/video actions for Alice to use Bob’s synced credentials (or vice versa).

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: MRV·high

#### B73 — Sync-endpoint fetch has no timeout/abort and no fallback, allowing hangs to stall all calendar/video ops

**Location:** `UNKNOWN (sync-endpoint fetch call site not included in PR #11059 diff; reports provided no file/line refs)` (exact lines not in diff)  ·  **Severity:** critical  ·  **Judge confidence:** 0.42

**Why this is real.** The clustered reports describe a specific control-flow defect: the code path that calls the new/central “sync endpoint” uses a plain `fetch(...)` without an AbortController/timeout and without a try/catch fallback to the prior local `refresh...` function when the endpoint errors or stalls. In Node/undici, `fetch` can wait indefinitely (or until long socket-level timeouts), so a slow/hung sync endpoint can block requests that require token refresh/sync, effectively stalling bookings touching the affected apps. The PR diff itself doesn’t include the relevant file, and the reports include no file/line references, so a reviewer must locate the sync-endpoint fetch wrapper in the post-PR tree and confirm the absence of `signal`/timeout and fallback logic.

**How to replicate.** 1) Configure the deployment to use the sync endpoint (whatever env/config flag points token refresh/sync at the parent endpoint) and set it to a host that accepts connections but never responds (e.g., an nginx location that sleeps/hangs).
2) Trigger an operation that requires calendar/video app sync/refresh (e.g., create a booking that writes to Google/Microsoft calendar or uses a video provider that needs token refresh).
3) Observe the server request: it hangs for a long time (until OS/TCP timeout) instead of failing fast; downstream calendar/video operations do not proceed.
Expected: request fails quickly with a controlled error and/or falls back to refreshing directly against the provider (pre-PR behavior). Actual: the entire flow stalls waiting on the sync-endpoint fetch.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·high

#### B74 — Zod schema uses computed keys via `.toString()`, collapsing distinct keys into the same "[object Object]" property and dropping expiry fields

**Location:** `packages/app-store/_utils/oauth/refreshOAuthToken.ts:12–26`  ·  **Severity:** high  ·  **Judge confidence:** 0.64

**Why this is real.** The reported code builds `minimumTokenResponseSchema` with computed property names like `[z.string().toString()]` and `[z.number().toString()]`. Zod schema instances do not override `Object.prototype.toString`, so both expressions evaluate to the identical string "[object Object]", causing the second property to overwrite the first in the object literal. As a result, the schema effectively only enforces the explicit `accessToken` field and (with `.strip()`/unknown-keys stripping) removes other response fields such as `expires_in`/`expiryDate`, which is a functional parsing bug rather than a style issue.

**How to replicate.** 1) Find `minimumTokenResponseSchema` in the file and confirm it defines two computed keys using `zodSchema.toString()` (e.g., one intended for a string key and another intended for numeric/expiry catch-all).
2) Observe that both computed keys evaluate to the same runtime key: `String(z.string()) === "[object Object]"` and `String(z.number()) === "[object Object]"`.
3) Trigger an OAuth refresh flow against any provider that returns `access_token` plus an expiry field (commonly `expires_in`, `expires_at`, or similar).
4) Compare expected vs actual: expected parsed token data includes the expiry value persisted/propagated; actual parsed output (after schema parse + strip) loses the expiry field, leaving only the access token (and possibly causing repeated refreshes or missing `expiryDate` downstream).

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: MRV·high

#### B75 — Env-example instructs generating a 24-byte key while requiring 32 bytes for AES-256 credential sync encryption

**Location:** `.env.example:215–219`  ·  **Severity:** high  ·  **Judge confidence:** 0.56

**Why this is real.** The issue is a self-contradictory instruction in the repo’s environment configuration example: a comment states the encryption key “must be 32 bytes for aes256”, but the very next line instructs generating it with `openssl rand -base64 24`, which produces only 24 random bytes (before encoding). If the implementation expects a 32-byte AES-256 key (common for `aes-256-*`), following the documented command yields an invalid key length and causes decryption/encryption to fail (e.g., throwing “invalid key length” or producing non-interoperable ciphertext). The clustered reports did not include a file/line reference in the PR diff; this verification relies on the reported offending lines being present in the post-PR tree.

**How to replicate.** 1) In a self-hosted setup, follow the `.env.example` instruction exactly and set the credential-sync encryption key to the output of `openssl rand -base64 24`.
2) Start the app and trigger the credential sync/webhook endpoint that encrypts/decrypts payloads using AES-256 (e.g., initiate a sync request from the UI or send the expected webhook request).
3) Observe server logs: expected behavior is successful decrypt/encrypt and a 2xx response; actual behavior is a runtime crypto error (commonly “invalid key length”) or consistently failing sync because the key material does not meet the AES-256 requirement.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: MRV·low

#### B76 — Race condition: check-then-insert creates duplicate Credentials for same (userId, appId) without unique constraint

**Location:** `N/A (not specified in deduplicated reports; engineer should search for the webhook handler and OAuth callback code that does `findFirst` then `create` on the Credential table)` (exact lines not in diff)  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The reports describe a concrete TOCTOU pattern: code does a `findFirst` for an existing Credential row and then, if missing, does a `create`, while also stating an `upsert` is "impossible"—which is only true if there is no unique key for (userId, appId). Without a DB-level unique constraint, two concurrent requests can both observe "no row" and both insert, producing duplicate credentials for the same user/app. The reports also note a second writer path (the local OAuth callback) targeting the same (userId, appId) slot, increasing the likelihood of concurrent writes and inconsistent/duplicated rows.

**How to replicate.** 1) Ensure a user has no existing Credential row for a given appId/provider. 2) Trigger two concurrent writes that both attempt to create that credential: e.g., (a) deliver the same integration webhook twice in parallel (or reconnect + in-flight sync), or (b) race the webhook handler against the OAuth callback for the same user/app. 3) After both requests complete, query the Credentials table filtering by that userId and appId. Expected: at most one row. Actual: two (or more) rows exist, and subsequent `findFirst` calls may pick an arbitrary one, causing flakiness/incorrect credential usage.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: MRV·high

#### B77 — (untitled)

**Location:** `?` (exact lines not in diff)  ·  **Severity:** ?  ·  **Judge confidence:** 0.00

**Why this is real.** (missing)

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: MRV·high

#### B78 — API route default-imports zod, making `z` undefined and crashing on module load

**Location:** `apps/web/pages/api/webhook/app-credential.ts:1–12`  ·  **Severity:** critical  ·  **Judge confidence:** 0.78

**Why this is real.** The route reportedly begins with a default import (`import z from "zod"`) and then calls into it early (e.g., `z.object(...)` around line 9). In this repo, other files consistently use `import { z } from "zod"` because zod does not provide a stable default export in the runtime configuration used here; as a result, `z` can be `undefined` and `z.object(...)` throws `TypeError: Cannot read properties of undefined (reading 'object')` when the module is first evaluated. This is a functional crash (not a style issue) because it prevents the handler from loading at all; the PR diff is not provided here, so this verification relies on the clustered reports’ quoted lines and the repository’s established import pattern.

**How to replicate.** 1) Checkout the PR branch and open `apps/web/pages/api/webhook/app-credential.ts`; confirm it contains `import z from "zod"` and later uses `z.object(...)` near the top-level. 2) Start the app (e.g., `pnpm dev`) and send a POST request to `POST /api/webhook/app-credential` with any JSON body. 3) Observe the server logs show a `TypeError` during module load (`...reading 'object'`) and the endpoint returns HTTP 500 instead of processing the webhook.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·medium

#### B79 — Webhook secret check has no rate limiting, enabling unlimited online guessing/brute force

**Location:** `apps/web/pages/api/webhook/app-credential.ts:18–26`  ·  **Severity:** medium  ·  **Judge confidence:** 0.80

**Why this is real.** The handler authenticates requests solely by comparing a header value to an environment secret: `req.headers[process.env.CALCOM_WEBHOOK_HEADER_NAME || "calcom-webhook-secret"] !== process.env.CALCOM_WEBHOOK_SECRET` and immediately returns `res.status(403)` on mismatch. There is no rate limiting, lockout, IP throttling, or other brute-force protection anywhere in this endpoint, so an unauthenticated caller can send unlimited guesses against the webhook secret. That makes the secret effectively an online password and weak/short secrets become practically guessable over time.

**How to replicate.** 1) Deploy/run the app with `APP_CREDENTIAL_SHARING_ENABLED=true` and set `CALCOM_WEBHOOK_SECRET` to some value. 2) Send repeated POST requests to `/api/webhook/app-credential` with an invalid `calcom-webhook-secret` header (or the configured header name), varying the header each time. 3) Observe that every request is processed and returns `403 {"message":"Invalid webhook secret"}` without any backoff, throttling headers, temporary bans, or increasing delay—allowing high-rate brute force attempts. Expected: requests should be rate-limited/blocked after some threshold to prevent online guessing.

**Found by** 1 cells (1 distinct report texts, 1 findings): sonnet: MRV·high

#### B80 — Webhook app-credential sync updates keys but leaves credential type stale

**Location:** `apps/web/pages/api/webhook/app-credential.ts:78–92`  ·  **Severity:** medium  ·  **Judge confidence:** 0.62

**Why this is real.** At the update site (around line 78 per the report), the handler updates the existing AppCredential row with the new secret payload (e.g., `key: keys`) but does not also update the row's discriminator/type (i.e., it omits something like `type: appMetadata.type`). This means an AppCredential that was created under an older app type (or whose integration type changed over time) can be successfully synced (keys updated) while still retaining an outdated `type` value in the DB. Any later resolution logic that routes by `credential.type` will then select the wrong integration despite the keys being current.

**How to replicate.** 1) In the DB, create (or pick) an existing app credential row whose `type` is the legacy/old integration type but whose `appId`/slug corresponds to an app whose `appMetadata.type` has changed (or simulate by editing `type` to an old value). 2) Call the webhook endpoint that hits `pages/api/webhook/app-credential.ts` to sync/update that credential (same credential id/app linkage), providing new `keys` so the update path is taken (not create). 3) Observe in the DB after the request: `key`/payload is updated, but `type` remains the old value. 4) Trigger any code path that loads and dispatches integration behavior based on `credential.type`; expected: it uses the app’s current integration type, actual: it routes using the stale stored `type` and behaves as the wrong integration.

**Found by** 1 cells (1 distinct report texts, 1 findings): sol: MRV·low

#### B81 — (untitled)

**Location:** `?` (exact lines not in diff)  ·  **Severity:** ?  ·  **Judge confidence:** 0.00

**Why this is real.** (missing)

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: CE·high

#### B82 — Salesforce CalendarService throws HttpError without importing it, causing ReferenceError on refresh failure

**Location:** `packages/lib/CalendarService/SalesforceCalendarService.ts:-1–-1`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The Salesforce calendar service’s refresh-token error path reportedly does `throw new HttpError(...)` (or equivalent) when `refreshResponse.ok` is false, but the file does not import/define `HttpError`. In JavaScript/TypeScript, referencing an undeclared identifier at runtime throws `ReferenceError: HttpError is not defined`, which masks the real HTTP failure and breaks the refresh flow. The PR diff does not include this file, so verification is by inspecting the existing post-PR source for a `new HttpError` usage without a corresponding import.

**How to replicate.** 1) In the Salesforce CalendarService source, locate the refresh-token request handling (the code that checks `if (!response.ok)` on the refresh call). 2) Confirm it throws `new HttpError(...)` (or `throw HttpError(...)`) and confirm there is no `import { HttpError } ...` (or local definition) in the file. 3) Runtime repro: configure an integration state that triggers a refresh request returning non-2xx (e.g., invalid/expired refresh_token or wrong client_secret so Salesforce returns 400/401). 4) Call any CalendarService method that forces a token refresh; expected: a handled/typed HTTP error; actual: `ReferenceError: HttpError is not defined` thrown instead.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: CE·low

#### B83 — Webhook credentials-write endpoint lacks rate limiting, enabling brute-force of shared secret and arbitrary credential writes

**Location:** `UNKNOWN (not provided in the deduplicated reports; PR diff does not include the affected file)` (exact lines not in diff)  ·  **Severity:** critical  ·  **Judge confidence:** 0.38

**Why this is real.** The deduplicated reports describe an unauthenticated/weakly-authenticated webhook endpoint that accepts a "secret" and then writes encrypted credentials for an arbitrary (userId, appSlug) pair, but does not apply any rate limiting. If the only gate is a shared secret and the handler allows caller-supplied userId/appSlug, lack of throttling enables iterative guessing of the secret and, once guessed, overwriting credentials for other users/apps. The reports do not include file/line references and the affected file is not part of this PR’s diff, so a human must confirm by locating the handler and verifying: (1) secret check is the only auth, (2) userId/appSlug come from the request, and (3) no rate-limit middleware/guard is applied.

**How to replicate.** 1) Locate the webhook route handler by searching the codebase for the endpoint path used for app/webhook credential updates (keywords: "webhook", "appSlug", "userId", "secret", "encrypt", "credentials", "upsert").
2) Confirm in code that the request body/query contains a shared secret and caller-controlled userId/appSlug, and that the handler performs a DB write/upsert of credentials.
3) Run the app locally and send a high-volume sequence of POST requests to that endpoint with varying `secret` values (and fixed `userId`/`appSlug`), e.g., via a simple script; observe the server continues processing requests without 429/lockout/backoff.
4) After determining/guessing the correct secret (or using a known valid one in test), send a request specifying a different victim `userId` and `appSlug` with attacker-controlled encrypted payload; expected secure behavior: reject/authorize per-user and/or rate limit; actual behavior per reports: accepts and writes credentials for the specified pair.

**Found by** 1 cells (1 distinct report texts, 1 findings): sonnet: van·medium

---

## PR 4 — 101 distinct real bugs (8 goldens + 93 the goldens missed)
(<https://github.com/ai-code-review-evaluation/discourse-graphite/pull/4>)

### Bug index

| # | sev | location | title | found by (cells) |
|---|---|---|---|---|
| B1 | critical | `app/models/topic_embed.rb:13–20` | Stored XSS: RSS/Atom item HTML is imported and rendered as raw HTML without sanitization | 65 |
| B2 | high | `app/models/topicembed.rb:58–65` | absolutize_urls treats protocol-relative URLs (//...) as root-relative and rewrites them to the article host | 48 |
| B3 | high | `app/models/topicembed.rb:48–52` | Unbounded open-uri fetch in TopicEmbed can hang jobs or exhaust Sidekiq memory | 46 |
| B4 | high | `app/models/topicembed.rb:15–28` | TopicEmbed import has check-then-create race on unique embedurl, raising RecordNotUnique under concurrency | 46 |
| B5 | critical | `lib/topicretriever.rb:14–53` | Redirect-based SSRF: only initial URL host is validated while open-uri follows redirects | 44 |
| B6 | high | `db/migrate/20131223171005createtoptopics.rb:3–3` | Destructive `force: true` in create_table migration can drop existing data | 42 |
| B7 | high | `lib/tasks/disqus.thor:114–152` | Disqus importer silently drops --category/-c support and no longer assigns imported topics to the requested category | 42 |
| B8 | high | `lib/topicretriever.rb:27–28` | Redis throttle key can become permanent due to non-atomic SETNX + EXPIRE | 41 |
| B9 | high | `app/controllers/embed_controller.rb:15–33` | EmbedController enqueues RetrieveTopic jobs on cache-miss before any request-time throttling/validation, enabling Sidekiq queue flooding | 39 |
| B10 | high | `app/views/embed/loading.html.erb:8–10` | Embed loading page reloads forever with no terminal failure state | 32 |
| B11 | critical | `app/models/topicembed.rb:11–13` | XSS via unescaped feed-supplied URL in TopicEmbed imported-from footer | 29 |
| B12 | high | `app/models/topicembed.rb:34–37` | TopicEmbed advances contentsha1 even when post revision fails, permanently skipping future re-syncs | 27 |
| B13 | medium | `app/models/topicembed.rb:79–82` | Embed URL lookup uses exact, unnormalized string match, allowing duplicate topics for equivalent URLs | 26 |
| B14 | high | `app/models/topic_embed.rb:23–34` | TopicEmbed re-import crashes when the embedded post was deleted (embed.post is nil) | 24 |
| B15 | high | `app/jobs/scheduled/pollfeed.rb:31–35` | Pollfeed aborts entire feed import on first bad item (no per-item rescue) | 24 |
| B16 | high | `lib/topicretriever.rb:41–43` | Unrescued inline feed poll aborts HTTP fallback on embed cache miss | 23 |
| B17 | medium | `spec/controllers/embedcontrollerspec.rb:39–43` | EmbedController spec still expects synchronous TopicRetriever call though controller enqueues :retrieve_topic job | 22 |
| B18 | low | `app/assets/javascripts/embed.js:5–12` | Embed script throws when #discourse-comments container is missing (no null-check before appendChild) | 17 |
| B19 | high | `db/migrate/20131217174004createtopicembeds.rb:6–10` | TopicEmbed embedurl column defaults to varchar(255), causing failures for valid long URLs during imports/polling | 15 |
| B20 | critical | `app/jobs/scheduled/pollfeed.rb:28–31` | PollFeed uses Kernel.open on an unvalidated admin setting, allowing pipe-prefixed command execution (admin-to-RCE) | 15 |
| B21 | critical | `lib/topicretriever.rb:27–35` | Throttle key is acquired before successful fetch and uses non-atomic setnx+expire, causing skipped retries or permanent lockout | 15 |
| B22 | high | `app/assets/javascripts/embed.js:15–22` | postMessage origin validation uses substring match, allowing spoofed origins to resize the embed iframe | 13 |
| B23 | medium | `app/models/topicembed.rb:12–14` | TopicEmbed import mutates caller-owned contents via `<<`, causing duplicate footers and FrozenError on frozen strings | 13 |
| B24 | high | `app/models/topicembed.rb:11–58` | TopicEmbed URL guard uses line-anchored regex and later calls URI() without rescue, allowing malformed/multiline URLs to crash imports | 12 |
| B25 | high | `app/assets/javascripts/embed.js:5–12` | embed.js throws when #discourse-comments container is missing (null appendChild) | 11 |
| B26 | critical | `app/jobs/scheduled/pollfeed.rb:30–35` | Feed polling crashes on Ruby 2.0/1.9 when calling String#scrub on RSS item content | 11 |
| B27 | high | `lib/tasks/disqus.rake:25–62` | disqus:import regresses to live HTTP fetch per thread with no error handling (and drops -c category option), causing imports to abort or mis-categorize | 10 |
| B28 | medium | `app/controllers/embedcontroller.rb:21–27` | Embed requests are wrongly rejected due to strict/unnormalized Referer host check (and requiring Referer) | 10 |
| B29 | medium | `app/models/topicembed.rb:34–37` | Existing TopicEmbed updates ignore title-only changes, leaving topic titles stale | 9 |
| B30 | high | `app/jobs/scheduled/poll_feed.rb:24–52` | PollFeed job crashes on RSS items without <content> because it calls i.content.scrub without a nil-guard | 9 |
| B31 | critical | `lib/topicretriever.rb:44–47` | Embed/topic retrieval synchronously runs full feed poll (Jobs::PollFeed) on cache miss, coupling embeds to feed health and enabling resource exhaustion | 9 |
| B32 | high | `app/models/topicembed.rb:46–48` | TopicEmbed uses open(url) without requiring open-uri, causing URL opens to be treated as local files | 9 |
| B33 | critical | `app/jobs/scheduled/pollfeed.rb:12–37` | PollFeed job crashes on RSS/summary-only items due to unconditional i.content.scrub call | 8 |
| B34 | critical | `app/views/embed/best.html.erb:6–6` | Malformed ERB terminator `<%- end if %>` breaks or miscompiles the header conditional | 7 |
| B35 | ? | `?` | (untitled) | 7 |
| B36 | high | `app/views/layouts/embed.html.erb:4–5` | Embed layout references standalone embed assets that are not added to assets.precompile, breaking production | 7 |
| B37 | critical | `lib/topicretriever.rb:49–50` | Embed topic retrieval can crash or silently no-op when embedbyusername is blank/missing, leaving embeds stuck on infinite “loading” | 7 |
| B38 | high | `lib/import_remote/readability.rb:45–92` | Readability import sanitizer preserves javascript: URLs in whitelisted href/src attributes (stored XSS on click) | 6 |
| B39 | high | `spec/controllers/embed_controller_spec.rb:44–49` | EmbedController spec expects synchronous TopicRetriever call but controller enqueues async :retrieve_topic job | 6 |
| B40 | high | `lib/topicretriever.rb:32–55` | Redis throttle key is set before retrieval succeeds, suppressing retries after failures | 5 |
| B41 | high | `app/controllers/embedcontroller.rb:27–28` | Invalid X-Frame-Options value (`allowall`) is ignored by browsers, weakening framing protection | 5 |
| B42 | critical | `app/views/embed/best.html.erb:18–25` | Embed best view renders imported post HTML as raw, enabling XSS from untrusted imported content | 5 |
| B43 | high | `lib/pollfeed.rb:29–30` | Unbounded open-uri fetch in PollFeed lacks timeouts/limits and can hang Sidekiq workers | 4 |
| B44 | high | `Gemfile:209–211` | Gemfile updated with new gems but default Gemfile.lock not regenerated, breaking frozen/deployment bundler installs | 4 |
| B45 | high | `lib/topicretriever.rb:36–37` | Race condition: non-atomic exists?/create! on TopicEmbed causes RecordNotUnique under concurrent imports | 4 |
| B46 | medium | `app/assets/javascripts/embed.js:17–21` | Incorrect postMessage origin validation uses substring match (bypassable) | 4 |
| B47 | medium | `UNKNOWN (not provided in reports; affected file not part of PR diff)` | Embed update path revises only post body; feed title changes never update topic title | 4 |
| B48 | high | `lib/topicretriever.rb:14–15` | Embeddable host validation uses strict string equality, rejecting valid hosts with different casing or with a scheme included | 4 |
| B49 | critical | `db/migrate/20131219203905_add_cookmethod_to_posts.rb:3–3` | Migration backfills posts.cookmethod to rawhtml, causing all existing posts to bypass cooking/sanitization | 4 |
| B50 | medium | `app/controllers/embed_controller.rb:15–30` | Embed controller caches the temporary “loading” placeholder, causing stale/looping reload behavior | 4 |
| B51 | ? | `?` | (untitled) | 4 |
| B52 | medium | `spec/jobs/pollfeedspec.rb:18–30` | PollFeed specs for missing URL/username are vacuous because feedpollingenabled? is never set true | 3 |
| B53 | medium | `app/jobs/scheduled/pollfeed.rb:20–22` | Dead feed-modified cache key means PollFeed always re-downloads and reprocesses the full feed | 3 |
| B54 | high | `lib/tasks/disqus.thor:148–154` | Disqus importer now live-fetches thread URLs via TopicEmbed, skipping unreachable/non-http threads and losing original created_at/permalink body | 3 |
| B55 | high | `lib/tasks/disqus.thor:148–163` | Disqus importer is no longer idempotent: reruns duplicate all replies when TopicEmbed.import_remote returns an existing post | 3 |
| B56 | high | `lib/topic_embed.rb:48–52` | Topic embed remote import uses open(url) without requiring open-uri, causing ENOENT instead of HTTP fetch | 3 |
| B57 | high | `app/models/topic_embed.rb:31–38` | TopicEmbed.import assumes embed.post exists and updates content_sha1 even if post revision fails, causing crashes or permanent stale embeds | 3 |
| B58 | high | `db/migrate/20131219203905addcookmethodtoposts.rb:3–3` | Rails migration adds NOT NULL column with DEFAULT, causing full table rewrite and ACCESS EXCLUSIVE lock on PostgreSQL < 11 | 2 |
| B59 | high | `db/schema.rb:125–140` | Embed URL column limited to 255 chars causes import/embed jobs to fail for long real-world URLs | 2 |
| B60 | ? | `?` | (untitled) | 2 |
| B61 | high | `lib/pollfeed.rb:35–35` | Poll feed processing calls `String#scrub` via `stringscrub`, crashing on Ruby 2.0 (requires Ruby >= 2.1) | 2 |
| B62 | medium | `app/models/topicembed.rb:12–16` | Embed source hash includes localized footer, causing false-positive content changes on locale/footer updates | 2 |
| B63 | critical | `lib/tasks/disqus.thor:148–148` | Disqus import passes untrusted thread <link> to importremote/open without URI validation (SSRF/LFI/RCE) | 2 |
| B64 | critical | `migrations/createtoptopics.rb:3–3` | Migration uses `force: true`, risking silent table drop and data loss on re-run | 2 |
| B65 | high | `lib/post_revisor.rb:85–90` | `skip_validations` allows saving posts/topics with invalid or unsafe data (validations fully bypassed) | 2 |
| B66 | high | `jobs/pollfeed.rb:35–35` | PollFeed job crashes on RSS items without a content field (nil.scrub) | 2 |
| B67 | critical | `app/models/post.rb:128–136` | Stored XSS: Post.cook returns raw HTML unchanged when cook_method=raw_html, bypassing sanitization/filtering | 2 |
| B68 | ? | `?` | (untitled) | 2 |
| B69 | high | `app/models/topic_embed.rb:21–34` | TopicEmbed import uses non-atomic exists?/create! allowing concurrent duplicates and unhandled RecordNotUnique | 2 |
| B70 | critical | `script/import_scripts/disqus.rb:118–132` | Disqus importer drops original topic/OP created_at by switching to TopicEmbed.import_remote without forwarding created_at | 1 |
| B71 | high | `app/jobs/regular/poll_feed.rb:18–56` | poll_feed job processes unbounded RSS items, creating/enqueuing work for every entry in a single run | 1 |
| B72 | ? | `?` | (untitled) | 1 |
| B73 | high | `app/views/embed/best.html.erb:6–6` | ERB syntax error: invalid `end if` terminator breaks embed best template rendering | 1 |
| B74 | critical | `db/migrate/20240101000000_create_topic_embeds.rb:5–12` | Migration uses `force: true` on `create_table`, risking silent drop/recreate of `topic_embeds` data on re-run | 1 |
| B75 | high | `lib/topic_embed/importer.rb:41–74` | Topic embed import crashes when Readability returns nil content | 1 |
| B76 | high | `db/schema.rb:1–1` | Migrations add posts.cookmethod and topic_embeds table but schema dump is not regenerated (schema drift) | 1 |
| B77 | medium | `app/controllers/embedcontroller.rb:16–16` | EmbedController enqueues RetrieveTopic job but spec expects synchronous TopicRetriever call | 1 |
| B78 | low | `app/jobs/regular/retrievetopic.rb:1–1` | RetrieveTopic job unnecessarily eager-loads mail stack via stray require_dependency | 1 |
| B79 | high | `app/models/topicembed.rb:1–1` | `require_dependency 'nokogiri'` can raise `LoadError` in Rails development due to `:load` dependency mechanism | 1 |
| B80 | medium | `app/models/topicembed.rb:25–35` | TopicEmbed stores redundant topic_id that can go stale when an embedded post is moved to another topic | 1 |
| B81 | high | `app/views/layouts/embed.html.erb:8–16` | Embedded iframe height is posted only on load, causing clipped content after resize/wrap | 1 |
| B82 | medium | `config/routes.rb:245–245` | New /embed/best route is unnamed and unconstrained, so it has no URL helper and accepts unintended formats | 1 |
| B83 | medium | `N/A (not referenced in the deduplicated reports; not modified in PR #4 diff)` | Embed URL is constructed by naive string concatenation, breaking when discourseUrl lacks a trailing slash | 1 |
| B84 | medium | `lib/discourse_graphite/topic_retriever.rb:17–17` | Missing presence check before calling `downcase` on `SiteSetting.embed_by_username` can raise NoMethodError | 1 |
| B85 | high | `app/views/embed/best.html.erb:1–20` | embed/best.html.erb can call @topicview.topic when @topicview is nil due to malformed conditional/end modifier | 1 |
| B86 | high | `app/controllers/embed_controller.rb:9–16` | embedurl param not type-checked allows non-String, causing unrescued TypeError in URI parsing and Sidekiq retry churn | 1 |
| B87 | medium | `layouts/embed.html.erb:11–11` | Embed iframe resize postMessage uses request.referer as targetOrigin, breaking when Referer is missing/invalid | 1 |
| B88 | high | `lib/topicretriever.rb:9–9` | Invalid or wrong-host embed URLs are treated as successful retrieval, causing infinite loading loop | 1 |
| B89 | high | `lib/topicembed.rb:48–52` | OpenURI follows redirects, bypassing host allowlist when fetching embedded topic HTML | 1 |
| B90 | medium | `pollfeed.rb:1–1` | Feed item URL fallback uses entry.id (often not a URL), causing items to be silently skipped | 1 |
| B91 | high | `app/controllers/embedcontroller.rb:28–28` | Embed endpoint trusts spoofable Referer/embedurl and uses Referer as postMessage targetOrigin | 1 |
| B92 | low | `script/retrieve_topic.rb:1–5` | Unused `require_dependency 'email/sender'` in retrieve_topic script | 1 |
| B93 | high | `app/views/layouts/embed.html.erb:11–11` | Unescaped request.referer interpolated into JS string breaks postMessage targetOrigin (and can enable injection) | 1 |
| B94 | medium | `spec/controllers/embed_controller_spec.rb:1–30` | Embed controller specs don’t render views, so embed templates can break without failing tests | 1 |
| B95 | medium | `spec/controllers/embed_controller_spec.rb:8–16` | Embed controller spec for missing embed_url is a false positive due to embeddable_host default failure | 1 |
| B96 | high | `lib/topic_embed/import_remote.rb:120–140` | Disqus-to-TopicEmbed import drops created_at, stamping imported topics with import time | 1 |
| B97 | ? | `?` | (untitled) | 1 |
| B98 | high | `N/A (not referenced in reports; affected file not included in this PR diff)` | Scheduled and inline poll can run concurrently and duplicate work when inline poll exceeds throttle TTL | 1 |
| B99 | medium | `lib/topicembed.rb:13–13` | Using `<<` to append to `contents` mutates the caller's String and can crash on frozen strings | 1 |
| B100 | high | `topicretriever.rb:41–48` | Cache miss on arbitrary URL triggers synchronous full RSS fetch+import (DoS vector) | 1 |
| B101 | high | `app/views/embed/loading.html.erb:7–11` | Embed loading page auto-reloads every 30s, amplifying unauthenticated request/job flooding risk | 1 |

### Verification cards

#### B1 — Stored XSS: RSS/Atom item HTML is imported and rendered as raw HTML without sanitization

**Location:** `app/models/topic_embed.rb:13–20`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple reports point to `app/models/topic_embed.rb:13` storing feed-controlled content as `rawhtml` (e.g., `raw: rawhtml(i.content)` / equivalent) and the corresponding behavior being asserted in `spec/models/topicembedspec.rb:36-38` (`post.cooked == post.raw`). This means attacker-supplied RSS/Atom HTML is persisted and later served from the forum origin without the normal Discourse cooking/sanitization pipeline, enabling persistent XSS. The PR diff does not include the cook/sanitize implementation, so verification relies on these referenced lines and the data flow they describe.

**How to replicate.** 1) Host an RSS/Atom feed whose item content includes executable HTML/JS, e.g. `<img src=x onerror=alert(document.domain)>` or CDATA containing `&lt;script&gt;alert(1)&lt;/script&gt;`.
2) Configure the app to poll/import that feed (the scheduled job `app/jobs/scheduled/pollfeed.rb` is reported to pass `i.content` straight into the import path at ~line 31).
3) Run the poll job (or wait for schedule) to create the embedded topic/post.
4) Visit the created topic/post page: Expected: HTML should be sanitized and scripts/handlers removed. Actual: the imported post renders the attacker-controlled HTML as raw, executing in users' browsers (stored XSS on the forum origin).

**Found by** 65 cells (205 distinct report texts, 205 findings): fable: CE·low, van·high, van·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; sonnet: CE·medium, MRV·high, MRV·low, MRV·medium, van·low, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; terra: CE·high, CE·medium, MRV·high, MRV·low, van·high, van·low, van·medium; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium

#### B2 — absolutize_urls treats protocol-relative URLs (//...) as root-relative and rewrites them to the article host

**Location:** `app/models/topicembed.rb:58–65`  ·  **Severity:** high  ·  **Judge confidence:** 0.70

**Why this is real.** Multiple reports point to `app/models/topicembed.rb` around lines 64–65 where the URL-rewriting logic uses a check like `href.start_with?('/')` and then prefixes the article URI host/scheme (e.g. `href = "#{uri.scheme}://#{uri.host}#{href}"`). Because protocol-relative URLs begin with `//`, they satisfy `start_with?('/')` and are incorrectly rewritten as if they were root-relative paths on the article host, yielding a broken URL such as `https://article-host//cdn.example.com/img.png` instead of preserving `//cdn.example.com/img.png` or converting it to `https://cdn.example.com/img.png`. The file is not part of this PR’s diff, so verification is based on the consistent line references and described control flow in the deduplicated reports.

**How to replicate.** 1) Locate the method in `app/models/topicembed.rb` that rewrites `<a href>`/`<img src>` attributes (the reports cite ~58–65). 2) Confirm it has a branch that checks `start_with?('/')` and then builds an absolute URL by concatenating the embed/article URI scheme+host with the original string. 3) Consider an embedded article URL like `https://example.com/blog/post.html` containing HTML `<img src="//cdn.example.com/img.png">`. Expected: the rewritten `src` should remain protocol-relative (`//cdn.example.com/img.png`) or be absolutized to `https://cdn.example.com/img.png`. Actual per the code path: it matches the leading `/` branch and becomes `https://example.com//cdn.example.com/img.png` (or otherwise incorrectly points at the article host), breaking the link/image.

**Found by** 48 cells (116 distinct report texts, 116 findings): fable: CE·low, van·high, van·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·medium, van·high, van·medium, van·xhigh; terra: CE·medium, MRV·low, MRV·medium, van·low, van·xhigh; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium

#### B3 — Unbounded open-uri fetch in TopicEmbed can hang jobs or exhaust Sidekiq memory

**Location:** `app/models/topicembed.rb:48–52`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** The code at/around the reported location performs a remote fetch using open-uri and reads the entire response into memory (e.g., `open(url).read`). This call is made without explicit open/read timeouts and without a maximum byte limit, so a slow/stalled origin can tie up the worker indefinitely and a very large response can be fully buffered into memory, potentially OOM-killing the Sidekiq process. This is a functional reliability/security defect (resource exhaustion), not a style issue; the evidence here relies on the deduplicated reports because the PR diff for this file is not provided.

**How to replicate.** 1) Configure/trigger the code path that fetches an embed/article/feed URL through TopicEmbed (use a URL that TopicEmbed will fetch).
2) Point the URL to (a) an endpoint that never finishes sending data (slowloris/chunked stream) or sleeps for a long time before responding, and (b) an endpoint that returns a very large body (e.g., hundreds of MB).
3) Run the Sidekiq job/process that performs the fetch.
Expected: the job times out quickly and/or stops after a bounded number of bytes.
Actual: with `open(url).read`, the job can hang for a long time (no timeout) or memory usage grows until the worker is killed or becomes unstable (no response-size cap).

**Found by** 46 cells (94 distinct report texts, 94 findings): fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·xhigh; sonnet: CE·low, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; glm-vis: CE·low, CE·medium, MRV·high, MRV·low, van·high; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·xhigh; terra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### B4 — TopicEmbed import has check-then-create race on unique embedurl, raising RecordNotUnique under concurrency

**Location:** `app/models/topicembed.rb:15–28`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The code path reported at `app/models/topicembed.rb:15` performs a lookup-then-create sequence (e.g., `where(embedurl: ...).first` followed by `create!`) against a column guarded by a unique index on `embedurl`. Under concurrent first-retrievals of the same URL, both workers can observe “no row”, then both attempt `create!`; the loser raises `ActiveRecord::RecordNotUnique` instead of treating the embed as already imported. The file is not part of this PR’s diff, so verification relies on reading the existing post-PR code at/around those lines and confirming the non-atomic check-then-act logic and absence of an upsert/lock/rescue retry.

**How to replicate.** 1) Ensure the DB has a unique index on `topic_embeds.embedurl` (as implied by the reports). 2) Trigger two concurrent jobs/requests that import the same previously-unseen `embedurl` (e.g., run two threads/processes calling the retrieval/import method for the same URL at the same time). 3) Expected: exactly one TopicEmbed row is created and both workers proceed using it. Actual: one worker succeeds, the other crashes with `ActiveRecord::RecordNotUnique` (or `RecordInvalid` depending on validations), which can abort the remaining items in that retrieval run.

**Found by** 46 cells (67 distinct report texts, 67 findings): fable: CE·low, van·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; sonnet: CE·medium, MRV·high, MRV·low, van·high, van·low, van·medium, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-vis: CE·low, CE·medium, MRV·high, MRV·low, van·high, van·low; sol: CE·high, MRV·medium, van·high, van·xhigh; terra: CE·low, MRV·high, MRV·low, van·low; astra: MRV·high, MRV·medium

#### B5 — Redirect-based SSRF: only initial URL host is validated while open-uri follows redirects

**Location:** `lib/topicretriever.rb:14–53`  ·  **Severity:** critical  ·  **Judge confidence:** 0.78

**Why this is real.** The reports consistently describe code in lib/topicretriever.rb that validates only the initial hostname (e.g., parsing the input URL and checking `uri.host`) and then fetches content via open-uri (e.g., `open(url).read`). open-uri follows HTTP redirects by default, so if validation occurs only before the first request and the redirect destination is not re-checked (host/scheme/IP range), an attacker can use an allowed/whitelisted host that 30x-redirects to `127.0.0.1`, RFC1918 ranges, or `169.254.169.254` and the server will fetch it. The PR diff does not include this file, so this verification relies on the line references and behavior described in the reports rather than a patch hunk.

**How to replicate.** 1) Find where TopicRetriever is invoked (e.g., a feature that fetches/embeds remote topic content) and confirm it accepts a user-supplied URL.
2) Choose an allowed domain (one that passes the hostname allowlist) that can issue a redirect, or use any allowed domain with an open-redirect endpoint.
3) Provide a URL like `https://allowed.example/redirect?to=http://169.254.169.254/latest/meta-data/` (or to `http://127.0.0.1:PORT/`).
4) Observe server-side behavior: expected is the fetch should be rejected once it redirects off the approved host / into private or link-local address space; actual is the request follows the redirect and retrieves internal/metadata content because the redirect destination is not revalidated.

**Found by** 44 cells (69 distinct report texts, 69 findings): fable: CE·low, van·medium; opus: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·xhigh; sonnet: CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium, van·xhigh; glm-flash: MRV·high, MRV·low, MRV·medium, van·high; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; terra: CE·medium, MRV·high, van·high, van·medium; astra: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### B6 — Destructive `force: true` in create_table migration can drop existing data

**Location:** `db/migrate/20131223171005createtoptopics.rb:3–3`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** The migration’s `create_table` call includes `force: true` (reported at line 3), i.e., `create_table :toptopics, force: true do |t| ...`. In Rails, `force: true` drops the table if it already exists before recreating it. That turns a normally safe/failed re-run (which would raise if the table exists) into silent, irreversible data loss if the migration is ever replayed against a DB where `toptopics` already exists.

**How to replicate.** 1) In a Rails console or via SQL, create/populate a `toptopics` table with at least one row. 2) Ensure the migration is considered pending (e.g., delete its version row from `schema_migrations` while keeping the table). 3) Run `rails db:migrate`. Expected: migration should fail because the table already exists (preventing accidental overwrite). Actual: with `force: true`, the existing `toptopics` table is dropped and recreated, and the row(s) are lost.

**Found by** 42 cells (82 distinct report texts, 82 findings): fable: CE·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium, van·xhigh; sonnet: CE·low, MRV·high, MRV·medium; glm-flash: CE·high, CE·low, MRV·high, MRV·low, MRV·medium, van·high, van·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·low; terra: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; astra: CE·medium, MRV·high, MRV·low

#### B7 — Disqus importer silently drops --category/-c support and no longer assigns imported topics to the requested category

**Location:** `lib/tasks/disqus.thor:114–152`  ·  **Severity:** high  ·  **Judge confidence:** 0.86  ·  ⚠️ `distinct=false` (cluster may span two bugs)

**Why this is real.** In the post-PR code, the CLI option is removed (the options list no longer includes `method_option :category, aliases: '-c'`), and the category lookup/assignment code is deleted. The import path now calls `post = TopicEmbed.import_remote(user, t[:link], title: t[:title])`, which does not take or apply a category ID, whereas the pre-change code explicitly did `PostCreator.new(..., category: category_id)`. This is a behavioral regression: existing automation that passes `--category/-c` will fail (unknown option) and imports can no longer be directed into a chosen category, forcing them into the default/uncategorized behavior.

**How to replicate.** 1) In a Discourse instance with this PR applied, run the Thor task as previously documented/used: `bundle exec thor disqus:import --post_as admin --category "Support" ...` (or `-c Support`).
2) Expected (pre-PR): the task accepts `--category/-c` and imported topics are created in the "Support" category.
3) Actual (post-PR): Thor rejects the invocation with an unknown option error (since `:category` is no longer defined), and even if invoked without the flag, the created topic comes from `TopicEmbed.import_remote(...)` with no category assignment, so imports are not placed into the intended category.

**Found by** 42 cells (77 distinct report texts, 77 findings): fable: CE·low, van·high, van·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium, van·xhigh; sonnet: CE·medium, MRV·high, MRV·low, MRV·medium, van·medium, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, van·high, van·medium; glm-vis: CE·high, CE·medium, MRV·high, van·medium; sol: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; terra: MRV·medium; astra: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### B8 — Redis throttle key can become permanent due to non-atomic SETNX + EXPIRE

**Location:** `lib/topicretriever.rb:27–28`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** In `lib/topicretriever.rb` around lines 27–28, the throttle/lock is implemented as two separate Redis commands: `redis.setnx(throttle_key, 1)` followed by `redis.expire(throttle_key, THROTTLE_SECONDS)` (or equivalent). Because these are not atomic, a process crash/kill between the `setnx` and `expire` leaves the key present with no TTL. Subsequent runs see the key and treat the URL as throttled forever, so retrieval for that embed URL is permanently suppressed.

**How to replicate.** 1) Configure a Redis instance and run the code path that triggers the embed URL throttle (the one guarded by the SETNX/EXPIRE pair). 2) Instrument or pause execution right after `setnx` returns success (e.g., add a `sleep` between the `setnx` and `expire` lines), then kill the worker/process before `expire` executes. 3) Verify in Redis: `TTL <throttle_key>` returns -1 (no expiry) while the key exists. 4) Trigger the same URL retrieval again: expected behavior is that the throttle expires after the intended window and retrieval resumes; actual behavior is that retrieval continues to be skipped indefinitely because the key never expires.

**Found by** 41 cells (74 distinct report texts, 74 findings): fable: CE·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; sonnet: CE·medium, MRV·high; glm-flash: CE·high, CE·medium, MRV·high, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·medium, van·high, van·medium; sol: CE·high, MRV·high, van·high, van·xhigh; terra: CE·high, CE·medium, van·high; astra: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium

#### B9 — EmbedController enqueues RetrieveTopic jobs on cache-miss before any request-time throttling/validation, enabling Sidekiq queue flooding

**Location:** `app/controllers/embed_controller.rb:15–33`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** Although this PR does not include the embed_controller.rb diff, the deduplicated reports consistently point to the same control-flow: on an anonymous embed request (cache miss), the controller enqueues a `RetrieveTopic` background job immediately (e.g., `Jobs.enqueue(:retrieve_topic, ...)`) and only later relies on throttling inside the worker. This means request-time throttling/validation is bypassed: even if the worker later decides the work is throttled, the Sidekiq queue has already grown, so repeated requests can create unbounded queued jobs.

**How to replicate.** 1) In a dev/staging environment with Sidekiq enabled, send many GET requests to the embed endpoint that triggers topic retrieval on cache miss (e.g., /embed?embed_url=<unique-url>), each with a (possibly forged) Referer header if required by the controller.
2) Ensure each request is a cache miss by varying embed_url (e.g., append a unique query string each time).
3) Observe Sidekiq queue size: expected behavior is early rejection/rate-limit before enqueuing; actual behavior is that every request enqueues a new RetrieveTopic job, growing the queue even if the worker later throttles/drops execution.

**Found by** 39 cells (112 distinct report texts, 112 findings): fable: CE·low, van·high, van·low; opus: CE·high, CE·low, CE·medium, MRV·medium, van·medium, van·xhigh; sonnet: CE·medium, MRV·high, MRV·low, MRV·medium, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; sol: CE·high, CE·low, CE·medium, van·high, van·low, van·medium, van·xhigh; terra: van·high

#### B10 — Embed loading page reloads forever with no terminal failure state

**Location:** `app/views/embed/loading.html.erb:8–10`  ·  **Severity:** high  ·  **Judge confidence:** 0.82

**Why this is real.** The view unconditionally schedules a page reload every 30 seconds: `setTimeout(function() { document.location.reload(); }, 30000);`. There is no conditional check, retry cap, or error/timeout UI, so if the underlying retrieval can never succeed (invalid URL, network failure, misconfiguration), the client will reload indefinitely and keep hitting the server forever. This is functional behavior (infinite polling loop), not a style concern.

**How to replicate.** 1) Configure/trigger an embed retrieval that will never become ready (e.g., embed an invalid/unreachable URL or simulate retrieval failure). 2) Load the embed/iframe so it renders `app/views/embed/loading.html.erb`. 3) Observe the browser reloading the same loading page every ~30 seconds indefinitely. Expected: after some number of failed attempts or a timeout, the page should stop polling and display an error state (and ideally stop generating repeated server requests/jobs); Actual: it reloads forever.

**Found by** 32 cells (62 distinct report texts, 62 findings): fable: CE·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium, van·xhigh; sonnet: CE·medium, MRV·low; glm-flash: CE·high, CE·low, CE·medium, MRV·high, van·high, van·low, van·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high; sol: CE·high, van·high, van·xhigh; terra: CE·low; astra: CE·medium, MRV·high

#### B11 — XSS via unescaped feed-supplied URL in TopicEmbed imported-from footer

**Location:** `app/models/topicembed.rb:11–13`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple reviewers point to the same code region in `app/models/topicembed.rb` (around lines 12–13) where the feed-provided `url` is interpolated directly into an anchor tag without HTML escaping, e.g. `<a href='#{url}'>#{url}</a>`. Because the URL comes from an untrusted external feed and is only weakly prefix-validated (`^https?://`), a crafted URL containing a single quote can break out of the `href` attribute and inject new attributes/HTML, leading to stored XSS when the imported post is rendered. The PR diff does not include this file, so this verification relies on the reported line references and the described string interpolation pattern.

**How to replicate.** 1) Create or control an RSS/Atom feed that Discourse imports via TopicEmbed, and set an item/link URL to something like `https://example.com/' onmouseover='alert(1)` (or `https://example.com/'><img src=x onerror=alert(1)>`). 2) Trigger the TopicEmbed import so it creates a post containing the "imported from" footer. 3) View the resulting topic/post in a browser. Expected: the imported-from link is safely encoded and inert. Actual: the crafted URL breaks out of the href attribute or tag context, resulting in injected HTML/JS execution (stored XSS).

**Found by** 29 cells (46 distinct report texts, 46 findings): fable: CE·low, van·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium

#### B12 — TopicEmbed advances contentsha1 even when post revision fails, permanently skipping future re-syncs

**Location:** `app/models/topicembed.rb:34–37`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** In `app/models/topicembed.rb` around lines 34–37, the code path calls the revisor (e.g., `revisor.revise!(...)`) but does not check its return value / persistence success before updating the embed’s checksum (e.g., `update_column(:contentsha1, new_sha1)` or equivalent). This means a rejected/failed revision (validation/callback/permission) can still advance `contentsha1`, making the system believe the new content was imported even though the post body did not change. Because subsequent sync checks compare the current content’s SHA to `contentsha1`, the failed update will never be retried and the embedded topic content can remain stale indefinitely (reports indicate the file is not modified in this PR, so verification relies on the current code in that file).

**How to replicate.** 1) Locate the import/update method in `TopicEmbed` that computes a new content SHA and then revises the first post via `PostRevisor` (or similar) followed by an unconditional `contentsha1` write.
2) Create a scenario where `revisor.revise!` fails/returns false (e.g., make the target post/topic non-editable, trigger a validation/callback rejection, or otherwise cause the revisor save to fail).
3) Run the embed import/update with changed remote content so a new SHA is computed.
Expected: if the revision fails, `contentsha1` should remain unchanged so a later run retries.
Actual: `contentsha1` is updated despite the failed revision; the post content remains old, and later runs skip updating because the stored SHA now matches the new remote content.

**Found by** 27 cells (34 distinct report texts, 34 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium; sonnet: MRV·low; glm-flash: CE·low, MRV·low, MRV·medium, van·low; glm-vis: CE·high, CE·low, MRV·low; sol: CE·high, MRV·high, MRV·low, MRV·medium; terra: CE·high; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### B13 — Embed URL lookup uses exact, unnormalized string match, allowing duplicate topics for equivalent URLs

**Location:** `app/models/topicembed.rb:79–82`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72

**Why this is real.** The code (per the aggregated reports; this file is not part of the PR diff) performs an exact lookup on the stored embed URL, e.g. `TopicEmbed.where(embed_url: embed_url).first` / `find_by(embed_url: embed_url)` at/around line 79. Because the input is used verbatim (no canonicalization such as stripping fragments, normalizing trailing slashes, or normalizing query strings/host casing), logically equivalent URLs (like `https://site/a` vs `https://site/a/` vs `https://site/a#x`) will not match the existing record and can cause creation of separate TopicEmbed/Topic records for the same resource. This is a functional correctness bug (duplicate discussions / split history), not a style issue.

**How to replicate.** 1) Enable/confirm Discourse embedding is set up for a host and can create topics from an `embed_url`.
2) Trigger an embed for a URL, e.g. request the embed endpoint (or run the embed creation path) with `embed_url=https://example.com/article` and observe a topic created and a TopicEmbed row stored with that exact string.
3) Trigger embedding again for a semantically equivalent variant, e.g. `https://example.com/article/` (trailing slash) or `https://example.com/article#comments` (fragment) or `https://EXAMPLE.com/article` (host case).
Expected: the existing embedded topic is found and reused. Actual: the lookup misses and a new topic/topicembed is created, resulting in duplicate topics for the same article (and potentially bypassing any per-URL throttling keyed on the raw string).

**Found by** 26 cells (42 distinct report texts, 42 findings): fable: van·high, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·medium; glm-flash: MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium; sol: CE·high, MRV·high, MRV·medium, van·low, van·xhigh; terra: MRV·low, MRV·medium; astra: MRV·high, MRV·low, MRV·medium

#### B14 — TopicEmbed re-import crashes when the embedded post was deleted (embed.post is nil)

**Location:** `app/models/topic_embed.rb:23–34`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The code path that updates an existing embed assumes the associated Post still exists, e.g. it calls `PostRevisor.new(embed.post)` / `post_revisor = PostRevisor.new(post)` without checking for nil. If the embedded post has been deleted/trashed, `embed.post` will return nil (association can’t find the record due to deletion/default scope), so `PostRevisor.new(nil).revise!` raises (typically a NoMethodError inside PostRevisor) and the poll/import request aborts with a 500. This is a functional crash scenario, not a style issue; the reports indicate these exact lines but the PR diff does not include this file, so verification relies on reading the current file at the referenced lines.

**How to replicate.** 1) Create an embed so a TopicEmbed row exists and is linked to a created Post (initial import works). 2) Delete/trash that Post (or delete the Topic/Post in a way that leaves the TopicEmbed row behind). 3) Trigger the embed update path again (e.g., hit the embed poll/import endpoint for the same embed URL so it tries to revise the existing post). Expected: the system should recreate the post or clean up the embed and re-import. Actual: it attempts `PostRevisor.new(embed.post).revise!` with embed.post == nil and raises, returning a 500 and preventing further re-import attempts.

**Found by** 24 cells (68 distinct report texts, 68 findings): fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium, van·xhigh; sonnet: MRV·medium; glm-flash: CE·high, CE·low, MRV·high, MRV·low, MRV·medium, van·high; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium

#### B15 — Pollfeed aborts entire feed import on first bad item (no per-item rescue)

**Location:** `app/jobs/scheduled/pollfeed.rb:31–35`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The code iterates `rss.items.each do |item|` (around line 31) and processes each entry inline, including calling methods on item fields (reports cite `item.content.scrub` / `nil.scrub`) and other parsing steps, but there is no `rescue` inside the loop to isolate failures per item. As a result, any exception raised while handling one item (nil content, malformed URL in absolutization, RecordNotUnique, network fetch error) will unwind the loop and abort processing of all subsequent items. The PR diff for this file is not included here; this verification relies on the repeated line-specific reports pointing to the same unrescued loop in `pollfeed.rb`.

**How to replicate.** 1) Create/point a polled RSS/Atom feed to one with multiple items where an early item is malformed (e.g., an item with no `<content>` so `content` is nil, or an invalid URL that triggers an exception in URL absolutization). 2) Run the scheduled Pollfeed job (or invoke the job method directly) so it processes the feed. 3) Observe that items before the bad entry are imported, then the job crashes/aborts at the bad item; items after it are not imported in that run (and with job retries disabled, they remain skipped until the next poll). Expected behavior is that one bad item is skipped/logged while the rest of the feed continues importing.

**Found by** 24 cells (41 distinct report texts, 41 findings): fable: CE·low, van·high; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·high, MRV·low; glm-flash: CE·high, CE·low, CE·medium, van·high; glm-vis: CE·high, CE·low, CE·medium, MRV·medium; sol: CE·high, CE·medium, van·high; terra: CE·high, CE·medium; astra: CE·low

#### B16 — Unrescued inline feed poll aborts HTTP fallback on embed cache miss

**Location:** `lib/topicretriever.rb:41–43`  ·  **Severity:** high  ·  **Judge confidence:** 0.70

**Why this is real.** The reported code path around `lib/topicretriever.rb:41` calls `Jobs::Pollfeed.new.execute({})` synchronously inside the retrieval flow (e.g., in/near `performretrieve`) and does not rescue exceptions from that call. Because the poll runs inline and unhandled errors propagate, any feed-level failure (network error, malformed RSS) aborts the method before it can reach the direct `fetchhttp` fallback, so otherwise reachable articles are never retrieved and embeds remain stuck. This file is not part of the PR diff per the prompt, so verification relies on reading the referenced lines in the post-PR tree to confirm the inline call and lack of exception handling/ensure around it.

**How to replicate.** 1) Configure an embed URL that is not yet cached (clear the plugin/cache store). 2) Point the RSS/feed source used by `Jobs::Pollfeed` to an unavailable/malformed endpoint (e.g., invalid host or serve broken XML). 3) Trigger retrieval for the uncached embed (load a post containing the embed or call the retriever method). Expected: the code should fall back to a direct HTTP fetch and still retrieve the target article. Actual: the inline `Pollfeed.execute` raises, the exception propagates, and the HTTP fallback is skipped, leaving the embed/article unresolved (often a perpetual loading state).

**Found by** 23 cells (35 distinct report texts, 35 findings): fable: CE·low, van·medium; opus: CE·high, CE·medium, MRV·low, MRV·medium, van·medium, van·xhigh; glm-flash: CE·high; glm-vis: CE·low, CE·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, van·xhigh; terra: CE·high, MRV·medium; astra: CE·high, CE·low, MRV·high, MRV·medium

#### B17 — EmbedController spec still expects synchronous TopicRetriever call though controller enqueues :retrieve_topic job

**Location:** `spec/controllers/embedcontrollerspec.rb:39–43`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The clustered reports all point to expectations around lines 39–43 that stub/expect a direct TopicRetriever invocation (e.g., `expect(TopicRetriever).to receive(:new)` and `...retrieve`). However, the controller behavior has changed to enqueue a background job (e.g., `Jobs.enqueue(:retrieve_topic, ...)`) instead of calling `TopicRetriever.new(...).retrieve` inline, so these expectations can never be satisfied. The PR does not include this spec file in its diff, so the verification relies on the reported line references and the controller’s new async contract.

**How to replicate.** 1) Check the post-PR controller action handling embeds (EmbedController) and confirm it calls `Jobs.enqueue(:retrieve_topic, ...)` rather than `TopicRetriever.new(...).retrieve`.
2) Open `spec/controllers/embedcontrollerspec.rb` around lines 39–43 and observe it still expects `TopicRetriever` to be instantiated and `retrieve` called.
3) Run `bundle exec rspec spec/controllers/embedcontrollerspec.rb`.
Expected: spec asserts the async enqueue behavior (job name + payload) and passes. Actual: spec fails with an unmet expectation because `TopicRetriever.new(...).retrieve` is never called.

**Found by** 22 cells (28 distinct report texts, 28 findings): opus: CE·low, CE·medium, MRV·low, MRV·medium, van·medium, van·xhigh; sonnet: CE·high; glm-vis: CE·low; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·low, van·medium; terra: CE·high, CE·medium, MRV·high, van·high, van·low; astra: CE·high

#### B18 — Embed script throws when #discourse-comments container is missing (no null-check before appendChild)

**Location:** `app/assets/javascripts/embed.js:5–12`  ·  **Severity:** low  ·  **Judge confidence:** 0.92  ·  ⚠️ `distinct=false` (cluster may span two bugs)

**Why this is real.** The code unconditionally does `var comments = document.getElementById('discourse-comments')` and then immediately calls `comments.appendChild(iframe);`. If the host page does not include an element with id `discourse-comments`, `getElementById` returns `null`, so calling `.appendChild(...)` throws a `TypeError` at runtime. This is a real crash condition triggered by normal DOM state, not a style issue.

**How to replicate.** 1) Include this embed.js on any page that does NOT contain `<div id="discourse-comments"></div>`. 2) Define the required globals (e.g., `window.discourseUrl='https://forum.example.com/'; window.discourseEmbedUrl=location.href;`). 3) Load the page and observe the browser console: expected behavior would be a no-op or a clear warning; actual behavior is an exception like `TypeError: Cannot read properties of null (reading 'appendChild')`, and the embed initialization aborts.

**Found by** 17 cells (27 distinct report texts, 27 findings): fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·low, MRV·medium, van·low, van·medium, van·xhigh; sonnet: MRV·high; glm-flash: CE·low, MRV·medium, van·high, van·low, van·medium; sol: CE·low, CE·medium

#### B19 — TopicEmbed embedurl column defaults to varchar(255), causing failures for valid long URLs during imports/polling

**Location:** `db/migrate/20131217174004createtopicembeds.rb:6–10`  ·  **Severity:** high  ·  **Judge confidence:** 0.70

**Why this is real.** Multiple reports pinpoint the migration line defining the column as a default-length string (e.g., `t.string :embedurl`), which in Rails maps to `varchar(255)` unless a larger `:limit` is specified. Real-world article/feed URLs (especially with tracking/query params) can exceed 255 characters; when such a URL is inserted into `topic_embeds.embedurl`, Postgres raises a "value too long"/`StatementInvalid` error, aborting the import/poll job. The file is not part of this PR's diff, so this verification relies on the reported offending line reference (`:6`) and standard Rails schema behavior for `t.string`.

**How to replicate.** 1) Ensure the migration has been applied and `topic_embeds.embedurl` is a `varchar(255)` (e.g., `\d topic_embeds` in psql). 2) Attempt to create a TopicEmbed (or run the feed import/poll job) with an embed URL longer than 255 chars, e.g. `TopicEmbed.create!(embedurl: 'http://example.com/?' + 'a'*300, topic_id: some_topic_id)`. 3) Expected: record is created and job continues. Actual: database insert fails with a length/statement error and the import/polling process aborts or partially processes then crashes.

**Found by** 15 cells (30 distinct report texts, 30 findings): fable: CE·low; opus: CE·medium, MRV·high, MRV·medium, van·xhigh; sonnet: CE·low, CE·medium; glm-flash: CE·medium, MRV·high, van·high; glm-vis: MRV·high, MRV·medium; sol: van·medium, van·xhigh; astra: MRV·high

#### B20 — PollFeed uses Kernel.open on an unvalidated admin setting, allowing pipe-prefixed command execution (admin-to-RCE)

**Location:** `app/jobs/scheduled/pollfeed.rb:28–31`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74

**Why this is real.** In `app/jobs/scheduled/pollfeed.rb` the scheduled job fetches the feed by calling `open(SiteSetting.feed_polling_url)` (reported around lines 28–30). In Ruby, `Kernel#open` treats a string starting with `"|"` as a shell command to execute ("kernelopen" behavior), so a setting value like `"|id"` is executed instead of being treated as a URL. Because `SiteSetting.feed_polling_url` is not validated/parsed before passing into `open`, an admin-configurable value can trigger command execution in the Sidekiq/job process; the PR diff doesn’t include this file, so this verification relies on the reported line references and Ruby’s documented `Kernel#open` semantics.

**How to replicate.** 1) In the admin UI (or Rails console), set the site setting `feed_polling_url` to a pipe-prefixed payload, e.g. `|touch /tmp/pollfeed_pwned`.
2) Trigger the scheduled PollFeed job (wait for it to run, or invoke the job class/method that calls `open(SiteSetting.feed_polling_url)` in a Rails console).
3) Observe that the command is executed on the server running the job: `/tmp/pollfeed_pwned` is created (actual). Expected behavior is that the job only performs an HTTP(S) fetch of a URL and rejects non-HTTP(S) inputs rather than executing anything.

**Found by** 15 cells (19 distinct report texts, 19 findings): fable: CE·low, van·low; opus: CE·high, CE·low; sonnet: CE·medium, MRV·high; glm-flash: CE·high, MRV·high; glm-vis: CE·medium, MRV·high, van·high, van·medium; sol: van·high, van·medium; astra: MRV·high

#### B21 — Throttle key is acquired before successful fetch and uses non-atomic setnx+expire, causing skipped retries or permanent lockout

**Location:** `lib/topicretriever.rb:27–35`  ·  **Severity:** critical  ·  **Judge confidence:** 0.72  ·  ⚠️ `distinct=false` (cluster may span two bugs)

**Why this is real.** Multiple reports point to code around lines 27–35 that (a) records the throttle before the retrieval succeeds and (b) implements the throttle with `$redis.setnx(...)` followed by a separate `$redis.expire(...)`. If the fetch fails and Sidekiq retries within the TTL window, the worker can see the throttle key already set and return early "success" without re-attempting the failed work. Separately, because `setnx` and `expire` are not atomic, a process crash between them can leave the key without a TTL (TTL = -1), permanently blocking future retrieval for that URL; this is a functional correctness bug, not a style issue. (The file is not in this PR diff, so this is verified based on the consistent line-referenced reports.)

**How to replicate.** 1) Skipped retry path: enqueue the job that calls TopicRetriever for a given URL; force the actual fetch/parsing to raise (e.g., network failure/timeout) after the throttle key has been set. Observe Sidekiq schedules a retry; when it runs within ~60s, the code hits the throttle early-return (because the key already exists) and exits without fetching; expected: the retry should re-attempt the fetch and only throttle after a successful completion.
2) Permanent lockout path: run two Redis commands as the code does—first `SETNX retrieved:<url> 1`, then kill the process before `EXPIRE retrieved:<url> 60` executes. In Redis, `TTL retrieved:<url>` returns -1 (no expiry); subsequent runs will always see the key present and never retrieve that URL again; expected: throttle key should always have an expiry (atomic `SET ... NX EX 60` or Lua).

**Found by** 15 cells (18 distinct report texts, 18 findings): opus: MRV·high, MRV·low; glm-flash: CE·high, CE·low; glm-vis: CE·high, CE·medium, van·low; sol: CE·high, CE·low, CE·medium, MRV·low, MRV·medium; terra: MRV·low, MRV·medium; astra: MRV·low

#### B22 — postMessage origin validation uses substring match, allowing spoofed origins to resize the embed iframe

**Location:** `app/assets/javascripts/embed.js:15–22`  ·  **Severity:** high  ·  **Judge confidence:** 0.86  ·  ⚠️ `distinct=false` (cluster may span two bugs)

**Why this is real.** The message handler accepts a sender based on a substring/prefix check: `if (discourseUrl.indexOf(e.origin) === -1) { return; }` (line 17). If `discourseUrl` is `https://forum.example.com/`, an attacker origin like `https://forum.example.co` (or any string that appears within `discourseUrl`) makes `indexOf(...)` return 0 and passes the check, even though it is a different origin. That lets an attacker-controlled frame/window send `{ type: 'discourse-resize', height: ... }` and force `iframe.height = e.data.height + "px"` (line 21).

**How to replicate.** 1) On a test page that includes this embed.js, set `discourseUrl = "https://forum.example.com/"` and include the Discourse embed (so `#discourse-comments` exists). 2) Also include (or open) an attacker-controlled iframe/window hosted at `https://forum.example.co` (note the missing final 'm'—different origin, but a prefix of the real one). 3) From that attacker iframe/window, run `parent.postMessage({type:'discourse-resize', height: 50000}, '*');`. Expected: the message is rejected because the origin is not exactly `https://forum.example.com`. Actual: it is accepted due to the substring check and the Discourse iframe is resized to 50000px height (layout disruption/overlay potential).

**Found by** 13 cells (16 distinct report texts, 16 findings): fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; sonnet: MRV·low; glm-flash: CE·high, CE·low; glm-vis: CE·high, CE·low, CE·medium; sol: CE·high

#### B23 — TopicEmbed import mutates caller-owned contents via `<<`, causing duplicate footers and FrozenError on frozen strings

**Location:** `app/models/topicembed.rb:12–14`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The code appends the imported-from footer using in-place mutation: `contents << "\n<hr>..."` (reports point to lines ~12–14). Using `<<` modifies the caller-provided String object, so if the same `contents` instance is reused (retries/re-imports) the footer accumulates repeatedly. If `contents` is frozen (e.g., from `# frozen_string_literal: true` or explicitly `.freeze`), `<<` raises `FrozenError`, making this a functional bug rather than a style issue; the PR diff does not include this file, so this is based on the referenced post-PR line locations in the reports.

**How to replicate.** 1) In a Rails console, create a reusable string: `c = "Hello"`; call the import method (e.g., `TopicEmbed.import(url, title, c, user_id, ...)`) twice with the same `c` object. Expected: imported footer appears once per stored post; actual: `c` is mutated and the second call appends a second footer (and any downstream SHA1/validation based on `contents` changes as a side effect).
2) Trigger frozen input: `c = "Hello".freeze` (or use a frozen string literal in code) and call the same import path. Expected: import succeeds; actual: raises `FrozenError` at the `contents << "\n<hr>..."` line.

**Found by** 13 cells (16 distinct report texts, 16 findings): fable: CE·low, van·low; opus: CE·medium, MRV·high, van·high, van·low, van·medium, van·xhigh; glm-flash: CE·low, van·high; sol: CE·high; astra: CE·low, MRV·high

#### B24 — TopicEmbed URL guard uses line-anchored regex and later calls URI() without rescue, allowing malformed/multiline URLs to crash imports

**Location:** `app/models/topicembed.rb:11–58`  ·  **Severity:** high  ·  **Judge confidence:** 0.68

**Why this is real.** Multiple reports point to a scheme/prefix check like `url =~ /^https?\:\/\//` around line 11 and later parsing like `URI(url)` inside `absolutize_urls` around lines 57–58. In Ruby, `^` is line-anchored (matches after newlines), so a multiline string such as `"javascript:...\nhttp://x"` can pass the `^https?://` gate even though the overall value is not a safe/valid URL. Separately, the guard only checks a prefix, so malformed values (e.g., containing spaces) can still pass and then `URI(url)` can raise `URI::InvalidURIError`; if not rescued, that exception aborts the feed/import job.

**How to replicate.** 1) Locate `app/models/topicembed.rb` and confirm there is a URL scheme check around line ~11 using a regex anchored with `^` (e.g., `/^https?:\/\//`) rather than `\A`.
2) Confirm `absolutize_urls` (around lines ~57–58) calls `URI(url)` / `URI.parse(url)` without a `rescue URI::InvalidURIError`.
3) Trigger: provide a feed item/link (or stored embed URL) that passes the prefix regex but is not a valid URI, e.g. `"http:// bad"` (space) or a multiline value `"javascript:alert(1)\nhttp://example.com"`.
4) Run the code path that processes links (the feed polling/import job that calls `absolutize_urls`).
Expected: invalid URLs are rejected/skipped without killing the job.
Actual: `URI::InvalidURIError` is raised from `URI(url)` and the import/polling job crashes/aborts; multiline input can also bypass the intended scheme validation.

**Found by** 12 cells (12 distinct report texts, 12 findings): fable: CE·low; opus: CE·high, CE·medium, MRV·high, MRV·low; sonnet: CE·high, MRV·high; glm-flash: CE·high, CE·low, van·medium; sol: van·high, van·xhigh

#### B25 — embed.js throws when #discourse-comments container is missing (null appendChild)

**Location:** `app/assets/javascripts/embed.js:5–12`  ·  **Severity:** high  ·  **Judge confidence:** 0.93  ·  ⚠️ `distinct=false` (cluster may span two bugs)

**Why this is real.** The script assigns `var comments = document.getElementById('discourse-comments')` and then unconditionally calls `comments.appendChild(iframe);`. If the host page includes this embed script but does not define an element with id `discourse-comments`, `getElementById` returns null and `appendChild` throws a TypeError, aborting the IIFE before the `message` listener is registered.

**How to replicate.** 1) Include the generated `embed.js` on any HTML page but omit `<div id="discourse-comments"></div>`. 2) Load the page and open the browser console. Expected: the script should no-op or fail gracefully. Actual: it throws (e.g., "Cannot read properties of null (reading 'appendChild')"), and the rest of the embed initialization (including `window.addEventListener('message', ...)`) never runs.

**Found by** 11 cells (15 distinct report texts, 15 findings): fable: van·high; opus: van·high, van·medium, van·xhigh; sonnet: van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, van·xhigh; glm-vis: MRV·medium

#### B26 — Feed polling crashes on Ruby 2.0/1.9 when calling String#scrub on RSS item content

**Location:** `app/jobs/scheduled/pollfeed.rb:30–35`  ·  **Severity:** critical  ·  **Judge confidence:** 0.78

**Why this is real.** The job calls `i.content.scrub` when processing feed items (e.g., reported as `content = CGI.unescapeHTML(i.content.scrub)` around lines 33–35). `String#scrub` is a Ruby core API introduced in Ruby >= 2.1, so on the repository’s supported Ruby 2.0/1.9-era runtimes this raises `NoMethodError: undefined method 'scrub' for "...":String` and aborts the poll. Additionally, many RSS 2.0 feeds provide only `<description>` and `i.content` may be nil, making `i.content.scrub` raise `NoMethodError` even on Rubies that do have `scrub`.

**How to replicate.** 1) Run the app/job under Ruby 2.0 (or 1.9.3) as implied by the project’s era/Gemfile comments. 2) Configure a feed to be polled and trigger the scheduled `PollFeed` job (or run it manually) with any item present. 3) Observe the job crashing at the `i.content.scrub` line with `NoMethodError` (either because `scrub` is missing on Ruby < 2.1, or because `i.content` is nil for feeds without `<content>`), and confirm that no embeds/items are imported for that poll run.

**Found by** 11 cells (11 distinct report texts, 11 findings): fable: CE·low; opus: MRV·high, MRV·low, MRV·medium; sonnet: MRV·medium; glm-flash: van·high; glm-vis: CE·medium, MRV·medium; sol: MRV·high; terra: CE·low, van·low

#### B27 — disqus:import regresses to live HTTP fetch per thread with no error handling (and drops -c category option), causing imports to abort or mis-categorize

**Location:** `lib/tasks/disqus.rake:25–62`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The reports consistently describe that the importer’s main loop was changed to call `TopicEmbed.import_remote(user, t[:link], ...)` inside `parser.threads.each`, performing network I/O (via open-uri) for every thread. Because this call is not wrapped in any `begin/rescue`, a single `OpenURI::HTTPError`, timeout, redirect error, or nil/invalid `t[:link]` will raise and abort the entire import mid-run, leaving a partial import. The same change set also removed the documented `--category/-c` option and category lookup from the task, so existing invocations now fail with an unknown-option error and/or imported topics lose intended category placement; the PR diff for `TopicEmbed.import_remote` is not included here, so this verification relies on the deduplicated reports’ quoted call sites and behavior.

**How to replicate.** 1) Prepare a Disqus export where at least one thread has a dead/unreachable permalink in `link` (e.g., `https://example.invalid/missing`). 2) Run the task in the PR’s post-merge tree (e.g., `bundle exec rake disqus:import[/path/to/export.xml]`). Expected (pre-regression): importer creates topics/posts from the export data without requiring live HTTP, completing the run. Actual (post-regression): the run performs a live fetch per thread; when it hits the dead URL it raises (e.g., `OpenURI::HTTPError`/timeout) and stops, leaving only earlier threads imported. 3) Additionally, run the previously-documented invocation with category (e.g., `bundle exec rake disqus:import[/path/to/export.xml] -c mycat` or equivalent Thor option): expected is successful import into the specified category; actual is an unknown-option failure or topics going to the default category because the option/lookup was removed.

**Found by** 10 cells (20 distinct report texts, 20 findings): glm-flash: CE·high, CE·low, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium

#### B28 — Embed requests are wrongly rejected due to strict/unnormalized Referer host check (and requiring Referer)

**Location:** `app/controllers/embedcontroller.rb:21–27`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The controller enforces embedding access by requiring a Referer and then doing an exact host string compare, e.g. `uri(request.referer || '').host != SiteSetting.embeddable_host` (and/or a preceding `request.referer` presence check). This is a real functional bug because `URI(...).host` is normalized differently than the admin setting (scheme/path/port/case/www variants), so legitimate embeds can be denied with 403 even when coming from the intended site. Additionally, some legitimate browser/referrer-policy situations omit Referer entirely for iframe requests, causing embeds to be rejected even when the request is otherwise valid.

**How to replicate.** 1) In admin settings, set the embeddable host to a value an operator might reasonably enter, e.g. `https://example.com/` or `Example.com` (mixed case), or set it to `example.com:8080` (includes port).
2) Add an embed on a page served from `https://example.com` (or `https://www.example.com` if you set `example.com`) that loads the Discourse embed endpoint in an iframe.
3) Observe: the iframe request returns 403/InvalidAccess (blank embed) because `URI(request.referer).host` yields just `example.com` (no scheme/path/port, typically downcased) and therefore will not equal the unnormalized `embeddable_host` string, or because the Referer header is missing.
4) Expected: legitimate embeds from the configured site should be accepted despite harmless formatting differences (scheme/trailing slash/case/www) and should not hard-fail solely due to Referer stripping by the browser/policy.

**Found by** 10 cells (11 distinct report texts, 11 findings): opus: MRV·low, van·xhigh; glm-flash: CE·medium, MRV·low, van·high, van·low, van·medium; glm-vis: CE·medium, MRV·high, MRV·low

#### B29 — Existing TopicEmbed updates ignore title-only changes, leaving topic titles stale

**Location:** `app/models/topicembed.rb:34–37`  ·  **Severity:** medium  ·  **Judge confidence:** 0.85

**Why this is real.** In the existing-embed update branch (around lines 34–37), the code gates updates on the body checksum (e.g., `if contentsha1 != embed.contentsha1`) and, when it does update, it revises only the post raw via a call like `revisor.revise!(user, absolutizeurls(url, contents), ...)` and then stores the new `contentsha1`. There is no corresponding update of the topic/title field in this path, so when an upstream feed/article title is corrected but the body content remains the same, the condition is false and the title is never propagated. This is a functional defect (stale topic titles after successful re-polls), not a style issue; the PR diff does not include this file, so this verification relies on the reported line references and described code.

**How to replicate.** 1) Import/embed a feed item/article into Discourse so a TopicEmbed/topic is created with title T1 and body B. 2) Change the upstream title to T2 but keep the body exactly B (so the body SHA1 remains unchanged). 3) Trigger the embed refresh/poll that calls TopicEmbed’s update logic for existing records. Expected: the existing Discourse topic title updates to T2. Actual: the topic title remains T1 because the update path only checks `contentsha1` (derived from body) and only revises the post body, never applying the new title.

**Found by** 9 cells (14 distinct report texts, 14 findings): opus: MRV·high, MRV·low, MRV·medium; sol: MRV·high, van·xhigh; terra: MRV·high; astra: MRV·high, MRV·low, MRV·medium

#### B30 — PollFeed job crashes on RSS items without <content> because it calls i.content.scrub without a nil-guard

**Location:** `app/jobs/scheduled/poll_feed.rb:24–52`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** In the per-item loop the job unconditionally dereferences the feed item's content, e.g. `content = i.content.scrub` (or equivalent) before calling `TopicEmbed.import(...)`. For many valid RSS 2.0 feeds, the body is provided as `<description>` (and `i.content` is nil/undefined), so calling `.scrub` raises `NoMethodError` and aborts the entire job run. Because the job is configured with `sidekiq_options retry: false`, the failure is not retried and the same bad item will keep crashing each hourly poll, effectively wedging feed import until the feed changes.

**How to replicate.** 1) Configure Graphite to poll a valid RSS 2.0 feed that has items with `<description>` but no `<content>` / `content:encoded` (common “description-only” feeds). 2) Trigger the scheduled job (wait for hourly run or run the PollFeed job manually in Rails/Sidekiq). 3) Observe the job raising `NoMethodError: undefined method 'scrub' for nil:NilClass` at the `i.content.scrub` line; expected behavior is that the job imports items (using description as fallback) and continues past items even if one is malformed. 4) Verify subsequent hourly polls continue to fail on the same item and no later items are imported.

**Found by** 9 cells (14 distinct report texts, 14 findings): glm-flash: CE·high, CE·low, MRV·low, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium

#### B31 — Embed/topic retrieval synchronously runs full feed poll (Jobs::PollFeed) on cache miss, coupling embeds to feed health and enabling resource exhaustion

**Location:** `lib/topicretriever.rb:44–47`  ·  **Severity:** critical  ·  **Judge confidence:** 0.78

**Why this is real.** In `perform_retrieve`, the code calls `Jobs::PollFeed.new.execute({})` inline (reported at `lib/topicretriever.rb:44-47`). Because this executes the entire feed fetch/parse/import synchronously inside the embed retrieval path, any slow/hanging feed blocks the worker and any exception in `PollFeed` aborts the retrieval before the normal HTTP fetch path runs. This is a functional defect (availability/behavior change) rather than a style issue: embed retrieval becomes dependent on external feed polling success and can be repeatedly triggered by cache-miss requests.

**How to replicate.** 1) In a dev instance, enable the site setting that causes `perform_retrieve` to run feed polling (e.g., `feed_polling_enabled = true`) and set `feed_polling_url` to an unreachable host (or a server that accepts connections but never responds). 2) Trigger an embed retrieval cache miss (e.g., request `/embed/best?url=https://example.com/some/new/path` or whatever endpoint enqueues/executes `TopicRetriever#perform_retrieve` for an unknown URL). 3) Observe that the job blocks or fails while executing `Jobs::PollFeed.new.execute({})`, and the normal per-URL HTTP retrieval does not proceed; subsequent requests for different URLs repeat the whole-feed poll again, tying embed availability/performance to the feed server.

**Found by** 9 cells (11 distinct report texts, 11 findings): opus: van·medium, van·xhigh; glm-flash: MRV·high, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium

#### B32 — TopicEmbed uses open(url) without requiring open-uri, causing URL opens to be treated as local files

**Location:** `app/models/topicembed.rb:46–48`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The reports consistently point to `importremote` calling `open(url).read` (e.g., `Readability::Document.new(open(url).read, ...)`) in `app/models/topicembed.rb` around lines 46–48, but this model file only requires Nokogiri and does not `require 'open-uri'`. In Ruby, `open("http://...")` only gains URL-handling behavior when open-uri is loaded; otherwise `Kernel#open` treats the string as a local path, leading to `Errno::ENOENT` for URLs. This creates a real load-order coupling where it only works if some other file (notably `app/jobs/scheduled/pollfeed.rb`) happened to require `open-uri` first.

**How to replicate.** 1) Ensure `app/jobs/scheduled/pollfeed.rb` (or any other file requiring `open-uri`) is not loaded first (e.g., Rails console in development with lazy autoloading, or run the import task path that loads TopicEmbed directly). 2) Invoke the code path that calls `TopicEmbed#importremote` with an HTTP(S) URL (e.g., via the Disqus import thor task mentioned in the reports, or directly in a console if the method is accessible). 3) Expected: it fetches the remote page content over HTTP and parses it. Actual: Ruby attempts to open a local file literally named like `http://example.com/...` and raises `Errno::ENOENT (No such file or directory)`.

**Found by** 9 cells (9 distinct report texts, 9 findings): fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, van·xhigh; sonnet: MRV·high, MRV·medium

#### B33 — PollFeed job crashes on RSS/summary-only items due to unconditional i.content.scrub call

**Location:** `app/jobs/scheduled/pollfeed.rb:12–37`  ·  **Severity:** critical  ·  **Judge confidence:** 0.72

**Why this is real.** The job unconditionally calls `CGI.unescapeHTML(i.content.scrub)` (reported at `app/jobs/scheduled/pollfeed.rb:35`). For common RSS 2.0 feeds and for items that only have `<description>/<summary>` (no `content`), SimpleRSS exposes `i.content` as `nil`, so `nil.scrub` raises `NoMethodError` and aborts the entire job. The same file reportedly sets `sidekiq_options retry: false` (around line 12), so the crash is not retried and one bad item prevents importing all subsequent items in that poll.

**How to replicate.** 1) Configure the plugin/feature to poll a standard RSS 2.0 feed that lacks an Atom `<content>` element (e.g., many WordPress RSS feeds, or any feed with only `<description>`).
2) Run the scheduled job (or invoke it synchronously) so it processes at least one item without `content`.
Expected: the poll imports items using description/summary or skips malformed items and continues.
Actual: the job raises `NoMethodError` at the `i.content.scrub` line, aborts the batch mid-feed, and because `retry: false` is set it will not retry and will fail again on the next hourly run.

**Found by** 8 cells (13 distinct report texts, 13 findings): glm-flash: CE·high, MRV·high, MRV·low, MRV·medium; glm-vis: CE·low, CE·medium, MRV·low, MRV·medium

#### B34 — Malformed ERB terminator `<%- end if %>` breaks or miscompiles the header conditional

**Location:** `app/views/embed/best.html.erb:6–6`  ·  **Severity:** critical  ·  **Judge confidence:** 0.88

**Why this is real.** The template closes the header conditional with `<%- end if %>` (line 6), which ERB/Erubi compiles into Ruby code containing `end if`. `end if` is not a valid way to close a normal `if/else` in ERB (it should be just `end`), and depending on the ERB compiler’s emitted buffering statements it can either raise a template compilation error (syntax error) or turn the entire preceding `if/else` into a modifier-`if` whose condition becomes the next generated output expression (fragile, accidental behavior). This is a functional correctness bug, not a style issue, because it can break `/embed/best` rendering or change what HTML is emitted.

**How to replicate.** 1) Ensure the view is rendered (not just controller specs): in a Rails console or request spec, render `app/views/embed/best.html.erb` with `@topic_view` set so `@topic_view.posts.present?` is true (the normal success path). 2) Hit the route that uses this template (e.g., GET `/embed/best` for a topic with posts). Expected: the template compiles and returns 200 with the correct header link text plus the logo link. Actual: the template may fail to compile with an `ActionView::Template::Error`/Ruby syntax error due to `end if`, returning 500; or it may compile but bind the `if` condition to the next emitted buffer append, making output ordering/guarding dependent on ERB emission details.

**Found by** 7 cells (16 distinct report texts, 16 findings): opus: CE·high, CE·medium; glm-flash: MRV·high; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium

#### B35 — (untitled)

**Location:** `?` (exact lines not in diff)  ·  **Severity:** ?  ·  **Judge confidence:** 0.00

**Why this is real.** (missing)

**Found by** 7 cells (10 distinct report texts, 10 findings): opus: van·xhigh; glm-flash: CE·high, MRV·high; glm-vis: CE·medium, MRV·high, MRV·medium; sol: van·high

#### B36 — Embed layout references standalone embed assets that are not added to assets.precompile, breaking production

**Location:** `app/views/layouts/embed.html.erb:4–5`  ·  **Severity:** high  ·  **Judge confidence:** 0.80

**Why this is real.** The embed layout includes a new standalone stylesheet bundle via `<%= stylesheet_link_tag 'embed' %>` (reported at embed.html.erb:4-5), but the PR adds `app/assets/stylesheets/embed.css.scss` / `app/assets/javascripts/embed.js` without any corresponding change to `config.assets.precompile`. In Rails 4 + sprockets-rails (typical Discourse setup), only `application.(js|css)` and explicitly precompiled bundles are available when `config.assets.compile = false`, so this reference will raise an `AssetNotPrecompiledError` or produce a missing `/assets/embed-<digest>.css` request in production.

**How to replicate.** 1) In a production-like environment set `config.assets.compile = false` and run `RAILS_ENV=production bundle exec rake assets:precompile`. 2) Boot the app in production mode and request an embed page that uses this layout (e.g., `/embed/best?embed_url=https%3A%2F%2Fexample.com%2Fpost`). 3) Expected: embed page loads with styles and the third-party embed works. Actual: the response errors with an `AssetNotPrecompiled` for `embed.css` (or the browser requests `/assets/embed-<digest>.css` and gets 404), leaving the embedded widget unstyled/broken.

**Found by** 7 cells (7 distinct report texts, 7 findings): opus: MRV·medium; glm-flash: MRV·high, MRV·medium; glm-vis: CE·high, MRV·high, van·high; sol: van·high

#### B37 — Embed topic retrieval can crash or silently no-op when embedbyusername is blank/missing, leaving embeds stuck on infinite “loading”

**Location:** `lib/topicretriever.rb:49–50`  ·  **Severity:** critical  ·  **Judge confidence:** 0.93

**Why this is real.** The reported code at lib/topicretriever.rb:49-50 uses the configured embedding username without validation: `user = user.where(usernamelower: sitesetting.embedbyusername.downcase).first` followed by `return if user.blank?`. If `embedbyusername` is the shipped default empty string (or nil), calling `.downcase` can raise (NoMethodError), causing the job to fail repeatedly; if it does not raise (e.g., empty string), `return if user.blank?` silently exits without importing/creating a topic and without surfacing an error. In both cases, the embed request never transitions out of the loading state, which is functional breakage rather than a style issue. (The file/lines are not in this PR’s diff; this verification relies on the reports’ cited lines.)

**How to replicate.** 1) Configure a site with the default/blank embedding import username (embedbyusername = ''), or set it to a username that does not exist/deleted. 2) Hit an embed endpoint/page that triggers topic retrieval (an embedded discussion for a valid URL). 3) Observe: the embed shows the loading frame/page and keeps reloading/re-enqueuing retrieval. Expected: either a topic is created and the embed loads normally, or a clear configuration/error message is returned/logged. Actual: the job either crashes on `.downcase` (if nil) or returns early on `user.blank?`, so no topic is created and the embed remains stuck on “loading” indefinitely with no actionable error.

**Found by** 7 cells (7 distinct report texts, 7 findings): opus: MRV·medium; sol: CE·low, MRV·high, MRV·low, MRV·medium; terra: MRV·high; astra: MRV·low

#### B38 — Readability import sanitizer preserves javascript: URLs in whitelisted href/src attributes (stored XSS on click)

**Location:** `lib/import_remote/readability.rb:45–92`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** In the readability import sanitization, the tag/attribute allowlist keeps URL-bearing attributes like `a[href]` and `img[src]` but does not restrict allowed URL schemes (e.g., no `protocols`/scheme validation for `href`/`src`). As a result, values such as `href="javascript:alert(1)"` survive unchanged through sanitization. Additionally, the URL “absolutize” logic only rewrites relative paths (e.g., those starting with `/`), so `javascript:` URLs are not touched and remain in the cooked/imported HTML.

**How to replicate.** 1) Host an HTML page containing something like `<article><a href="javascript:alert(document.domain)">click</a></article>`.
2) In Discourse (this plugin/app), use the "import remote" / readability-based import path to import that page into a topic (same path used for embedding/importing remote articles).
3) Inspect the resulting cooked HTML/topic content: the `<a>` tag remains and still has `href="javascript:..."`.
4) Click the link as a normal viewer: expected behavior is that the sanitizer strips or neutralizes the unsafe URL; actual behavior is script execution in the forum origin context upon click (stored XSS vector for anyone viewing imported content).

**Found by** 6 cells (8 distinct report texts, 8 findings): glm-flash: CE·high, CE·low, CE·medium, MRV·high; glm-vis: CE·medium, MRV·high

#### B39 — EmbedController spec expects synchronous TopicRetriever call but controller enqueues async :retrieve_topic job

**Location:** `spec/controllers/embed_controller_spec.rb:44–49`  ·  **Severity:** high  ·  **Judge confidence:** 0.82

**Why this is real.** In the controller spec around lines 44-49, the test sets Mocha expectations like `TopicRetriever.expects(:new)` and `retriever.expects(:retrieve)`, asserting the controller directly instantiates and runs the retriever. But the controller implementation (reported at `app/controllers/embed_controller.rb` around line 15) calls `Jobs.enqueue(:retrieve_topic, ...)` (or `:retrievetopic` per reports) instead of calling `TopicRetriever` synchronously, so the spec’s mocked collaborator is never invoked and the example fails with unsatisfied expectations (or, worse, tests the wrong contract). This is a real behavioral mismatch between test and code, not a style issue.

**How to replicate.** 1) Check `app/controllers/embed_controller.rb` (around line 15) and confirm the action enqueues `Jobs.enqueue(:retrieve_topic, embed_url: ..., user_id: ...)` rather than calling `TopicRetriever.new(...).retrieve`.
2) Open `spec/controllers/embed_controller_spec.rb` lines ~44-49 and confirm it expects `TopicRetriever.expects(:new)` and `retriever.expects(:retrieve)`.
3) Run `bundle exec rspec spec/controllers/embed_controller_spec.rb` with Sidekiq/Jobs not running inline; observe the failing example due to Mocha expectations never being satisfied. Expected (per spec): retriever is called; actual: only a background job is enqueued.

**Found by** 6 cells (6 distinct report texts, 6 findings): opus: van·medium, van·xhigh; glm-flash: CE·low; glm-vis: CE·medium, MRV·low, MRV·medium

#### B40 — Redis throttle key is set before retrieval succeeds, suppressing retries after failures

**Location:** `lib/topicretriever.rb:32–55`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** Per the reports, `retrievedrecently?` writes the 60s throttle marker using `$redis.setnx(...)` followed by `$redis.expire(..., 60)` before `performretrieve` is executed. Because the key is committed before the actual retrieval/import work, any exception or early-return in `performretrieve` leaves the marker in Redis for its full TTL. Subsequent retries within 60 seconds hit `retrievedrecently?` and return without attempting work, so the job can “succeed” while no topic is created and no error is surfaced. (The PR diff for this file isn’t available here; this verification relies on the consistent, matching reports.)

**How to replicate.** 1) Configure/enqueue a retrieval for an embed URL that will reliably fail in `performretrieve` (e.g., a URL that times out, returns 404, or triggers a parsing/readability failure).
2) Run the job once: it will set the Redis throttle key via `setnx+expire`, then raise during `performretrieve`.
3) Immediately retry the same job (or let Sidekiq retry) within 60 seconds.
Expected: the retry should attempt the retrieval again (or at least surface the prior failure).
Actual: the retry returns early due to the existing throttle key and does no work; no topic is created, and the failure is effectively masked until the TTL expires.

**Found by** 5 cells (5 distinct report texts, 5 findings): sonnet: van·low; glm-flash: MRV·high, MRV·low, MRV·medium; glm-vis: MRV·high

#### B41 — Invalid X-Frame-Options value (`allowall`) is ignored by browsers, weakening framing protection

**Location:** `app/controllers/embedcontroller.rb:27–28`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple reports point to `app/controllers/embedcontroller.rb:28` setting `X-Frame-Options` to the literal value `allowall` (e.g., `response.headers["X-Frame-Options"] = "allowall"`). Per the X-Frame-Options spec, only `DENY`, `SAMEORIGIN`, and (legacy) `ALLOW-FROM <uri>` are valid; `allowall` is not and is ignored by modern browsers. This means the application is relying on other checks (e.g., a Referer-based gate) for framing behavior, which is fragile because Referer is not a reliable security control and may be absent or manipulated in some flows.

**How to replicate.** 1) Start the app and hit the embed endpoint handled by `EmbedController` (e.g., the route that renders an embeddable page).
2) Use `curl -i <embed-url>` and observe the response header `X-Frame-Options: allowall`.
3) Create a simple HTML page on another origin that iframes the embed URL; load it in a modern browser.
Expected: the browser should enforce a clear framing policy (block or explicitly allow specific origins).
Actual: because `allowall` is invalid, browsers ignore the header, so framing is not controlled by X-Frame-Options and depends only on other app logic (e.g., referer checks), enabling unexpected cross-origin framing/clickjacking risk.

**Found by** 5 cells (5 distinct report texts, 5 findings): fable: CE·low, van·medium; opus: CE·high, CE·medium, van·xhigh

#### B42 — Embed best view renders imported post HTML as raw, enabling XSS from untrusted imported content

**Location:** `app/views/embed/best.html.erb:18–25`  ·  **Severity:** critical  ·  **Judge confidence:** 0.62

**Why this is real.** In the embed rendering template, the post body is output using Rails' raw helper (e.g., `<%= raw post.cooked %>`), which bypasses HTML escaping. If `post.cooked` can contain attacker-controlled HTML from `TopicEmbed.import`/remote feeds, that HTML will be emitted verbatim in `/embed/best`, enabling script injection. The clustered reports all point to this same mechanism and note there are no specs asserting sanitization/escaping of imported content, so the unsafe branch is not guarded by tests.

**How to replicate.** 1) Configure Discourse embedding for a host you control. 2) On that host, serve an embeddable page whose imported content includes a payload like `<img src=x onerror=alert(1)>` (or `<script>alert(1)</script>` if allowed by the importer). 3) Trigger the embed import (visit the page with the Discourse embed script or run the embed retrieval job), then open `/embed/best?embed_url=<that page URL>` (or the equivalent embed best endpoint for the imported URL). Expected: imported HTML is sanitized/escaped so no JS runs. Actual: because the template renders `post.cooked` via `raw`, the payload is reflected and executes in the embed page context.

**Found by** 5 cells (5 distinct report texts, 5 findings): fable: van·high; opus: van·medium; sonnet: van·low; glm-vis: CE·low, van·low

#### B43 — Unbounded open-uri fetch in PollFeed lacks timeouts/limits and can hang Sidekiq workers

**Location:** `lib/pollfeed.rb:29–30`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** In pollfeed.rb the code performs a remote fetch using open-uri without any explicit timeouts, size limits, or per-item exception handling (as reported at lines ~29-30: `open(SiteSetting.feedpollingurl)` / `open(...).read`). With open-uri defaults, a slow or stalled remote host can block the thread for a very long time and a huge response can be read fully into memory; any network/parse error can bubble up and fail the job. This is a functional reliability bug (worker starvation / potential OOM), not a style issue; the PR diff does not include this file, so verification relies on inspecting the post-PR tree at the referenced lines.

**How to replicate.** 1) Configure `SiteSetting.feedpollingurl` to a URL that accepts a connection but never responds (e.g., a local test server that sleeps indefinitely) OR to a URL that returns a very large body (hundreds of MB). 2) Trigger the feed polling job (run the scheduled job or invoke the code path that calls PollFeed). 3) Observe Sidekiq: expected behavior is the job times out/handles the failure and continues; actual behavior is a worker thread remains stuck in the open/read call for a long time (or memory usage spikes drastically for a large response), potentially starving other jobs and/or crashing due to OOM.

**Found by** 4 cells (7 distinct report texts, 7 findings): glm-flash: CE·high, CE·low; glm-vis: CE·high, van·low

#### B44 — Gemfile updated with new gems but default Gemfile.lock not regenerated, breaking frozen/deployment bundler installs

**Location:** `Gemfile:209–211`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** In the PR, `Gemfile` adds new dependencies around lines 209–211 (e.g., `gem 'ruby-readability'` and `gem 'simple-rss'`). However, per the evidence pack/reports, only `gemfilerails4.lock` was regenerated while the repository’s default `Gemfile.lock` was left unchanged (the PR contains no diff updating `Gemfile.lock`). This creates a real Gemfile/lockfile mismatch: on the default (non-rails4) lockfile path, Bundler detects the lock is out of sync with the Gemfile and aborts in frozen/deployment mode.

**How to replicate.** 1) Check out the PR branch/merge commit.
2) Ensure you are using the default lockfile path (do not point bundler to the rails4 lockfile).
3) Run `bundle install --deployment` (or set `BUNDLE_FROZEN=true` and run `bundle install`, or run `bundle check`).
Expected: Bundler installs using the committed `Gemfile.lock`.
Actual: Bundler errors that `Gemfile.lock` is out of date with `Gemfile` (because `ruby-readability`/`simple-rss` are in `Gemfile` but not reflected in the default lockfile), forcing a lockfile regeneration and breaking CI/deploy flows that require frozen locks.

**Found by** 4 cells (6 distinct report texts, 6 findings): opus: van·medium; glm-flash: MRV·high, MRV·low; glm-vis: MRV·high

#### B45 — Race condition: non-atomic exists?/create! on TopicEmbed causes RecordNotUnique under concurrent imports

**Location:** `lib/topicretriever.rb:36–37`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The code performs a check-then-act sequence on the unique embedurl: it does `topicembed.where(embedurl: embedurl).exists?` (around line 36) and then later does `topicembed.create!(embedurl: embedurl, ...)` (around line 37). Under concurrency, two workers can both observe `exists? == false` and both attempt `create!`; the database unique index on `embedurl` makes one raise `ActiveRecord::RecordNotUnique`, which (per the reports) is not handled, aborting the retrieval/import flow. The PR diff does not include this file, so this verification relies on the reported line references and the known uniqueness constraint behavior.

**How to replicate.** 1) Ensure `topicembeds.embedurl` has a UNIQUE index (as implied by the reports). 2) Pick an `embedurl` not yet present. 3) Trigger two imports for the same `embedurl` concurrently (e.g., run a staff-triggered "retrieve topic" that bypasses throttling at the same time as the hourly `PollFeed` job, or start two retrieve jobs in parallel). 4) Expected: one TopicEmbed is created and the other path no-ops cleanly. Actual: both paths pass the `exists?` precheck, the loser hits the UNIQUE constraint during `create!`, raising `ActiveRecord::RecordNotUnique` and causing the job/request to fail and potentially abandon remaining feed items.

**Found by** 4 cells (5 distinct report texts, 5 findings): opus: CE·high, CE·medium, van·xhigh; sonnet: MRV·high

#### B46 — Incorrect postMessage origin validation uses substring match (bypassable)

**Location:** `app/assets/javascripts/embed.js:17–21`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The embed client’s message handler is reported to gate messages with a substring check: `if (discourseurl.indexOf(e.origin) === -1) { return; }`. This is not an origin equality/allowlist check; any `e.origin` that happens to be a substring/prefix of `discourseurl` will be accepted, and valid origins with minor string differences (e.g., trailing slash/path differences in `discourseurl`) can be rejected. The file isn’t part of this PR’s diff, so this verification relies on the reported line and the known-broken pattern it describes.

**How to replicate.** 1) Configure `discourseurl` to a value like `https://discourse.example.com` (or any forum URL) and include the embed script on a page you control.
2) Serve the embedding page from an origin that is a substring/prefix of `discourseurl` (e.g., `https://discourse.example` if you can control it, or another crafted origin that appears inside the `discourseurl` string).
3) From the embedding page, send a forged message: `window.postMessage({ type: 'discourse-resize', height: 5000 }, '*')` (or to the iframe/window used by the handler, depending on implementation).
Expected: the handler should ignore the message because `e.origin` is not exactly the configured Discourse origin.
Actual: the message passes the substring check and the iframe height changes (collapses/expands), demonstrating origin validation bypass.

**Found by** 4 cells (5 distinct report texts, 5 findings): glm-flash: CE·medium, MRV·low; glm-vis: MRV·high, MRV·low

#### B47 — Embed update path revises only post body; feed title changes never update topic title

**Location:** `UNKNOWN (not provided in reports; affected file not part of PR diff)` (exact lines not in diff)  ·  **Severity:** medium  ·  **Judge confidence:** 0.60

**Why this is real.** All reports agree the update branch accepts/derives a new title but only calls the post revisor with the new raw body (e.g., "PostRevisor.revise! receives newraw and nothing else" / "the title argument is accepted but never written"). That means when an already-imported embed is re-polled and its feed title changes, the code updates only the first post’s raw content, leaving the topic title unchanged forever. This is a functional mismatch: change detection (via content hash) triggers an update, but the update applies only half of the changed fields (body but not title), causing persistent divergence between source and forum.

**How to replicate.** 1) Import an article/feed item as an embed topic with title "Old Title". 2) Change only the source title to "New Title" (keep same URL) and run the embed import/poll again. 3) Observe: the topic’s first post body updates (if content changes) but the topic title in the topic list remains "Old Title". Expected: the Discourse topic title should change to "New Title" when the feed title changes for an existing embed.

**Found by** 4 cells (4 distinct report texts, 4 findings): glm-flash: MRV·medium; glm-vis: MRV·high, MRV·medium; sol: van·high

#### B48 — Embeddable host validation uses strict string equality, rejecting valid hosts with different casing or with a scheme included

**Location:** `lib/topicretriever.rb:14–15`  ·  **Severity:** high  ·  **Judge confidence:** 0.86

**Why this is real.** The host gate is implemented as a direct string comparison (reported as `SiteSetting.embeddablehost != URI(@embedurl).host`). This is a real correctness bug because DNS hostnames are case-insensitive, so `Example.com` and `example.com` should match but won’t with a case-sensitive `!=` check. Additionally, if an admin enters a full URL like `https://example.com` into the setting, it will never equal `URI(@embedurl).host` (which is just `example.com`), effectively rejecting all embeds for that site.

**How to replicate.** 1) Configure the application setting `embeddablehost` to either (a) `Example.com` (different casing) or (b) `https://example.com` (includes scheme). 2) Attempt an embed retrieval using an embed URL like `https://example.com/some/path`. 3) Expected: host validation passes and the topic is retrievable/embeddable. Actual: validation fails because the code compares the raw setting string to `URI(embedurl).host` with strict equality, so it rejects the request.

**Found by** 4 cells (4 distinct report texts, 4 findings): glm-flash: CE·low; sol: CE·high, CE·medium; astra: MRV·medium

#### B49 — Migration backfills posts.cookmethod to rawhtml, causing all existing posts to bypass cooking/sanitization

**Location:** `db/migrate/20131219203905_add_cookmethod_to_posts.rb:3–3`  ·  **Severity:** critical  ·  **Judge confidence:** 0.90

**Why this is real.** The migration reportedly adds the column with `add_column :posts, :cookmethod, :integer, default: 1, null: false` (line 3). In Rails/ActiveRecord, adding a NOT NULL column with a DEFAULT backfills all existing rows to that default, so every historical post gets `cookmethod = 1`. If enum value `1` corresponds to `rawhtml`, the rendering logic will take the raw/unsafe branch and skip the normal cooking + sanitization pipeline, making this a functional and security-impacting defect (the file was not in the PR diff, so this relies on the reports’ cited line).

**How to replicate.** 1) Start with a database containing at least one existing Post whose raw contains Markdown/HTML (e.g., `<script>alert(1)</script>` or `**bold**`). 2) Deploy/apply the migration `20131219203905_add_cookmethod_to_posts`. 3) Query the DB: `SELECT id, cookmethod FROM posts LIMIT 5;` — observe existing rows now have `cookmethod = 1`. 4) Load a topic containing an old post in the UI (or hit the post serializer endpoint). Expected: historical posts remain cooked/sanitized (Markdown converted, unsafe HTML stripped). Actual: posts render using the rawhtml path (raw source returned as trusted cooked HTML), bypassing cooking/sanitization and potentially executing user-supplied HTML/JS.

**Found by** 4 cells (4 distinct report texts, 4 findings): sol: MRV·low, van·low; terra: MRV·medium, van·low

#### B50 — Embed controller caches the temporary “loading” placeholder, causing stale/looping reload behavior

**Location:** `app/controllers/embed_controller.rb:15–30`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The controller reportedly calls `discourse_expires_in 1.minute` unconditionally near the top of the action (e.g., around line 15), before branching between the temporary “loading discussion…” response and the real embedded topic HTML. Because the loading branch includes a self-reload (meta refresh) every ~30 seconds, applying a 1-minute cache header to that placeholder means intermediaries/browsers can keep serving the cached loading page even after the topic becomes available, and can contribute to an indefinite reload loop when the embed lookup never succeeds. This is a functional caching bug (wrong cache semantics for a transient placeholder), not a style issue; the reports all point to the same mechanism in `embed_controller.rb`.

**How to replicate.** 1) Enable/allow embeds and request an embed URL for a topic that does not yet exist (or make the embed lookup fail permanently, e.g., by pointing to a non-existent topic/external URL). 2) Observe the response body is the “loading discussion…” placeholder containing a 30-second auto-reload, and the response headers include a 1-minute cache (`discourse_expires_in 1.minute`). 3) Create/fix the topic shortly after and re-request the same embed URL within that 1-minute window: expected behavior is to start returning the real embedded content immediately; actual behavior is that clients/proxies can continue to receive the cached loading placeholder for up to a minute. If the lookup never succeeds, the iframe continues to reload every 30 seconds indefinitely with no cap.

**Found by** 4 cells (4 distinct report texts, 4 findings): opus: van·high, van·xhigh; sonnet: van·high; glm-flash: CE·medium

#### B51 — (untitled)

**Location:** `?` (exact lines not in diff)  ·  **Severity:** ?  ·  **Judge confidence:** 0.00

**Why this is real.** (missing)

**Found by** 4 cells (4 distinct report texts, 4 findings): fable: van·high; opus: CE·low, MRV·high; sol: van·high

#### B52 — PollFeed specs for missing URL/username are vacuous because feedpollingenabled? is never set true

**Location:** `spec/jobs/pollfeedspec.rb:18–30`  ·  **Severity:** medium  ·  **Judge confidence:** 0.82

**Why this is real.** In the examples around lines 18–30, the spec stubs only the individual setting under test (e.g., `SiteSetting.stubs(:feedpollingurl).returns(nil)` / `SiteSetting.stubs(:embedbyusername).returns(nil)`) but never stubs `SiteSetting.feedpollingenabled?` to `true`. If `execute` is implemented as a guard chain like `return unless feedpollingenabled? && feedpollingurl.present? && embedbyusername.present?`, the default `feedpollingenabled? == false` short-circuits before URL/username are even evaluated, so these tests would still pass even if the URL/username guard checks were deleted. The PR does not modify this file in its diff, so this verification relies on the reported line references and typical Discourse guard logic.

**How to replicate.** 1) Open `spec/jobs/pollfeedspec.rb` and confirm the 'requires feedpollingurl' and 'requires embedbyusername' examples stub only `feedpollingurl` or `embedbyusername` but do not stub `feedpollingenabled?` to true. 2) Confirm `pollfeed` is stubbed/spied such that `execute` is expected not to call it. 3) Temporarily edit the job implementation to remove the URL (or username) presence check from `execute` (leave `feedpollingenabled?` as the only guard). 4) Run the spec suite: the two examples still pass, demonstrating the tests never exercised those guards and are therefore defective.

**Found by** 3 cells (8 distinct report texts, 8 findings): opus: van·medium, van·xhigh; sol: MRV·high

#### B53 — Dead feed-modified cache key means PollFeed always re-downloads and reprocesses the full feed

**Location:** `app/jobs/scheduled/pollfeed.rb:20–22`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72

**Why this is real.** The job computes a cache key (reported around lines 20-22) like `feedkey = "feed-modified:" + Digest::SHA1.hexdigest(...)` but never reads from or writes to it. Because `feedkey` is unused, there is no conditional GET (no If-Modified-Since/ETag) and no early-exit based on cached "last modified" state, so each hourly run necessarily downloads and parses the entire feed again. The PR does not include this file in its diff, so this verification relies on the reported line references and the fact that the computed variable is dead code in the current post-PR tree.

**How to replicate.** 1) Configure the app with a feed URL that rarely changes and enable/run the scheduled PollFeed hourly job. 2) Run the job twice (manually trigger twice or wait two hourly intervals) without changing the upstream feed content. 3) Observe via logs/HTTP proxy that both runs fetch the full feed (200 with full body) rather than using a conditional request (304 Not Modified / If-Modified-Since / ETag) and that the job proceeds to parse/import again. Expected: the second run should skip download/parse when unchanged by using the computed cache key to store/check last-modified/etag; actual: it always re-downloads and re-processes because the cache key is never used.

**Found by** 3 cells (4 distinct report texts, 4 findings): fable: van·high; opus: van·xhigh; sol: van·medium

#### B54 — Disqus importer now live-fetches thread URLs via TopicEmbed, skipping unreachable/non-http threads and losing original created_at/permalink body

**Location:** `lib/tasks/disqus.thor:148–154`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** At the reported location the importer was changed to create the first post via a remote-embed path, e.g. `post = topicembed.importremote(user, t[:link], title: t[:title])`, instead of directly creating a post with the Disqus thread metadata (`raw: "[[permalink](#{t[:link]})]"` and `created_at: Date.parse(t[:createdat])`). This is a functional contract change: `TopicEmbed.import_remote` performs a live HTTP fetch of `t[:link]` (and returns nil for non-http(s) or failed fetches), which means some Disqus threads are silently skipped (and thus their comments never import) and the original thread `created_at` is no longer applied (topics get import-time timestamps). The PR diff for `topicembed.importremote` is not in this PR, so verification relies on reading the post-PR `lib/tasks/disqus.thor` around line 148 and confirming it delegates to `TopicEmbed.import_remote` rather than `PostCreator` with explicit `raw`/`created_at`.

**How to replicate.** 1) Prepare a Disqus export containing at least two threads: (a) one with `link` set to a non-http(s) URL (e.g. `mailto:test@example.com` or a relative/invalid URL) or an http(s) URL that is unreachable from the importer host; (b) one normal reachable http(s) URL. 2) Run the Disqus import task (the Thor task implemented in `lib/tasks/disqus.thor`). 3) Observe results: expected behavior (pre-change) is that both threads are created with a first post containing a permalink markdown body and the topic/post timestamps matching the Disqus `createdAt`. Actual behavior (post-change) is that the unreachable/non-http thread is skipped entirely (no topic, no comments) because `importremote` returns nil, and imported topics use the current import time rather than honoring `t[:createdat]` and no longer include the explicit permalink body.

**Found by** 3 cells (3 distinct report texts, 3 findings): fable: CE·low; opus: CE·medium, MRV·medium

#### B55 — Disqus importer is no longer idempotent: reruns duplicate all replies when TopicEmbed.import_remote returns an existing post

**Location:** `lib/tasks/disqus.thor:148–163`  ·  **Severity:** high  ·  **Judge confidence:** 0.82

**Why this is real.** Post-PR, the importer replaces `PostCreator.new(...).create` with `post = TopicEmbed.import_remote(user, t[:link], title: t[:title])` and then unconditionally appends replies via `t[:posts].each do |p| ...` whenever `post.present?`. `TopicEmbed.import_remote` is designed to return an already-existing embedded topic/post when the same remote URL was imported before, so re-running the task will re-enter the same topic and re-create every Disqus comment again, producing duplicates (no check for already-imported replies, no upsert key, no idempotency guard).

**How to replicate.** 1) Run the Thor task to import a Disqus export containing at least one thread with multiple comments (e.g., `bundle exec thor disqus:import path/to/disqus.xml --post-as someuser`). 2) Run the exact same import command a second time. Expected: the importer should detect the thread/topic and comments are already imported and skip them. Actual: `TopicEmbed.import_remote` returns the existing topic post for the same `t[:link]`, and the following `t[:posts].each` loop re-creates all replies, resulting in a second copy of each Disqus comment under the existing topic. (Variant: include one thread whose `t[:link]` is invalid/unreachable so the first run aborts mid-way; rerunning then duplicates replies for the threads that were already imported before the abort.)

**Found by** 3 cells (3 distinct report texts, 3 findings): opus: CE·high, MRV·high; sol: MRV·high

#### B56 — Topic embed remote import uses open(url) without requiring open-uri, causing ENOENT instead of HTTP fetch

**Location:** `lib/topic_embed.rb:48–52`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The reported code path calls `open(url).read` (topicembed.rb around line 48) to fetch remote HTML, but `topic_embed.rb` only requires Nokogiri (e.g., `require_dependency 'nokogiri'`) and does not `require 'open-uri'`. In Ruby, without open-uri loaded, `Kernel#open` treats a string like `"http://..."` as a local filename, so it raises `Errno::ENOENT` instead of performing an HTTP request. Because topicembed.rb is not part of this PR's diff, this verification relies on the consistent line references and descriptions in the deduplicated reports.

**How to replicate.** 1) Start a fresh Rails/Sidekiq process that loads the app but does not otherwise load open-uri (e.g., run the Disqus/embedding task or `rails console`/`rails runner` in a clean boot). 2) Trigger the embed retrieval/import path (e.g., call `TopicEmbed.import_remote('http://example.com')` or enqueue the retrieve topic job for an embedded URL). 3) Observe that instead of fetching the URL, the process raises `Errno::ENOENT` trying to open a file literally named like the URL; expected behavior is to download the remote HTML and continue embedding.

**Found by** 3 cells (3 distinct report texts, 3 findings): glm-flash: MRV·high, MRV·low; glm-vis: CE·high

#### B57 — TopicEmbed.import assumes embed.post exists and updates content_sha1 even if post revision fails, causing crashes or permanent stale embeds

**Location:** `app/models/topic_embed.rb:31–38`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** In the update/re-import path, the code compares the new hash and then revises the existing post via something like `PostRevisor.new(embed.post, ...)` (reported at app/models/topicembed.rb:31-34). If `embed.post` is nil (e.g., the post was deleted but the TopicEmbed row remains), this will raise (NoMethodError inside PostRevisor init or downstream) and abort the import loop. The same block then unconditionally does `embed.update_column(:content_sha1, ...)` even when the underlying `@post.save(validate: ...)`/revision fails (reported by reviewers), which marks the embed as up-to-date and prevents future retries—this is a functional correctness bug, not a style issue. (The verifying lines are not shown in this PR’s diff; this card relies on the clustered reviewer reports’ cited locations.)

**How to replicate.** 1) Create a TopicEmbed record pointing to an existing post (or let one be created via embedding). 2) Delete the associated post (or otherwise make `topic_embed.post` return nil) without deleting the TopicEmbed row. 3) Trigger the re-import/update path (e.g., run the feed polling job / call the importer for that URL). Expected: importer should either recreate the post/topic or skip/clean up the orphaned embed and continue processing other items. Actual: `PostRevisor.new(nil, ...)` crashes mid-loop, and subsequent feed items are never processed. Separately, induce a revision failure (e.g., make the post invalid for the chosen validation mode) and re-import the same URL; expected: import should not advance `content_sha1` and should retry later. Actual: `content_sha1` is updated even though the revise failed, so subsequent imports see matching sha1 and never attempt to fix the content.

**Found by** 3 cells (3 distinct report texts, 3 findings): fable: van·low; glm-vis: CE·high, CE·medium

#### B58 — Rails migration adds NOT NULL column with DEFAULT, causing full table rewrite and ACCESS EXCLUSIVE lock on PostgreSQL < 11

**Location:** `db/migrate/20131219203905addcookmethodtoposts.rb:3–3`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The migration reportedly contains `add_column :posts, :cookmethod, :integer, default: 1, null: false` (line 3 per the reports). On PostgreSQL versions prior to 11, adding a column with both a non-null DEFAULT and `null: false` forces a full table rewrite and takes an `ACCESS EXCLUSIVE` lock for the duration, blocking reads/writes on `posts`. This is a well-known operational hazard in production on large tables; since this file was not part of the PR diff, this verification relies on the consistent line-referenced reports.

**How to replicate.** 1) Use PostgreSQL 9.6 or 10 (or any < 11) and create a large `posts` table (e.g., millions of rows). 2) Run the migration containing `add_column :posts, :cookmethod, :integer, default: 1, null: false`. 3) In a second session, attempt any `SELECT/UPDATE/INSERT` on `posts` while the migration runs and/or inspect `pg_locks`/`pg_stat_activity`. Expected: schema change should be near-instant and not block normal traffic; Actual: migration holds an ACCESS EXCLUSIVE lock and can take minutes due to table rewrite, blocking application traffic and causing downtime.

**Found by** 2 cells (5 distinct report texts, 5 findings): opus: van·xhigh; sol: van·xhigh

#### B59 — Embed URL column limited to 255 chars causes import/embed jobs to fail for long real-world URLs

**Location:** `db/schema.rb:125–140`  ·  **Severity:** high  ·  **Judge confidence:** 0.60

**Why this is real.** The schema defines the URL field as a bounded string (e.g., `t.string "embedurl"` / `limit: 255`), which maps to `varchar(255)` in Postgres. Real article URLs (especially with long paths or tracking/query parameters) can exceed 255 characters; when such a URL is inserted/updated, Postgres raises `PG::StringDataRightTruncation` and the surrounding import/embedding transaction fails. The PR diff does not include this file, so this verification relies on the reporters' consistent observation that the persisted column is `varchar(255)` while the application accepts unbounded URLs without pre-validation.

**How to replicate.** 1) Create or import an article whose URL is >255 characters (e.g., a normal base URL plus a long query string with UTM/tracking params). 2) Trigger the embedding/import workflow that persists the URL into the `embedurl` column (e.g., run the async job / visit the page that enqueues the embed job). 3) Observe the background job failing with `PG::StringDataRightTruncation` during INSERT/UPDATE. Expected: article imports/embeds successfully; Actual: transaction rolls back, the job fails (often repeatedly re-enqueued), and the UI can remain stuck on a loading state because the record never persists.

**Found by** 2 cells (3 distinct report texts, 3 findings): glm-flash: CE·high; sol: van·high

#### B60 — (untitled)

**Location:** `?` (exact lines not in diff)  ·  **Severity:** ?  ·  **Judge confidence:** 0.00

**Why this is real.** (missing)

**Found by** 2 cells (3 distinct report texts, 3 findings): glm-flash: MRV·low, van·low

#### B61 — Poll feed processing calls `String#scrub` via `stringscrub`, crashing on Ruby 2.0 (requires Ruby >= 2.1)

**Location:** `lib/pollfeed.rb:35–35`  ·  **Severity:** high  ·  **Judge confidence:** 0.70

**Why this is real.** The reports consistently point to `pollfeed.rb:35` invoking `stringscrub`/`scrub` during feed item processing. `String#scrub` is a Ruby 2.1+ API, and the `stringscrub` gem itself requires Ruby >= 2.1, so under the Ruby 2.0 runtime used by Discourse at the time this code would raise `NoMethodError` (or fail to load the gem) even for otherwise valid strings. The PR diff is not available here, so this verification relies on the line reference and the documented Ruby version incompatibility mechanism.

**How to replicate.** 1) Run the app/plugin under Ruby 2.0 with the Gemfile/Gemfile.lock corresponding to this code. 2) Trigger the poll feed job/endpoint that processes feed items (the code path that executes `lib/pollfeed.rb`, line 35). 3) Observe that when a feed item is handled, execution hits the `scrub` call and raises an exception (`NoMethodError: undefined method 'scrub' for String` or a gem load/version error), causing the poll/feed processing to crash instead of returning/recording results.

**Found by** 2 cells (3 distinct report texts, 3 findings): glm-flash: CE·high; glm-vis: CE·medium

#### B62 — Embed source hash includes localized footer, causing false-positive content changes on locale/footer updates

**Location:** `app/models/topicembed.rb:12–16`  ·  **Severity:** medium  ·  **Judge confidence:** 0.64

**Why this is real.** The reported lines indicate the model appends a localized footer (via I18n/site text) to the imported embed content and then computes a SHA1 over that final string (e.g., content is modified with a translated footer and then `Digest::SHA1.hexdigest(...)` is computed). Because the footer text is presentation/locale-dependent rather than part of the upstream source, any change to locale or footer translation changes the hash even when the remote page content is identical, so the code will incorrectly detect a change and create needless post revisions. The PR diff does not include this file, so verification relies on inspecting the post-PR tree at the referenced lines.

**How to replicate.** 1) Configure/enable embedding/import so a remote URL is imported into a Discourse topic using TopicEmbed. 2) Import a URL once, ensuring the topic is created and its stored embed hash reflects the initial import. 3) Change the site locale (or modify the translation string used for the embed footer / the footer text itself) without changing the remote URL content. 4) Re-run the embed import/sync for the same URL. Expected: no update/revision since upstream content is unchanged. Actual: the computed SHA1 differs solely due to the localized footer, so the system thinks the content changed and revises/updates the post(s).

**Found by** 2 cells (2 distinct report texts, 2 findings): opus: van·medium; sol: CE·high

#### B63 — Disqus import passes untrusted thread <link> to importremote/open without URI validation (SSRF/LFI/RCE)

**Location:** `lib/tasks/disqus.thor:148–148`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74

**Why this is real.** At lib/tasks/disqus.thor:148 the task calls `topicembed.importremote(user, t[:link], ...)`, where `t[:link]` comes directly from the imported Disqus XML `<link>` field. The reports indicate `importremote` ultimately uses `open(...)`/`Kernel.open` to fetch the URL and that any `^https?` validation happens only after the fetch, meaning a crafted export can drive an arbitrary fetch (SSRF/LFI) and potentially command execution on some Ruby versions/configs if `open` is invoked on a string starting with `|`.

**How to replicate.** 1) Inspect `lib/tasks/disqus.thor` around line 148 and confirm the Disqus thread link `t[:link]` is passed directly into `topicembed.importremote(...)` without any `URI.parse` + scheme/host allowlist validation. 2) Inspect `TopicEmbed.import_remote` (or similarly named method) and confirm it calls `open(url)`/`Kernel.open(url)` (or `URI.open`) before any `http/https` scheme checks. 3) Create a Disqus export XML where a thread's `<link>` is `file:///etc/passwd` (LFI) or an internal URL like `http://127.0.0.1:3000/admin` (SSRF), then run the Disqus import Thor task as an admin; observe the importer reads/fetches that resource and embeds its content into the created topic (actual), whereas expected behavior is to reject non-http(s) schemes and disallow internal/localhost targets before any fetch. (If `Kernel.open` is used unsafely, also test `<link>|touch /tmp/pwned` to see whether a shell command is executed; expected is that it is rejected as an invalid URL.)

**Found by** 2 cells (2 distinct report texts, 2 findings): opus: MRV·high; sonnet: MRV·high

#### B64 — Migration uses `force: true`, risking silent table drop and data loss on re-run

**Location:** `migrations/createtoptopics.rb:3–3`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74

**Why this is real.** Automated reports consistently flag that `migrations/createtoptopics.rb:3` uses `force: true` on `create_table` (i.e., `create_table ..., force: true do |t|`). In Rails migrations, `force: true` drops an existing table before recreating it, which can silently destroy production data if the migration is re-run (e.g., via `db:migrate:redo`/`rollback`/rebuild workflows). The PR diff for this file is not shown here, so this verification relies on the reported line-level evidence rather than an hunk header.

**How to replicate.** 1) Create a database and run migrations so the `top_topics` table exists and contains rows. 2) Re-run the migration (e.g., `rails db:migrate:redo VERSION=<the createtoptopics migration version>` or rollback then migrate up again). 3) Observe that the table is dropped/recreated due to `force: true`, causing existing rows to be lost; expected behavior is that rerunning should not silently drop data (or should require an explicit `drop_table`/safety mechanism).

**Found by** 2 cells (2 distinct report texts, 2 findings): fable: van·high; glm-flash: CE·low

#### B65 — `skip_validations` allows saving posts/topics with invalid or unsafe data (validations fully bypassed)

**Location:** `lib/post_revisor.rb:85–90`  ·  **Severity:** high  ·  **Judge confidence:** 0.66

**Why this is real.** Around lib/post_revisor.rb:85 the PR introduces a `skip_validations`/`skipvalidations` option that leads to saving a post with ActiveRecord validations disabled (i.e., a `save`/`save!` call with `validate: false` when the flag is set). That means required-field checks (e.g., title presence) and safety checks implemented as validations/callback validations can be bypassed for attacker-influenced imported content. This is not a style issue: it changes persistence semantics so invalid records can be committed (e.g., nil/blank titles when both `opts[:title]` and the imported document title are nil).

**How to replicate.** 1) In Rails console (or the code path used by `importremote`), construct a revise/create call that passes the new option: `skip_validations: true` (or `skipvalidations: true`, per the importer) while providing invalid data (e.g., missing/blank title and/or content that normally fails spam/host/content validations).
2) Ensure both the explicit title option and the imported document's title are nil/blank.
3) Run the import/revise.
Expected: the save is rejected by validations (e.g., title can't be blank, spam/host rules trigger) and the record is not persisted.
Actual: the record is persisted because the save path disables validations when `skip_validations` is true, allowing topics/posts with nil/blank titles or otherwise invalid/unsafe content.

**Found by** 2 cells (2 distinct report texts, 2 findings): opus: CE·high; glm-flash: CE·low

#### B66 — PollFeed job crashes on RSS items without a content field (nil.scrub)

**Location:** `jobs/pollfeed.rb:35–35`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** The job calls `i.content.scrub` (reported at `pollfeed.rb:35`) without guarding for `i.content` being nil, e.g. `CGI.unescapeHTML(i.content.scrub)`. For many valid RSS/Atom feeds, an item may omit a `content` element (using only description/summary), which makes `i.content` nil and causes `NoMethodError: undefined method `scrub' for nil:NilClass`. This is a functional crash path, not a style issue; the reports note the spec stubs the pollfeed pipeline so this path is not exercised by tests.

**How to replicate.** 1) Configure the PollFeed job to fetch a feed where items do not provide a `content` field (common RSS 2.0: only `<description>`). 2) Run the job (or invoke the feed-to-topic pipeline method) against that feed. 3) Observe the job raising `NoMethodError` at the line calling `i.content.scrub`; expected behavior would be to fall back to another field (e.g., description/summary/link) and still import/embed the item into a topic/post.

**Found by** 2 cells (2 distinct report texts, 2 findings): fable: van·high; glm-vis: CE·medium

#### B67 — Stored XSS: Post.cook returns raw HTML unchanged when cook_method=raw_html, bypassing sanitization/filtering

**Location:** `app/models/post.rb:128–136`  ·  **Severity:** critical  ·  **Judge confidence:** 0.88

**Why this is real.** In Post#cook, the new logic explicitly skips the normal cooking/sanitization pipeline: `return raw if cook_method == Post.cook_methods[:raw_html]`. This returns user-controlled HTML verbatim and also bypasses `Plugin::Filter.apply(:after_post_cook, ...)`, which is where downstream filters/sanitizers would normally run. Any code path that sets `cook_method` to `:raw_html` and persists `raw`/`cooked` can therefore store and later render arbitrary HTML/JS (stored XSS).

**How to replicate.** 1) Ensure there is a code path that creates/updates a Post with `cook_method` set to `Post.cook_methods[:raw_html]` (the PR comment mentions RSS/imported posts). 2) Supply `raw` content containing executable HTML/JS, e.g. `<img src=x onerror=alert(document.domain)>` (or `<script>...</script>`). 3) Cause the post to be cooked/saved and then rendered (e.g., view the topic page or any embed template that outputs cooked HTML). Expected: HTML should be sanitized/escaped and JS should not execute. Actual: because `cook` returns `raw` unchanged for `:raw_html`, the payload is stored and executed in the viewer’s browser (stored XSS).

**Found by** 2 cells (2 distinct report texts, 2 findings): fable: van·high; glm-vis: CE·medium

#### B68 — (untitled)

**Location:** `?` (exact lines not in diff)  ·  **Severity:** ?  ·  **Judge confidence:** 0.00

**Why this is real.** (missing)

**Found by** 2 cells (2 distinct report texts, 2 findings): glm-vis: CE·high, MRV·medium

#### B69 — TopicEmbed import uses non-atomic exists?/create! allowing concurrent duplicates and unhandled RecordNotUnique

**Location:** `app/models/topic_embed.rb:21–34`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The import logic is a classic check-then-create race: it first checks something like `TopicEmbed.exists?(embed_url: url)` and then later does `TopicEmbed.create!(embed_url: url, topic_id: topic.id)`. Under concurrency, two workers can both pass the `exists?` check and the loser hits the DB unique constraint, raising `ActiveRecord::RecordNotUnique`. Because the exception is not rescued around `create!`, the job fails after side effects (topic/post creation, enqueued work), producing inconsistent state and the reported stuck/infinite-loading behavior. (The PR diff does not include this file; this verification relies on the line reference and behavior described in the reports.)

**How to replicate.** 1) Ensure the `topic_embeds` table has a unique index on `embed_url` (or equivalent).
2) Trigger two concurrent imports/embeds for the exact same URL (e.g., enqueue the same TopicEmbed import Sidekiq job twice, or hit the endpoint that creates embedded topics twice in parallel).
3) Observe: both workers pass the `exists?` guard, one succeeds, the other raises `ActiveRecord::RecordNotUnique` from `TopicEmbed.create!`.
Expected: the second import should be idempotent (find-or-create) and not fail; Actual: one job fails with an uncaught exception, potentially leaving the UI waiting (infinite loading) or leaving partially-created records/queued jobs.

**Found by** 2 cells (2 distinct report texts, 2 findings): fable: van·high; glm-flash: CE·low

#### B70 — Disqus importer drops original topic/OP created_at by switching to TopicEmbed.import_remote without forwarding created_at

**Location:** `script/import_scripts/disqus.rb:118–132`  ·  **Severity:** critical  ·  **Judge confidence:** 0.66

**Why this is real.** Per the reports, the PR rewrites the Disqus thread import from `PostCreator.new(..., created_at: Date.parse(t[:createdAt]), category: category_id)` to `TopicEmbed.import_remote(user, t[:link], title: t[:title])`. `TopicEmbed.import_remote` (and the underlying TopicEmbed import path) does not accept/forward `created_at`, so the created time of the imported OP/topic will default to the import run time. This creates a real data-integrity bug in migrations: topics appear “new” and can even end up with an OP dated after its replies (which still use the original Disqus timestamps).

**How to replicate.** 1) Prepare a Disqus export where a thread has `createdAt` far in the past and at least one reply with its own old `createdAt`.
2) Run the Disqus import task in this repo (the code path calling `TopicEmbed.import_remote(user, t[:link], title: t[:title])`).
3) In the resulting Discourse instance, inspect the imported topic: the topic/first post timestamp will match the import run time ("now"), while imported replies retain the original Disqus timestamps.
Expected: the topic/OP created_at matches the Disqus thread createdAt and sorts correctly chronologically; Actual: topic/OP is timestamped at import time and can sort as brand-new, with replies appearing older than the OP.

**Found by** 1 cells (2 distinct report texts, 2 findings): glm-vis: MRV·medium

#### B71 — poll_feed job processes unbounded RSS items, creating/enqueuing work for every entry in a single run

**Location:** `app/jobs/regular/poll_feed.rb:18–56`  ·  **Severity:** high  ·  **Judge confidence:** 0.64

**Why this is real.** The poller fetches the remote feed and then iterates every entry without any limit, e.g. `rss = Feedjira.parse(URI.open(url).read)` followed by `rss.items.each do |item|` (or `rss.entries.each`) and then invokes `PostCreator`/enqueues per-item processing inside that loop. Because there is no cap (no `take(n)`, no `break` after N items, no pagination/backoff), a feed with thousands of items will be fully processed in one job execution, leading to multi-hour job runtime and flooding Sidekiq with thousands of enqueued post/topic jobs. The PR diff referenced in the prompt does not include this file/hunk, so this verification relies on the reported code path description; a human can confirm by locating the unbounded `each` over `rss.items` in `poll_feed.rb` and observing there is no bounding logic anywhere on that path.

**How to replicate.** 1) Point the plugin/site setting that defines the polled RSS feed URL to a test RSS feed containing thousands of `<item>` entries (or a real feed with a very large history). 2) Run the poll job manually (e.g., from Rails console `Jobs.enqueue(:poll_feed, ...)` or by triggering the scheduled job) and watch the Sidekiq dashboard/logs. Expected: poller should process a bounded number of new items per run (and/or defer the rest). Actual: the job iterates the entire `rss.items` collection, creates topics/posts for each, and enqueues per-post processing jobs for all entries in one poll, causing excessive runtime and a surge in queued jobs/topics.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·high

#### B72 — (untitled)

**Location:** `?` (exact lines not in diff)  ·  **Severity:** ?  ·  **Judge confidence:** 0.00

**Why this is real.** (missing)

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·medium

#### B73 — ERB syntax error: invalid `end if` terminator breaks embed best template rendering

**Location:** `app/views/embed/best.html.erb:6–6`  ·  **Severity:** high  ·  **Judge confidence:** 0.86

**Why this is real.** The template closes an ERB `if` block with `<%- end if %>` (line 6). In ERB/Ruby, `end if` is not valid syntax for closing a block; the correct terminator is just `end`. When this template is rendered, Rails will attempt to compile it and raise an `ActionView::SyntaxError`, causing the embed page to fail at runtime.

**How to replicate.** 1) Run the app with this PR applied. 2) Hit the route/action that renders `embed/best` (e.g., request the embed "best" view in a browser). Expected: the embed page renders with a header and posts list. Actual: the request errors during template compilation with an ERB/Ruby syntax error pointing at the line `<%- end if %>`.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·high

#### B74 — Migration uses `force: true` on `create_table`, risking silent drop/recreate of `topic_embeds` data on re-run

**Location:** `db/migrate/20240101000000_create_topic_embeds.rb:5–12`  ·  **Severity:** critical  ·  **Judge confidence:** 0.55

**Why this is real.** The migration defines the table with `create_table :topic_embeds, force: true do |t|` (exact filename/lines may vary; this migration is not shown in the PR diff, so verification is by searching the post-PR tree). In Rails migrations, `force: true` translates to a `DROP TABLE IF EXISTS` before creating the table, which will delete all existing rows if the migration is ever re-run (e.g., via `db:migrate:redo`, a mistaken rollback/forward, or an environment restore that re-applies migrations). That makes the embed URL → topic mapping destructible and can cause downstream logic (e.g., `TopicEmbed.topic_id_for_embed`) to return nil for known URLs after the drop.

**How to replicate.** 1) In a DB with production-like data, insert at least one mapping row into `topic_embeds` for a known `embed_url` pointing to an existing topic. 2) Re-run the migration that contains `create_table :topic_embeds, force: true` (e.g., `rails db:migrate:redo VERSION=<that_migration_version>` or manually invoke the migration `down` then `up`). 3) Observe that the table is dropped/recreated and all rows are lost; querying by the known `embed_url` returns no row. 4) Trigger the embed retrieval/import flow for that URL: expected behavior is it reuses the existing topic; actual behavior is the lookup returns nil and the system creates a duplicate topic because the mapping was destroyed.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·high

#### B75 — Topic embed import crashes when Readability returns nil content

**Location:** `lib/topic_embed/importer.rb:41–74`  ·  **Severity:** high  ·  **Judge confidence:** 0.66

**Why this is real.** In `import_remote`, the code passes Readability output directly into the importer: `import(url, doc.content, opts)`. In `import`, the first mutation assumes a String: `contents << ...` (e.g., appending extra text/metadata). When `Readability::Document` fails to extract an article (common for non-HTML URLs, empty bodies, or pages with no readable content), `doc.content` can be `nil`, causing `NoMethodError: undefined method '<<' for nil:NilClass` and the embed import job to fail repeatedly. (This file is not part of the PR diff, so this verification relies on the reported code behavior/path.)

**How to replicate.** 1) Configure an embed URL for a page that yields no readable article (e.g., a PDF/non-HTML URL, or an HTML page with an empty body). 2) Trigger the embed import (e.g., by requesting the embed iframe or enqueueing the retrieve/import job for that URL). 3) Observe the background job error `undefined method '<<' for nil:NilClass` originating from `import` when it executes `contents << ...`. Expected: importer gracefully handles missing content (skips import or uses fallback). Actual: job fails on every retry, no TopicEmbed/topic is created, and the embed iframe stays stuck on “loading discussion…” with periodic reloads.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·high

#### B76 — Migrations add posts.cookmethod and topic_embeds table but schema dump is not regenerated (schema drift)

**Location:** `db/schema.rb:1–1`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The reports indicate this PR introduces a migration adding a `posts.cookmethod` column and creating a `topic_embeds` table, but the diff contains no corresponding update to the tracked schema dump (`db/schema.rb` or `db/structure.sql`). That is a functional defect because environments that build the database from the committed schema dump (e.g., `db:schema:load`, `db:reset`, CI test DB setup) will not have the new column/table even though application code (e.g., post cooking logic) expects `cookmethod` to exist, leading to runtime errors or incorrect behavior. This is an omission bug (missing file update), so there are no “offending lines” in the diff to quote beyond the absence of the schema changes.

**How to replicate.** 1) Checkout the PR branch/commit. 2) Create a fresh database using the schema dump instead of migrations (e.g., `RAILS_ENV=test bundle exec rake db:drop db:create db:schema:load` or `bundle exec rake db:reset`). 3) Boot the app or run a code path that cooks a post (or run a spec that triggers post cooking). Expected: cooking succeeds and TopicEmbed-related queries work. Actual: errors such as missing column `posts.cookmethod` and/or missing table `topic_embeds` (e.g., `ActiveRecord::StatementInvalid: PG::UndefinedColumn` / `PG::UndefinedTable`) because the schema dump lacked the PR’s migration changes.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·medium

#### B77 — EmbedController enqueues RetrieveTopic job but spec expects synchronous TopicRetriever call

**Location:** `app/controllers/embedcontroller.rb:16–16`  ·  **Severity:** medium  ·  **Judge confidence:** 0.78

**Why this is real.** The controller code (per the report) enqueues an async job at `app/controllers/embedcontroller.rb:16` (e.g., a `Jobs::RetrieveTopic` enqueue), meaning topic retrieval happens later/out-of-band. However, the controller spec (reported at `spec/controllers/embedcontrollerspec.rb:43`) asserts `TopicRetriever.new` is invoked synchronously during the request, which cannot be true if the controller only enqueues a job. This is a real contract mismatch between shipped behavior and the test, so the test does not (and cannot) validate the actual behavior the controller implements.

**How to replicate.** 1) Open `app/controllers/embedcontroller.rb` around line 16 and confirm the action enqueues `Jobs::RetrieveTopic` (or equivalent) instead of directly calling `TopicRetriever.new`/`TopicRetriever#retrieve`. 2) Open `spec/controllers/embedcontrollerspec.rb` around line 43 and confirm it expects `TopicRetriever.new` to be called during the controller action. 3) Run the controller spec: expected (per test) is an immediate `TopicRetriever.new` call; actual (per controller) is only a job enqueue, so either the spec fails or it passes only because of incorrect stubbing, meaning it doesn't assert the real behavior.

**Found by** 1 cells (1 distinct report texts, 1 findings): opus: MRV·low

#### B78 — RetrieveTopic job unnecessarily eager-loads mail stack via stray require_dependency

**Location:** `app/jobs/regular/retrievetopic.rb:1–1`  ·  **Severity:** low  ·  **Judge confidence:** 0.60

**Why this is real.** The report indicates the file begins with an unrelated `require_dependency 'email/sender'` at line 1. This is a genuine defect because it forces the job worker to load the email delivery subsystem even though RetrieveTopic should not depend on sending email, increasing boot time/memory and potentially triggering mail-specific initialization/side effects. The PR does not modify this file, so verification must be done by directly opening the post-PR code and confirming that this require is present and unused.

**How to replicate.** 1) Open `app/jobs/regular/retrievetopic.rb` on the PR branch and confirm it contains `require_dependency 'email/sender'` at the top.
2) Search within the same file for any references to `Email::Sender` (or other constants from `email/sender`)—expected: none.
3) Run the job worker (or Rails runner to execute the job) with minimal config and enable load/require tracing (e.g., instrument `ActiveSupport::Dependencies` or use `RUBYOPT='--enable-frozen-string-literal'` plus logging) to observe that `email/sender` (and its transitive mail stack) gets loaded when `RetrieveTopic` is loaded—expected: it should not be loaded for this job; actual: it is loaded due to the top-level require.

**Found by** 1 cells (1 distinct report texts, 1 findings): opus: van·xhigh

#### B79 — `require_dependency 'nokogiri'` can raise `LoadError` in Rails development due to `:load` dependency mechanism

**Location:** `app/models/topicembed.rb:1–1`  ·  **Severity:** high  ·  **Judge confidence:** 0.76

**Why this is real.** The file begins with `require_dependency 'nokogiri'` (reported at `app/models/topicembed.rb:1`). In Rails development (`cache_classes=false`), `ActiveSupport::Dependencies` may use `mechanism = :load`, causing `require_dependency` to ultimately call `Kernel#load` rather than `require`; `load` does not resolve extension-less feature names the way `require` does (and will not properly load native extensions like Nokogiri), leading to `LoadError` and preventing the `TopicEmbed` model from being loaded at all. This is a functional runtime failure, not a style issue; the PR diff does not include this file, so verification is based on the reported code location/behavior.

**How to replicate.** 1) Run the app in Rails development mode with `config.cache_classes = false` (default in development). 2) Ensure Nokogiri is present in the bundle (Gemfile includes `nokogiri`). 3) Boot the app (or open a Rails console) and trigger autoload of `TopicEmbed` (e.g., reference `TopicEmbed` or hit any request path that loads the model). Expected: the model loads normally. Actual: Rails raises `LoadError` for `nokogiri` while loading `app/models/topicembed.rb`, breaking boot/autoload in development.

**Found by** 1 cells (1 distinct report texts, 1 findings): sonnet: MRV·high

#### B80 — TopicEmbed stores redundant topic_id that can go stale when an embedded post is moved to another topic

**Location:** `app/models/topicembed.rb:25–35`  ·  **Severity:** medium  ·  **Judge confidence:** 0.55

**Why this is real.** The model persists both a `topic_id` and a `post_id` for the same embed record even though `topic_id` is derivable from `post.topic_id`. Because controller-side lookups/updates are reported to use only `topic_id` (not `post_id`), if Discourse moves the post to a different topic, `topicembed.topic_id` can remain pointing to the original topic while the `post_id` now belongs to a different topic. This creates a real data-integrity bug: the embed record can reference the wrong topic and subsequent operations can target inconsistent resources. (This file is not part of the PR diff, so this verification relies on the reported code behavior and the referenced line location.)

**How to replicate.** 1) Create an embedded post that results in a `TopicEmbed` row with both `post_id` and `topic_id` populated. 2) Use Discourse’s post-moving feature to move that post to a different topic (so `posts.topic_id` changes). 3) Trigger whatever controller action updates/reads the embed (the report indicates it identifies the embed by `topic_id` only). Expected: the embed follows the moved post/new topic consistently. Actual: the embed lookup/update still uses the stale `topic_id`, so it continues to associate with the old topic while the referenced post now belongs to the new topic, causing incorrect embed behavior.

**Found by** 1 cells (1 distinct report texts, 1 findings): opus: MRV·high

#### B81 — Embedded iframe height is posted only on load, causing clipped content after resize/wrap

**Location:** `app/views/layouts/embed.html.erb:8–16`  ·  **Severity:** high  ·  **Judge confidence:** 1.00

**Why this is real.** The embed layout sets a one-shot handler like `window.onload = function() { ... parent.postMessage(... height ...) ... }`, which only reports the iframe height a single time at load. When the host page is resized (or fonts/images load later) the embedded discussion height can increase due to text reflow, but no further height messages are sent; combined with the typical `scrolling="no"` iframe usage, the additional content becomes inaccessible. The file is not part of this PR’s diff, so this verification relies on the reported code location/behavior.

**How to replicate.** 1) Load a Discourse embed page (using this layout) inside a host page `<iframe ... scrolling="no">` that listens for the posted height and sets the iframe’s CSS height. 2) Ensure the embed contains enough text/comments to wrap differently. 3) After the iframe finishes loading, narrow the host page/iframe width (e.g., resize the browser window or change a responsive container width). Expected: the iframe height updates to fit the newly wrapped/taller content. Actual: the iframe height stays fixed (only set on initial load) and the bottom of the discussion is clipped with no scrolling available.

**Found by** 1 cells (1 distinct report texts, 1 findings): astra: MRV·high

#### B82 — New /embed/best route is unnamed and unconstrained, so it has no URL helper and accepts unintended formats

**Location:** `config/routes.rb:245–245`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The PR adds `get 'embed/best' => 'embed#best'` with no `as:` option and no format constraint/defaults. In Rails, omitting `as:` means no named route helper (e.g., `embed_best_path`) will be generated, which can cause runtime errors anywhere the app tries to build this URL via helpers. Omitting a format constraint/default (e.g., JSON-only) also means the same action will be routed for HTML requests (`/embed/best`) as well as `/embed/best.json`, which is incorrect if `embed#best` is intended to be JSON-only or to have a separate HTML route.

**How to replicate.** 1) After applying the PR, run `bin/rails routes | grep -n "embed/best"` and observe the route exists but has no named prefix (no helper name shown). 2) In a Rails console (or any view/controller), attempt to call `embed_best_path` (or `embed_best_url`); expected: helper exists for the new endpoint; actual: `NoMethodError` because the route is unnamed. 3) Send requests to both `/embed/best` and `/embed/best.json`; expected (for a JSON-only embed endpoint): `/embed/best` should not match or should be rejected/404, while `/embed/best.json` should be the only accepted format; actual: both route to `embed#best` because the route has no format constraint.

**Found by** 1 cells (1 distinct report texts, 1 findings): opus: CE·medium

#### B83 — Embed URL is constructed by naive string concatenation, breaking when discourseUrl lacks a trailing slash

**Location:** `N/A (not referenced in the deduplicated reports; not modified in PR #4 diff)` (exact lines not in diff)  ·  **Severity:** medium  ·  **Judge confidence:** 0.58

**Why this is real.** The clustered reports indicate the code builds the request URL by concatenating a configured `discourseUrl` with a relative path like `"embed/best?..."`. If `discourseUrl` does not end with `/`, the resulting string becomes `https://forum.example.comembed/best?...`, which is an invalid endpoint and fails silently unless the host page (or configuration) happens to include a trailing slash. This is a functional correctness bug (bad URL construction), not a style issue; however, the exact offending lines cannot be quoted because the reports include no file/line references and the PR diff does not touch the relevant code.

**How to replicate.** 1) Find where the embed URL is formed (search the repo for `embed/best` or for concatenation with `discourseUrl`). 2) Configure/set `discourseUrl` to a value without a trailing slash (e.g., `https://discourse.example.com`). 3) Trigger whatever code path loads the embed/best content. Expected: request goes to `https://discourse.example.com/embed/best?...`. Actual: request URL becomes `https://discourse.example.comembed/best?...` (or otherwise malformed), causing 404/network failure and a broken embed unless `discourseUrl` ends with `/`.

**Found by** 1 cells (1 distinct report texts, 1 findings): opus: van·high

#### B84 — Missing presence check before calling `downcase` on `SiteSetting.embed_by_username` can raise NoMethodError

**Location:** `lib/discourse_graphite/topic_retriever.rb:17–17`  ·  **Severity:** medium  ·  **Judge confidence:** 0.58

**Why this is real.** The same lookup logic is duplicated in multiple places, but with different guards. In `pollfeed.rb` the report indicates it is guarded (e.g., checking `SiteSetting.embed_by_username.present?` before doing `SiteSetting.embed_by_username.downcase`), while `topic_retriever.rb` reportedly calls `SiteSetting.embed_by_username.downcase` directly inside `User.where(usernamelower: SiteSetting.embed_by_username.downcase).first`. If the setting is blank/nil, the unguarded `.downcase` will crash at runtime with `NoMethodError`, making this a functional bug (not just style/duplication).

**How to replicate.** 1) In the running app/plugin environment, ensure `SiteSetting.embed_by_username` is unset or set to an empty value. 2) Trigger the code path that uses `TopicRetriever` (the code that fetches/embeds content and performs `User.where(usernamelower: SiteSetting.embed_by_username.downcase).first`). 3) Expected: it should safely behave as “no embed user configured” and proceed without error. Actual: it raises `NoMethodError: undefined method 'downcase' for nil:NilClass` (or for an empty non-string value), because `.downcase` is called without a presence check.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: CE·medium

#### B85 — embed/best.html.erb can call @topicview.topic when @topicview is nil due to malformed conditional/end modifier

**Location:** `app/views/embed/best.html.erb:1–20`  ·  **Severity:** high  ·  **Judge confidence:** 0.58

**Why this is real.** The reported template uses an unusual/malformed conditional closure (`<%- end if %>`) around branches that both reference `@topicview.topic`. If `@topicview` is ever nil, any line like `@topicview.topic` will raise `NoMethodError` (`undefined method `topic' for nil:NilClass`) at render time. The report indicates this file was not modified in the PR diff, so verification must be done by directly inspecting `app/views/embed/best.html.erb` in the post-PR tree for the `end if` and `@topicview.topic` usage.

**How to replicate.** 1) Open `app/views/embed/best.html.erb` and locate the conditional that ends with `<%- end if %>` and the link(s) that use `@topicview.topic`.
2) Identify a controller/action rendering this template where `@topicview` can be unset (e.g., an embed endpoint hit with a missing/invalid topic id or a path that skips assigning `@topicview`).
3) Request that endpoint in a browser or via curl with inputs that lead to `@topicview == nil`.
Expected: template still renders (or shows a graceful message). Actual: template render crashes with `undefined method 'topic' for nil:NilClass` (or fails due to the malformed conditional structure).

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: CE·low

#### B86 — embedurl param not type-checked allows non-String, causing unrescued TypeError in URI parsing and Sidekiq retry churn

**Location:** `app/controllers/embed_controller.rb:9–16`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The controller reads the URL via something equivalent to `@embedurl = params.require(:embedurl)` (per the report’s embedcontroller.rb:9-16). In Rails, `require` enforces presence but not type, so a request like `?embedurl[]=x` yields an Array/Hash instead of a String; later code passes this value into URI parsing in TopicRetriever, where `URI(@embedurl)` (topicretriever.rb:15-18) raises `TypeError` for non-String inputs. The rescue only catches `URI::InvalidURIError`, so this TypeError escapes and crashes the enqueued job, leading to repeated Sidekiq retries/job churn. (embed_controller.rb is not in this PR’s diff; this verification relies on the reported line ranges and the described control/data flow.)

**How to replicate.** 1) Find the controller action in app/controllers/embed_controller.rb around lines 9-16 that does `params.require(:embedurl)` and enqueues a background job (directly or indirectly) using that value. 2) Find TopicRetriever (topicretriever.rb around lines 15-18) calling `URI(@embedurl)` inside a `rescue URI::InvalidURIError`. 3) Trigger the endpoint anonymously with a non-scalar embedurl, e.g. `GET /<embed-endpoint>?embedurl[]=http://example.com` (or send JSON with `embedurl: []`/`{}`), and observe: expected behavior is a 4xx validation error without enqueuing; actual behavior is the job is enqueued, then fails with `TypeError` (not caught by the rescue) and is retried by Sidekiq repeatedly (visible in Sidekiq/rails logs).

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: CE·medium

#### B87 — Embed iframe resize postMessage uses request.referer as targetOrigin, breaking when Referer is missing/invalid

**Location:** `layouts/embed.html.erb:11–11`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72

**Why this is real.** The embed layout sends a postMessage to the parent using the HTTP referrer as the target origin (e.g., `window.parent.postMessage(..., '<%= request.referer %>')` around line 11). `postMessage` requires `targetOrigin` to be either `'*'` or a valid origin string (scheme + host + optional port), but `request.referer` is often nil/empty (suppressed by Referrer-Policy, privacy settings, cross-origin rules) and when present typically includes a full URL with path/query, which is not a valid origin. As a result, the browser will throw/ignore the message, silently breaking the iframe auto-resize behavior.

**How to replicate.** 1) Serve any page that embeds the Discourse `embed` page in an `<iframe>`, and set `Referrer-Policy: no-referrer` (or use a browser/privacy setting that strips the Referer header). 2) Load the host page so the iframe loads `/embed`. 3) Observe in devtools that the iframe does not auto-resize (and/or a console error like a DOMException for invalid postMessage target origin); expected behavior is that the embedded content posts its height to the parent, which then resizes the iframe.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: CE·low

#### B88 — Invalid or wrong-host embed URLs are treated as successful retrieval, causing infinite loading loop

**Location:** `lib/topicretriever.rb:9–9`  ·  **Severity:** high  ·  **Judge confidence:** 1.00

**Why this is real.** At lib/topicretriever.rb:9 the control flow is reported as `performretrieve unless (invalidhost? || retrievedrecently?)`. This means that when `invalidhost?` is true (malformed/wrong-host URL), the method skips `performretrieve` and can still return as if background work completed, rather than surfacing a 4xx/invalid-input result. The result is a real behavioral defect: the controller/view that polls for completion never receives an error state, so it keeps reloading indefinitely. (This file is not part of the PR diff, so verification relies on inspecting the referenced line in the post-PR tree.)

**How to replicate.** 1) In the UI or API endpoint that triggers topic retrieval via an embed URL, submit an embed URL with an unsupported host or malformed URL (so `invalidhost?` would be true). 2) Observe the subsequent "loading"/polling behavior (page reloads or repeated status checks). Expected: request should fail with a 4xx (invalid input / unsupported host) and stop polling. Actual: the system appears to accept the job but never progresses (keeps reloading/polling forever) because no retrieval is performed and no error is returned.

**Found by** 1 cells (1 distinct report texts, 1 findings): sol: MRV·high

#### B89 — OpenURI follows redirects, bypassing host allowlist when fetching embedded topic HTML

**Location:** `lib/topicembed.rb:48–52`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** The code reportedly fetches remote HTML with `open(url)` (e.g., `html = open(url).read`) at topicembed.rb:48. Ruby's OpenURI follows HTTP 3xx redirects by default, so even if TopicRetriever/TopicEmbed performs a host check on the *original* `url`, the actual content fetched can come from a different host after a redirect. This makes the host/embeddable-domain constraint ineffective and allows an embeddable site with an open redirect to supply attacker-controlled HTML to the importer (amplifying downstream XSS/URL-injection issues).

**How to replicate.** 1) Find the code path where an embed request provides a URL that is validated against an allowed host/domain before calling `open(url)` in lib/topicembed.rb (~line 48). 2) Configure an allowed/embeddable host A that returns `302 Location: https://attacker.example/payload.html` for a chosen path. 3) Trigger the embed/import for `https://A.example/redirect` (whatever controller/job calls TopicEmbed/TopicRetriever). Expected: fetch is constrained to A.example only; Actual: OpenURI follows the redirect and fetches attacker.example content, which is then parsed/imported as if it came from A.example.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: CE·medium

#### B90 — Feed item URL fallback uses entry.id (often not a URL), causing items to be silently skipped

**Location:** `pollfeed.rb:1–1`  ·  **Severity:** medium  ·  **Judge confidence:** 0.50

**Why this is real.** The deduplicated report indicates `pollfeed.rb` "falls back to i.id" when a feed entry has no URL. In many feed formats, `id` is a GUID/opaque identifier (e.g., `tag:example.com,2024:post-123`), not an HTTP(S) URL; if downstream code assumes a real URL (for normalization, fetching, or deduping), this fallback makes valid entries appear invalid and they get skipped. The report also notes there is no logging on the skip path, making the failure silent; this is a behavioral defect (missed content) rather than a style nit. (The PR diff does not include this file, so this verification relies on the report and must be confirmed by locating the `url = i.url || i.id`-style line in `pollfeed.rb` in the post-PR tree.)

**How to replicate.** 1) In `pollfeed.rb`, find the code path that derives an entry URL (commonly something like `url = entry.url || entry.id`). 2) Provide a feed where an item has no `<link>`/URL but does have an `<id>` that is not an http(s) URL (e.g., an Atom `<id>tag:example.com,2024:abc</id>`). 3) Run the poller against that feed. Expected: the item is processed (or at least a warning is logged that it cannot be processed due to missing URL). Actual: the item is skipped/dropped because the derived "url" is not a valid URL, and there is no log message explaining the drop.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: CE·low

#### B91 — Embed endpoint trusts spoofable Referer/embedurl and uses Referer as postMessage targetOrigin

**Location:** `app/controllers/embedcontroller.rb:28–28`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** The embed implementation relies on `request.referer` (a client-controlled header) and the client-supplied `embedurl` to decide what origin is allowed. As reported (this file is not part of the PR diff, so verification is by reading the current tree), the referer check at/around line 28 is effectively a weak host equality check and can be bypassed via crafted Referer/embedurl values (e.g., case/format variations), letting an attacker-origin pass validation. The corresponding view then uses the Referer-derived value as the `postMessage` targetOrigin, so a spoofed Referer can cause messages intended for a legitimate parent to be sent to an attacker-controlled origin.

**How to replicate.** 1) Inspect `app/controllers/embedcontroller.rb` around line 28 and confirm it compares/derives the allowed origin from `request.referer` and/or `params[:embedurl]` without strict, normalized origin parsing and verification.
2) Inspect `app/views/layouts/embed.html.erb` around line 9 and confirm it does `window.parent.postMessage(..., <%= request.referer %>)` (or equivalent), using the Referer as targetOrigin.
3) Run the app locally and request the embed endpoint (e.g., `/embed`) while setting a forged `Referer: https://attacker.example/` header and an `embedurl` parameter that passes the controller check.
Expected: the embed response should refuse/deny or only postMessage to the canonical, verified origin.
Actual: the endpoint renders and the embedded page posts messages with targetOrigin derived from the spoofed Referer, enabling redirecting/embed messaging to attacker origins.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: CE·low

#### B92 — Unused `require_dependency 'email/sender'` in retrieve_topic script

**Location:** `script/retrieve_topic.rb:1–5`  ·  **Severity:** low  ·  **Judge confidence:** 0.60

**Why this is real.** The file reportedly contains a top-level load like `require_dependency 'email/sender'`, but the rest of `script/retrieve_topic.rb` does not reference `Email::Sender` (or any symbol defined by that file). This is not just style: an unnecessary `require_dependency` can introduce unwanted side effects during load, slow execution, and (most importantly) cause a `LoadError` if that dependency is removed/renamed even though the script does not actually need it. The PR diff for this file is not available here, so this verification relies on the report and can be confirmed by inspecting the post-PR file contents.

**How to replicate.** 1) Open `script/retrieve_topic.rb` in the post-PR tree. 2) Locate the line `require_dependency 'email/sender'` near the top. 3) Search the remainder of the file for `Email::Sender` (and related identifiers from `email/sender`). Expected: at least one real usage justifying the require. Actual: no usage exists, so the require is dead. Optional runtime check: temporarily rename/remove the `email/sender` file (or adjust load paths) and run `ruby script/retrieve_topic.rb ...`; the script will fail at load time even though it never uses the required code.

**Found by** 1 cells (1 distinct report texts, 1 findings): fable: van·high

#### B93 — Unescaped request.referer interpolated into JS string breaks postMessage targetOrigin (and can enable injection)

**Location:** `app/views/layouts/embed.html.erb:11–11`  ·  **Severity:** high  ·  **Judge confidence:** 0.88

**Why this is real.** The template embeds server-controlled data directly into a JavaScript string literal: `parent.postMessage(..., '<%= request.referer %>');`. ERB’s default escaping is for HTML, not JavaScript, so characters like a trailing backslash (or a single quote) in the Referer header can escape/break the closing quote and make the inline script syntactically invalid. When that happens, the `postMessage` call never executes, so the expected resize message is not sent.

**How to replicate.** 1) Serve the embed page that uses this layout. 2) Request it while forcing a Referer header that ends with a backslash or contains a single quote, e.g. via curl: `curl -H "Referer: https://evil.test/\\" http://localhost:3000/.../embed` (or `Referer: https://evil.test/'`). 3) Open the response in a browser/inspect the rendered HTML: the generated JS contains an unterminated/broken string for the second `postMessage` argument. Expected: page posts `{type:'discourse-resize', ...}` to the parent; Actual: browser console shows a JS syntax error and no resize postMessage is sent.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: CE·high

#### B94 — Embed controller specs don’t render views, so embed templates can break without failing tests

**Location:** `spec/controllers/embed_controller_spec.rb:1–30`  ·  **Severity:** medium  ·  **Judge confidence:** 0.66

**Why this is real.** The controller spec file defines controller examples (e.g., `RSpec.describe EmbedController, type: :controller do`) but does not include `render_views`. In RSpec Rails, controller specs default to not rendering templates, so actions can return a successful response while `app/views/embed/best.html.erb` / `loading.html.erb` are never executed; template syntax/runtime errors therefore won’t be caught and can ship with green tests. This is a real test-coverage defect: it allows broken view code paths to pass CI undetected.

**How to replicate.** 1) Temporarily introduce an obvious error into `app/views/embed/best.html.erb` (e.g., add `<% raise 'boom' %>` or a syntax error). 2) Run the existing spec suite for the embed controller (e.g., `bundle exec rspec spec/controllers/embed_controller_spec.rb`). Expected: a failing spec due to template rendering error. Actual: specs still pass because views are not rendered. 3) Start the app and hit the embed endpoint that renders `best` in a browser/request; expected: page renders; actual: 500 error from the template exception.

**Found by** 1 cells (1 distinct report texts, 1 findings): opus: van·xhigh

#### B95 — Embed controller spec for missing embed_url is a false positive due to embeddable_host default failure

**Location:** `spec/controllers/embed_controller_spec.rb:8–16`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72

**Why this is real.** The example around line 8 (e.g., `it 'is 404 without an embed_url' do ... get ... expect(response.status).to eq(404) end`) passes even when the controller’s `params.require(:embed_url)` logic is never exercised. With the default/empty `embeddable_host` configuration, the controller fails earlier in `ensure_embeddable` (host not allowed/blank), returning/raising before Rails can raise the expected missing-parameter error. This is a genuine defect in the spec: it claims to test “missing param” behavior but actually tests “embeddable host misconfiguration returns 404,” so regressions in `params.require` would not be caught (the controller patch is not in this PR diff; this conclusion follows directly from the report’s described control flow).

**How to replicate.** 1) Open `spec/controllers/embed_controller_spec.rb` and find the test named like `is 404 without an embed_url` (around line 8). 2) Check whether the spec sets an allowed/non-empty embeddable host; if it does not, the request will be rejected by `ensure_embeddable` before `params.require(:embed_url)` is reached. 3) Confirm by temporarily configuring `embeddable_host` to a valid allowed value for the test (or stubbing `ensure_embeddable` to pass) and re-running that example: it should no longer return 404; instead it should raise `ActionController::ParameterMissing` / return 400 (depending on how the controller rescues), demonstrating the current expectation is asserting the wrong behavior.

**Found by** 1 cells (1 distinct report texts, 1 findings): opus: van·xhigh

#### B96 — Disqus-to-TopicEmbed import drops created_at, stamping imported topics with import time

**Location:** `lib/topic_embed/import_remote.rb:120–140`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The deduplicated reviewer reports indicate the new Disqus import path calls `TopicEmbed.import_remote(...)` without passing the historical timestamp (e.g., it omits an argument like `created_at: Date.parse(t[:createdat])`). Because `created_at` is not provided, `import_remote` will create the topic with the default current timestamp (time of import), causing all imported topics to share the import date/time and losing original chronological ordering. The PR diff does not include this file, so verification requires reading the post-PR tree and confirming the `TopicEmbed.import_remote` call lacks a `created_at:` keyword argument derived from the source record.

**How to replicate.** 1) Locate the Disqus import code path in the post-PR codebase that iterates Disqus threads/posts and invokes `TopicEmbed.import_remote`.
2) Confirm the source data includes a historical timestamp field (e.g., `t[:createdat]` / similar) but the call to `TopicEmbed.import_remote` does not pass `created_at:`.
3) Run an import with at least two Disqus threads with clearly different original dates (e.g., 2012 and 2020).
Expected: imported Discourse topics preserve the original created_at values and sort chronologically by those dates.
Actual: imported topics have created_at near the import execution time (clustered around 'now'), and historical ordering is lost.

**Found by** 1 cells (1 distinct report texts, 1 findings): opus: van·xhigh

#### B97 — (untitled)

**Location:** `?` (exact lines not in diff)  ·  **Severity:** ?  ·  **Judge confidence:** 0.00

**Why this is real.** (missing)

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: CE·medium

#### B98 — Scheduled and inline poll can run concurrently and duplicate work when inline poll exceeds throttle TTL

**Location:** `N/A (not referenced in reports; affected file not included in this PR diff)` (exact lines not in diff)  ·  **Severity:** high  ·  **Judge confidence:** 0.55

**Why this is real.** The clustered reports describe two entry points (a scheduled poll job and an inline poll path) that both trigger the same polling work, guarded only by a 60s throttle/TTL. Without a shared mutex/lock across both code paths, if the inline poll takes longer than the throttle TTL, a second invocation (e.g., the scheduled job) can re-enter while the first is still running, duplicating the poll and any side effects. This is a real concurrency bug (duplicate execution) rather than a style issue; however, the exact offending lines and line numbers cannot be quoted because the relevant file was not part of this PR’s diff and the reports did not include file/line references.

**How to replicate.** 1) Identify the two call sites in the codebase: (a) the scheduled job that runs the poll periodically and (b) the inline/request-triggered poll endpoint/method. 2) Modify or instrument the poll implementation to take >60s (e.g., insert a sleep or use a slow upstream) and ensure the throttle TTL is 60s. 3) Trigger the inline poll, then while it is still running, wait until the TTL expires and let the scheduled job fire (or trigger the inline poll again after 60s). Expected: second invocation should be prevented until the first completes. Actual: a second poll starts concurrently, duplicating work/requests/state updates.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: CE·medium

#### B99 — Using `<<` to append to `contents` mutates the caller's String and can crash on frozen strings

**Location:** `lib/topicembed.rb:13–13`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72

**Why this is real.** The code at/around line 13 reportedly does `contents << ...` (e.g., appending a suffix/prefix directly onto the `contents` String). In Ruby, `String#<<` mutates the receiver in-place, so if `contents` is a String provided by the caller, this unexpectedly changes the caller’s object. Additionally, if `contents` is frozen (common when passed as a frozen literal or explicitly `.freeze`d), `<<` raises `FrozenError`, turning what should be normal processing into a runtime exception; the PR diff doesn’t include this file, so this verification relies on the report’s cited line.

**How to replicate.** 1) Find the method in `lib/topicembed.rb` that takes/uses a `contents` String and locate line 13 where it does `contents << ...`. 2) In a Rails console (or unit test), call that method with a frozen String, e.g. `contents = "abc".freeze` and pass it as the `contents` argument. 3) Expected: method returns processed output without mutating the input and without crashing. Actual: raises `FrozenError: can't modify frozen String` (and even when not frozen, the original `contents` object will be modified, observable by checking it after the call).

**Found by** 1 cells (1 distinct report texts, 1 findings): fable: van·high

#### B100 — Cache miss on arbitrary URL triggers synchronous full RSS fetch+import (DoS vector)

**Location:** `topicretriever.rb:41–48`  ·  **Severity:** high  ·  **Judge confidence:** 0.66

**Why this is real.** The deduplicated reports all point to `topicretriever.rb:41` where the URL lookup path treats a miss as a reason to synchronously run a full RSS “fetch-and-import” of the entire feed. This is a real defect because any caller that can cause lookups for previously unseen URLs can force repeated expensive network+parsing+DB work in the request path (i.e., attacker-triggerable amplification/DoS). Note: this file is not part of the PR diff, so verification is by inspecting the post-PR tree at/around the referenced line and confirming the miss path directly invokes the RSS import routine instead of deferring/queuing/caching it.

**How to replicate.** 1) Locate the method in `topicretriever.rb` responsible for resolving a topic by URL (around line ~41) and confirm that when the URL is not found in cache/DB it immediately calls the RSS fetch+import routine for the whole feed.
2) Run the service in dev and identify an endpoint/action that calls this resolver with a URL parameter.
3) Send repeated requests with distinct, never-before-seen URL values (e.g., add a unique querystring each time) so the lookup always misses.
Expected: misses should be cheap (e.g., return not-found, or enqueue a background refresh at most once per interval).
Actual: each miss performs a full RSS fetch/import synchronously, causing high latency and rapidly increasing CPU/IO/DB load.

**Found by** 1 cells (1 distinct report texts, 1 findings): fable: van·high

#### B101 — Embed loading page auto-reloads every 30s, amplifying unauthenticated request/job flooding risk

**Location:** `app/views/embed/loading.html.erb:7–11`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The new template adds an unconditional reload loop: `setTimeout(function() { document.location.reload(); }, 30000);`. This causes any client that reaches the embed loading page to repeatedly re-request the same embed route forever (every 30 seconds) with no user interaction. If the embed request path enqueues background work per request (as reported), this view turns a single visit into an ongoing stream of requests/jobs, magnifying DoS potential rather than being a style issue.

**How to replicate.** 1) Load the embed loading page in a browser (the route that renders `embed/loading.html.erb`). 2) Open DevTools -> Network and observe the page automatically re-requesting itself every ~30 seconds (repeated GETs without clicks). 3) In parallel, monitor Sidekiq/Redis (queue size, enqueued jobs, Redis memory) while the page runs; expected: a single request/one-time load, actual: infinite periodic requests that (if the controller enqueues per request) continuously enqueue jobs and grow Redis/Sidekiq load.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: CE·high

---

## PR 10 — 41 distinct real bugs (7 goldens + 34 the goldens missed)
(<https://github.com/ai-code-review-evaluation/discourse-graphite/pull/10>)

### Bug index

| # | sev | location | title | found by (cells) |
|---|---|---|---|---|
| B1 | medium | `app/models/embeddablehost.rb:17–35` | Embeddable hosts saved with a port never match because lookup drops the port | 59 |
| B2 | high | `db/post_migrate/*_backfill_embeddable_hosts.rb:23–27` | Migration interpolates embeddable host strings into raw SQL, breaking on quotes and enabling SQL injection | 56 |
| B3 | high | `app/models/embeddable_host.rb:15–30` | EmbeddableHost allows duplicate host mappings, making lookup via `.first` nondeterministic | 52 |
| B4 | medium | `app/assets/javascripts/admin/components/embeddable-host.js.es6:43–51` | Delete action swallows destroyRecord() failures (no popupAjaxError catch) | 51 |
| B5 | high | `app/services/store.js.es6:192–202` | Plural *_ids hydration blindly calls .map on null/undefined and can drop unresolved relationship ids | 48 |
| B6 | high | `app/controllers/admin/embeddable_hosts_controller.rb:20–45` | Admin::EmbeddableHostsController update/destroy nil-dereference on missing record or params causes 500 | 46 |
| B7 | medium | `app/models/embeddablehost.rb:2–6` | EmbeddableHost hostname validation regex rejects valid hosts (long gTLDs, localhost/IP) and is inconsistent about ports | 43 |
| B8 | low | `assets/javascripts/discourse/components/embeddable-host.js:63–76` | Creating an embeddable host with no category overwrites server-assigned Uncategorized on the client until reload | 41 |
| B9 | high | `db/migrate/20150818190757createembeddablehosts.rb:10–16` | Migration assumes site_settings rows exist and dereferences execute(...)[0], crashing on nil | 37 |
| B10 | medium | `app/controllers/admin/embeddablehostscontroller.rb:24–26` | EmbeddableHost persists arbitrary categoryid without verifying category exists or is accessible | 24 |
| B11 | high | `db/migrate/20150818190757createembeddablehosts.rb:2–33` | Migration irreversibly deletes legacy site settings inside `change`, causing rollback to fail and permanent config loss | 22 |
| B12 | medium | `db/migrate/20150818190757createembeddablehosts.rb:25–32` | Migration backfills embeddable hosts verbatim (including schemes/paths), breaking hostname-only lookups | 21 |
| B13 | medium | `spec/controllers/admin/embeddablehostscontrollerspec.rb:1–20` | New admin controller specs only assert superclass, leaving create/update/destroy and edge cases untested | 19 |
| B14 | high | `app/controllers/admin/embeddingcontroller.rb:9–12` | PUT /admin/customize/embedding update is a no-op that returns 200 without persisting changes | 17 |
| B15 | critical | `db/migrate/20150818190757_create_embeddable_hosts.rb:3–3` | Migration uses create_table force: true causing silent drop/recreate and data loss | 16 |
| B16 | high | `app/models/embeddablehost.rb:6–10` | before_validation mutates host with sub! causing NoMethodError when host is nil | 15 |
| B17 | medium | `app/models/topic.rb:869–875` | expandable_first_post? no longer gated by configured embeddable hosts, causing regression when hosts are cleared | 15 |
| B18 | critical | `db/migrate/20150818190757_create_embeddable_hosts.rb:10–16` | CreateEmbeddableHosts migration can crash or mis-map categories due to fragile SiteSetting/category lookup and nil indexing | 15 |
| B19 | high | `db/migrate/20150818190757_create_embeddable_hosts.rb:31–40` | Irreversible destructive data migration in `change` permanently deletes site settings on rollback | 14 |
| B20 | critical | `db/migrate/20150818190757createembeddablehosts.rb:18–31` | Migration skips importing legacy embeddable hosts by using cmdtuples on a SELECT, then deletes the only copy of the config | 12 |
| B21 | medium | `config/routes.rb:153–153` | Routes expose REST actions for embeddable_hosts that the controller doesn't implement (ActionNotFound on GET) | 9 |
| B22 | high | `app/models/topicembed.rb:36–43` | Feed-polled TopicEmbed imports can lose category and land in Uncategorized when no EmbeddableHost matches | 7 |
| B23 | low | `test/javascripts/helpers/create-pretender.js.es6:226–229` | Pretender /fruits/:id handler ignores requested id and always returns fruits[0], making store.find('fruit', 2) test assert the wrong record | 6 |
| B24 | medium | `app/models/embeddablehost.rb:14–17` | EmbeddableHost lookup is case-sensitive because only DB side is lowercased | 4 |
| B25 | high | `app/serializers/embeddingserializer.rb:3–3` | EmbeddingSerializer emits only embeddable_host_ids (no sideloaded embeddable_hosts), breaking client hydration | 4 |
| B26 | high | `app/models/embeddablehost.rb:17–20` | Embed host lookup uses lower(host) without a supporting functional index, causing sequential scans on embed requests | 3 |
| B27 | low | `app/models/embeddablehost.rb:2–3` | EmbeddableHost host format validation allows trailing newline due to end-anchor, creating broken allowlist entries | 3 |
| B28 | medium | `app/models/topic_embed.rb:36–43` | TopicEmbed.import can create embedded topics with nil category when EmbeddableHost lookup returns nil | 3 |
| B29 | medium | `app/assets/javascripts/discourse/adapters/rest.js.es6:22–22` | REST adapter only replaces first underscore in type name, breaking admin routing for multi-underscore models | 2 |
| B30 | medium | `app/controllers/admin/embeddablehostscontroller.rb:16–18` | EmbeddableHost destroy action always reports success even when destroy fails | 2 |
| B31 | high | `app/controllers/embedcontroller.rb:61–75` | EmbedController authorization can be bypassed by forging the Referer header | 2 |
| B32 | high | `assets/javascripts/discourse/controllers/admin-graphite-hosts.js.es6:86–121` | Failed host.save leaves rejected buffered edits applied locally (no rollback on save error) | 1 |
| B33 | high | `assets/javascripts/discourse/routes/admin-embedding.js.es6:6–9` | Admin embedding route calls store.find without an id, causing findAll-style parsing and an empty model | 1 |
| B34 | high | `app/assets/javascripts/discourse/app/routes/admin-customize-embedding.js:7–9` | Admin /admin/customize/embedding route crashes because it queries an unregistered Ember model type | 1 |
| B35 | medium | `app/assets/javascripts/admin/components/embeddable-host.js.es6:43–51` | Delete action can fire multiple concurrent destroyRecord requests (no in-flight guard) | 1 |
| B36 | medium | `app/assets/javascripts/admin/controllers/admin-embedding.js.es6:6–7` | Unhandled promise rejection when saving admin embedding settings (update promise not handled) | 1 |
| B37 | low | `app/assets/javascripts/admin/templates/embedding.hbs:1–12` | Embeddable hosts table header renders even when list is empty due to truthy empty array in Ember {{if}} | 1 |
| B38 | high | `app/controllers/embedcontroller.rb:61–75` | Embed allowlist check does not scope requested topic/embed_url to the referer host's permitted category | 1 |
| B39 | ? | `?` | (untitled) | 1 |
| B40 | high | `db/migrate/20150818190757createembeddablehosts.rb:22–31` | Migration splits embeddable host list on newlines instead of pipe delimiter, losing hosts | 1 |
| B41 | medium | `app/models/embeddable_host.rb:1–30` | EmbeddableHost missing presence validation for non-null category_id causes DB NotNullViolation | 1 |

### Verification cards

#### B1 — Embeddable hosts saved with a port never match because lookup drops the port

**Location:** `app/models/embeddablehost.rb:17–35`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The model allows saving hosts that include a port (e.g. via a permissive host format/validation that does not reject `example.com:8080`), but the runtime lookup uses `uri(url).host` (or equivalent) which returns only the hostname without the port. As a result, code that compares the stored `host` string to the parsed URL host (e.g., `recordforhost`/`hostallowed?` comparing against `urihost(url)`) can never match when the stored value includes `:PORT`, making such configurations ineffective. The reports all describe the same mechanism; the PR diff itself is not shown here, so this verification relies on the reported line reference (`embeddablehost.rb:17`) and the described use of `uri.host`.

**How to replicate.** 1) In Rails console, create an allowed host record with a port: `EmbeddableHost.create!(host: 'example.com:8080')` (it is accepted by validation per report). 2) Call the allow-check with a URL including that port, e.g. `EmbeddableHost.hostallowed?('http://example.com:8080/some/path')` (or whatever entrypoint checks embedding). 3) Expected: returns true / embedding is allowed. Actual: returns false / embedding is rejected because the parsed URL host is `example.com` (port dropped) and does not equal the stored `example.com:8080`.

**Found by** 59 cells (118 distinct report texts, 118 findings): fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium; opus: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·low, van·xhigh; sonnet: MRV·low; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; terra: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium

#### B2 — Migration interpolates embeddable host strings into raw SQL, breaking on quotes and enabling SQL injection

**Location:** `db/post_migrate/*_backfill_embeddable_hosts.rb:23–27`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The reports consistently point to a post-migration that builds an INSERT with raw string interpolation, e.g. `execute("INSERT INTO embeddable_hosts ... VALUES ('#{h}', ...)")` around line ~23. Because `h` comes from the legacy embeddable-hosts setting, any value containing an apostrophe will terminate the SQL string literal and cause a syntax error (or worse, allow crafted SQL to be executed). This is a functional correctness and safety issue, not a style nit; it can crash the migration or insert corrupted data during upgrade/backfill.

**How to replicate.** 1) Before running the backfill migration, set the legacy embeddable hosts setting to include a host with a quote, e.g. `example.com` and `evil'host.com` (or a value like `a'); DELETE FROM embeddable_hosts; --`). 2) Run the migration/backfill (e.g. `bundle exec rake db:migrate` / `db:post_migrate`). 3) Observe the migration failing with a SQL syntax error near the quote, or (with a crafted payload) executing unintended SQL. Expected: hosts are inserted safely regardless of characters; actual: the raw-interpolated SQL breaks or becomes injectable.

**Found by** 56 cells (171 distinct report texts, 171 findings): fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; opus: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·xhigh; sonnet: CE·high, CE·low, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; sol: CE·high, CE·low, MRV·high, MRV·low, van·low; terra: CE·low, CE·medium, MRV·low, van·high; astra: CE·high, CE·low, CE·medium

#### B3 — EmbeddableHost allows duplicate host mappings, making lookup via `.first` nondeterministic

**Location:** `app/models/embeddable_host.rb:15–30`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** The underlying defect is that the host-to-category mapping is not enforced as unique (neither case-insensitively in the model nor via a DB unique index per the reports), while the lookup logic selects an arbitrary matching row. In the model method typically written like `where("lower(host) = ?", host.downcase).first`, `.first` has no `ORDER BY`, so if multiple rows exist for the same host (e.g., different categories), the returned record/category is unspecified and can vary depending on query plan/row order. The PR diff does not include this file, so this verification relies on the consistent reports pointing to the lack of uniqueness enforcement plus unordered `.first` selection.

**How to replicate.** 1) Insert two EmbeddableHost rows with the same hostname differing only by case (or identical) but different `category_id` (e.g., `host='Example.com', category_id=1` and `host='example.com', category_id=2`). 2) Trigger the host lookup used by embedding (e.g., call `EmbeddableHost.record_for_host('example.com')` or hit the embed endpoint that resolves the host). 3) Observe that the chosen category is whichever row happens to be returned first by the DB; it may flip after deletes/inserts/vacuum/restart because there is no uniqueness constraint and no deterministic ordering. Expected: host resolves to a single, well-defined category; actual: arbitrary category selection or inconsistent behavior.

**Found by** 52 cells (88 distinct report texts, 88 findings): fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; opus: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium, van·xhigh; sonnet: MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; glm-vis: CE·medium, MRV·high, MRV·low, MRV·medium, van·low; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; terra: CE·medium, MRV·high, MRV·low, MRV·medium, van·low, van·medium, van·xhigh; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### B4 — Delete action swallows destroyRecord() failures (no popupAjaxError catch)

**Location:** `app/assets/javascripts/admin/components/embeddable-host.js.es6:43–51`  ·  **Severity:** medium  ·  **Judge confidence:** 0.88

**Why this is real.** In the delete action, the code calls `this.get('host').destroyRecord().then(() => { ... });` but never attaches a rejection handler (e.g. `.catch(popupAjaxError)`). If the DELETE request fails, the promise rejects and no UI error is shown; additionally `deleteHost` is only sent in the `.then(...)`, so the row is never removed and the admin gets no feedback about the failure.

**How to replicate.** 1) Go to the admin UI where embeddable hosts are listed (the table row rendered by this component). 2) Click the delete button and confirm. 3) Force the delete request to fail (e.g., DevTools -> Network -> Offline, or mock the endpoint to return 500/403). Expected: an error popup via `popupAjaxError` and clear feedback that deletion failed. Actual: no error popup/feedback; the row remains because `deleteHost` is never called, and the rejection may surface only as an unhandled promise rejection in the console.

**Found by** 51 cells (75 distinct report texts, 75 findings): fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; opus: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium, van·xhigh; sonnet: MRV·high, MRV·low, MRV·medium, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high; sol: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### B5 — Plural *_ids hydration blindly calls .map on null/undefined and can drop unresolved relationship ids

**Location:** `app/services/store.js.es6:192–202`  ·  **Severity:** high  ·  **Judge confidence:** 0.86

**Why this is real.** In the plural branch introduced by the patch, the code does `const hydrated = obj[k].map(function(id) { ... });` and then `delete obj[k];` unconditionally. If `obj[k]` is `null`, `undefined`, or a scalar (possible for nullable/optional relationships or inconsistent serializers), calling `.map` throws a TypeError. Even when `obj[k]` is an array, `_lookupSubType(...)` can return falsy for missing referenced records, producing `[record, null, ...]` while still deleting the original `*_ids`, silently losing the original id list needed to preserve the relationship.

**How to replicate.** 1) Ensure a model payload contains a nullable plural relationship key like `comment_ids: null` (or omit it, leaving `obj[k]` undefined) and run the store hydration path that calls `_hydrateEmbedded`. Expected: hydration should tolerate null/absent ids and leave the object usable; Actual: it throws `TypeError: Cannot read properties of null/undefined (reading 'map')` at the plural branch.
2) Send a partial REST response where `topic_ids: [1,2]` but only record `1` is included in `root` (id `2` missing). Expected: either keep `topic_ids` intact or avoid inserting nulls so the relationship can be resolved later; Actual: `obj[pluralized]` becomes `[<record 1>, null]` and `topic_ids` is deleted, losing the unresolved id.

**Found by** 48 cells (122 distinct report texts, 122 findings): fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; sonnet: MRV·high, van·low, van·medium, van·xhigh; glm-flash: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; sol: CE·high, CE·low, MRV·low, MRV·medium, van·low, van·xhigh; terra: van·xhigh; astra: MRV·low

#### B6 — Admin::EmbeddableHostsController update/destroy nil-dereference on missing record or params causes 500

**Location:** `app/controllers/admin/embeddable_hosts_controller.rb:20–45`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** The controller logic (as described by multiple reports pointing at ~line 25) dereferences values without nil checks, e.g. `params[:embeddablehost][:host]` (crashes when the wrapper param is missing) and calls methods on a possibly-missing record, e.g. `save_host(EmbeddableHost.find_by(id: params[:id]))` / `embeddable_host.destroy` (crashes when `find_by` returns nil for a bad id). These are concrete runtime `NoMethodError`/nil-dereference failures reachable via HTTP requests, producing a 500 instead of a controlled 404/422 response.

**How to replicate.** 1) Trigger missing-record crash: issue an authenticated request to update or destroy a non-existent record, e.g. `PATCH /admin/embeddable_hosts/999999.json` or `DELETE /admin/embeddable_hosts/999999.json`. Expected: 404 (not found) or handled error; Actual: 500 due to `save_host(nil)` or `nil.destroy`.
2) Trigger missing-param crash: issue `PATCH /admin/embeddable_hosts/<valid_id>.json` with body missing the `embeddablehost` wrapper (or with `embeddablehost[host]` omitted/blank). Expected: validation error (422) or parameter error; Actual: 500 from `params[:embeddablehost][:host]` or subsequent nil usage.

**Found by** 46 cells (139 distinct report texts, 139 findings): fable: CE·high, CE·low, CE·medium, MRV·low, MRV·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·xhigh; sonnet: CE·high, CE·medium, MRV·high, MRV·medium, van·low; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·low, van·medium; sol: CE·high, CE·low, MRV·low, MRV·medium; terra: CE·low, CE·medium, MRV·low, MRV·medium; astra: CE·high, CE·low, MRV·high, MRV·low, MRV·medium

#### B7 — EmbeddableHost hostname validation regex rejects valid hosts (long gTLDs, localhost/IP) and is inconsistent about ports

**Location:** `app/models/embeddablehost.rb:2–6`  ·  **Severity:** medium  ·  **Judge confidence:** 0.64

**Why this is real.** Multiple reviewers point to the model-level format validation in `app/models/embeddablehost.rb` (reported around line 2) using a hostname regex that caps the TLD length to 2–5 letters (e.g., a fragment like `\.[a-z]{2,5}`) and requires an alphabetic TLD. That mechanism necessarily rejects legitimate modern gTLDs such as `.technology`/`.photography` as well as common non-DNS hosts used in embedding setups like `localhost` and raw IPv4 addresses. Reports also indicate the regex permits `:port` while downstream host extraction (e.g., `URI#host`/`urihost`) drops ports, making saved `example.com:3000` impossible to match later—this is a functional mismatch, not a style nit.

**How to replicate.** 1) Open `app/models/embeddablehost.rb` and find the `validates ... format: { with: /.../ }` for the host field; confirm it contains an alphabetic TLD restriction with a `{2,5}` quantifier (and likely an optional `:\d+` port segment).
2) In a Rails console, attempt to create records:
   - `EmbeddableHost.create!(host: "example.photography")` (or `.technology`, `.museum`) => expected: valid host saved; actual: validation error.
   - `EmbeddableHost.create!(host: "localhost")` and `EmbeddableHost.create!(host: "192.168.0.1")` => expected: allowed for local/private embedding; actual: validation error.
3) If the regex allows ports, save `EmbeddableHost.create!(host: "example.com:3000")`, then exercise the lookup path that compares against `URI.parse(url).host` (or `urihost`) for `http://example.com:3000/...` => expected: match; actual: mismatch because lookup uses `example.com` (port stripped) while the stored value includes `:3000`.

**Found by** 43 cells (89 distinct report texts, 89 findings): fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·low; opus: CE·medium, MRV·high, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium, van·xhigh; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium; sol: CE·high, CE·medium, MRV·high, MRV·medium, van·high, van·xhigh; terra: van·high, van·low, van·medium; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium

#### B8 — Creating an embeddable host with no category overwrites server-assigned Uncategorized on the client until reload

**Location:** `assets/javascripts/discourse/components/embeddable-host.js:63–76`  ·  **Severity:** low  ·  **Judge confidence:** 0.62

**Why this is real.** All reports point to the success handler for saving a new host assigning the host's category from the (still null) UI selection, e.g. `host.set('category_id', this.get('categoryId'));` followed by `host.set('category', this.site.categories.findBy('id', host.get('category_id')));`. When no category is selected, `categoryId` remains null, so `findBy('id', null)` yields undefined and the component overwrites the association the backend defaulted to Uncategorized. This is a real state bug (UI becomes inconsistent with persisted data) rather than a style issue; the file wasn’t part of the PR diff, so this verification relies on the consistent mechanism described in the deduplicated reports.

**How to replicate.** 1) In the UI where embeddable hosts are created/edited (the component using `embeddable-host.js`), add a new host and leave the category unselected/blank. 2) Click Save. 3) Observe: the host row shows no category (blank/undefined badge) immediately after save. 4) Reload the page (or re-fetch hosts from the server). Expected: it should show Uncategorized immediately after save (since backend defaults it). Actual: it only shows Uncategorized after reload because the client overwrote `host.category` using `findBy('id', null)`.

**Found by** 41 cells (62 distinct report texts, 62 findings): fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low; opus: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·low, van·xhigh; glm-flash: CE·high, MRV·high, MRV·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium; sol: MRV·high, MRV·medium, van·high, van·medium, van·xhigh; terra: CE·medium, van·low, van·medium, van·xhigh; astra: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium

#### B9 — Migration assumes site_settings rows exist and dereferences execute(...)[0], crashing on nil

**Location:** `db/migrate/20150818190757createembeddablehosts.rb:10–16`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** In `db/migrate/20150818190757createembeddablehosts.rb`, the migration reads settings via expressions like `execute(...)[0]['id'].to_i` / `execute(...)[0]['value'].to_i` (reports cite lines ~10, ~13, ~15). If the SQL query returns zero rows (common when a setting was never explicitly stored), `execute(...)[0]` is `nil`, so `nil['value']` (or `nil['id']`) raises `NoMethodError`, aborting the migration. The PR diff doesn’t include this file, so this verification relies on the consistent line-specific evidence from the reports.

**How to replicate.** 1) Create a database state where `site_settings` has no row for `name = 'embedcategory'` and/or no row for `name = 'uncategorizedcategoryid'` (e.g., a fresh install where defaults are not persisted as rows, or manually delete those rows).
2) Run migrations including `20150818190757createembeddablehosts.rb` (e.g., `bundle exec rake db:migrate`).
Expected: migration should fall back safely to defaults when settings rows are missing.
Actual: migration crashes with `NoMethodError` when it executes `execute(...)[0]['id'/'value']` on an empty result.

**Found by** 37 cells (98 distinct report texts, 98 findings): fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium; sol: CE·high, CE·low, MRV·high; terra: CE·low, CE·medium, MRV·medium; astra: CE·high, CE·low, CE·medium

#### B10 — EmbeddableHost persists arbitrary categoryid without verifying category exists or is accessible

**Location:** `app/controllers/admin/embeddablehostscontroller.rb:24–26`  ·  **Severity:** medium  ·  **Judge confidence:** 0.68

**Why this is real.** Multiple reports point to the same assignment in this controller (around line 24): `host.categoryid = params[:embeddablehost][:categoryid]` followed by saving the record, with no check like `Category.exists?(...)` or authorization/visibility validation. Because the `categoryid` value is taken directly from params and persisted, a nonexistent/deleted (or read-restricted) category id can be stored, creating a dangling relationship that is later used when importing/creating embedded topics. The PR diff does not include this file, so this verification relies on the reported line reference and the described behavior in code paths that later use `host.categoryid` during import/topic creation.

**How to replicate.** 1) In the admin UI (or via HTTP), create or update an EmbeddableHost and set `embeddablehost[categoryid]` to a non-existent category id (e.g., a large integer), or to an id of a category that will be deleted after saving.
2) Save succeeds (actual), because the controller/model does not validate that the category exists/is allowed.
3) Trigger an embed import for that host (e.g., by embedding a page that causes `TopicEmbed.import` / topic creation).
Expected: the system should reject the invalid category id at save-time (or coerce to nil/default) with a clear error.
Actual: import/topic creation fails or routes content to an unintended/private category because the stored `categoryid` is invalid or unauthorized.

**Found by** 24 cells (43 distinct report texts, 43 findings): fable: CE·low, CE·medium, MRV·high, MRV·low; opus: CE·high, CE·low, CE·medium, MRV·low, MRV·medium; sonnet: MRV·low; glm-flash: MRV·high, MRV·medium, van·high; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, MRV·low, MRV·medium, van·high; astra: MRV·high, MRV·medium

#### B11 — Migration irreversibly deletes legacy site settings inside `change`, causing rollback to fail and permanent config loss

**Location:** `db/migrate/20150818190757createembeddablehosts.rb:2–33`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** All reports point to this migration defining `def change` while also running raw SQL via `execute`, including a destructive `DELETE FROM site_settings ...` around line 31. In Rails, data-changing `execute` statements inside `change` are not automatically reversible, so `db:rollback` will raise `ActiveRecord::IrreversibleMigration` and cannot restore the deleted `embeddable_hosts`/`embed_category` settings. Because the migration deletes the only copy of the legacy configuration (with no backup/down path), rolling back (or a failed deploy requiring rollback) permanently loses operator settings; the PR diff isn’t provided here, so this verification is based on the consistent line-referenced reports.

**How to replicate.** 1) In an environment with legacy settings present, set `site_settings` entries for `embeddable_hosts` and `embed_category` (or whatever names appear in the migration) to non-empty values. 2) Run `rails db:migrate` to apply `20150818190757createembeddablehosts`. 3) Run `rails db:rollback STEP=1`. Expected: schema and data return to pre-migration state, including the legacy site settings. Actual: rollback fails with an irreversible migration error (or, if rollback proceeds partially, the legacy settings have already been deleted and are not restored), leaving embedding configuration unrecoverable from the DB.

**Found by** 22 cells (29 distinct report texts, 29 findings): fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; opus: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·xhigh; sonnet: CE·low, MRV·high, MRV·low; glm-flash: CE·high; glm-vis: CE·medium; sol: CE·high; terra: MRV·high, MRV·medium; astra: MRV·high, MRV·low

#### B12 — Migration backfills embeddable hosts verbatim (including schemes/paths), breaking hostname-only lookups

**Location:** `db/migrate/20150818190757createembeddablehosts.rb:25–32`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The migration backfill reportedly does `val.split("\n").each do |h| EmbeddableHost.create(host: h) end` (around line 25), which copies legacy allowlist entries verbatim into the new `embeddable_hosts.host` column. If legacy values include full URLs like `https://example.com/path`, the runtime authorization code typically compares against `URI(url).host` (e.g., `example.com`), so stored values containing schemes/paths will never match, causing previously allowed embeds to be rejected after the old setting is removed. The reports also note no rejection of blank lines, meaning empty-string rows can be inserted, indicating the backfill lacks basic normalization/validation.

**How to replicate.** 1) Before running the migration, set the legacy embeddable-host allowlist setting to include URL-form entries, e.g. a newline-delimited value like `https://example.com/path\nhttp://allowed.test`. 2) Run the migration that creates `embeddable_hosts` and performs the backfill. 3) Inspect the `embeddable_hosts` table: it will contain rows with hosts exactly `https://example.com/path` rather than just `example.com`. 4) Attempt to embed content from `https://example.com/path` after upgrade: expected behavior is it remains allowed (as it was pre-migration), but actual behavior is it is rejected because the lookup uses only `URI(...).host` (`example.com`) which does not equal the stored string (`https://example.com/path`).

**Found by** 21 cells (41 distinct report texts, 41 findings): fable: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; opus: CE·low, CE·medium, MRV·high, MRV·medium; glm-flash: CE·medium; glm-vis: van·medium; sol: CE·high, CE·low, MRV·high, MRV·medium; terra: CE·low, CE·medium, MRV·high; astra: CE·high, CE·low, CE·medium

#### B13 — New admin controller specs only assert superclass, leaving create/update/destroy and edge cases untested

**Location:** `spec/controllers/admin/embeddablehostscontrollerspec.rb:1–20`  ·  **Severity:** medium  ·  **Judge confidence:** 0.64

**Why this is real.** The spec file reportedly contains only a class-ancestry check (e.g., an assertion equivalent to `expect(described_class < Admin::AdminController).to eq(true)`), and no examples that hit controller actions (`create`, `update`, `destroy`, `show`) or validate behavior (staff-only access, uncategorized fallback, nil-record handling). Because the PR diff for this file is not provided here, this verification relies on the clustered reviewer reports; however, if the spec truly only asserts inheritance, it cannot fail when request/parameter/record-handling bugs exist in the controller, meaning it is a real test gap rather than a style nit.

**How to replicate.** 1) Open `spec/controllers/admin/embeddablehostscontrollerspec.rb` in the post-PR tree. 2) Confirm the only expectation(s) are about superclass/ancestry and that there are no request examples like `post :create`, `put :update`, `delete :destroy`, or `get :show` with assertions on responses/side effects. 3) Observe that with such a spec, a regression like "calling update with a missing/invalid id raises (500)" or "non-staff can hit mutating endpoints" would still allow the test suite to pass (expected: failing spec; actual: no spec covers it, so green suite).

**Found by** 19 cells (25 distinct report texts, 25 findings): fable: CE·high, MRV·high, MRV·low, MRV·medium, van·high, van·medium; opus: MRV·high, MRV·low, MRV·medium, van·medium, van·xhigh; sonnet: van·xhigh; glm-flash: CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: MRV·high, MRV·low, MRV·medium

#### B14 — PUT /admin/customize/embedding update is a no-op that returns 200 without persisting changes

**Location:** `app/controllers/admin/embeddingcontroller.rb:9–12`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** Multiple reports point to `app/controllers/admin/embeddingcontroller.rb:9` where the `update` action does not read any request params nor call any persistence method; it simply re-renders the current `@embedding` (e.g., `render_serialized(@embedding, EmbeddingSerializer)`). Because the action returns a successful response while performing no mutation, any client "save" request will appear to succeed (HTTP 200) even though nothing is updated. This is a functional contract bug (misleading endpoint behavior), not a style issue; the controller method effectively discards the request body.

**How to replicate.** 1) Send a PUT request to `/admin/customize/embedding` with a JSON body that changes a setting (any field the UI intends to save). 2) Observe the response is 200 and returns the serialized embedding. 3) Reload the page or re-fetch the embedding; expected: the updated value persists. Actual: the value is unchanged because `update` ignores params and performs no save/update call.

**Found by** 17 cells (23 distinct report texts, 23 findings): fable: van·high, van·medium; opus: CE·low, CE·medium, van·medium, van·xhigh; glm-flash: CE·high, CE·low, MRV·high, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; sol: MRV·high, MRV·medium

#### B15 — Migration uses create_table force: true causing silent drop/recreate and data loss

**Location:** `db/migrate/20150818190757_create_embeddable_hosts.rb:3–3`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74

**Why this is real.** The migration reportedly calls `create_table :embeddable_hosts, force: true` (referenced at line 3 in multiple reports). In Rails migrations, `force: true` issues a DROP TABLE (if it exists) before creating the table, which silently deletes any existing `embeddable_hosts` table and all its rows. That makes the migration destructive on re-runs or if the table already exists (e.g., created manually or by a plugin), and it masks partial-failure states instead of failing loudly.

**How to replicate.** 1) In a database where an `embeddable_hosts` table already exists (e.g., create it manually) and insert at least one row. 2) Run the migration `20150818190757_create_embeddable_hosts.rb` (or re-run it in a reset/test environment). Expected: migration should fail or no-op if the table exists, preserving existing data. Actual: the existing table is dropped and recreated, and the previously inserted row(s) are lost.

**Found by** 16 cells (24 distinct report texts, 24 findings): fable: CE·medium, MRV·medium; opus: CE·low, CE·medium, van·low, van·medium, van·xhigh; sonnet: MRV·low, MRV·medium; glm-flash: MRV·high, MRV·low; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium, van·high

#### B16 — before_validation mutates host with sub! causing NoMethodError when host is nil

**Location:** `app/models/embeddablehost.rb:6–10`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The model runs a before_validation hook that unconditionally calls a mutating string method on the attribute (e.g., `self.host.sub!(...)`). If `host` is `nil` (missing param or explicitly null), Ruby raises `NoMethodError: undefined method 'sub!' for nil:NilClass` during the callback, so normal validations (like a format/presence validation intended to yield a validation error response) never execute and the request becomes a 500. The PR diff for this file is not shown, so this verification relies on the consistent line-referenced reports pointing to `app/models/embeddablehost.rb:6` / `7-10`.

**How to replicate.** 1) Find the before_validation callback in `app/models/embeddablehost.rb` around lines 6-10 that does `self.host.sub!(...)` (or equivalent) without a nil guard.
2) Trigger a create/update where `host` is absent or null (e.g., POST to the admin embeddable-host create endpoint with params `{ embeddablehost: {} }` or missing `embeddablehost[:host]`).
3) Actual: the request raises `NoMethodError` in the callback and returns HTTP 500.
4) Expected: the model should fail validation (HTTP 422 / error payload) indicating `host` is invalid/missing rather than crashing.

**Found by** 15 cells (22 distinct report texts, 22 findings): fable: CE·high, CE·low, CE·medium, MRV·low, MRV·medium; opus: CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high; glm-flash: CE·medium, MRV·high, MRV·low; glm-vis: MRV·high; sol: CE·low

#### B17 — expandable_first_post? no longer gated by configured embeddable hosts, causing regression when hosts are cleared

**Location:** `app/models/topic.rb:869–875`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The reports indicate that in the post-PR code around `app/models/topic.rb:869`, `expandable_first_post?` was changed to only check something equivalent to `SiteSetting.embed_truncate? && has_topic_embed?`, and the prior guard requiring configured embeddable hosts (e.g., `SiteSetting.embeddable_hosts.present?` or an `EmbeddableHost.exists?` check) was removed. That means once a topic has an embed record (`has_topic_embed?`), enabling `embed_truncate` will keep `expandable_first_post?` true even if all allowed embedding hosts are later deleted/cleared, silently changing the previous behavior where clearing hosts disabled this feature. This is a behavioral regression (logic bug), not a style issue, because it changes feature enablement conditions and can expose expandable/truncated behavior when the admin has effectively disabled embedding by removing all hosts.

**How to replicate.** 1) Ensure embedding is enabled at least once so an embedded topic exists (create an embedded topic while at least one EmbeddableHost/embeddable host entry is configured). 2) Enable the setting controlling truncation (e.g., `SiteSetting.embed_truncate = true`). 3) Delete all allowed embedding hosts (remove all EmbeddableHost rows / clear the embeddable hosts setting so there are zero configured hosts). 4) Fetch the topic JSON or view the topic; observe `expandable_first_post?` behavior (e.g., an `expandable_first_post` field or UI expander remains active) because the method still returns true due to `embed_truncate && has_topic_embed?`. Expected: once no embeddable hosts are configured, expandable/truncated embed behavior should be off (method returns false), matching the prior host-gated semantics.

**Found by** 15 cells (21 distinct report texts, 21 findings): fable: CE·high, MRV·high; opus: MRV·high, MRV·low, MRV·medium; sonnet: MRV·high, MRV·low; glm-flash: CE·low, CE·medium, MRV·high, MRV·medium; glm-vis: MRV·high, MRV·low; terra: van·high, van·medium

#### B18 — CreateEmbeddableHosts migration can crash or mis-map categories due to fragile SiteSetting/category lookup and nil indexing

**Location:** `db/migrate/20150818190757_create_embeddable_hosts.rb:10–16`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74

**Why this is real.** The migration reportedly does unguarded indexing on raw SQL results, e.g. `execute(...)[0]['id'].to_i` for the embed category and `execute(...)[0]['value'].to_i` for `uncategorizedcategoryid`. If either query returns zero rows, `[0]` is `nil` and `['id']`/`['value']` raises `NoMethodError`, aborting the migration. Additionally, the embed-category lookup is described as an inner join on `s.value = c.name`, which fails when the setting stores an id/slug or the category was renamed/case-changed, silently defaulting hosts to the wrong category (often uncategorized); this is a functional defect, not a style issue. (This file is not shown in the PR diff per the prompt, so this verification is based on the deduplicated reports’ cited lines/behavior.)

**How to replicate.** 1) In a test DB, remove or omit the `SiteSetting` row for the embed category (or for `uncategorizedcategoryid`), or set the embed-category setting value to a category id/slug instead of an exact `categories.name` match. 2) Run `rails db:migrate` up through `20150818190757_create_embeddable_hosts.rb`. Expected: migration completes and uses a valid category id. Actual: migration raises `NoMethodError` due to `execute(...)[0]` being nil, or it incorrectly assigns embeddable hosts to uncategorized because the `s.value = c.name` join returns no rows.

**Found by** 15 cells (21 distinct report texts, 21 findings): fable: CE·low, MRV·high, MRV·low, MRV·medium; opus: CE·medium, MRV·high, MRV·medium, van·high, van·xhigh; glm-flash: CE·high, CE·low, van·low; glm-vis: CE·high, CE·low, CE·medium

#### B19 — Irreversible destructive data migration in `change` permanently deletes site settings on rollback

**Location:** `db/migrate/20150818190757_create_embeddable_hosts.rb:31–40`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The migration reportedly performs raw SQL data operations inside `def change`, including `execute "DELETE FROM site_settings WHERE name IN ('embeddablehosts','embedcategory')"` (report points to line ~31). Because these deletes are not reversible and there is no explicit `def down` that re-inserts the deleted `site_settings` rows, rolling back the migration drops the new table but cannot restore the deleted configuration, causing permanent data loss. The PR diff isn’t provided here, so this verification relies on the consistent line-level description from the deduplicated reports.

**How to replicate.** 1) In a DB with existing `site_settings` rows for names `embeddablehosts` and `embedcategory` (populate them with non-empty values). 2) Run `rails db:migrate` to apply `20150818190757_create_embeddable_hosts`. 3) Confirm the settings rows were deleted (and hosts inserted into the new table if applicable). 4) Run `rails db:rollback STEP=1`. Expected: original `site_settings` rows restored (or rollback fully reversible). Actual: rollback cannot restore the deleted `site_settings` rows; embedding configuration is lost even though the schema rollback drops the embeddable hosts table.

**Found by** 14 cells (20 distinct report texts, 20 findings): fable: MRV·high, MRV·low; opus: MRV·high; glm-flash: CE·low, MRV·high, MRV·low; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; astra: CE·low, MRV·high

#### B20 — Migration skips importing legacy embeddable hosts by using cmdtuples on a SELECT, then deletes the only copy of the config

**Location:** `db/migrate/20150818190757createembeddablehosts.rb:18–31`  ·  **Severity:** critical  ·  **Judge confidence:** 0.95

**Why this is real.** The migration gates the import on `if embeddablehosts && embeddablehosts.cmdtuples > 0`, but `cmdtuples` is the affected-row count for DML; for PostgreSQL `SELECT` results it is 0, so this condition is never true even when rows are returned. As a result, the insert loop never runs and the subsequent unconditional `delete from site_settings where name in ('embeddablehosts', 'embedcategory')` removes the legacy settings, permanently losing all configured embeddable hosts on upgrade. (The PR diff does not include this file; this verification relies on the reported offending lines.)

**How to replicate.** 1) In a PostgreSQL-backed environment, create legacy rows in `site_settings`: one with `name='embeddablehosts'` and a non-empty host list value, and optionally `name='embedcategory'`.
2) Run the migration `20150818190757createembeddablehosts.rb` (e.g., `rake db:migrate`).
3) Observe that the `embeddable_hosts` table remains empty (no imported rows) while the `site_settings` rows for `embeddablehosts`/`embedcategory` are deleted.
Expected: hosts are copied into `embeddable_hosts` before deleting legacy settings. Actual: import block is skipped and settings are deleted, disabling previously configured embedding.

**Found by** 12 cells (13 distinct report texts, 13 findings): opus: CE·medium, MRV·low; sonnet: MRV·high; glm-flash: CE·high, MRV·high; glm-vis: MRV·high, MRV·low, MRV·medium; sol: MRV·low, MRV·medium; terra: MRV·medium, van·high

#### B21 — Routes expose REST actions for embeddable_hosts that the controller doesn't implement (ActionNotFound on GET)

**Location:** `config/routes.rb:153–153`  ·  **Severity:** medium  ·  **Judge confidence:** 0.86

**Why this is real.** The PR adds `resources :embeddable_hosts, constraints: AdminConstraint.new` (config/routes.rb:153). In Rails, `resources` without an `only:`/`except:` generates the full REST set (index/show/new/edit/create/update/destroy). If `Admin::EmbeddableHostsController` only defines mutating actions (create/update/destroy) and does not define `index`, `show`, `new`, or `edit`, then GET requests to the generated routes will dispatch to missing actions and raise `AbstractController::ActionNotFound` (500) instead of being unroutable or handled.

**How to replicate.** 1) In the post-PR code, run `bin/rails routes | grep embeddable_hosts` and observe routes like `GET /admin/embeddable_hosts(.:format) admin/embeddable_hosts#index` and `GET /admin/embeddable_hosts/:id(.:format) admin/embeddable_hosts#show` are present.
2) Open `app/controllers/admin/embeddable_hosts_controller.rb` and confirm it does not implement `index/show/new/edit` (only create/update/destroy).
3) As an admin (or with an authenticated admin session), request `GET /admin/embeddable_hosts.json` (or `GET /admin/embeddable_hosts/1`).
Expected: no route exists (404) or a valid index/show response. Actual: Rails raises `AbstractController::ActionNotFound` for the missing action, resulting in a 500 error.

**Found by** 9 cells (10 distinct report texts, 10 findings): fable: CE·high, CE·medium, van·medium; opus: CE·medium, van·medium; sonnet: CE·high, MRV·high, MRV·low; glm-flash: CE·high

#### B22 — Feed-polled TopicEmbed imports can lose category and land in Uncategorized when no EmbeddableHost matches

**Location:** `app/models/topicembed.rb:36–43`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The reported post-PR code derives category solely from a per-host lookup: `eh = EmbeddableHost.record_for_host(url)` followed by `category: eh.try(:category_id)` (or equivalent). When `record_for_host(url)` returns nil (no matching embeddable host row, or host mismatch like www vs bare), `eh.try(:category_id)` becomes nil and the created topic has no category, silently falling back to Uncategorized. This is a real behavioral regression because the former site-wide fallback (`SiteSetting.embed_category`) was removed, and feed polling paths can call `TopicEmbed.import` without first ensuring/validating an EmbeddableHost exists.

**How to replicate.** 1) Configure a Discourse instance with RSS/Atom feed polling enabled (so `Jobs::PollFeed` runs) and set the old embed default category to a non-default category (pre-PR behavior baseline). 2) Ensure there is NO `EmbeddableHost` row matching the host of the feed item link URLs (e.g., feed is on example.com but item links are on www.example.com or a different domain). 3) Trigger `Jobs::PollFeed` (or run it manually) so it calls `TopicEmbed.import` for feed entries. Expected (pre-PR): imported topics go into the configured embed category; Actual (post-PR): `record_for_host(url)` is nil, `category` becomes nil, and topics are created in Uncategorized with no warning/error.

**Found by** 7 cells (11 distinct report texts, 11 findings): fable: CE·medium, MRV·high, MRV·low, MRV·medium, van·low; opus: MRV·high; glm-flash: van·medium

#### B23 — Pretender /fruits/:id handler ignores requested id and always returns fruits[0], making store.find('fruit', 2) test assert the wrong record

**Location:** `test/javascripts/helpers/create-pretender.js.es6:226–229`  ·  **Severity:** low  ·  **Judge confidence:** 0.80

**Why this is real.** The Pretender route for single-fruit fetch is defined as `this.get('/fruits/:id', function() { ... return { fruit: fruits[0] }; })` (around lines 226-229), which never reads `request.params.id` and always serves the first fixture. As a result, any call like `store.find('fruit', 2)` receives the payload for fruit id=1 (apple), so downstream tests that assert apple’s data under an id=2 request are validating a fixture quirk rather than correct find-by-id behavior. This is a functional defect in the test server/mock, not a style issue.

**How to replicate.** 1) Inspect `test/javascripts/helpers/create-pretender.js.es6` and locate the `this.get('/fruits/:id', ...)` handler; note it returns `fruits[0]` unconditionally. 2) In `test/javascripts/models/store-test.js.es6` (the updated "find embedded" test), observe it calls `store.find('fruit', 2)` but asserts properties matching apple (e.g., colors ids [1,2]) rather than banana (colorids [3]). 3) To observe behavior concretely, temporarily log/inspect the response for GET /fruits/2 (or change the handler to select by `request.params.id`); expected: response fruit.id == 2, actual (current): response fruit.id == 1, and once fixed the test assertions will fail because banana has different embedded colors.

**Found by** 6 cells (7 distinct report texts, 7 findings): glm-flash: CE·high, MRV·high; glm-vis: CE·high, MRV·high, van·high, van·medium

#### B24 — EmbeddableHost lookup is case-sensitive because only DB side is lowercased

**Location:** `app/models/embeddablehost.rb:14–17`  ·  **Severity:** medium  ·  **Judge confidence:** 0.90

**Why this is real.** The reported code does `host = uri.host` and then performs `where("lower(host) = ?", host).first`. In PostgreSQL, `lower(host)` is compared to the bind parameter exactly as provided; if `host` contains any uppercase characters (e.g., "EvilTrout.com"), it will not equal the lowercased DB expression ("eviltrout.com"). This is a functional mismatch in normalization (only the stored side is lowercased), causing legitimate embeds to be rejected; the PR diff itself isn’t shown here, so this is verified based on the consistent line-level reports.

**How to replicate.** 1) Configure an allowed embeddable host as `eviltrout.com` in the DB/UI. 2) Trigger an embed using a URL whose hostname includes uppercase characters, e.g. embed snippet or referer like `http://EvilTrout.com/some/path`. 3) The lookup using `where("lower(host) = ?", host)` fails to find the configured host, so the embed path treats it as an invalid host (topic retrieval/import does not run). Expected: host matches regardless of DNS-equivalent capitalization; Actual: request is rejected and the embed never loads (often stuck on a loading state).

**Found by** 4 cells (7 distinct report texts, 7 findings): fable: CE·medium, MRV·high, MRV·medium; sol: MRV·medium

#### B25 — EmbeddingSerializer emits only embeddable_host_ids (no sideloaded embeddable_hosts), breaking client hydration

**Location:** `app/serializers/embeddingserializer.rb:3–3`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The reports consistently point to `app/serializers/embeddingserializer.rb:3` defining the association like `has_many :embeddable_hosts, ... embed: :ids` (notably without `include: true`). In AMS-style serializers, `embed: :ids` alone produces only an `embeddable_host_ids` array and does not emit a root/side-loaded `embeddable_hosts` collection. The frontend store code path described in the reports (`lookupSubType` for each id) requires those host records to exist in a top-level side-load array; because the payload never includes them, hydration resolves to missing/undefined records and the admin list renders empty. The PR diff does not include this file, so this verification relies on the reported offending line and the known serializer behavior.

**How to replicate.** 1) Load the admin embedding UI that fetches embeddings (e.g., navigate to `/admin/customize/embedding`).
2) Inspect the network response for the embeddings endpoint (e.g., GET `/admin/customize/embedding.json` or equivalent).
3) Actual: the JSON includes something like `embeddable_host_ids: [..]` but no side-loaded/top-level `embeddable_hosts: [...]` array of host objects.
4) Expected: when the client hydrates `embedding.embeddable_hosts` by id, the response should also include the full embeddable host records in a root collection so `lookupSubType` can resolve them; otherwise the table/list shows blank/empty entries despite ids being present.

**Found by** 4 cells (4 distinct report texts, 4 findings): opus: CE·medium; sonnet: CE·high; glm-flash: MRV·high, MRV·low

#### B26 — Embed host lookup uses lower(host) without a supporting functional index, causing sequential scans on embed requests

**Location:** `app/models/embeddablehost.rb:17–20`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** In `EmbeddableHost.ensure_embeddable` the lookup is performed with a case-insensitive predicate like `where("lower(host) = ?", host.downcase)` (reported at line 17). The accompanying migration `createembeddablehosts.rb` (reported lines 3-7) creates the table but does not add an index on `host`, and even a plain index on `host` would not be used by `lower(host)` anyway; without a functional index on `lower(host)` (or normalized storage), this forces a table scan for each embed request. This is a real performance bug on a hot path (public embeds), not a style issue, because it changes the query pattern from a cached/in-memory check to an uncached DB lookup that cannot be indexed as written.

**How to replicate.** 1) Ensure the PR is applied and the `embeddable_hosts` table exists (run migrations). 2) Add enough rows to `embeddable_hosts` to make scans noticeable (e.g., thousands of distinct hosts). 3) Trigger an embed request path (e.g., request the public `/embed/comments` endpoint for some host/domain). 4) Observe the SQL generated includes `lower(host) = ...` and run `EXPLAIN (ANALYZE, BUFFERS)` for that query: expected behavior is an index scan for host lookup, but actual behavior will be a sequential scan (or otherwise non-indexed scan) due to the missing functional index, leading to increased latency and DB load per request.

**Found by** 3 cells (3 distinct report texts, 3 findings): fable: van·high; opus: van·xhigh; sol: CE·high

#### B27 — EmbeddableHost host format validation allows trailing newline due to end-anchor, creating broken allowlist entries

**Location:** `app/models/embeddablehost.rb:2–3`  ·  **Severity:** low  ·  **Judge confidence:** 0.67

**Why this is real.** The reported code in `app/models/embeddablehost.rb` validates `host` with a regex anchored using an end-of-string anchor that can match *before* a trailing newline (reported as `\z`/`\Z`), e.g. `validates :host, format: { with: /\A...\Z/ }`. In Ruby, `\Z` (and similarly `$`) will match before a final newline, so an input like `"example.com\n"` can pass format validation and be persisted with the newline intact. Later, lookups comparing `lower(host)` to a parsed URI host (which will be `"example.com"` without the newline) will not match, producing a silently broken allowlist entry; the reports note nothing strips the newline server-side and this is reachable via API.

**How to replicate.** 1) Find the `EmbeddableHost` model validation in `app/models/embeddablehost.rb` (around line 2) and confirm the host format regex uses an end anchor that matches before a trailing newline (e.g., `\Z` or `$`) rather than a strict end anchor (`\z`) and/or does not normalize/strip whitespace.
2) Create an allowlist entry via the API/console with a trailing newline, e.g. `EmbeddableHost.create!(host: "example.com\n")` (or the corresponding endpoint payload).
3) Observe: the record is accepted and stored containing `\n` (actual behavior). Expected: validation should reject or normalize such input so that stored host equals `"example.com"`.
4) Attempt to use/resolve an embed for `https://example.com/...` and observe the allowlist lookup fails (because `lower(host)` in DB includes the newline while `uri.host` does not), so the allowlisted host is not recognized.

**Found by** 3 cells (3 distinct report texts, 3 findings): opus: van·high; sonnet: van·low; glm-vis: van·high

#### B28 — TopicEmbed.import can create embedded topics with nil category when EmbeddableHost lookup returns nil

**Location:** `app/models/topic_embed.rb:36–43`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72

**Why this is real.** The reports consistently point to TopicEmbed.import assigning the new topic's category from the embeddable host record, e.g. `eh = EmbeddableHost.record_for_host(url)` and then `category: eh.try(:category_id)` (or equivalent). If `record_for_host` returns nil (no matching host, or the host row was deleted/edited between validations and this second lookup), `eh.try(:category_id)` silently becomes nil and the topic is created uncategorized rather than falling back to the configured default category. The PR diff itself is not provided here, so this verification relies on the line references and behavior described in the deduplicated reports.

**How to replicate.** 1) Configure embedding, ensuring there is a default/fallback category (previously governed by a site setting like `uncategorized_category_id`). 2) Trigger TopicEmbed.import with a URL that passes initial host validation (or use a feed polling URL path that calls import) but does not have a corresponding EmbeddableHost row at the time import assigns category (e.g., delete/edit the EmbeddableHost record during the window between validation/fetch and the second lookup, or import from feed polling where no EmbeddableHost exists). 3) Observe the created topic: expected behavior is it lands in the configured default category; actual behavior is category_id is nil (uncategorized) with no error raised.

**Found by** 3 cells (3 distinct report texts, 3 findings): sonnet: MRV·high, van·low; glm-flash: CE·high

#### B29 — REST adapter only replaces first underscore in type name, breaking admin routing for multi-underscore models

**Location:** `app/assets/javascripts/discourse/adapters/rest.js.es6:22–22`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** At/around line 22 the adapter normalizes the Ember Data type with a single-string replace (reported as `type.replace('_', '-')`). In JavaScript, `String.prototype.replace` with a string argument replaces only the first match, so a type like `foo_bar_baz` becomes `foo-bar_baz` instead of `foo-bar-baz`. Any later lookup/comparison that expects fully hyphenated types (e.g., for admin route selection or identity-map keys) will silently miss, causing wrong URL selection; this is a functional defect, not a style nit. (The PR diff isn’t provided here; verification is by inspecting the post-PR file at the reported line.)

**How to replicate.** 1) Open `app/assets/javascripts/discourse/adapters/rest.js.es6` and locate the type normalization around line 22 (`type = type.replace('_', '-')` or equivalent).
2) Identify the code path that decides whether a request goes to an admin endpoint (e.g., comparing the normalized `type` against an allowlist of admin types / choosing `/admin/` vs `/`).
3) Trigger a request for a model whose type contains multiple underscores (e.g., `foo_bar_baz`) through the adapter’s URL building (e.g., `adapter.buildURL('foo_bar_baz', ...)` or by interacting with a route that loads that type).
Expected: all underscores are converted (`foo-bar-baz`) so the admin-type match succeeds and the request targets the correct admin path.
Actual: only the first underscore is converted (`foo-bar_baz`), the admin match fails, and the adapter routes to the non-admin path (e.g., `/` instead of `/admin/`) or uses a mismatched type key for caching/hydration.

**Found by** 2 cells (2 distinct report texts, 2 findings): fable: van·low; opus: MRV·high

#### B30 — EmbeddableHost destroy action always reports success even when destroy fails

**Location:** `app/controllers/admin/embeddablehostscontroller.rb:16–18`  ·  **Severity:** medium  ·  **Judge confidence:** 0.78

**Why this is real.** The destroy action calls `host.destroy` but does not check its return value and then unconditionally renders a success payload (e.g., `host.destroy` followed by `render json: success_json`). In Rails, `destroy` can fail (returning false / leaving the record persisted) when callbacks abort the destroy or when the database rejects it (e.g., FK constraints). Because the result is ignored, the controller can return 200/success even though the host was not deleted; this is a functional correctness bug, not a style issue. (This file was not part of the PR diff per the report, so verification relies on inspecting the current post-PR source at the referenced lines.)

**How to replicate.** 1) Create an EmbeddableHost record. 2) Ensure destruction will fail: add/enable a `before_destroy` callback that throws `:abort`, or create dependent rows with a restrictive foreign key so the DB rejects delete. 3) Call the admin destroy endpoint for that host (DELETE request to the controller action). Expected: non-success response (e.g., 422/500) and an error JSON; Actual: success JSON is returned while the record still exists when you reload/check the database.

**Found by** 2 cells (2 distinct report texts, 2 findings): opus: CE·medium; sol: MRV·medium

#### B31 — EmbedController authorization can be bypassed by forging the Referer header

**Location:** `app/controllers/embedcontroller.rb:61–75`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The controller’s embeddable gate is implemented by checking only a client-supplied header: `embeddable_host.host_allowed?(request.referer)` (per the report, in/around `ensure_embeddable`). Since `Referer` is not an authenticated signal and can be freely set by non-browser HTTP clients (curl/requests/Postman), an attacker can bypass the intended “only allowed hosts may embed” restriction simply by sending a forged `Referer: https://<allowed-host>/`. The same area is also described as CSRF-exempt (`skip_before_filter :verify_authenticity_token`), which removes an additional browser-side safeguard and makes header-forgery exploitation straightforward.

**How to replicate.** 1) Configure Discourse embedding with at least one allowed embeddable host (e.g., `allowed.example`). 2) From any machine, use curl to call the embed endpoints directly (e.g., the topic comments/count endpoint under `EmbedController`) while forging the header: `curl -H 'Referer: https://allowed.example/' 'https://<forum-host>/<embed-endpoint>?topic_id=<id-or-slug>'`. 3) Expected: request is rejected when not actually originating from an allowed embed host context. Actual: request is authorized and returns embed content (comments/count) solely because the forged Referer passes `host_allowed?`, enabling anyone who knows an allowed hostname to read embed content without controlling that host.

**Found by** 2 cells (2 distinct report texts, 2 findings): sonnet: MRV·low; glm-vis: MRV·medium

#### B32 — Failed host.save leaves rejected buffered edits applied locally (no rollback on save error)

**Location:** `assets/javascripts/discourse/controllers/admin-graphite-hosts.js.es6:86–121`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The reported code path calls `host.save(props)` where `props` are the buffered edit values, which (in Ember Data) assigns those attributes onto the live record before the request is resolved. The `.catch(...)` handler only shows an alert and does not call `host.rollbackAttributes()`/restore the pre-edit state, so after a 422/failed save the record remains mutated in memory. When the user later clicks “cancel” (which rolls back only the buffer), the UI re-renders from the already-mutated record and shows the rejected values as if they persisted.

**How to replicate.** 1) In the admin UI for Graphite hosts, edit an existing host row (change host to an invalid format that the backend rejects) and click Save. 2) Ensure the server responds with a validation error (e.g., HTTP 422). 3) Observe that an error/alert is shown but the row’s displayed host/category values are now the attempted (invalid) edits. 4) Click Cancel: expected behavior is that the row returns to the original saved values; actual behavior is that it continues to display the rejected edits because the underlying record was mutated by `host.save(props)` and never rolled back on failure.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·high

#### B33 — Admin embedding route calls store.find without an id, causing findAll-style parsing and an empty model

**Location:** `assets/javascripts/discourse/routes/admin-embedding.js.es6:6–9`  ·  **Severity:** high  ·  **Judge confidence:** 0.58

**Why this is real.** The route’s model hook loads the record via a call equivalent to `return this.store.find('embedding');` (no id). In Discourse’s store implementation, a `find` without an id is routed to the `findAll` code path, which extracts results from the plural root key (e.g. `embeddings`). However the backend `show` endpoint returns a singleton under the singular root key (`embedding`), so the store resolves the model as empty/undefined and downstream template checks like `{{if embedding.embeddablehosts}}` never become truthy.

**How to replicate.** 1) In the browser, navigate to the plugin’s admin embedding page (the route that uses `admin-embedding.js.es6`). 2) Observe in the network tab that the request hits the singleton `show` endpoint and returns JSON shaped like `{ "embedding": { ... } }`. 3) Despite the response, the page never renders the embeddable hosts table/section because the route’s model resolves to an empty result (it was parsed as a collection expecting `{ "embeddings": [...] }`). Expected: the embedding record loads and `embedding.embeddablehosts` drives the table; Actual: model stays empty and the table never appears.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: MRV·high

#### B34 — Admin /admin/customize/embedding route crashes because it queries an unregistered Ember model type

**Location:** `app/assets/javascripts/discourse/app/routes/admin-customize-embedding.js:7–9`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The new admin route calls Ember Data with an unknown type, e.g. `model() { return this.store.find('embedding'); }`. Discourse's store resolves model classes via container lookup (`model:<type>`), and this PR does not add a corresponding `embedding` model file (e.g. `app/assets/javascripts/discourse/app/models/embedding.js`) or any registration, so the lookup fails and the route throws instead of rendering an empty page/tab. The file containing the store implementation is not in this PR’s diff, so verification relies on the reported behavior plus checking that no `embedding` model is added in the PR tree.

**How to replicate.** 1) Apply the PR and boot the app in development. 2) Log in as an admin and navigate directly to `/admin/customize/embedding` (or click the new Embedding tab under Admin > Customize if present). 3) Observe the route transition fails with a JS exception about missing/unknown model type `embedding` (container cannot resolve `model:embedding`). Expected: the page loads (even if empty) without throwing; Actual: the admin tab is unreachable due to the exception.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: MRV·low

#### B35 — Delete action can fire multiple concurrent destroyRecord requests (no in-flight guard)

**Location:** `app/assets/javascripts/admin/components/embeddable-host.js.es6:43–51`  ·  **Severity:** medium  ·  **Judge confidence:** 0.78

**Why this is real.** In the `delete()` action, the code unconditionally calls `this.get('host').destroyRecord().then(...)` inside the confirm callback: `if (result) { this.get('host').destroyRecord().then(() => { ... }); }`. There is no state flag/check (e.g., `isDeleting`), no promise reuse, and no disabling of the delete control, so repeated clicks/confirms before the first request resolves can enqueue multiple `destroyRecord()` calls for the same record. This can lead to duplicate DELETE requests, inconsistent UI state, and avoidable backend errors (e.g., 404 on the second delete).

**How to replicate.** 1) In the admin UI where this component is used (embeddable host row), click the delete control for a host. 2) Before the first DELETE request finishes, trigger delete again (e.g., double-click the delete button quickly and confirm both bootbox dialogs, or click delete repeatedly if the UI allows). 3) Observe in the browser network panel that multiple DELETE requests are sent for the same host. Expected: once deletion is initiated, subsequent delete attempts are blocked/disabled until completion; Actual: multiple concurrent deletions can be initiated, potentially causing errors or double-remove logic.

**Found by** 1 cells (1 distinct report texts, 1 findings): sonnet: MRV·low

#### B36 — Unhandled promise rejection when saving admin embedding settings (update promise not handled)

**Location:** `app/assets/javascripts/admin/controllers/admin-embedding.js.es6:6–7`  ·  **Severity:** medium  ·  **Judge confidence:** 0.62

**Why this is real.** The reported code calls `embedding.update({ ... })` (around line 6) but does not return it or attach any `.then(...)`/`.catch(...)`/`await` handling. If the update request fails (e.g., server returns 4xx/5xx or the network errors), the promise rejection is unhandled and the controller never shows an error to the user. The PR diff was not provided for this file, so this verification relies on the reviewers' referenced line and the described missing promise handling at that call site.

**How to replicate.** In the admin UI page that uses `admin-embedding` controller, attempt to save embedding settings while forcing the request to fail (e.g., temporarily break the endpoint, return 500, or go offline in DevTools). Expected: the UI shows an error/flash explaining the save failed and no console errors. Actual: a console "Unhandled Promise Rejection" occurs and the user receives no clear failure feedback (save appears to silently fail).

**Found by** 1 cells (1 distinct report texts, 1 findings): opus: CE·medium

#### B37 — Embeddable hosts table header renders even when list is empty due to truthy empty array in Ember {{if}}

**Location:** `app/assets/javascripts/admin/templates/embedding.hbs:1–12`  ·  **Severity:** low  ·  **Judge confidence:** 0.74

**Why this is real.** The template reportedly guards the embeddable-hosts table with `{{#if embedding.embeddablehosts}} ... {{/if}}`. In Ember/Handlebars, an empty array is still truthy, so when `embedding.embeddablehosts` is `[]` (hydrated but empty), the block renders, showing the table/header with no rows. The PR diff does not include this file, so this verification relies on the reported code path and Ember truthiness semantics.

**How to replicate.** 1) Ensure the Embeddable Hosts list is empty (no hosts configured) but the property is present as an empty array (typical after hydration). 2) Navigate to the admin embedding page that uses `admin/templates/embedding.hbs`. 3) Actual: the embeddable-hosts table header/structure renders with no rows underneath. Expected: the entire table (including header) should be hidden when there are zero hosts (e.g., using `{{#if embedding.embeddablehosts.length}}` or an `{{#each}}`-based empty state).

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: van·medium

#### B38 — Embed allowlist check does not scope requested topic/embed_url to the referer host's permitted category

**Location:** `app/controllers/embedcontroller.rb:61–75`  ·  **Severity:** high  ·  **Judge confidence:** 0.63

**Why this is real.** The reported issue is that `hostallowed?` only validates that the request `Referer` matches an allowed/embeddable host, but does not verify that the requested `embed_url`/`topic_id` belongs to a topic/category configured for that specific host. As a result, once any host is on the allowlist, it can request embeds for topics associated with other embeddable hosts/categories (authorization bypass via mismatched scoping). This verification is based on the report because `embedcontroller.rb` is not included in this PR’s diff, so the exact lines must be confirmed by inspecting the post-PR file around line ~61.

**How to replicate.** 1) Configure Discourse embedding with at least two allowed embeddable hosts (e.g., hostA.com -> Category A, hostB.com -> Category B) and ensure both are enabled. 2) On hostA.com, create an embed request pointing to a topic in Category B (or directly request the embed endpoint with `topic_id`/`embed_url` for a Category B topic while sending a `Referer: https://hostA.com/...`). 3) Expected: the controller rejects the request because hostA is not authorized for that topic/category. Actual (per report): the request succeeds because only the referer host is checked; the topic/embed_url is not constrained to hostA’s category mapping.

**Found by** 1 cells (1 distinct report texts, 1 findings): opus: CE·medium

#### B39 — (untitled)

**Location:** `?` (exact lines not in diff)  ·  **Severity:** ?  ·  **Judge confidence:** 0.00

**Why this is real.** (missing)

**Found by** 1 cells (1 distinct report texts, 1 findings): fable: CE·medium

#### B40 — Migration splits embeddable host list on newlines instead of pipe delimiter, losing hosts

**Location:** `db/migrate/20150818190757createembeddablehosts.rb:22–31`  ·  **Severity:** high  ·  **Judge confidence:** 0.60

**Why this is real.** The migration reads the existing SiteSetting value and splits it using a newline delimiter (e.g., `...split("\n")` around line 22), but Discourse list-type settings are persisted pipe-delimited (per `app/models/sitesetting.rb` using `setting.split('|')`). If the stored value is `a.com|b.com`, splitting on `\n` produces a single element `"a.com|b.com"`, so only one EmbeddableHost row is created with an invalid host string. The migration then deletes/clears the original setting value (reported at line 31), making the data loss permanent after the migration runs.

**How to replicate.** 1) Before running the migration, set the `embeddable_hosts` site setting through the list editor to two hosts (e.g., enter `a.com` and `b.com`), which persists as `a.com|b.com`.
2) Run the migration that creates EmbeddableHost records.
3) Inspect the created rows: expected two rows (`a.com` and `b.com`), but actual is one row with `host = "a.com|b.com"`.
4) Verify that embedding for either `a.com` or `b.com` no longer matches, and that the original `embeddable_hosts` setting has been cleared/removed so the original list cannot be recovered automatically.

**Found by** 1 cells (1 distinct report texts, 1 findings): fable: MRV·medium

#### B41 — EmbeddableHost missing presence validation for non-null category_id causes DB NotNullViolation

**Location:** `app/models/embeddable_host.rb:1–30`  ·  **Severity:** medium  ·  **Judge confidence:** 0.62

**Why this is real.** The reports indicate the `embeddable_hosts.category_id` column is defined with `null: false` at the database level, but the `EmbeddableHost` model does not validate presence of `category_id` (e.g., it may validate other fields like `host` but lacks `validates :category_id, presence: true`). This mismatch means that creation/update paths that bypass controller strong-params (e.g., Rails console, seeds, background jobs, tests, or any code doing `EmbeddableHost.create!(host: ...)` without `category_id`) will raise an `ActiveRecord::NotNullViolation` instead of returning a clean model validation error. The file is not part of this PR’s diff, so verification relies on reading the current model validations and the schema/migration for the `embeddable_hosts` table.

**How to replicate.** 1) Open a Rails console in the app. 2) Run `EmbeddableHost.create!(host: "example.com")` (omit `category_id`). 3) Actual: the save hits the DB and raises `ActiveRecord::NotNullViolation` (or similar) because `category_id` is NULL. 4) Expected: `EmbeddableHost` should fail validation with an error on `category_id` (e.g., `embeddable_host.errors[:category_id]` includes "can't be blank") and not raise a database exception.

**Found by** 1 cells (1 distinct report texts, 1 findings): opus: van·xhigh

---

## PR 8 — 30 distinct real bugs (6 goldens + 24 the goldens missed)
(<https://github.com/ai-code-review-evaluation/discourse-graphite/pull/8>)

### Bug index

| # | sev | location | title | found by (cells) |
|---|---|---|---|---|
| B1 | high | `app/controllers/groups_controller.rb` | Unvalidated limit/offset in GroupsController#members allows negative SQL OFFSET and unbounded LIMIT | 55 |
| B2 | high | `app/controllers/admin/groups_controller.rb:170–175` | Updating a group without `visible` param unintentionally flips visibility to false | 53 |
| B3 | high | `app/controllers/admin/groupscontroller.rb:24–45` | Admin groups create/update regress to flat params, breaking legacy group:{...} payloads and causing silent no-op/visibility reset | 30 |
| B4 | medium | `app/controllers/admin/groups_controller.rb:22–35` | Admin group creation drops submitted aliaslevel and saves default instead | 29 |
| B5 | high | `app/assets/javascripts/discourse/models/group.js:25–45` | Out-of-order findMembers() responses can overwrite newer pagination state and show the wrong member page | 29 |
| B6 | medium | `app/assets/javascripts/discourse/models/group.js:21–52` | Removing the only member on the last page reloads members with a stale, now-out-of-range offset and shows an empty page | 29 |
| B7 | medium | `app/controllers/admin/groups_controller.rb:71–86` | Admin::GroupsController#add_members splits usernames without trimming, causing spaced names to be skipped while still returning success | 27 |
| B8 | medium | `app/assets/javascripts/admin/controllers/admin-group.js.es6:13–16` | Admin group members pagination creates a phantom extra page when member count is an exact multiple of page size | 26 |
| B9 | medium | `app/assets/javascripts/admin/controllers/admin-group.js.es6:56–75` | Admin group add/remove member actions drop the AJAX promise, making failures silent and leaving stale UI state | 25 |
| B10 | medium | `app/assets/javascripts/discourse/routes/group-members.js.es6:11–16` | Group members fetch is fired-and-forgotten in route, so errors are silently swallowed and UI can show empty/stale members | 22 |
| B11 | high | `app/controllers/admin/groupscontroller.rb:73–82` | Admin::GroupsController#remove_member deletes association with userid (integer) and persists removal before save, causing exceptions or partial failures | 21 |
| B12 | high | `app/controllers/admin/groupscontroller.rb:34–36` | PATCH updates unintentionally hide groups when `visible` param is omitted (and legacy membership changes are ignored) | 20 |
| B13 | high | `app/assets/javascripts/admin/templates/groupmember.hbs:1–6` | Remove-member link wrongly shown for automatic groups due to `automatic` resolving in member item context | 19 |
| B14 | medium | `app/controllers/admin/groups_controller.rb:71–71` | add_members crashes with 500 when `usernames` param is an array (calls `.split` on Array) | 17 |
| B15 | medium | `app/assets/javascripts/admin/controllers/admin-group.js.es6:61–66` | Admin group addMembers leaves usernames input uncleared, causing stale re-submissions (even after switching groups) | 16 |
| B16 | high | `app/assets/javascripts/discourse/models/group.js:23–52` | Group members reload/pagination uses live-edited group name, breaking after unsaved rename | 9 |
| B17 | medium | `spec/controllers/admin/groups_controller_spec.rb:38–125` | Admin::GroupsController specs hardcode group id=1, implicitly depending on seeded automatic group | 5 |
| B18 | medium | `app/controllers/admin/groupscontroller.rb:71–86` | Admin group addmembers accepts unbounded comma-separated usernames, causing N+1 queries and long-running request | 5 |
| B19 | medium | `spec/controllers/admin/groups_controller_spec.rb:74–130` | Admin::GroupsController spec regression: removed coverage for add/remove member edge cases and paginated members meta shape | 4 |
| B20 | medium | `app/controllers/admin/groups_controller.rb:40–45` | Group name is stripped on create but not on update, allowing whitespace-padded names | 4 |
| B21 | high | `app/assets/javascripts/discourse/templates/admin/group.hbs:1–53` | Admin group edit form implicitly submits on Enter, causing full page reload and lost unsaved changes | 4 |
| B22 | high | `app/assets/javascripts/discourse/models/group.js:21–24` | group.findMembers returns undefined on empty name instead of a promise | 2 |
| B23 | high | `app/controllers/admin/groups_controller.rb:-1–-1` | Admin addmembers can re-add existing user and raise RecordNotUnique, leaving partial membership updates | 1 |
| B24 | high | `config/routes.rb:49–50` | Admin group addmembers route passes :id but controller requires :groupid, causing 400 ParameterMissing | 1 |
| B25 | medium | `N/A (template containing the new form markup is not present in the provided PR diff; issue is identified from the report only)` | Label `for="name"` does not match the Ember `text-field` input id, breaking label-to-input association | 1 |
| B26 | high | `config/routes.rb:1–1` | Admin groups API no longer exposes GET /admin/groups/:id/users (route removed without read replacement) | 1 |
| B27 | medium | `app/assets/javascripts/admin/controllers/admin-group.js.es6:29–38` | `next` pagination can set offset to `user_count`, yielding an empty/out-of-range page | 1 |
| B28 | medium | `app/controllers/groups_controller.rb:320–360` | Group membership endpoints unnecessarily call group.save after mutating users association | 1 |
| B29 | medium | `admin/templates/group.hbs:14–14` | Admin group template bypasses userCountDisplay and renders raw zero user_count | 1 |
| B30 | ? | `?` | (untitled) | 1 |

### Verification cards

#### B1 — Unvalidated limit/offset in GroupsController#members allows negative SQL OFFSET and unbounded LIMIT

**Location:** `app/controllers/groups_controller.rb` (exact lines not in diff)  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The clustered reports consistently describe `members` reading pagination directly from request params (e.g., `limit = params[:limit].to_i` and `offset = params[:offset].to_i`) and passing them straight into an ActiveRecord query via `.limit(limit).offset(offset)` with no clamping/validation. A negative `offset` is then sent to PostgreSQL as `OFFSET -1`, which raises a SQL error and yields a 500 response; similarly, an arbitrarily large `limit` can force huge queries/serialization. The PR diff does not include this file, so exact line numbers cannot be cross-checked here; verification requires opening the post-PR `GroupsController#members` implementation and confirming the unvalidated param-to-query flow.

**How to replicate.** 1) Run the app and ensure there is a group with members. 2) Send a request to the members endpoint (e.g., `GET /groups/<group_id>/members.json?offset=-1`). 3) Observe actual behavior: the request triggers a server error (500) due to invalid SQL OFFSET. Expected behavior: the controller should reject invalid pagination (400) or clamp offset to 0. 4) Also test `GET /groups/<group_id>/members.json?limit=1000000` and observe excessive query/serialization time or resource usage; expected behavior is enforcing a reasonable maximum limit.

**Found by** 55 cells (147 distinct report texts, 147 findings): fable: van·high, van·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; sonnet: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·low, van·medium; terra: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; astra: CE·low

#### B2 — Updating a group without `visible` param unintentionally flips visibility to false

**Location:** `app/controllers/admin/groups_controller.rb:170–175`  ·  **Severity:** high  ·  **Judge confidence:** 0.62  ·  ⚠️ `distinct=false` (cluster may span two bugs)

**Why this is real.** The update logic reportedly assigns visibility unconditionally: `group.visible = params[:visible] == "true"`. When `params[:visible]` is absent (nil), this expression evaluates to `false`, so any PATCH/PUT that updates other fields will silently set `group.visible` to false. This is a functional behavior change (state corruption) compared to guarded assignments used for other optional params.

**How to replicate.** 1) Pick an existing group that is currently visible (public). 2) Send `PATCH /admin/groups/:id.json` with a payload that updates some other attribute (e.g., `{ "name": "new-name" }`) and omit the `visible` parameter entirely. 3) Expected: visibility remains unchanged. Actual: the group becomes invisible because `params[:visible]` is nil and the controller sets `visible` to false.

**Found by** 53 cells (151 distinct report texts, 151 findings): fable: van·high, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium, van·xhigh; sonnet: CE·medium, MRV·high, MRV·medium, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; terra: CE·low, CE·medium, MRV·high, MRV·medium, van·low, van·xhigh; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium

#### B3 — Admin groups create/update regress to flat params, breaking legacy group:{...} payloads and causing silent no-op/visibility reset

**Location:** `app/controllers/admin/groupscontroller.rb:24–45`  ·  **Severity:** high  ·  **Judge confidence:** 0.68

**Why this is real.** Multiple reports point to the same regression localized to the create/update actions around lines 24 and 37: the controller now reads permitted attributes from the top-level params instead of the established nested envelope (e.g., expecting `name` rather than `params[:group][:name]`). As a result, callers sending the long-supported payload `group: {...}` (and PATCH membership changes like `changes[:add]/changes[:delete]`) will have their fields ignored; the request can still return success, and for updates a missing `visible` parameter can be treated as false, unexpectedly hiding a group. The PR diff for this file is not available in the provided patch excerpt, so verification is based on the consistent line-referenced reports and should be confirmed by inspecting the post-PR controller code at the referenced lines.

**How to replicate.** 1) In post-PR code, inspect `Admin::GroupsController#create` (~line 24) and confirm it permits/reads flat params (e.g., `params.permit(:name, ...)`) rather than `params.require(:group).permit(...)`.
2) Send POST /admin/groups with a legacy payload: `{ "group": { "name": "legacy-group", "visible": true } }`.
   Expected (pre-regression): group created with name "legacy-group".
   Actual (post-regression): validation error for blank name or group created without the intended attributes.
3) Inspect `#update` (~line 37) and confirm it also reads flat params and/or assigns `visible` such that omission becomes false.
4) Send PUT/PATCH /admin/groups/:id with `{ "group": { "visible": true } }` and/or omit `visible` while updating another field.
   Expected: only provided fields change; omission should not flip visibility.
   Actual: update silently no-ops (fields ignored) and/or `visible` becomes false when omitted.
5) If the controller previously supported incremental membership updates, send PATCH with `{ "changes": { "add": ["user1"], "delete": [] } }` and observe it returns success but makes no membership changes.

**Found by** 30 cells (48 distinct report texts, 48 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·medium, van·xhigh; sonnet: MRV·high, MRV·low; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·low, MRV·high, MRV·low, MRV·medium, van·high, van·medium; sol: CE·high, CE·medium, MRV·high, MRV·medium, van·high; terra: CE·medium, MRV·high; astra: CE·low, MRV·high, MRV·low

#### B4 — Admin group creation drops submitted aliaslevel and saves default instead

**Location:** `app/controllers/admin/groups_controller.rb:22–35`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** In the `create` action, the new group is instantiated using only `params[:name]` and `params[:visible]` (e.g., `Group.new(name: params[:name], visible: params[:visible])` / equivalent assignments) and then saved, but there is no read/assignment of `params[:aliaslevel]`. As a result, even if the client submits a non-default alias level, it is silently ignored and the persisted record retains the model/database default after save/reload. The PR diff for this file is not present in the provided patch, so this verification relies on the reported line reference and the described controller behavior.

**How to replicate.** 1) In the admin UI (or via HTTP), create a new group and set a non-default alias level in the form.
2) Submit the create request; ensure the request payload includes `aliaslevel=<non-default>`.
3) After creation, reload the group (or fetch it via API/admin page) and compare the saved alias level.
Expected: the group’s alias level matches the submitted value. Actual: the alias level is the default (the submitted `aliaslevel` was ignored during creation).

**Found by** 29 cells (48 distinct report texts, 48 findings): fable: van·high, van·medium; opus: CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium, van·xhigh; glm-flash: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium, van·xhigh; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium, van·medium; sol: van·high, van·low, van·medium, van·xhigh; terra: van·high, van·low; astra: CE·low

#### B5 — Out-of-order findMembers() responses can overwrite newer pagination state and show the wrong member page

**Location:** `app/assets/javascripts/discourse/models/group.js:25–45`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** In findMembers(), each call issues an AJAX request and then unconditionally applies the response to shared model state: `Discourse.ajax(...).then(function(result) { self.setProperties({ ... offset: result.meta.offset, members: ... }) });`. There is no sequencing/token check or cancellation, so if findMembers() is called twice (e.g., rapid next/previous clicks or a reload after add/remove), a slower earlier request can resolve after a later one and overwrite `offset` and `members` with stale data, making the UI jump back to an older page.

**How to replicate.** Open the group members UI and trigger two member-list reloads back-to-back with different offsets (e.g., click “Next” then immediately “Previous”, or click “Next” twice quickly; alternatively click Next then immediately remove/add a member which calls `self.findMembers()` again). Use network throttling (Slow 3G) so the first request resolves after the second. Expected: the UI shows the members for the most recent pagination action. Actual: when the older request finishes last, `setProperties` applies its `meta.offset` and `members`, reverting the UI to the wrong page.

**Found by** 29 cells (44 distinct report texts, 44 findings): opus: CE·high, CE·medium, MRV·high, MRV·low; sonnet: MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·medium, van·low; glm-vis: CE·high; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·xhigh; terra: CE·medium, MRV·medium, van·high; astra: CE·medium, MRV·high, MRV·low, MRV·medium, van·high

#### B6 — Removing the only member on the last page reloads members with a stale, now-out-of-range offset and shows an empty page

**Location:** `app/assets/javascripts/discourse/models/group.js:21–52`  ·  **Severity:** medium  ·  **Judge confidence:** 0.83

**Why this is real.** After a deletion, `removeMember` does `self.findMembers();` without adjusting pagination state. In `findMembers`, the offset sent to the server is clamped using the *current* (pre-refresh) `user_count`: `var self = this, offset = Math.min(this.get("user_count"), Math.max(this.get("offset"), 0));`. If the last page becomes empty after deletion (total shrinks), `this.get('user_count')` is stale, so the request reuses an offset that is now beyond the new last page, returning an empty `members` list and leaving the UI on a blank page instead of moving to the new last valid page.

**How to replicate.** 1) Create/choose a group with `limit`=50 and 51 members so there are 2 pages (offsets 0 and 50). 2) Navigate to the last page (offset=50) which contains the single remaining member. 3) Remove that member via the UI (calls `removeMember` -> DELETE -> `findMembers()`). 4) Observe the subsequent GET to `/groups/<name>/members.json` uses `offset=50` (computed from stale `user_count=51`) even though the new total is 50, so the page renders with an empty member list. Expected: offset should clamp to the new last page boundary (offset 0) and show the remaining members.

**Found by** 29 cells (42 distinct report texts, 42 findings): fable: van·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; sonnet: MRV·medium; glm-flash: CE·high, CE·low, MRV·high, MRV·low, MRV·medium, van·high, van·medium; glm-vis: CE·high, CE·low, MRV·high, MRV·low, MRV·medium, van·low, van·medium; sol: CE·high, CE·medium, van·high, van·medium; terra: CE·medium, MRV·low, van·high, van·medium

#### B7 — Admin::GroupsController#add_members splits usernames without trimming, causing spaced names to be skipped while still returning success

**Location:** `app/controllers/admin/groups_controller.rb:71–86`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The add_members action (reported at ~line 71) takes the raw string and does `params[:usernames].split(",")` and then looks up each entry via an exact-match finder (e.g., `User.find_by_username(username)`), but it does not `strip` or reject blanks. As a result, input like "bob, alice" produces a second token " alice" (leading space), which will not match any real username and is silently skipped; the action still returns a success JSON response, giving no indication that one or more requested users were not added. The PR diff does not include this file, so this verification relies on the reviewers’ consistent line-referenced reports; a human can confirm by reading the add_members loop and observing the missing `strip`/blank filtering and unconditional success response.

**How to replicate.** 1) In the admin UI or via HTTP, call the group member add endpoint (e.g., POST /admin/groups/:id/add_members) with params user names string set to `"bob, alice"` (note the space after the comma).
2) Ensure both users exist with usernames exactly `bob` and `alice`.
3) Observe: only `bob` is added; `alice` is not added because the lookup is performed on the literal token `" alice"`.
4) The controller still returns a success JSON response (no error/warning), so the UI/API consumer cannot detect the partial failure from the response.

**Found by** 27 cells (51 distinct report texts, 51 findings): fable: van·medium; opus: CE·high, CE·low, CE·medium, MRV·medium, van·medium; sonnet: van·xhigh; glm-flash: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium; sol: CE·high, MRV·low, MRV·medium; terra: MRV·high; astra: MRV·high

#### B8 — Admin group members pagination creates a phantom extra page when member count is an exact multiple of page size

**Location:** `app/assets/javascripts/admin/controllers/admin-group.js.es6:13–16`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72

**Why this is real.** Multiple reviewers point to the same computation in this file around line 13: `totalPages = Math.floor(userCount / limit) + 1` (and related checks like `showingLast`). When `userCount % limit === 0`, `Math.floor(userCount/limit) + 1` overestimates by 1 (e.g., 100/50 -> 2 + 1 = 3), exposing a navigable extra page with no results and preventing `showingLast` from becoming true on the real last page. The PR diff does not include this file/hunk, so this verification relies on the consistent line-referenced reports rather than a shown patch.

**How to replicate.** 1) Ensure a group has a member count that is an exact multiple of the page size/limit used by the UI (e.g., 100 members with limit=50). 2) In the Discourse admin UI, open that group’s members list and use pagination to go to the last page. Expected: only 2 pages exist and the last page (page 2) is marked as last and contains members. Actual: UI allows navigating to page 3 (empty), and the ‘last page’ indicator logic (e.g., `showingLast`) does not trigger on page 2 because `totalPages` is inflated.

**Found by** 26 cells (63 distinct report texts, 63 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·medium, MRV·high, MRV·low, MRV·medium; astra: CE·high

#### B9 — Admin group add/remove member actions drop the AJAX promise, making failures silent and leaving stale UI state

**Location:** `app/assets/javascripts/admin/controllers/admin-group.js.es6:56–75`  ·  **Severity:** medium  ·  **Judge confidence:** 0.77

**Why this is real.** In the new actions, the controller triggers the mutation but does not return or handle the promise: inside `removeMember` it calls `self.get("model").removeMember(member);`, and in `addMembers` it calls `this.get("model").addMembers(this.get("usernames"));` without `return` or any `.catch(...)`/error handling. If the underlying AJAX request rejects (e.g., 422/404), the rejection is unhandled and no error feedback is shown, so the admin cannot tell the operation failed and the member list can remain unchanged/stale despite the UI action having been invoked.

**How to replicate.** 1) In the admin UI, open a group where membership mutations can fail (e.g., an automatic group, or attempt to remove a user who is not actually a member). 2) Click “Remove member” (confirm the bootbox) or use “Add members” with a username that triggers a server-side validation error. 3) Observe that no error is displayed to the admin and the UI provides no failure indication; the membership list remains unchanged even though the action was executed. Expected: the action should surface the failure (and/or only update/reload the member list after the promise resolves), and failures should be catchable/handled by callers.

**Found by** 25 cells (36 distinct report texts, 36 findings): opus: CE·high, CE·medium, MRV·low, MRV·medium; sonnet: MRV·high, MRV·medium; glm-flash: MRV·high, MRV·medium, van·low; glm-vis: MRV·high, MRV·medium; sol: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; terra: MRV·high, MRV·low, MRV·medium; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### B10 — Group members fetch is fired-and-forgotten in route, so errors are silently swallowed and UI can show empty/stale members

**Location:** `app/assets/javascripts/discourse/routes/group-members.js.es6:11–16`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** In the post-PR route, `setupController(...)` invokes the async load via a bare call like `model.findMembers();` (reported at ~line 11) and does not `return`/`await` it or attach an error handler (e.g. `.catch(popupAjaxError)`). Because the promise is discarded, route error handling does not run on rejection (403/404/network), and the controller renders with whatever initial/previous member state exists (often an empty table) with no visible error, which is a functional defect rather than a style issue. (The PR diff for the underlying `findMembers` implementation is not included in this PR; verification relies on the reported call-site behavior.)

**How to replicate.** 1) Navigate to a group members page that will fail to load members (e.g., a hidden/private group where the members endpoint returns 403, or simulate a network error in DevTools by going offline before the XHR). 2) Observe the members list: expected behavior is an error state/flash (popupAjaxError) or routed error handling; actual behavior is the page renders with an empty members table (or stale previous members) and no error indication. 3) Optional: click Next/Previous rapidly; expected behavior is serialized/predictable pagination, but actual behavior can show transient 0/0 counts or out-of-order results because overlapping requests race and the last response wins.

**Found by** 22 cells (31 distinct report texts, 31 findings): fable: van·medium; opus: CE·high, CE·medium, MRV·high, MRV·medium; sonnet: MRV·high, MRV·low, MRV·medium; glm-flash: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high; sol: CE·medium, MRV·high, MRV·low; astra: CE·high, CE·medium

#### B11 — Admin::GroupsController#remove_member deletes association with userid (integer) and persists removal before save, causing exceptions or partial failures

**Location:** `app/controllers/admin/groupscontroller.rb:73–82`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The controller code reportedly calls `group.users.delete(userid)` inside the member-removal action (around lines 73–82). In ActiveRecord, `has_many` association `delete` is intended to take model instances (or relation), and passing a raw integer id can raise `ActiveRecord::AssociationTypeMismatch` instead of removing the user. Additionally, the removal via `group.users.delete(...)` is applied immediately to the join table, but the action then uses `group.save` as the success signal—so if `group.save` fails (422), the membership may already have been removed, creating an inconsistent/partial update.

**How to replicate.** 1) Find the admin endpoint/action in `Admin::GroupsController` responsible for removing a member (the one containing `group.users.delete(userid)` and checking `group.save`). 2) Trigger it with a request where `userid` is an integer param (e.g., remove a real user from a real group). Expected: member is removed cleanly (200/204) and counters/callbacks remain consistent. Actual: (a) it may raise `ActiveRecord::AssociationTypeMismatch` and return 500, or (b) if `group.save` fails validations, the request returns 422 even though the membership was already deleted from the join table.

**Found by** 21 cells (27 distinct report texts, 27 findings): opus: CE·high, CE·low, CE·medium, van·high, van·xhigh; sonnet: MRV·high, MRV·medium, van·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·medium; glm-vis: CE·high, CE·medium, MRV·medium; sol: MRV·low, MRV·medium, van·low, van·medium; terra: van·high, van·low

#### B12 — PATCH updates unintentionally hide groups when `visible` param is omitted (and legacy membership changes are ignored)

**Location:** `app/controllers/admin/groupscontroller.rb:34–36`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple reports point to an unconditional assignment in the update path around line 34: `group.visible = params[:visible] == "true"`. When a PATCH request omits the `visible` key (common for partial updates and legacy membership PATCHes), `params[:visible]` is nil so the expression evaluates to false, silently flipping an existing visible group to invisible; the same legacy requests may include `changes.add`/`changes.delete`, which the ordinary update handler does not process, so membership changes are dropped while the request still succeeds. The PR diff is not available here, so this verification relies on the consistent line-specific reports.

**How to replicate.** 1) Ensure an existing group has `visible = true`. 2) Send `PATCH /admin/groups/:id` with a body that updates something other than visibility (e.g., name) and omit `visible` entirely (or send a legacy membership payload like `{ changes: { add: ["user1"] } }` without `visible`). 3) Observe: expected behavior is that visibility remains unchanged (and membership changes apply for the legacy payload). Actual behavior is that `visible` becomes false (group is hidden) and, for the legacy payload, membership does not change even though the response indicates success.

**Found by** 20 cells (48 distinct report texts, 48 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·medium, van·low, van·medium; glm-flash: CE·high, MRV·high, MRV·medium, van·low, van·medium; glm-vis: CE·medium, MRV·high, MRV·medium; sol: CE·low, MRV·medium; astra: MRV·low, van·high, van·medium

#### B13 — Remove-member link wrongly shown for automatic groups due to `automatic` resolving in member item context

**Location:** `app/assets/javascripts/admin/templates/groupmember.hbs:1–6`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The template guards the remove link with `{{unless automatic}} ... {{action removemember this}} ... {{/unless}}`. In this template the rendering context is a single group member (a user), not the group itself, so `automatic` is not a property on the current context and resolves to `undefined`/falsey; as a result the `unless` condition always passes and the remove link renders even for automatic groups. This is functional breakage (wrong UI state and a failing action), not a style concern; the PR diff does not include this file, so this conclusion relies on the reported template contents and Ember/Handlebars context resolution rules.

**How to replicate.** 1) In the admin UI, open an automatic group (e.g., a system/automatic group) and navigate to its Members list. 2) Observe that each member row shows a “remove” control/link even though automatic groups should not allow manual removals. 3) Click the remove control: expected behavior is that no remove option is available (or it is disabled/hidden) for automatic groups; actual behavior is that the UI offers removal and the request fails (commonly a 422 from the server) because automatic group membership cannot be removed.

**Found by** 19 cells (26 distinct report texts, 26 findings): fable: van·low; opus: CE·low, MRV·low, van·high, van·low; sonnet: CE·high, CE·low, MRV·low; glm-flash: CE·high, CE·low, CE·medium, van·low, van·medium, van·xhigh; glm-vis: CE·low, MRV·low, MRV·medium, van·high; sol: van·low

#### B14 — add_members crashes with 500 when `usernames` param is an array (calls `.split` on Array)

**Location:** `app/controllers/admin/groups_controller.rb:71–71`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The `add_members` action calls `params.require(:usernames).split(",")` (as referenced by multiple reports at/around line 71). `params.require(:usernames)` can legitimately be an Array when the client submits `usernames[]=a&usernames[]=b` (or JSON `{"usernames":[...]}`), and Arrays do not implement `split`, causing a `NoMethodError` and an unhandled 500 instead of a validation error (400/422). The PR diff provided here does not include this file, so this verification relies on the consistent line-referenced evidence from the reports.

**How to replicate.** 1) Locate `app/controllers/admin/groups_controller.rb` and find the `add_members` (or similarly named) action near line 71. Confirm it does `params.require(:usernames).split(",")`.
2) Trigger the endpoint as an admin (route typically resembles POST `/admin/groups/:id/members` or `/admin/groups/:id/add-members`; use the controller action name to confirm the exact path).
3) Send `usernames` as an array (e.g., form-encoded `usernames[]=alice&usernames[]=bob` or JSON body `{ "usernames": ["alice", "bob"] }`).
Expected: request is handled or rejected with 400/422 and a helpful message about invalid parameter type.
Actual: Rails raises `NoMethodError: undefined method 'split' for Array` and returns 500.

**Found by** 17 cells (22 distinct report texts, 22 findings): opus: CE·high, CE·low, CE·medium, MRV·low, van·high, van·low, van·medium; sonnet: CE·medium; glm-flash: CE·high, CE·low, MRV·high, MRV·low, MRV·medium, van·low; glm-vis: CE·medium, MRV·medium; astra: MRV·low

#### B15 — Admin group addMembers leaves usernames input uncleared, causing stale re-submissions (even after switching groups)

**Location:** `app/assets/javascripts/admin/controllers/admin-group.js.es6:61–66`  ·  **Severity:** medium  ·  **Judge confidence:** 0.86

**Why this is real.** In the new `addMembers` action the controller never resets the `usernames` property after a successful add: `// TODO: should clear the input` followed by `this.get("model").addMembers(this.get("usernames"));` with no subsequent `this.set("usernames", ...)` or other clearing logic. Because `usernames` is now a simple controller field (`usernames: null`) rather than being recomputed from `members`, its value persists across actions and potentially across group changes, so the same stale usernames can be re-submitted unintentionally.

**How to replicate.** 1) In the admin group UI, enter one or more usernames in the add-members input (bound to `usernames`). 2) Click "Add" and wait for the request to succeed. 3) Observe the input still contains the same usernames (expected: it should clear/reset). 4) Click "Add" again (or navigate/switch to another group and click "Add"): actual behavior re-sends the same usernames again; expected behavior is that the field would be empty, preventing accidental duplicate or cross-group additions.

**Found by** 16 cells (20 distinct report texts, 20 findings): opus: MRV·high, van·xhigh; sonnet: van·low, van·medium; glm-flash: CE·high, MRV·high, van·high, van·low, van·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, van·medium; sol: CE·high, CE·medium

#### B16 — Group members reload/pagination uses live-edited group name, breaking after unsaved rename

**Location:** `app/assets/javascripts/discourse/models/group.js:23–52`  ·  **Severity:** high  ·  **Judge confidence:** 0.82

**Why this is real.** In `findMembers`, the members URL is built from the mutable, two-way-bound `name` field: `Discourse.ajax('/groups/' + this.get('name') + '/members.json', ...)`. However membership mutations use the persisted numeric id (`/admin/groups/` + `this.get('id')` + `/members.json`) and then call `self.findMembers();` to refresh. If an admin edits the group name in the UI but hasn’t saved yet, `this.get('name')` no longer matches the server’s current group slug, so the refresh/pagination request targets the wrong (or non-existent) group and fails or shows another group’s members.

**How to replicate.** 1) Go to the admin group editor for an existing group that has members. 2) In the name field, type a new name but do NOT click Save. 3) Add a member (or remove an existing member). 4) Observe network requests: the add/remove hits `/admin/groups/<id>/members.json` successfully, then the UI triggers a reload via `findMembers()` which requests `/groups/<unsaved-new-name>/members.json?limit=...&offset=...`. Expected: refreshed member list for the original group. Actual: 404 / empty list / or members from a different group if the unsaved name matches another group, leaving the UI stale or misleading.

**Found by** 9 cells (10 distinct report texts, 10 findings): opus: CE·high; glm-flash: MRV·high; glm-vis: CE·medium; sol: van·medium; astra: CE·high, CE·medium, MRV·high, MRV·low, van·high

#### B17 — Admin::GroupsController specs hardcode group id=1, implicitly depending on seeded automatic group

**Location:** `spec/controllers/admin/groups_controller_spec.rb:38–125`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The new/modified specs issue requests like `xhr :put, :addmembers, groupid: 1, usernames: "l77t"` and also directly reference `Group.find(1)` / params `id: 1`, assuming the group with id 1 exists and is an automatic group. This makes the tests depend on seed/fixture ordering: on a DB where id 1 is missing (or not automatic), the controller will raise/return not found or take a different code path, so the asserted 422 behavior is either never reached or the spec can pass/fail for the wrong reason. This is a real correctness bug in the test suite (nondeterministic/fixture-coupled), not a style issue; the evidence comes from the clustered reports since the relevant lines are in the spec file rather than the PR’s main code changes.

**How to replicate.** 1) Inspect `spec/controllers/admin/groups_controller_spec.rb` around the referenced lines and confirm the hardcoded `groupid: 1` / `id: 1` and any `Group.find(1)` usage in the "automatic group" related examples.
2) Run only this spec file in an environment where the test DB is not pre-seeded with an automatic group at id=1 (e.g., disable seeds/fixtures, or truncate then create a non-automatic group first so it gets id=1).
Expected: the spec should deterministically exercise the automatic-group guard and assert 422.
Actual: the request will 404/raise `ActiveRecord::RecordNotFound` (no id=1), or it will hit the non-automatic path (id=1 exists but isn’t automatic), making the asserted 422 either fail or be meaningless.

**Found by** 5 cells (7 distinct report texts, 7 findings): opus: MRV·high, van·low, van·medium, van·xhigh; glm-flash: MRV·low

#### B18 — Admin group addmembers accepts unbounded comma-separated usernames, causing N+1 queries and long-running request

**Location:** `app/controllers/admin/groupscontroller.rb:71–86`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The addmembers action reportedly does `params.require(:usernames).split(",")` and then iterates the resulting array, doing a per-username lookup (e.g., `User.find_by_username(...)`) and then a per-username add/insert (e.g., `@group.add(user)`), with no cap on the number of elements. Because there is no length limit on the `usernames` param, a single request containing thousands of comma-separated names triggers thousands of sequential DB operations in one controller action, which can tie up a web worker and database. Reports also note usernames are not stripped (e.g., " bob"), leading to missed lookups and silent skipping; this is input-handling logic, not a style issue. (The file is not in this PR diff, so verification relies on the reported code pattern at/around line 71.)

**How to replicate.** 1) As an authenticated admin, send a POST/PUT request to the group add-members endpoint that hits `Admin::GroupsController#addmembers` with `usernames` set to a very large comma-separated list (e.g., 10,000 entries like `user1,user2,...`). 2) Observe in logs/APM that the request runtime grows linearly and executes one user lookup plus one group-membership insert per username (thousands of queries/operations). Expected: the controller should reject or cap overly large lists (and normalize/strip whitespace) to prevent a single request from consuming excessive time/resources; actual: it attempts to process the entire list serially and may skip whitespace-padded usernames.

**Found by** 5 cells (5 distinct report texts, 5 findings): opus: CE·medium, MRV·medium; glm-flash: CE·medium, van·low; glm-vis: CE·low

#### B19 — Admin::GroupsController spec regression: removed coverage for add/remove member edge cases and paginated members meta shape

**Location:** `spec/controllers/admin/groups_controller_spec.rb:74–130`  ·  **Severity:** medium  ·  **Judge confidence:** 0.66

**Why this is real.** The reports point to a deletion in `spec/controllers/admin/groups_controller_spec.rb` around lines 74-130 where existing examples asserting "silent success" when adding non-existent usernames and removing non-members were removed and not replaced with equivalent specs for the new add/remove endpoints or the new paginated members response shape. This leaves key controller branches (unknown usernames, removing a non-member, adding an already-present member) and the `members + meta(total/limit/offset)` contract untested, so regressions in those code paths will not be caught by CI. This is a real, concrete test-suite defect (loss of assertions) rather than a style concern; it directly reduces coverage of behavior that the client pagination logic depends on.

**How to replicate.** 1) Open the post-PR `spec/controllers/admin/groups_controller_spec.rb` and inspect the section around lines ~74-130; confirm the prior examples covering (a) adding non-existent users and (b) removing non-members are no longer present, and that there are no new examples asserting the `members` response includes `meta.total`, `meta.limit`, and `meta.offset`.
2) Confirm by running `RAILS_ENV=test bundle exec rspec spec/controllers/admin/groups_controller_spec.rb` and noting there are no failing tests despite missing assertions.
3) Demonstrate impact: temporarily modify the controller to (a) error on unknown usernames or (b) omit `meta.total/limit/offset` from the members response; re-run the spec file—expected: tests should fail; actual: they will not (or will fail only for unrelated reasons), proving the behavior is currently unprotected.

**Found by** 4 cells (5 distinct report texts, 5 findings): fable: van·high; opus: van·medium, van·xhigh; glm-vis: MRV·medium

#### B20 — Group name is stripped on create but not on update, allowing whitespace-padded names

**Location:** `app/controllers/admin/groups_controller.rb:40–45`  ·  **Severity:** medium  ·  **Judge confidence:** 0.78

**Why this is real.** In the create path the controller normalizes the incoming name with `(params[:name] || '').strip`, but in the update path it assigns the raw parameter: `group.name = params[:name]` (no `strip`). This inconsistency means an admin can rename an existing group to `' bob '` and the update endpoint will attempt to persist the whitespace-padded name, either storing a dirty value or causing confusing validation failures. This is a real behavioral bug (inconsistent normalization between endpoints), not a style issue; the PR diff doesn’t include this file, so this verification relies on the reported code lines.

**How to replicate.** 1) Create a group via the admin UI/API with name `' bob '`; creation normalizes to `'bob'` due to `.strip`, so it succeeds with name `bob`.
2) Edit/rename that same group via the update endpoint, submitting name `' bob '` (leading/trailing spaces).
Expected: update behaves like create (normalizes to `bob`) and round-trips consistently.
Actual: update does not strip whitespace (`group.name = params[:name]`), so the group may be saved as `' bob '` or the update may fail validation with an error that doesn’t match create behavior, breaking consistency and potentially downstream features that assume normalized group names.

**Found by** 4 cells (4 distinct report texts, 4 findings): glm-flash: van·high; glm-vis: CE·high, CE·medium, MRV·low

#### B21 — Admin group edit form implicitly submits on Enter, causing full page reload and lost unsaved changes

**Location:** `app/assets/javascripts/discourse/templates/admin/group.hbs:1–53`  ·  **Severity:** high  ·  **Judge confidence:** 0.84

**Why this is real.** The template wraps editable inputs in a plain HTML form (`<form class="form-horizontal">`, line 1) but does not attach any submit handler (e.g., no `{{action ... on="submit"}}`) to prevent native submission. Inside that form are text inputs like `{{text-field name="name" ...}}` (line 8) and `{{user-selector ...}}` (line 28); pressing Enter in these fields triggers the browser’s implicit form submit to the current URL, causing a full page reload. The buttons also omit explicit `type="button"` (e.g., ` <button {{action "save"}} ...>` on line 47), so the form has no safe default behavior for submission via keyboard.

**How to replicate.** 1) Go to the Admin → Groups page and open an existing group for editing. 2) Change the group name in the name text field (or type a username in the add-members selector). 3) Press Enter while focused in that input. Expected: Ember handles the action (or at least no navigation occurs) and the page remains in-place. Actual: the browser performs a native form submission (GET to the current URL), the page reloads, and any unsaved edits (name/visibility/alias level) are discarded.

**Found by** 4 cells (4 distinct report texts, 4 findings): glm-flash: van·medium; glm-vis: CE·high, CE·medium, MRV·high

#### B22 — group.findMembers returns undefined on empty name instead of a promise

**Location:** `app/assets/javascripts/discourse/models/group.js:21–24`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** In the post-PR code path where the group has no name, `findMembers` now exits with a bare `return;` (i.e., returns `undefined`) rather than returning a resolved promise. This creates an inconsistent return type: callers that previously did `group.findMembers().then(...)` will now throw `TypeError: Cannot read properties of undefined (reading 'then')` when `name` is empty. This is a functional regression from the previously-reported behavior of returning something like `Ember.RSVP.resolve([])` for the empty-name case; verification can be done by reading the early-return branch in `group.js` around the reported line.

**How to replicate.** 1) In the codebase at this PR’s HEAD, open `app/assets/javascripts/discourse/models/group.js` and locate `findMembers` around line 21.
2) Observe the guard for an empty/falsey group name (e.g., `if (!this.name) { return; }`).
3) From any caller (or in console/tests), create a new/unsaved group model with no `name` and call `group.findMembers().then(...)`.
Expected: the `.then(...)` runs with an empty array (or at least `findMembers` returns a promise). Actual: `findMembers()` returns `undefined`, so chaining `.then` throws and the empty-member-list case is not produced.

**Found by** 2 cells (2 distinct report texts, 2 findings): opus: CE·low; glm-vis: MRV·low

#### B23 — Admin addmembers can re-add existing user and raise RecordNotUnique, leaving partial membership updates

**Location:** `app/controllers/admin/groups_controller.rb:-1–-1`  ·  **Severity:** high  ·  **Judge confidence:** 0.66

**Why this is real.** The clustered reports consistently describe `addmembers` iterating over a comma-separated username list and calling `group.add(user)` unconditionally (i.e., without checking whether the user is already a member). In Discourse-like schemas the group membership join table has a uniqueness constraint (e.g., `group_id,user_id`), so calling `group.add(user)` for an existing member attempts a duplicate insert and raises `ActiveRecord::RecordNotUnique`, producing a 500. Because this happens mid-loop, earlier usernames may already have been inserted, causing a partially-applied update with no clear admin feedback. The referenced code is not included in this PR diff, so verification is by inspecting the current `addmembers` implementation for an unconditional `group.add(user)` inside the usernames loop and lack of rescue/transactionality.

**How to replicate.** 1) In the admin UI/API, pick a group that already contains user A. 2) Trigger the add-members action (e.g., POST to the addmembers endpoint) with `usernames` including A (optionally along with other valid users like `A,B`). 3) Observe that the request returns HTTP 500 (from `ActiveRecord::RecordNotUnique`) when it hits A if `group.add(user)` tries to insert a duplicate join row; if multiple usernames were provided, users earlier in the list may have been added successfully before the failure. Expected behavior is idempotent adds (no error when adding an existing member) and/or an all-or-nothing update with a clear response.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·medium

#### B24 — Admin group addmembers route passes :id but controller requires :groupid, causing 400 ParameterMissing

**Location:** `config/routes.rb:49–50`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The routes add a member-style endpoint under admin groups (e.g., `resources :groups do ... put 'members' ... end` at config/routes.rb:49-50), which supplies the group key as `params[:id]` for requests like `PUT /admin/groups/:id/members.json`. The deduplicated reports indicate the `addmembers` action instead calls `params.require(:groupid)`, so every real request to this route raises `ActionController::ParameterMissing` and returns HTTP 400. This is a functional mismatch between the route parameter name and what the controller requires, not a style issue.

**How to replicate.** 1) In the admin UI, open a group and use the "Add members" action (or manually send `PUT /admin/groups/1/members.json` with a JSON body including the members list). 2) Observe the server responds 400 with `ActionController::ParameterMissing` because the request contains `params[:id]` (from the member route) but not `params[:groupid]`. Expected: members are added to the group and the endpoint returns success; actual: no members are added and the request fails with 400.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·medium

#### B25 — Label `for="name"` does not match the Ember `text-field` input id, breaking label-to-input association

**Location:** `N/A (template containing the new form markup is not present in the provided PR diff; issue is identified from the report only)` (exact lines not in diff)  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The reported template adds a label like `<label for="name">` but renders the field with `{{text-field name="name"}}`. In Ember/Discourse, `text-field` does not automatically set the DOM `id` from the `name` attribute; it typically generates an auto id (e.g., `ember123`). This means the label’s `for="name"` references no element id, so clicking the label won’t focus the input and assistive tech cannot programmatically associate them.

**How to replicate.** 1) Navigate to the page/dialog that contains the new form.
2) Inspect the rendered DOM: find the `<label for="name">` and the `<input ...>` produced by `{{text-field name="name"}}`.
3) Observe the input has an auto-generated `id` (e.g., `emberNNN`) rather than `id="name"`.
4) Click the “Name” label: expected focus moves to the corresponding input; actual behavior is no focus change because the `for` target id does not exist.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·high

#### B26 — Admin groups API no longer exposes GET /admin/groups/:id/users (route removed without read replacement)

**Location:** `config/routes.rb:1–1`  ·  **Severity:** high  ·  **Judge confidence:** 0.42

**Why this is real.** The clustered reports indicate that the admin group routing previously included a read endpoint like `get "users"` under `/admin/groups/:id/...`, but post-PR it has been removed and replaced only with write routes for membership (e.g., `put "members"` / `delete "members"`). With no remaining GET route for the member list, any existing client calling `/admin/groups/:id/users` will now hit a routing failure (404) even though it previously returned the group’s users. The PR evidence pack notes the relevant file/lines are not present in the PR diff, so verification requires inspecting the post-PR `config/routes.rb` directly for the missing `get "users"` route under the admin/groups resource.

**How to replicate.** 1) In the post-PR code, open `config/routes.rb` and locate the `namespace :admin` / `resources :groups` block. 2) Confirm there is no `get "users"` member route (or equivalent) for groups, and only `put/delete "members"` exist. 3) Run the app (or use `rails routes`) and request `GET /admin/groups/<id>/users.json` (or the non-json variant used previously). Expected (pre-PR): 200 with list of users in the group. Actual (post-PR): 404 / no route matches.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: MRV·medium

#### B27 — `next` pagination can set offset to `user_count`, yielding an empty/out-of-range page

**Location:** `app/assets/javascripts/admin/controllers/admin-group.js.es6:29–38`  ·  **Severity:** medium  ·  **Judge confidence:** 0.90

**Why this is real.** In the `next` action, the new offset is computed as `offset = Math.min(group.get("offset") + group.get("limit"), group.get("user_count"));` and then applied via `group.set("offset", offset);`. Offsets for paged queries are normally 0-based start indices, so the maximum valid offset is the start of the last page (e.g., `user_count - limit`, clamped to 0), not `user_count` itself. With the current clamp, `offset` can become exactly `user_count` (or otherwise past the last page start), which will request members starting beyond the final record and can produce an empty page.

**How to replicate.** 1) Use a group whose `user_count` is an exact multiple of `limit` (e.g., `user_count=100`, `limit=50`). 2) Navigate to the second page (offset becomes 50). 3) Click “Next”. Expected: either no navigation (already at last page) or offset stays at the last page start (50). Actual: `next` computes `Math.min(50+50, 100)=100` and sets `offset=100`, so `findMembers()` is called for an out-of-range start and the UI can show an empty member list/page.

**Found by** 1 cells (1 distinct report texts, 1 findings): opus: CE·medium

#### B28 — Group membership endpoints unnecessarily call group.save after mutating users association

**Location:** `app/controllers/groups_controller.rb:320–360`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** In the `add_members`/`remove_member` actions, the controller mutates the association (e.g., `group.users << user` / `group.users.delete(user)`) and then calls `group.save`. Persisting a `has_many`/`has_many :through` association write already inserts/deletes the join row; calling `group.save` again is unnecessary and can fail due to unrelated `Group` validations/callbacks, incorrectly turning a successful membership change into an error response. The PR diff does not include this file, so this verification relies on the reported offending pattern in the current post-PR tree.

**How to replicate.** 1) Find `add_members` (or similarly named) in `app/controllers/groups_controller.rb` and confirm it does `group.users << ...` followed by `group.save` (and likewise `group.users.delete(...)` followed by `group.save` in `remove_member`).
2) Create or modify a `Group` so that `group.save` can fail due to an unrelated validation/callback (e.g., a plugin/custom validation requiring some attribute to be present, or a callback that rejects saving under certain conditions), while the group record already exists.
3) Hit the membership endpoint (UI: add/remove a user from the group; or POST to the controller action).
Expected: membership is added/removed successfully regardless of unrelated group validations.
Actual: the request fails (and/or returns validation errors) because `group.save` is attempted after the association update.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: van·low

#### B29 — Admin group template bypasses userCountDisplay and renders raw zero user_count

**Location:** `admin/templates/group.hbs:14–14`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The model defines a dedicated presentation helper `userCountDisplay` with the explicit intent to hide ugly zeros: `// don't display zero its ugly` and `if (c > 0) { return c; }` (group.js around lines 12-16 in the PR). However, the admin group template reportedly renders the raw count via `{{usercount}}` (admin/templates/group.hbs:14) instead of using `userCountDisplay`, so groups with `user_count = 0` will display “(0)” and any UI derived from that raw value (like pagination labels) can show “0/0”. This creates two divergent display paths for the same datum (template vs. computed property), making the zero-hiding logic ineffective in the admin view and prone to drift.

**How to replicate.** 1) In the admin UI, create or open a group that has no members (user_count == 0). 2) Navigate to the admin group detail page that uses `admin/templates/group.hbs`. 3) Observe the member count / pagination area: expected behavior (per `userCountDisplay`) is to show nothing for the count when it is zero; actual behavior is that the template shows the raw `{{usercount}}` value, displaying “(0)” and potentially “0/0” pagination.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: CE·medium

#### B30 — (untitled)

**Location:** `?` (exact lines not in diff)  ·  **Severity:** ?  ·  **Judge confidence:** 0.00

**Why this is real.** (missing)

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: CE·high

---

## PR 14740 — 49 distinct real bugs (6 goldens + 43 the goldens missed)
(<https://github.com/calcom/cal.com/pull/14740>)

### Bug index

| # | sev | location | title | found by (cells) |
|---|---|---|---|---|
| B1 | high | `packages/trpc/server/routers/viewer/bookings.ts` | Calendar sync uses requesting user's credentials instead of the booking organizer's | 55 |
| B2 | high | `unknown (reports did not include a file path; PR diff not provided in evidence pack)` | Non-atomic guest/attendee persistence causes DB/calendar divergence on calendar sync failure | 55 |
| B3 | high | `apps/web/server/routers/viewer/bookings/addGuests.schema.ts:10–22` | addGuests input schema allows unbounded guests array (email/DB fan-out DoS vector) | 50 |
| B4 | high | `apps/web/server/lib/email-manager.ts:1–1` | Attendee/guest dedupe uses case-sensitive email comparisons, allowing duplicate attendees and false negatives | 45 |
| B5 | high | `addguests.handler.ts:160–175` | add-guests handler emails raw guests list instead of filtered uniqueGuests, causing duplicate/wrong notifications | 36 |
| B6 | medium | `apps/web/components/dialogs/AddGuestsDialog.tsx:29–50` | AddGuestsDialog leaves stale `isInvalidEmail` (and email input) state on success/close, showing old validation banner when reopened | 35 |
| B7 | medium | `apps/web/components/dialog/addguestsdialog.tsx:43–47` | AddGuestsDialog error toast fallback is unreachable; users see raw error codes/undefined prefix | 35 |
| B8 | high | `packages/trpc/server/routers/viewer/bookings/addGuests.handler.ts:1–200` | Add-guests endpoint allows adding guests to cancelled/rejected/past bookings (no booking state/time validation) | 34 |
| B9 | high | `packages/trpc/server/routers/viewer/bookings/addGuests.handler.ts:82–88` | addGuests crashes with unhandled Prisma P2025 when booking.userId is null (id coerced to 0) | 29 |
| B10 | critical | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:52–53` | Authorization bypass: any attendee can add arbitrary guests to a booking and trigger organizer calendar invites | 29 |
| B11 | high | `packages/trpc/server/routers/viewer/bookings/addGuests.handler.ts:52–55` | Team admin authorization check wrongly requires user to be both admin and owner (&& instead of \|\|) | 26 |
| B12 | high | `packages/emails/email-manager.ts:522–553` | Team-member add-guest notification branch is unreachable because CalendarEvent.team is never populated by callers | 26 |
| B13 | high | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:167–170` | Add-guests email send failure is swallowed (no error context) and request still succeeds | 21 |
| B14 | high | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:44–90` | Add-guests endpoint can overbook seat-limited events by appending attendees without enforcing seatsPerTimeSlot | 19 |
| B15 | high | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:74–101` | Race condition in addGuests allows duplicate attendee rows (check-then-insert without transaction/unique constraint) | 18 |
| B16 | high | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:60–80` | Guest dedupe/blacklist checks are case-sensitive, allowing case-variant duplicate or blacklisted emails to be added | 12 |
| B17 | high | `packages/emails/templates/organizer-add-guests-email.ts:25–25` | Organizer add-guests email sets Reply-To to all attendee emails, leaking roster and risking oversized headers | 12 |
| B18 | medium | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:83–90` | Add-guests flow persists new guest attendees with empty name (blank greetings/ICS CN) | 10 |
| B19 | medium | `packages/ui/form/multiemail.tsx:26–35` | MultiEmail list items keyed by array index cause stale/shifted input values after middle-row removal | 10 |
| B20 | high | `packages/trpc/server/routers/viewer/bookings/addGuests/addguests.schema.ts:4–6` | Server-side addGuests input allows duplicate guest emails in one request | 9 |
| B21 | high | `packages/emails/templates/organizer-add-guests-email.ts:28–31` | Organizer add-guests email subject crashes on empty attendees due to unguarded attendees[0].name access | 8 |
| B22 | medium | `UNKNOWN (no test file path referenced in the reports; issue is the absence of tests in the PR diff):1–1` | New add-guests handler ships with zero test coverage (permission matrix/filtering/email flow unverified) | 6 |
| B23 | high | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:44–80` | addGuests mutation allows adding guests even when the EventType disables/blocks guests | 6 |
| B24 | high | `packages/emails/email-manager.ts:538–549` | sendAddGuestsEmails sends the wrong attendee template for newly-added guests (and uses a case-sensitive O(n×m) membership check) | 6 |
| B25 | medium | `unknown (not referenced in the clustered reports and not present in PR #14740 diff; likely the server-side add-guests mutation/handler for bookings/attendees)` | Add-guests mutation silently drops blacklisted/already-attending emails yet returns success (and misleading 'emailsmustbeuniquevalid' when all dropped) | 4 |
| B26 | low | `packages/ui/form/multiemail.tsx:48–48` | Remove-email tooltip is hardcoded in English instead of using i18n | 4 |
| B27 | high | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:26–56` | addGuests loads booking by raw id (with heavy includes) before authorization, enabling cross-tenant probing/enumeration | 4 |
| B28 | high | `packages/emails/email-manager.ts:541–549` | Add-guests email path bypasses hideCalendarNotes redaction and can leak additional notes to attendees | 4 |
| B29 | high | `apps/web/components/dialog/addguestsdialog.tsx:49–51` | Add Guests dialog mishandles empty MultiEmail rows, causing silent no-op or persistent invalid-email errors | 3 |
| B30 | medium | `unknown (reports mention a client-side handler `handleAdd` using `multiEmailValue`, but no file path is included and the file is not part of PR #14740 diff)` | Add action is a no-op when all multi-email rows are removed (empty array early-return) | 3 |
| B31 | medium | `packages/ui/form/multiemail.tsx:2–2` | MultiEmail leaf module imports @calcom/ui barrel, creating a circular dependency via index re-export | 3 |
| B32 | high | `packages/lib/server/emails/sendAddGuestsEmails.ts` | sendAddGuestsEmails uses the full AttendeeScheduledEmail template for newly added guests (wrong subject/body + blank-name attendee) | 2 |
| B33 | high | `packages/lib/emails/sendAddGuestsEmails.ts` | add-guests email notification is sent to all attendees on every call, enabling spam/harassment via repeated addGuests | 2 |
| B34 | medium | `packages/ui/form/multiemail.tsx:21–21` | MultiEmail label htmlFor references missing input id, breaking label/control association | 2 |
| B35 | high | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:138–155` | Add-guests on a recurring booking updates only one occurrence but sends a series-wide calendar invite | 2 |
| B36 | high | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:164–170` | Concurrent add-guests requests can overwrite calendar attendees with stale snapshot (lost updates) | 2 |
| B37 | medium | `packages/trpc/server/routers/viewer/bookings/addguests.schema.ts:5–8` | addguests input schema allows empty guests array, leading to misleading BAD_REQUEST message | 2 |
| B38 | high | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:80–86` | addGuests throws BAD_REQUEST when all submitted emails already attendees, enabling email probing and breaking retry/idempotency | 1 |
| B39 | medium | `apps/web/pages/api/book/[...slug].ts:74–78` | Guest email blacklist is undocumented/missing from .env.example and can be bypassed via email case differences | 1 |
| B40 | low | `unknown (reports did not include a path; code not in this PR diff)` | Redundant sequential role checks (isTeamAdmin + isTeamOwner) cause unnecessary DB round-trips on addGuests | 1 |
| B41 | medium | `packages/features/emails/sendAddGuestsEmails.ts:34–73` | Organizer gets duplicate “guests added” email for team bookings because organizer isn’t excluded from team member loop | 1 |
| B42 | medium | `unknown (not included in PR diff; reports did not provide a path)` | UI shows “Additional guests / Add members” action to users who are always forbidden by the backend | 1 |
| B43 | medium | `packages/trpc/server/routers/viewer/bookings.ts:1–1` | tRPC input allows non-integer bookingId, causing Prisma Int validation error and 500 response | 1 |
| B44 | high | `packages/core/EventManager.ts:1–1` | Newly added booking attendees are not synced to the existing external calendar event (stale attendee list passed to updateCalendarAttendees) | 1 |
| B45 | medium | `packages/trpc/server/routers/viewer/bookings.ts:187–205` | Booking lookup eagerly loads organizer.credentials (including secret keys) but never uses them | 1 |
| B46 | high | `packages/emails/email-manager.ts:539–560` | Attendee opt-out flag ignored when sending guest-change/new-invite emails | 1 |
| B47 | low | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:55–55` | Missing i18n key causes add-guests permission error to display raw `forbidden: youdonothavepermission` | 1 |
| B48 | medium | `apps/web/components/dialogs/AddGuestsDialog.tsx:49–51` | Add Guests button silently no-ops when all email rows are removed | 1 |
| B49 | medium | `packages/trpc/server/routers/viewer/eventTypes/get.handler.ts:128–136` | Null eventType.teamId is coerced to 0, causing incorrect team lookup/authorization checks | 1 |

### Verification cards

#### B1 — Calendar sync uses requesting user's credentials instead of the booking organizer's

**Location:** `packages/trpc/server/routers/viewer/bookings.ts` (exact lines not in diff)  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** All deduplicated reports describe the same concrete defect: the calendar update path constructs an EventManager (or equivalent calendar client) from `ctx.user` (the authenticated caller) rather than from `booking.user` (the organizer/owner of the calendar event). That means calendar writes execute with the attendee’s OAuth credentials (or none), which either targets the wrong calendar account or fails authorization when trying to update the organizer’s existing event. The PR diff/line refs were not provided in the evidence pack, so this verification relies on the consistent cross-tool reports pointing to the `ctx.user` vs `booking.user` construction as the offending code.

**How to replicate.** 1) Create a booking where the organizer has a connected calendar integration (e.g., Google) and the attendee does not (or has a different Google account). 2) As the attendee (authenticated), call the booking update flow that triggers calendar synchronization (e.g., edit booking details / update attendees / reschedule, depending on the route used in the PR). 3) Observe that the server attempts to update the external calendar event using the attendee’s credentials; expected: organizer’s calendar event is updated via organizer credentials. Actual: the update fails with an auth/permissions error or updates/looks for an event in the attendee’s calendar account, leaving the organizer’s event unchanged while DB rows may already be updated.

**Found by** 55 cells (140 distinct report texts, 140 findings): fable: van·high, van·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium, van·xhigh; sonnet: MRV·high, van·medium, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; terra: MRV·high, MRV·low, MRV·medium, van·medium, van·xhigh; astra: MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium

#### B2 — Non-atomic guest/attendee persistence causes DB/calendar divergence on calendar sync failure

**Location:** `unknown (reports did not include a file path; PR diff not provided in evidence pack)` (exact lines not in diff)  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** All deduplicated reports describe the same concrete defect mechanism: the code persists new booking attendees/guests to the database first, then performs an external calendar update/sync afterward, without a wrapping DB transaction and without any rollback/compensation if the calendar step fails. This creates a partial-success state where the DB is permanently mutated but the calendar event is not updated, and subsequent retries are rejected as duplicates because the DB already contains the guests. Because the evidence pack does not include the actual file/line references (and the relevant file is not in this PR’s diff), a human verifier must confirm by locating the handler/service that adds booking guests and checking that the DB write occurs before the provider calendar update and that failures in the calendar update do not revert the DB change.

**How to replicate.** 1) Find the API/handler that adds guests/attendees to an existing booking and triggers calendar synchronization. 2) Call it to add one or more new guest emails while ensuring the calendar provider update fails (e.g., revoke provider credentials, force the provider client to throw, or simulate a 5xx/network error). 3) Observe: request fails (or returns an error), but the booking’s guests/attendees are present in the database afterward. 4) Retry the same request with the same emails: expected behavior is a successful retry (or idempotent success) that results in calendar+DB consistency; actual behavior is rejection as “already present/duplicate” while the calendar event remains missing those attendees/notifications.

**Found by** 55 cells (131 distinct report texts, 131 findings): fable: van·high, van·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·xhigh; sonnet: CE·medium, MRV·high, MRV·low, MRV·medium, van·high; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; terra: CE·high, CE·low, CE·medium, MRV·high, MRV·medium, van·high, van·low, van·medium, van·xhigh; astra: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium

#### B3 — addGuests input schema allows unbounded guests array (email/DB fan-out DoS vector)

**Location:** `apps/web/server/routers/viewer/bookings/addGuests.schema.ts:10–22`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The reported issue is that the Zod input schema defines `guests` as an array but does not apply any upper-bound constraint (no `.max(...)`). In practice this looks like `guests: z.array(...)` (or equivalent) without a length cap, meaning a single authenticated request can submit thousands of guest emails. Even though this PR’s diff does not include the file, a human can confirm by opening the schema and verifying there is no `.max()` on the `guests` array, enabling unbounded downstream inserts/calendar payload growth and outbound email fan-out.

**How to replicate.** 1) Locate the add-guests mutation that uses `addGuests.schema.ts` (server-side) and confirm `guests` is accepted as an array from the client.
2) Send a single authenticated request to that mutation with `guests` containing a very large list (e.g., 5,000–20,000 unique email strings).
3) Observe actual behavior: the request is accepted/validated, and the server attempts to process all guests (DB inserts, calendar attendee updates, and/or outbound invitation emails) rather than rejecting with a validation error.
Expected behavior: schema validation rejects overly large guest lists (e.g., `guests.max(N)`) and returns a 4xx error without performing fan-out work.

**Found by** 50 cells (105 distinct report texts, 105 findings): fable: van·high, van·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium, van·xhigh; sonnet: CE·high, CE·low, MRV·high, MRV·medium, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium, van·xhigh; terra: CE·high, CE·low, CE·medium, MRV·high; astra: CE·low, CE·medium, MRV·medium

#### B4 — Attendee/guest dedupe uses case-sensitive email comparisons, allowing duplicate attendees and false negatives

**Location:** `apps/web/server/lib/email-manager.ts:1–1`  ·  **Severity:** high  ·  **Judge confidence:** 0.60  ·  ⚠️ `distinct=false` (cluster may span two bugs)

**Why this is real.** Multiple reports point to a case-sensitive equality/containment check in `email-manager.ts` (e.g., logic like `newGuests.includes(attendee.email)` or `guest === attendee.email`) being used to decide whether an email is already present. Because email local-parts are commonly treated case-insensitively in practice (and many systems normalize to lowercase), comparing raw strings without normalization lets `Test@Example.com` and `test@example.com` bypass dedupe and be inserted as separate attendee rows (or fail an `isAttendee` check). The PR diff does not include this file, so verification relies on reading the current post-PR code where these comparisons occur.

**How to replicate.** 1) Create a booking/event with an existing attendee email stored as `TestUser@example.com`.
2) Call the server endpoint/action that adds guests/attendees with `testuser@example.com` (different casing) in the `guests` array.
3) Observe: the code’s case-sensitive check does not consider the attendee already present, so it proceeds to add/insert another attendee/guest entry.
Expected: the second add should be treated as a duplicate (deduped or rejected) after normalizing emails (e.g., `toLowerCase().trim()`). Actual: duplicate attendee rows (or duplicate emails in guest list) are created, and downstream emails/invites can be sent twice.

**Found by** 45 cells (205 distinct report texts, 205 findings): fable: van·high; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium, van·xhigh; sonnet: MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, van·high, van·low, van·medium, van·xhigh; terra: CE·high, CE·low, MRV·high, MRV·low; astra: CE·low, CE·medium, MRV·low, MRV·medium

#### B5 — add-guests handler emails raw guests list instead of filtered uniqueGuests, causing duplicate/wrong notifications

**Location:** `addguests.handler.ts:160–175`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** Multiple reviewers point to the same concrete control-flow bug in `addguests.handler.ts` around ~line 168: the handler computes a filtered list like `uniqueGuests` (excluding already-attending/duplicate/rejected guests) and uses that list when persisting updates, but then calls the mailer with the original unfiltered input, e.g. `sendAddGuestsEmails({ guests, ... })` instead of `sendAddGuestsEmails({ guests: uniqueGuests, ... })`. This means the email-sending logic classifies pre-existing attendees as “newly added” and can pick the wrong template (e.g., scheduled-event email) or re-email guests that were intentionally filtered out. The PR diff does not include this file, so this verification relies on the consistent line-level references and described call-site behavior in the reports.

**How to replicate.** 1) Find an existing booked event with at least one attendee already on it (e.g., alice@example.com).
2) Call the “add guests” endpoint/handler with a payload that includes both the existing attendee (alice@example.com) and a truly new email (bob@example.com), possibly also including a duplicate address or an address previously rejected.
3) Observe emails sent: expected behavior is that only the newly added/unique guests receive an “added to event” style email, and existing/rejected/duplicate guests receive nothing.
4) Actual behavior (due to passing the raw `guests` array into `sendAddGuestsEmails`) is that alice@example.com (and possibly duplicates/rejected entries) also receives an email, potentially using the wrong template (e.g., a scheduled-event confirmation).

**Found by** 36 cells (78 distinct report texts, 78 findings): fable: van·high, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; sonnet: MRV·low, van·high, van·xhigh; glm-flash: CE·high, CE·low; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium; sol: CE·high, CE·medium, MRV·high, MRV·medium, van·low, van·xhigh; terra: CE·high, CE·low, CE·medium, van·low; astra: CE·low, CE·medium

#### B6 — AddGuestsDialog leaves stale `isInvalidEmail` (and email input) state on success/close, showing old validation banner when reopened

**Location:** `apps/web/components/dialogs/AddGuestsDialog.tsx:29–50`  ·  **Severity:** medium  ·  **Judge confidence:** 0.62

**Why this is real.** Multiple independent reports point to the same state bug in `addguestsdialog.tsx` around lines ~29–50: `isInvalidEmail` is set when validation fails (e.g., via a `setIsInvalidEmail(true)` path), but there is no corresponding reset (`setIsInvalidEmail(false)`) on successful submit, on dialog close (`onOpenChange`), or when the user edits the email input. This means the component can re-render/reopen with `isInvalidEmail` still true, so the warning banner persists even after the input is corrected or the dialog is reopened. The PR patch does not include this file, so this verification relies on the consistent reports describing missing reset logic in that component.

**How to replicate.** 1) Open the Add Guests dialog. 2) Enter an invalid email (e.g., `foo@`) and trigger validation/submission so the invalid-email banner appears. 3) Now either (a) correct the email to a valid one and submit successfully, or (b) close the dialog (ESC/overlay) and reopen it. Expected: the invalid-email banner (and any partially typed invalid multi-email value) should be cleared once input is fixed, after successful add, or when reopening the dialog. Actual: the invalid banner and/or previous input reappears because `isInvalidEmail` (and possibly the multi-email value) was never reset.

**Found by** 35 cells (84 distinct report texts, 84 findings): fable: van·high, van·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; sonnet: MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; sol: CE·medium, van·xhigh

#### B7 — AddGuestsDialog error toast fallback is unreachable; users see raw error codes/undefined prefix

**Location:** `apps/web/components/dialog/addguestsdialog.tsx:43–47`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72

**Why this is real.** Automated reports consistently point to apps/web/components/dialog/addguestsdialog.tsx around line 43 building the toast message as a template string (e.g. something like ``const message = `${err?.data?.code}: ${t(err?.message)}`;``) and then calling `showToast(message || t("unabletoaddguests"), ...)`. Because a template literal always produces a string (even when interpolations are `undefined`, yielding e.g. `"undefined: ..."`), `message` is always truthy and the `|| t("unabletoaddguests")` fallback is dead/unreachable. This results in user-visible toasts containing raw server codes/i18n keys and even `undefined:` prefixes instead of the intended localized fallback; the PR diff is not provided here, so this verification relies on the repeated line-specific reports.

**How to replicate.** 1) In the web app UI, open the Add Guests dialog. 2) Trigger an error path while adding guests (e.g., enter an invalid email, or simulate a server failure/response without `err.data` such as a 500 or network error). 3) Observe the toast: Actual behavior shows a string like `undefined: <raw error key/code>` or a non-localized message, because the constructed template string is always used. Expected behavior is a localized generic fallback message (e.g., `t("unabletoaddguests")`) when structured error data/message is missing or not translatable.

**Found by** 35 cells (58 distinct report texts, 58 findings): fable: van·high, van·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; sonnet: van·high; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low; sol: CE·high, CE·medium, MRV·low, MRV·medium, van·low; astra: CE·low, CE·medium

#### B8 — Add-guests endpoint allows adding guests to cancelled/rejected/past bookings (no booking state/time validation)

**Location:** `packages/trpc/server/routers/viewer/bookings/addGuests.handler.ts:1–200`  ·  **Severity:** high  ·  **Judge confidence:** 0.58

**Why this is real.** The deduplicated reports consistently describe that the add-guests handler "does not validate booking status or time" and that "booking.status never checked", so the code path that appends attendees and sends booking emails/ICS executes even when a booking is cancelled/rejected or already in the past. Because the file/lines were not part of PR #14740’s diff (per the prompt), verification must be done by inspecting the handler and confirming there is no guard such as checking `booking.status` (e.g., CANCELLED/REJECTED) and no check that `booking.startTime/endTime` is still in the future before updating guests and dispatching confirmations/invites.

**How to replicate.** 1) Create a booking that supports adding guests (any normal event type), then cancel it (or reject it) or wait until its start time is in the past.
2) As an attendee (or any actor allowed by the endpoint), call the add-guests API/mutation with one or more new guest emails.
3) Expected: request should be rejected (4xx) because the booking is cancelled/rejected/past and should be immutable/inactive.
4) Actual (per reports): guests are added anyway and the system sends "confirmed" booking emails/ICS/calendar updates containing meeting links for an inactive booking.

**Found by** 34 cells (83 distinct report texts, 83 findings): fable: van·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·medium, van·low, van·medium, van·xhigh; sonnet: MRV·medium, van·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium; sol: CE·high, CE·medium, van·high, van·medium; terra: van·medium; astra: CE·medium

#### B9 — addGuests crashes with unhandled Prisma P2025 when booking.userId is null (id coerced to 0)

**Location:** `packages/trpc/server/routers/viewer/bookings/addGuests.handler.ts:82–88`  ·  **Severity:** high  ·  **Judge confidence:** 0.70

**Why this is real.** The handler performs an organizer lookup using Prisma with a coerced fallback ID: `prisma.user.findFirstOrThrow({ where: { id: booking.userId || 0 } })` (line range reported as ~82–88). When `booking.userId` is `null`, this becomes `id: 0`, which will not match any real user and causes `findFirstOrThrow` to throw a Prisma error (typically P2025). Because this exception is not converted to a typed `TRPCError`, it bubbles up as an unhandled 500 with a raw Prisma error payload.

**How to replicate.** 1) Ensure there exists a Booking record where `userId` is NULL (e.g., an imported/legacy booking or any flow that can create bookings without an assigned user).
2) Call the tRPC endpoint that uses `addGuests.handler.ts` ("add guests" booking mutation) for that booking.
3) Observe the server response: expected is a clean, handled error (e.g., TRPCError NOT_FOUND/BAD_REQUEST stating organizer/user missing), but actual behavior is a 500 with an unhandled Prisma `findFirstOrThrow`/P2025 error because `userId` was coerced to 0.

**Found by** 29 cells (59 distinct report texts, 59 findings): fable: van·high; opus: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·xhigh; sonnet: MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high; sol: CE·high, van·medium; terra: MRV·high

#### B10 — Authorization bypass: any attendee can add arbitrary guests to a booking and trigger organizer calendar invites

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:52–53`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74

**Why this is real.** All deduped reports point to the same authorization guard at ~L52–53 where being an attendee (`isAttendee` / `isattendee`) is treated as sufficient permission to proceed (e.g., a check equivalent to “allow if organizer OR isAttendee”). That means an invitee (not the organizer/host) can call the `addguests` handler to mutate the booking and cause calendar updates/invitation emails to be sent to arbitrary third-party emails, leaking full event details (including meeting links) without organizer consent. The PR diff does not include this file, so verification relies on reading the post-PR handler around the referenced lines and confirming the permission condition includes `isAttendee` as an authorization grant rather than an informational role.

**How to replicate.** 1) Create a booking with Organizer O and invite Attendee A (A is a valid attendee on the booking).
2) Log in as Attendee A (not as Organizer O).
3) Call the TRPC endpoint backing `viewer.bookings.addGuests` (or the corresponding HTTP request) with the booking identifier (uid/id) and a list of arbitrary external guest emails (e.g., attacker-controlled addresses).
4) Observe actual behavior: the call succeeds and new guests are added; calendar updates and/or invitation emails (ICS) are sent containing full event details (location/video URL/password).
5) Expected behavior: only the organizer/host (or authorized team/admin roles) should be able to add new guests; an attendee should get an authorization error and no invitations/updates should be sent.

**Found by** 29 cells (41 distinct report texts, 41 findings): opus: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high, van·low, van·xhigh; glm-flash: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low; glm-vis: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·low, CE·medium, MRV·high, MRV·low, van·low; terra: CE·high, CE·low, CE·medium, MRV·medium

#### B11 — Team admin authorization check wrongly requires user to be both admin and owner (&& instead of ||)

**Location:** `packages/trpc/server/routers/viewer/bookings/addGuests.handler.ts:52–55`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** Multiple independent reports point to `addGuests.handler.ts` defining an `isTeamAdminOrOwner`-style check using `isTeamAdmin && isTeamOwner`. With `&&`, the condition only passes when the caller is simultaneously a team admin and the team owner, which contradicts the variable name and the intended permission semantics (“admin OR owner”). This is a functional authorization bug because legitimate team admins (who are not owners) will be denied; since the PR diff for this file is not provided here, this verification relies on the reviewers’ consistent line-level references (~52–55) to the offending expression.

**How to replicate.** 1) Create a team with two users: User A as team owner, User B as team admin (but not owner). 2) Sign in as User B and attempt the action that hits `addGuests.handler.ts` (e.g., add guests to a team booking via the UI flow that adds guest emails, or call the corresponding API/TRPC mutation). 3) Expected: team admin can add guests (authorization passes because admin OR owner). Actual: request is rejected/throws a forbidden/permission error because the code requires `isTeamAdmin && isTeamOwner`, which is false for an admin-only user.

**Found by** 26 cells (93 distinct report texts, 93 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·medium, MRV·high; terra: CE·high, CE·low

#### B12 — Team-member add-guest notification branch is unreachable because CalendarEvent.team is never populated by callers

**Location:** `packages/emails/email-manager.ts:522–553`  ·  **Severity:** high  ·  **Judge confidence:** 0.67

**Why this is real.** The new implementation tries to notify team hosts via `if (calendarEvent.team?.members) { for (const teamMember of calendarEvent.team.members) { ... } }` but this relies on `CalendarEvent` having a `team` object with `members`. In the surrounding codebase, the `CalendarEvent` object passed into email-manager is typically constructed as a literal from booking/event data; when that construction omits `team` (as the reports indicate), `calendarEvent.team` is `undefined` and the loop never executes, making team-host notifications for team bookings silently skip.

**How to replicate.** 1) Create a Team event type with at least two team members (A and B) as hosts. 2) Book the event so it is a team booking (both hosts are associated with the booking). 3) Use the UI/API flow that adds guests to an existing booking (triggering `sendAddGuestsEmails`). 4) Expected: both organizer A and the other team host(s) (e.g., B) receive an "OrganizerAddGuests" email. Actual: only the primary organizer email is sent; other team members are not emailed because `calendarEvent.team?.members` is missing and the loop never runs.

**Found by** 26 cells (45 distinct report texts, 45 findings): fable: van·high, van·low, van·medium; opus: CE·high, MRV·high, MRV·low, MRV·medium, van·xhigh; glm-flash: CE·high; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium, van·high; sol: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; terra: MRV·high, van·medium; astra: MRV·high

#### B13 — Add-guests email send failure is swallowed (no error context) and request still succeeds

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:167–170`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple deduplicated reports point to a catch block around the add-guests email dispatch that is written as `catch (err) { console.log("error sending addguestsemails") }` (reported at ~lines 167–170). This discards the actual `err` object and uses a bare console.log, so production logs lack any actionable failure details. Because the error is swallowed (no rethrow/return error), the handler can still return success after persisting guests, leading callers/UI to believe notifications were sent when they were not.

**How to replicate.** 1) Create or open an existing booking that supports adding guests and use the UI/API route that invokes `viewer.bookings.addGuests` (or equivalent) to add one or more new guest emails. 2) Force the email send to fail (e.g., misconfigure SMTP/SendGrid credentials, block outbound email network calls, or set an invalid mail provider config in a dev/staging environment). 3) Observe: the request completes successfully and the guest list persists/updates, but no guest notification emails are delivered. 4) Check server logs: only a fixed message like `error sending addguestsemails` appears with no stack trace/error object, making the failure undiagnosable and preventing easy retry since guests are already saved.

**Found by** 21 cells (29 distinct report texts, 29 findings): fable: van·high, van·medium; opus: MRV·high, MRV·low, van·medium, van·xhigh; glm-flash: CE·medium, MRV·high, MRV·low, van·low; glm-vis: MRV·high, MRV·low, MRV·medium; sol: CE·low, MRV·high, MRV·low; terra: MRV·low, MRV·medium; astra: MRV·high, MRV·low, MRV·medium

#### B14 — Add-guests endpoint can overbook seat-limited events by appending attendees without enforcing seatsPerTimeSlot

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:44–90`  ·  **Severity:** high  ·  **Judge confidence:** 0.64

**Why this is real.** The deduplicated reports consistently describe that this handler appends new guests by directly updating `booking.attendees` (via a Prisma `booking.update` / nested `attendees.create*`) and does not validate capacity for seated events (`seatsPerTimeSlot`). In particular, the handler is reported to read/possess `seatsPerTimeSlot` context but never checks `booking.attendees.length + uniqueGuests.length <= seatsPerTimeSlot` and does not create/update any seat-tracking records (e.g., BookingSeat) used by the seated-booking flow. Because the PR diff does not include this file, this verification relies on the reported code behavior/line references: guests are appended unconditionally, so seat-limited bookings can be overfilled.

**How to replicate.** 1) Create an event type configured as a seated/seat-limited event with `seatsPerTimeSlot = 2` (or any small number). 2) Create a booking for a specific timeslot with 2 attendees (fully booked). 3) Call the viewer bookings add-guests endpoint (the TRPC procedure backed by `addguests.handler.ts`) to add 1+ additional guests to that booking. Expected: request should be rejected (or only add up to remaining seats) and/or use the seated-booking seat allocation logic; Actual: guests are appended as attendees successfully, resulting in `attendees.count > seatsPerTimeSlot` (overbooked slot) and no corresponding seat-allocation records if the system uses a separate seat table/flow.

**Found by** 19 cells (46 distinct report texts, 46 findings): fable: van·high, van·medium; opus: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium

#### B15 — Race condition in addGuests allows duplicate attendee rows (check-then-insert without transaction/unique constraint)

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:74–101`  ·  **Severity:** high  ·  **Judge confidence:** 0.67

**Why this is real.** The reported code path performs a read of existing attendees and then conditionally writes new attendees via `booking.update(... createMany ...)` based on an in-memory dedupe/filter. Because the read (duplicate check) and the subsequent `createMany` are not wrapped in a database transaction and there is no unique constraint on (bookingId,email), two concurrent requests can both observe "not present" and both insert the same attendee. The PR diff does not include this file, so verification relies on the consistent line-referenced reports pointing to this non-atomic read-then-write flow around lines ~74–101.

**How to replicate.** 1) Pick an existing booking with no attendee for email `dup@example.com`. 2) From two clients (or one script), send two addGuests requests concurrently to the same booking, both including `dup@example.com` (e.g., fire both requests without awaiting the other). 3) Observe that both requests succeed and the booking ends up with two attendee records for `dup@example.com` (or duplicated guest entries in the UI). Expected: only one attendee row per (booking,email); Actual: duplicates appear due to the race in the check-then-insert logic.

**Found by** 18 cells (18 distinct report texts, 18 findings): fable: van·medium; opus: CE·high, CE·low, CE·medium, MRV·low, MRV·medium, van·xhigh; sonnet: MRV·high; glm-flash: van·medium, van·xhigh; glm-vis: MRV·low, van·high, van·low, van·medium; sol: CE·high, CE·medium; terra: CE·low, MRV·low

#### B16 — Guest dedupe/blacklist checks are case-sensitive, allowing case-variant duplicate or blacklisted emails to be added

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:60–80`  ·  **Severity:** high  ·  **Judge confidence:** 0.70

**Why this is real.** Multiple reports point to direct string equality checks in `addguests.handler.ts` (around lines ~60–77) such as `guest === attendee.email` for existing-attendee dedupe and comparing raw `guest` values against a lowercased blacklist. Because email local/domain parts are compared without normalization (e.g., no `.toLowerCase()` on both sides), case variants like `Alice@Example.com` bypass both duplicate detection and blacklist filtering. The PR diff does not include this file, so verification relies on the reported line-level evidence and the described comparisons.

**How to replicate.** 1) Ensure a booking already has an attendee with email `bob@example.com` stored. 2) Call the add-guests endpoint/handler with guests including `Bob@Example.com`. Expected: it should be detected as an existing attendee (or duplicate) and not be added. Actual: it passes `guest === attendee.email` and a new attendee row is created differing only by case.

Blacklist path: 1) Add `blocked@example.com` to the blacklist (commonly stored/compared in lowercase). 2) Submit guest `Blocked@Example.com`. Expected: rejected/filtered as blacklisted. Actual: if the code compares raw `guest` against lowercased blacklist entries, the guest is accepted. (Optional observation: if all submitted guests are filtered out by these checks, the handler reportedly throws `emailsmustbeuniquevalid`, which misdescribes the reason.)

**Found by** 12 cells (22 distinct report texts, 22 findings): opus: van·high, van·low, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low; glm-vis: CE·low, CE·medium, MRV·high, MRV·medium

#### B17 — Organizer add-guests email sets Reply-To to all attendee emails, leaking roster and risking oversized headers

**Location:** `packages/emails/templates/organizer-add-guests-email.ts:25–25`  ·  **Severity:** high  ·  **Judge confidence:** 0.87

**Why this is real.** The Nodemailer payload explicitly sets `replyTo: [this.calEvent.organizer.email, ...this.calEvent.attendees.map(({ email }) => email)]` (line 25). This means every recipient of this organizer/team-member notification receives an email whose Reply-To header contains the full attendee email list, disclosing addresses to each recipient and allowing unbounded growth of the header as attendees increase. For large bookings or repeated guest additions, the Reply-To header can exceed provider limits and cause message rejection/truncation, turning the notification into a silent/partial failure depending on upstream handling.

**How to replicate.** 1) Create a booking/event with an organizer and multiple attendees (or use a seats/large-attendee event), then trigger the 'add guests' flow so `OrganizerAddGuestsEmail` is sent. 2) Inspect the delivered email headers (in a mail catcher like MailHog/Mailpit or your SMTP provider logs): Expected: Reply-To should be a single address (e.g., organizer or a controlled alias) or otherwise privacy-preserving; Actual: `Reply-To` contains the organizer plus every attendee email. 3) Increase attendees to dozens/hundreds (or repeatedly add guests) and resend: Expected: email still delivers reliably; Actual: some providers reject/truncate due to excessive header size, and recipients may not receive the organizer notification.

**Found by** 12 cells (14 distinct report texts, 14 findings): opus: CE·medium, MRV·high; glm-flash: MRV·high, MRV·medium; glm-vis: CE·low, MRV·high, MRV·low, MRV·medium; sol: MRV·low; terra: MRV·high, MRV·medium; astra: MRV·low

#### B18 — Add-guests flow persists new guest attendees with empty name (blank greetings/ICS CN)

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:83–90`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple reviewers point to the same concrete code pattern in this file/region: new guest attendees are created with an explicit empty string for the display name (e.g. `name: ""`) while filling other fields like email (and often organizer-derived `timeZone`/`locale`). Persisting `name: ""` is not a harmless placeholder: downstream email templates and ICS attendee rendering commonly use the attendee name as the display name/greeting and as the CN parameter, which becomes blank ("hi ,", `CN=""`, or `To:  <email>`). This is a functional defect (bad user-facing output and incorrect attendee identity data), not a style issue; the PR diff is not provided here, so this verification relies on the consistent line-referenced reports.

**How to replicate.** 1) Create a booking with an organizer and at least one existing attendee. 2) Call the add-guests endpoint/handler for that booking with a guest email that does not yet exist as an attendee (so the handler creates a new attendee record). 3) Observe the created attendee row: its `name` is persisted as an empty string. 4) Trigger sending of guest/organizer emails and/or download the ICS for the booking: expected is the guest addressed by a name or at least the email as display name; actual is blank name in greeting/headers (e.g., "hi ," / " <guest@email>") and ICS attendee has empty CN (e.g., `CN=""`).

**Found by** 10 cells (15 distinct report texts, 15 findings): opus: MRV·high, MRV·medium; sonnet: MRV·high; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high

#### B19 — MultiEmail list items keyed by array index cause stale/shifted input values after middle-row removal

**Location:** `packages/ui/form/multiemail.tsx:26–35`  ·  **Severity:** medium  ·  **Judge confidence:** 0.70

**Why this is real.** Multiple reports point to the component rendering a removable list of email inputs using an array-index React key (e.g., a map rendering items with `key={index}` around lines ~26–31) while removing items via splice/filter from the middle. In React, using the array index as the key on a mutable list causes DOM/component instances to be reused for different logical items after a deletion, so the input state/value/focus can appear to “move” to the wrong row. This is a functional correctness issue (wrong displayed values / state association), not a style nit; the PR diff does not include this file, so verification is based on the reports’ cited lines.

**How to replicate.** 1) Open any UI that uses the MultiEmail component (a form that lets you add multiple email rows). 2) Add at least three rows and type distinct values (e.g., a@a.com, b@b.com, c@c.com). 3) Delete the middle row (b@b.com). Expected: remaining rows keep their own values (a@a.com, c@c.com). Actual with `key={index}`: React may reuse the DOM node for the next item, causing the value/focus/IME state to appear to shift—e.g., c@c.com row may display b@b.com’s input state or vice versa.

**Found by** 10 cells (13 distinct report texts, 13 findings): fable: van·low; opus: van·low, van·medium, van·xhigh; glm-flash: MRV·low, van·high, van·low, van·medium; glm-vis: CE·low, van·low

#### B20 — Server-side addGuests input allows duplicate guest emails in one request

**Location:** `packages/trpc/server/routers/viewer/bookings/addGuests/addguests.schema.ts:4–6`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** In `addguests.schema.ts` the guests list is validated only as an array of emails (e.g., `z.array(z.string().email())`) with no `.refine(...)`/deduplication to enforce uniqueness. The reports indicate the client dialog schema *does* refine for uniqueness, but server-side validation is the actual security boundary; a direct API call can therefore submit `["a@x.com","a@x.com"]` and pass validation. The handler then forwards the array into `createMany` (and only filters against existing attendees, not duplicates within the same request), resulting in either duplicate attendee rows/duplicate notifications or a Prisma unique-constraint error (P2002) bubbling as a 500.

**How to replicate.** 1) Locate the server mutation/route that uses `addguests.schema.ts` (viewer bookings addGuests).
2) Call it directly (e.g., via tRPC client, curl against the API, or modifying a request in DevTools) with a valid `bookingId` and `guests: ["dup@example.com", "dup@example.com"]`.
3) Expected: server rejects the request (422) or deduplicates to a single guest.
4) Actual: the request passes schema validation and reaches persistence; depending on DB constraints it either inserts two attendee rows for the same email (leading to duplicate calendar invites/emails) or throws a Prisma P2002 unique constraint error causing a server 500.

**Found by** 9 cells (17 distinct report texts, 17 findings): opus: van·low; glm-flash: CE·high, CE·low, CE·medium, MRV·low; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium

#### B21 — Organizer add-guests email subject crashes on empty attendees due to unguarded attendees[0].name access

**Location:** `packages/emails/templates/organizer-add-guests-email.ts:28–31`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** In `packages/emails/templates/organizer-add-guests-email.ts` the subject template reads from the first attendee without any guard, e.g. `name: this.calevent.attendees[0].name` (reported at ~L28-29). If `this.calevent.attendees` is an empty array (or undefined), `this.calevent.attendees[0]` is `undefined` and `.name` throws a runtime `TypeError`, which can abort email payload construction/sending. This is a functional correctness bug (runtime exception) rather than a style issue; the PR diff didn’t include this file, so this verification relies on the reports’ line references.

**How to replicate.** 1) Find the code in `packages/emails/templates/organizer-add-guests-email.ts` where the subject is built and confirm it directly accesses `this.calevent.attendees[0].name` without optional chaining/fallback.
2) Trigger the template with a `calevent` object where `attendees: []` (e.g., in a unit test, or by invoking the email-sending path with an event that has no attendees).
Expected: email subject renders with a safe fallback (or email still sends).
Actual: subject construction throws `Cannot read properties of undefined (reading 'name')`, causing the email send/payload generation to fail (and potentially rejecting a batch `Promise.all` send).

**Found by** 8 cells (8 distinct report texts, 8 findings): fable: van·high, van·low; opus: CE·medium, MRV·low, van·low, van·medium; glm-flash: CE·low, MRV·low

#### B22 — New add-guests handler ships with zero test coverage (permission matrix/filtering/email flow unverified)

**Location:** `UNKNOWN (no test file path referenced in the reports; issue is the absence of tests in the PR diff):1–1`  ·  **Severity:** medium  ·  **Judge confidence:** 0.62

**Why this is real.** This is a real gap because the reports indicate the PR introduces a new ~174-line add-guests handler/mutation plus new UI components/templates, but adds no unit/integration/e2e tests covering any of it. Multiple reviewers specifically note that the permission matrix (organizer/attendee/team admin/owner), blacklist filtering, and dedupe logic are untested, meaning regressions in these security- and data-integrity-sensitive branches would not be caught by CI. The prompt states there is no file reference in the reports and the file is not part of this PR diff here, so verification must be done by inspecting the PR diff and confirming no new/modified test files exist alongside the new handler/components.

**How to replicate.** 1) Open the PR diff and search for added/changed test files (e.g., filenames containing `.test.`, `.spec.`, `__tests__`, `playwright`, `cypress`). 2) Confirm the PR adds the add-guests handler/mutation and related UI/email code, but no corresponding tests were added or updated. 3) (Optional) Locally introduce an intentional regression in the handler (e.g., flip an auth condition or remove dedupe) and run the repo test suite; expected: a targeted test should fail; actual: no new test fails because none exists for this new behavior.

**Found by** 6 cells (10 distinct report texts, 10 findings): opus: van·xhigh; glm-flash: MRV·high, MRV·low; glm-vis: MRV·high, MRV·medium, van·medium

#### B23 — addGuests mutation allows adding guests even when the EventType disables/blocks guests

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:44–80`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The add-guests handler proceeds with adding invitees to a booking without any guard that checks the associated EventType’s guest policy (e.g., `disableGuests` / “guests hidden/disabled” settings). Multiple reports pinpoint that around lines ~44 and ~74 the code updates/creates guests but never rejects bookings whose `eventType` forbids guests, meaning a caller can bypass the organizer’s configuration purely via this mutation. The PR diff does not include this file, so verification is by reading the current handler around the referenced lines and confirming there is no conditional returning an error when the EventType disallows guests.

**How to replicate.** 1) Create or pick an Event Type where guest additions are disabled/hidden (e.g., `disableGuests` enabled / guests turned off in settings). 2) Create a booking for that Event Type. 3) Call the viewer bookings addGuests mutation (the one implemented by `addguests.handler.ts`) with one or more guest emails for that booking. Expected: the mutation should fail (e.g., forbidden/bad request) because guests are disabled for the Event Type. Actual: the mutation succeeds and the guests are added/associated with the booking despite the Event Type’s no-guests setting.

**Found by** 6 cells (6 distinct report texts, 6 findings): opus: CE·medium; sol: CE·high, van·medium, van·xhigh; terra: van·high, van·xhigh

#### B24 — sendAddGuestsEmails sends the wrong attendee template for newly-added guests (and uses a case-sensitive O(n×m) membership check)

**Location:** `packages/emails/email-manager.ts:538–549`  ·  **Severity:** high  ·  **Judge confidence:** 0.81

**Why this is real.** In sendAddGuestsEmails the template choice is inverted: `if (newGuests.includes(attendee.email)) { return sendEmail(() => new AttendeeScheduledEmail(calendarEvent, attendee)); } else { return sendEmail(() => new AttendeeAddGuestsEmail(calendarEvent, attendee)); }`. This causes attendees whose email appears in `newGuests` (i.e., the newly added guests) to receive the generic "scheduled" email (with full calendar invite flow) instead of the "added to event" template, while all other attendees get the add-guests email. Additionally, `newGuests.includes(attendee.email)` is a case-sensitive linear scan inside `.map(...)`, making the decision depend on email casing and scaling as O(attendees × newGuests).

**How to replicate.** 1) Create an event with at least one existing attendee (A). 2) Trigger the "add guests" flow such that sendAddGuestsEmails is called with `newGuests` containing a newly added guest email (G). 3) Observe outgoing emails: expected behavior is that G receives an "added to event" email (AttendeeAddGuestsEmail) and existing attendees receive the "guests were added" notification (or at least not the "you're scheduled" invite). Actual behavior per code: G matches `newGuests.includes(attendee.email)` and receives AttendeeScheduledEmail, while non-new attendees receive AttendeeAddGuestsEmail. (Optional) Add `newGuests` as `g@x.com` while attendee email is `G@x.com`: the includes check fails and flips the template choice due to case sensitivity.

**Found by** 6 cells (6 distinct report texts, 6 findings): opus: CE·high, CE·medium; sonnet: MRV·high; glm-vis: CE·low; astra: CE·low, CE·medium

#### B25 — Add-guests mutation silently drops blacklisted/already-attending emails yet returns success (and misleading 'emailsmustbeuniquevalid' when all dropped)

**Location:** `unknown (not referenced in the clustered reports and not present in PR #14740 diff; likely the server-side add-guests mutation/handler for bookings/attendees)` (exact lines not in diff)  ·  **Severity:** medium  ·  **Judge confidence:** 0.62

**Why this is real.** Per the deduplicated reports, the handler filters the requested guest list to a reduced `uniqueGuests` set (dropping blacklisted addresses and/or emails already present as attendees) but still returns a success response (e.g., a 'guests added' message) without indicating which inputs were skipped. The evidence is the specific behavior around the hardcoded error key/message `'emailsmustbeuniquevalid'`: when filtering removes every submitted email, the code throws BadRequest with `'emailsmustbeuniquevalid'`, even though the input emails can be valid/unique and were excluded for other reasons (blacklist/existing attendee). This is a functional correctness bug (silent partial application + incorrect error reporting), not a style issue, because it causes the UI to claim invitations were added when they were not and misleads users during retries.

**How to replicate.** 1) Configure the blacklist env var mentioned in reports (e.g., `BLACKLISTED_GUEST_EMAILS` / similar) to include `blocked@example.com`.
2) Create or open an event/booking where adding guests is supported.
3) Call the add-guests flow with a mixed list: `['ok1@example.com', 'blocked@example.com']`.
Expected: API/UI should either reject with a clear validation error identifying the blacklisted email, or return a response listing which guests were added vs skipped.
Actual (per reports): UI shows success ('guests added') but `blocked@example.com` is silently not added (no attendee row / no email).
4) Now submit only filtered-out emails, e.g., `['blocked@example.com']` (or an email already an attendee).
Expected: error like 'guest is blacklisted' / 'already invited'.
Actual (per reports): server returns BadRequest with message/key `'emailsmustbeuniquevalid'`, which misstates the real cause.

**Found by** 4 cells (8 distinct report texts, 8 findings): glm-flash: MRV·high, MRV·medium; glm-vis: CE·high, MRV·low

#### B26 — Remove-email tooltip is hardcoded in English instead of using i18n

**Location:** `packages/ui/form/multiemail.tsx:48–48`  ·  **Severity:** low  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple reviewers point to the same line in `packages/ui/form/multiemail.tsx` where the tooltip for the remove action is a literal English string (e.g., `content="remove email"`) rather than using the existing `t(...)` translation function used elsewhere in the component (e.g., for the adjacent “add another” label). This is a real functional i18n defect: in any non-English locale, the tooltip will remain English while surrounding UI strings are localized. The file wasn’t part of this PR’s diff here, so this verification relies on the consistent line-referenced reports.

**How to replicate.** 1) Set the app language/locale to a non-English language (e.g., French). 2) Navigate to a UI that uses the shared MultiEmail control (e.g., the Add Guests dialog where you can add multiple emails). 3) Add at least one guest email so a remove (X/trash) button appears. 4) Hover the remove button: expected a translated tooltip; actual tooltip text is the English literal “remove email”.

**Found by** 4 cells (7 distinct report texts, 7 findings): fable: van·medium; glm-flash: MRV·high; glm-vis: MRV·high, van·medium

#### B27 — addGuests loads booking by raw id (with heavy includes) before authorization, enabling cross-tenant probing/enumeration

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:26–56`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The handler first loads the booking using an unscoped lookup like `prisma.booking.findFirst({ where: { id: bookingId }, include: { attendees: true, references: true, eventType: true, user: { include: { credentials: true }}}})` (reports cite addguests.handler.ts ~26-56 / 43-49), i.e., it does not constrain the query by the requester’s user/team. The authorization check happens only after this fetch, and the code path reportedly throws NOT_FOUND when `!booking` before throwing FORBIDDEN, so an authenticated attacker can (a) force materialization of sensitive relations for arbitrary booking IDs and (b) distinguish “exists vs not exists” by observing NOT_FOUND vs FORBIDDEN (or different timing), which is a real access-control/data-leak bug rather than a style issue. The PR diff does not include this file, so this verification relies on the reported code locations.

**How to replicate.** 1) Sign in as User A (any authenticated account). 2) Obtain/guess a bookingId belonging to User B (different org/team) and call the tRPC mutation that hits `viewer.bookings.addGuests` with that bookingId. 3) Observe that the server performs a heavy booking fetch (attendees/references/eventType/organizer credentials) before failing auth; compare responses for (a) an existing чужой bookingId vs (b) a random non-existent bookingId—expected: both should return FORBIDDEN (or identical behavior) without loading unrelated data; actual: NOT_FOUND is returned for non-existent IDs while existing чужие IDs take the auth branch (FORBIDDEN) after doing the full include query, making existence enumerable and causing unnecessary cross-tenant data access in the DB layer.

**Found by** 4 cells (4 distinct report texts, 4 findings): sonnet: MRV·medium; glm-flash: CE·high, MRV·low, van·low

#### B28 — Add-guests email path bypasses hideCalendarNotes redaction and can leak additional notes to attendees

**Location:** `packages/emails/email-manager.ts:541–549`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** In the new add-guests sender, attendee emails are constructed with the full formatted event object: `return sendEmail(() => new AttendeeScheduledEmail(calendarEvent, attendee));` / `return sendEmail(() => new AttendeeAddGuestsEmail(calendarEvent, attendee));`. Unlike the existing scheduled-email flow (which explicitly sanitizes/redacts booking notes when `hideCalendarNotes` is enabled), this path never applies that redaction before passing `calendarEvent` into the templates, so any sensitive fields present on `calendarEvent` (e.g., `additionalNotes`) can be included in emails sent to newly added guests despite the hide-notes privacy setting.

**How to replicate.** 1) Create a booking/event with `hideCalendarNotes` enabled and set a non-empty `additionalNotes`/private notes field on the CalendarEvent. 2) Use the “add guests” feature so `sendAddGuestsEmails(calEvent, newGuests)` runs with the new guest email in `newGuests`. 3) Observe the email received by the newly added guest: expected behavior is that private notes are omitted/redacted (same as scheduled-email privacy behavior), but actual behavior is that the attendee email template receives the unredacted `calendarEvent` and can render those notes.

**Found by** 4 cells (4 distinct report texts, 4 findings): terra: MRV·medium; astra: MRV·high, MRV·low, MRV·medium

#### B29 — Add Guests dialog mishandles empty MultiEmail rows, causing silent no-op or persistent invalid-email errors

**Location:** `apps/web/components/dialog/addguestsdialog.tsx:49–51`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The handler contains an early return: `if (multiemailvalue.length === 0) { return; }` (lines 49–51). But the MultiEmail UI is reported to initialize/maintain an empty row as `[""]`, so `length === 0` does not catch the "no email entered" state and validation instead fails on the empty string; conversely, when the user removes all rows and the array becomes `[]`, clicking Add becomes a silent no-op with no toast/message. Additionally, reports indicate the submit logic uses the raw `multiemailvalue` (which can include empty strings) instead of the sanitized `validationResult.data`, so any leftover blank row blocks submission entirely; this verification relies on the clustered reports because this file was not part of the PR diff.

**How to replicate.** 1) Open the Add Guests dialog (where MultiEmail starts with a single empty row). 2) Click "Add" without typing an email: expected behavior is either disabled Add or a clear per-field error; actual behavior is a generic validation error (e.g., "emails must be unique and valid") because `[""]` bypasses the `length===0` guard and fails email validation. 3) Add two rows, fill only one email, leave the other blank, then click Add: expected is the valid email is accepted (or the blank row is ignored with a clear indication); actual is the entire add is blocked by the blank string and the mutation never fires. 4) Remove every email row via the MultiEmail remove control so the array becomes `[]`, then click Add: expected is feedback (disabled button / message); actual is nothing happens due to the early `return`.

**Found by** 3 cells (3 distinct report texts, 3 findings): opus: MRV·low, MRV·medium; glm-flash: MRV·low

#### B30 — Add action is a no-op when all multi-email rows are removed (empty array early-return)

**Location:** `unknown (reports mention a client-side handler `handleAdd` using `multiEmailValue`, but no file path is included and the file is not part of PR #14740 diff)` (exact lines not in diff)  ·  **Severity:** medium  ·  **Judge confidence:** 0.60

**Why this is real.** All reports describe the same concrete control-flow defect: `handleAdd` performs a silent guard like `if (!multiEmailValue?.length) return;` (or equivalent) when the user has removed the last email row, which makes `multiEmailValue` an empty array. Because it returns without any UI feedback (no validation error/toast and no re-adding an input row), the primary "Add" action appears broken/unresponsive even though the click is being handled. This is a real UX/logic bug (reachable state + dead action) rather than a style nit; the reports also note the empty-array state is reachable by deleting rows until none remain.

**How to replicate.** Open the UI that allows adding multiple emails (the one wired to `handleAdd` and `multiEmailValue`). Remove/delete email rows until no rows remain (so `multiEmailValue` becomes `[]`). Click the footer/action "Add" button: expected behavior is to either (a) prevent removal of the last row, (b) re-create an empty input row, or (c) show a validation message/toast explaining that at least one email is required; actual behavior is nothing happens (silent return), making the button look dead.

**Found by** 3 cells (3 distinct report texts, 3 findings): glm-flash: CE·medium; glm-vis: MRV·low, MRV·medium

#### B31 — MultiEmail leaf module imports @calcom/ui barrel, creating a circular dependency via index re-export

**Location:** `packages/ui/form/multiemail.tsx:2–2`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** The reports indicate that `packages/ui/form/multiemail.tsx` (a leaf module) imports UI primitives from its own package barrel (e.g., `import { ... } from "@calcom/ui";` at/near line 2). Because the `@calcom/ui` entrypoint (`index.tsx`) re-exports `MultiEmail` (directly or indirectly), that import path forms a cycle: `multiemail.tsx -> @calcom/ui (index) -> re-export MultiEmail -> multiemail.tsx`. This is a real dependency bug (not style): circular imports can yield undefined exports or initialization-order issues depending on the bundler/optimizer and can also break tree-shaking and increase coupling. The PR diff does not include this file, so verification must be done by inspecting the post-PR code tree as referenced by the reports.

**How to replicate.** 1) In the post-PR tree, open `packages/ui/form/multiemail.tsx` and confirm it imports from the package barrel: `from "@calcom/ui"` (or an equivalent internal barrel path).
2) Open `packages/ui/index.tsx` (or the barrel entry used by `@calcom/ui`) and confirm it re-exports `MultiEmail` (e.g., `export * from "./form/multiemail"` or similar).
3) Run a build that bundles `@calcom/ui` (e.g., `pnpm -F @calcom/ui build` or the repo build) and inspect output for circular-dependency warnings, or exercise a page/component that uses `MultiEmail` and observe potential runtime failures (e.g., some imported primitives resolve as `undefined` due to initialization order). Expected: no circular dependency; Actual: barrel import creates a cycle through the re-export.

**Found by** 3 cells (3 distinct report texts, 3 findings): opus: CE·high, van·xhigh; sol: CE·medium

#### B32 — sendAddGuestsEmails uses the full AttendeeScheduledEmail template for newly added guests (wrong subject/body + blank-name attendee)

**Location:** `packages/lib/server/emails/sendAddGuestsEmails.ts` (exact lines not in diff)  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The clustered reports all describe the same concrete logic error: the "add guests" mailer path calls the scheduling-confirmation email (e.g., `attendeeScheduledEmail` / `sendAttendeeScheduledEmail`) for brand-new guests, while the existing-attendee path uses the shorter add-guest templates (`attendeeaddguestsemail` / `organizeraddguestsemail`) and/or subject keys like `newguestsadded`/`guestsaddedeventtypesubject`. The handler also constructs new attendees with an empty name (`name: ""`), so the scheduled-email template renders a confirmation addressed to a blank name and includes booking confirmation semantics (calendar invite + cancel/reschedule context) that do not apply to "guest added" recipients. This is a functional behavior bug (wrong email template/content and incorrect attendee data), not a style concern; note the PR diff does not include this file, so verification requires locating `sendAddGuestsEmails` in the post-PR tree and confirming the above calls/fields in code.

**How to replicate.** 1) In code, search for `sendAddGuestsEmails` and inspect the branch that handles newly created guest attendees.
2) Confirm that for new guests it invokes the scheduled/confirmed email template (e.g., `sendAttendeeScheduledEmail` / `attendeeScheduledEmail`) and constructs the attendee object with `name: ""`.
3) Run locally: create a booking, then add a new guest email that was not on the booking; observe the new guest receives a full "booking scheduled/confirmed" email (often with ICS + cancel/reschedule semantics and blank greeting) instead of the intended "guest added" email/subject keys.
Expected: new guests get the add-guest email template/subject (no misleading booking confirmation context, proper subject). Actual: they get the scheduling confirmation email with stale scheduled/confirmed content and blank-name personalization.

**Found by** 2 cells (3 distinct report texts, 3 findings): glm-vis: CE·low, MRV·low

#### B33 — add-guests email notification is sent to all attendees on every call, enabling spam/harassment via repeated addGuests

**Location:** `packages/lib/emails/sendAddGuestsEmails.ts` (exact lines not in diff)  ·  **Severity:** high  ·  **Judge confidence:** 0.56

**Why this is real.** The deduplicated reports consistently state that `sendAddGuestsEmails` "sends an email to every attendee on the booking on every invocation rather than only the newly added guests" and that the caller can be an attendee (low privilege) who can loop the addGuests mutation. The reported defect mechanism is that the email-sending code targets the full attendee/organizer/team recipient set each time the endpoint is invoked, instead of computing a recipient delta (only newly added guests), turning the endpoint into an unthrottled notification amplifier. This file/logic is not shown in the PR diff per the prompt, so a human verifier must confirm by inspecting `sendAddGuestsEmails` and its call site(s) for iteration over all `booking.attendees`/organizer/team members rather than just the new guests list.

**How to replicate.** 1) Create a booking with an organizer and at least one attendee (A1) (optionally add additional attendees and team members to magnify the effect). 2) As attendee A1 (not the organizer), call the API/mutation to add guests (e.g., add one new guest email per request). 3) Repeat step 2 in a loop with a different guest email each time. Expected: only the newly added guest(s) receive an email (or at most a single notification per action limited to the organizer), and other attendees are not re-notified repeatedly. Actual (per reports): every invocation triggers 'guests added' emails to the organizer and all existing attendees (and possibly team members), so repeated calls generate repeated emails to all of them (email-bomb/spam relay).

**Found by** 2 cells (2 distinct report texts, 2 findings): glm-flash: CE·low; glm-vis: MRV·high

#### B34 — MultiEmail label htmlFor references missing input id, breaking label/control association

**Location:** `packages/ui/form/multiemail.tsx:21–21`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72

**Why this is real.** Automated reviewers report that `multiemail.tsx` contains a `<label htmlFor="emails">` (around line 21) but there is no element rendered with `id="emails"`. That makes the label-to-control association dead: clicking the label will not focus the intended field and assistive technologies cannot correctly map the label to an input. The PR diff does not include this file, so this verification relies on the reported line reference and the post-PR tree code.

**How to replicate.** 1) Open `packages/ui/form/multiemail.tsx` and locate the `<label htmlFor="emails">` around line 21. 2) Search within the component render for any element with `id="emails"` (e.g., `<input id="emails" ...>`); confirm none exists. 3) Run the app and navigate to any form that uses this MultiEmail component; click the label text: expected focus moves to the corresponding email input, actual focus does not (and an accessibility checker will flag 'label has no associated control').

**Found by** 2 cells (2 distinct report texts, 2 findings): fable: van·medium; opus: CE·high

#### B35 — Add-guests on a recurring booking updates only one occurrence but sends a series-wide calendar invite

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:138–155`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** The reported code at/around line 138 adds new attendees via a `createMany` tied to the single `booking` being edited (one occurrence), while the event payload used for notifications/ICS is based on the recurring series (e.g., carries `recurringEvent` / `recurringEventId`). This creates a mismatch: the database has the guest on only one occurrence, but the generated calendar invite represents the whole series, so the guest is invited to all instances while follow-up flows (cancel/reschedule/reminders) that read per-occurrence attendees will not include them for the other occurrences. This file was not modified in the PR diff provided, so verification relies on the reviewers’ shared line-specific reports rather than a patch hunk.

**How to replicate.** 1) Create a recurring event type and book a recurring series (multiple occurrences). 2) Call the add-guests endpoint/mutation for one occurrence in the series (the booking being edited has a `recurringEventId` linking it to the series). 3) Observe: the new guest receives an ICS/invite that applies to the entire recurring series (calendar shows all occurrences). 4) Check data/behavior: only that one occurrence has a booking-attendee row for the new guest; other occurrences in the same `recurringEventId` do not. 5) Trigger a reminder/cancel/reschedule for a different occurrence in the same series: expected the new guest is included; actual they are skipped because they are not attached in the DB for those other occurrences.

**Found by** 2 cells (2 distinct report texts, 2 findings): opus: CE·high, MRV·high

#### B36 — Concurrent add-guests requests can overwrite calendar attendees with stale snapshot (lost updates)

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:164–170`  ·  **Severity:** high  ·  **Judge confidence:** 0.70

**Why this is real.** The reports point to lines ~164–165 where the handler performs a provider update by sending the full attendee list derived from the current request's local snapshot, rather than applying a merge/append or any version/ETag check. Because the external calendar write is an unversioned full "replace attendees" operation, two concurrent add-guest calls can race: the later-finishing request can push an older/smaller attendee list and effectively delete guests added by the other request. This is a real lost-update concurrency bug; the PR provides no patch hunk for this file, so verification must rely on inspecting these lines in the post-PR tree for a full-list attendee replacement without concurrency control.

**How to replicate.** 1) Use a booking with a connected calendar provider (Google/Microsoft) so attendee updates sync externally. 2) Fire two add-guests requests concurrently against the same booking (e.g., two clients adding different guests A and B at nearly the same time). 3) Observe the external calendar event attendees after both requests succeed: expected attendees include both A and B; actual attendees intermittently include only one set (whichever request performed the last provider "replace attendees" write), demonstrating lost updates due to racing full-list writes.

**Found by** 2 cells (2 distinct report texts, 2 findings): sol: CE·high; astra: van·high

#### B37 — addguests input schema allows empty guests array, leading to misleading BAD_REQUEST message

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.schema.ts:5–8`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72  ·  ⚠️ `distinct=false` (cluster may span two bugs)

**Why this is real.** In `addguests.schema.ts` the input validation for guests is defined as `guests: z.array(z.string().email())` (per the report) and does not include a `.min(1)` constraint, so `guests: []` passes schema validation. When the endpoint is invoked directly (bypassing the UI dialog’s client-side guard), the empty list is accepted and only fails later in the handler, which (per the report) returns a `BAD_REQUEST` with message key `"emailsmustbeuniquevalid"`, a message that describes invalid/duplicate emails rather than the real condition of supplying no guests. This is a functional validation gap (accepting an invalid request shape) that causes an incorrect error to surface.

**How to replicate.** 1) Invoke the viewer bookings `addGuests` tRPC procedure directly (e.g., via an API client / curl / Postman against the tRPC endpoint) with a valid booking identifier and payload `{ guests: [] }`.
2) Observe the request passes input validation (because `z.array(...)` permits empty arrays) and then fails downstream.
Expected: a validation error indicating at least one guest email is required.
Actual: the endpoint fails with `BAD_REQUEST` using the message key `"emailsmustbeuniquevalid"` (misleadingly implying duplicate/invalid emails), or the UI toast shows that incorrect message.

**Found by** 2 cells (2 distinct report texts, 2 findings): opus: CE·medium; sonnet: CE·high

#### B38 — addGuests throws BAD_REQUEST when all submitted emails already attendees, enabling email probing and breaking retry/idempotency

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:80–86`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** Multiple reviewers flag logic around line ~80 that filters the submitted guest emails against existing attendees and then throws a distinct `BAD_REQUEST` when the filtered list is empty (i.e., every submitted address is already an attendee). This creates an observable behavioral difference: the endpoint succeeds when at least one email is new, but fails when all are already present, which lets a caller infer whether a specific email is on the booking. The same branch also makes the operation non-idempotent: after a mid-flight failure where attendees were created but downstream side effects (calendar/email) didn’t complete, a retry will hit the “no new guests” path and permanently prevent recovery.

**How to replicate.** 1) Find/seed a booking with a known attendee email (E1) and another email not on the booking (E2). 2) Call the addGuests endpoint with only [E1]. Observe it returns a `BAD_REQUEST` (or otherwise distinct error) because all submitted emails were filtered out as already-attendees. 3) Call addGuests with [E2] (or [E1,E2]) and observe it succeeds, demonstrating email membership probing. 4) For retry-safety: trigger a partial failure after attendees are persisted but before invites/calendar updates (e.g., temporarily break SMTP/calendar provider or force an exception after DB write). Retry the exact same request; observe it now fails with `BAD_REQUEST` due to all guests already existing, and side effects remain missing.

**Found by** 1 cells (2 distinct report texts, 2 findings): opus: CE·medium

#### B39 — Guest email blacklist is undocumented/missing from .env.example and can be bypassed via email case differences

**Location:** `apps/web/pages/api/book/[...slug].ts:74–78`  ·  **Severity:** medium  ·  **Judge confidence:** 0.60

**Why this is real.** The code introduces an operator-configured guest blacklist via an environment variable (e.g., `process.env.BLACKLISTED_GUEST_EMAILS`) but the report indicates there is no corresponding `.env.example` entry or documentation in the PR, so self-hosted operators cannot discover or correctly configure it (feature ships effectively inert by default). Additionally, the check at lines ~74–78 compares raw strings (e.g., `blacklistedGuestEmails.includes(guest.email)` after a simple `split(',')`), meaning `Guest@Example.com` will not match a blacklist entry `guest@example.com`, allowing a trivial case-variant bypass. This is functional/security behavior, not style: it changes access-control outcomes based on string casing and undiscoverable configuration.

**How to replicate.** 1) Deploy the post-PR code without adding any new env var (as would happen for a self-host following `.env.example`): create a booking with any guest email; observe no blacklist enforcement because the feature is not configurable/discoverable. 2) Now set the env var to include a lowercased email (e.g., `BLACKLISTED_GUEST_EMAILS=guest@example.com`) and restart. 3) Attempt to create a booking with guest email `Guest@Example.com` (case changed). Expected: booking rejected due to blacklist. Actual: booking succeeds because the code performs a case-sensitive `includes` check on un-normalized strings.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·medium

#### B40 — Redundant sequential role checks (isTeamAdmin + isTeamOwner) cause unnecessary DB round-trips on addGuests

**Location:** `unknown (reports did not include a path; code not in this PR diff)` (exact lines not in diff)  ·  **Severity:** low  ·  **Judge confidence:** 0.48

**Why this is real.** The clustered reports describe code in the addGuests request path that does `await isTeamAdmin(...)` and then `await isTeamOwner(...)` sequentially. If the authorization intent is “admin OR owner”, this is either redundant (owner typically implies admin privileges) or at least should be a single combined check/query; as written it forces two separate awaited checks (very likely two DB queries) on every request. This is a genuine performance/efficiency defect (extra latency and load) rather than a style nit, but the exact file/line cannot be quoted because the reports provide no file reference and the code is not present in the PR diff.

**How to replicate.** 1) Locate the addGuests handler/mutation in the post-PR codebase and find the authorization block where it awaits `isTeamAdmin(...)` and `isTeamOwner(...)` one after another. 2) Enable DB/query logging (e.g., Prisma query logs) and run an addGuests request as a team owner/admin. 3) Observe two separate role-check queries/calls executed sequentially before the mutation proceeds; expected behavior is a single check (or one query that covers both roles) with no redundant second round-trip.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: MRV·low

#### B41 — Organizer gets duplicate “guests added” email for team bookings because organizer isn’t excluded from team member loop

**Location:** `packages/features/emails/sendAddGuestsEmails.ts:34–73`  ·  **Severity:** medium  ·  **Judge confidence:** 0.62

**Why this is real.** The function sends an organizer notification once (e.g., a call like `await organizerAddGuestsEmail({ ... , teamMember: undefined })`) and then iterates `for (const member of calendarEvent.team.members) { await organizerAddGuestsEmail({ ..., teamMember: member }) }` without excluding the organizer when they are included in `calendarEvent.team.members`. If the organizer is also a team member (common in team bookings), they match one of the looped `member`s and receive the same email a second time. This is a behavioral defect (duplicate notifications), not a style issue; the evidence here relies on the deduplicated reports since the relevant file is not part of this PR’s diff.

**How to replicate.** 1) Create a team event type where the organizer is also present in the team membership list used to populate `calendarEvent.team.members`. 2) Book the event and then add a guest (triggering `sendAddGuestsEmails`). 3) Observe the organizer’s inbox: expected is one “guest added” email; actual is two emails for the same guest addition (one from the standalone organizer send, one from the team-members loop).

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·low

#### B42 — UI shows “Additional guests / Add members” action to users who are always forbidden by the backend

**Location:** `unknown (not included in PR diff; reports did not provide a path)` (exact lines not in diff)  ·  **Severity:** medium  ·  **Judge confidence:** 0.46

**Why this is real.** The reports describe a concrete permission mismatch: the dropdown menu appends an “Add members / Additional guests” entry with no permission gating, but the submit handler/API explicitly denies everyone except the organizer, an attendee, and (admin && owner). This creates a reachable UI action for ordinary team members that can never succeed and predictably results in a Forbidden error toast after valid input. Because the relevant file is not part of this PR’s diff and no line refs were provided, this verification relies on the reported behavior/logic mismatch rather than a specific hunk in the patch.

**How to replicate.** 1) Log in as a regular team member (not organizer/attendee of the booking; not admin+owner). 2) Navigate to a team booking details page where the actions dropdown is available. 3) Open the dropdown and click “Additional guests” / “Add members”. 4) Enter valid email(s) and submit. Expected: action hidden/disabled for this role, or request succeeds. Actual: the dialog is available, but submission fails with a Forbidden error toast because backend permission checks reject the user.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·medium

#### B43 — tRPC input allows non-integer bookingId, causing Prisma Int validation error and 500 response

**Location:** `packages/trpc/server/routers/viewer/bookings.ts:1–1`  ·  **Severity:** medium  ·  **Judge confidence:** 0.55

**Why this is real.** The reports describe a tRPC input schema that validates `bookingId` as `z.number()` (no `.int()` or positivity/range constraint). Because Prisma expects an `Int` for the corresponding column, a request like `bookingId: 1.5` passes Zod validation but then fails at the Prisma client boundary with a validation error ("expected int, provided float"), which surfaces as an InternalServerError (500) instead of a client input error (400). The PR diff does not include the file/lines for this schema, so this verification relies on the reports and can be confirmed by locating the procedure that takes `bookingId` and checking whether it uses `z.number()` without `.int()`.

**How to replicate.** 1) Find the tRPC procedure that accepts `bookingId` (likely a booking read/update/cancel endpoint) and confirm its input schema uses `bookingId: z.number()` (without `.int()`). 2) Invoke the procedure (via the app UI devtools, tRPC client, or direct HTTP request) with `bookingId` set to a float, e.g. `1.5`. 3) Observe: Zod validation passes, Prisma throws a client validation error about expecting an int, and the server returns a 500. Expected: input validation rejects the request with a 4xx (e.g., 400) before reaching Prisma.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·medium

#### B44 — Newly added booking attendees are not synced to the existing external calendar event (stale attendee list passed to updateCalendarAttendees)

**Location:** `packages/core/EventManager.ts:1–1`  ·  **Severity:** high  ·  **Judge confidence:** 0.58

**Why this is real.** This issue is reported in the deduplicated reviewer notes, but the relevant code is not present in this PR diff, so it must be confirmed by inspecting the post-PR tree directly. The defect mechanism described is: the booking is updated via Prisma using an `attendee.createMany(...)`/similar write, but the in-memory event/booking attendee list used for `eventManager.updateCalendarAttendees(...)` is not refreshed/merged to include the newly created attendee emails. As a result, the calendar update call can rebuild/update the external calendar event with an attendee list that omits the just-added guests (or mis-reconciles ordering), producing a real data-sync bug rather than a style issue.

**How to replicate.** 1) Use a booking type connected to a writable external calendar (e.g., Google Calendar) so a calendar event is created. 2) Create a booking with at least one attendee/guest so the calendar event has attendees. 3) Update/edit the booking to add one or more new attendee emails (the flow that performs `createMany` for attendees and then calls `eventManager.updateCalendarAttendees`). 4) Observe: the DB shows the new attendee rows, but the external calendar event attendees do not include the newly added guests (or the attendee list is inconsistent), indicating the update used a stale attendee list rather than re-reading/merging attendees before calling the calendar update.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: MRV·low

#### B45 — Booking lookup eagerly loads organizer.credentials (including secret keys) but never uses them

**Location:** `packages/trpc/server/routers/viewer/bookings.ts:187–205`  ·  **Severity:** medium  ·  **Judge confidence:** 0.56

**Why this is real.** In the booking query’s Prisma include tree, the organizer/user relation is fetched with credentials, e.g. an include like `user: { include: { credentials: true } }` (or equivalent nested include under `organizer`). Those credential rows typically contain provider tokens/keys and are expensive/sensitive to load, but the rest of the handler never references `user.credentials`, meaning the query is doing unnecessary work and widening exposure of secrets in memory. The PR diff doesn’t show this file change, so this verification relies on the reports: a human can confirm by locating the booking query and checking that `credentials` is included but not referenced anywhere in the handler/response mapping.

**How to replicate.** 1) In the post-PR code, open the booking router/handler (file above) and find the Prisma query that fetches a booking (e.g., `prisma.booking.findUnique/findFirst`).
2) Confirm it includes organizer/user credentials (e.g., `include: { user/organizer: { include: { credentials: true }}}`).
3) Search within the same handler for any usage of `credentials` (e.g., `.credentials`, destructuring, passing into downstream calls). Expected: credentials are used (or explicitly selected fields). Actual: credentials are never read, yet will be fetched from the DB.
4) (Runtime confirmation) Hit the endpoint that returns booking details (the one using this query) with a test organizer that has many credentials; observe via Prisma query logging/DB logs that it performs extra reads from the credentials table compared to a version without that include.

**Found by** 1 cells (1 distinct report texts, 1 findings): fable: van·high

#### B46 — Attendee opt-out flag ignored when sending guest-change/new-invite emails

**Location:** `packages/emails/email-manager.ts:539–560`  ·  **Severity:** high  ·  **Judge confidence:** 1.00

**Why this is real.** At ~line 539 the code reportedly does `emailstosend.push(...calendarevent.attendees.map((attendee) => { ... }))` and, inside that mapping, constructs/schedules attendee-facing emails (new-invite and/or existing-attendee/guest-change notifications) without first checking the attendee opt-out setting (`disableStandardEmails.all.attendee`). This means even attendees who explicitly disabled standard attendee emails can still be included in the send list and receive notifications, violating the intended opt-out behavior. The PR diff does not include this file/hunk, so this verification relies on the referenced post-PR line location from the reports.

**How to replicate.** 1) Configure an attendee user/profile such that `disableStandardEmails.all.attendee` is enabled (or the equivalent setting that is mapped to this flag in code). 2) Create or update a calendar event in a way that triggers attendee notifications (e.g., add a new attendee or change event details that send “guest change” emails). 3) Observe outbound emails: expected behavior is that the opted-out attendee should not receive the new-invite/guest-change emails; actual behavior is they are still included in `emailsToSend` and receive the notification.

**Found by** 1 cells (1 distinct report texts, 1 findings): terra: MRV·low

#### B47 — Missing i18n key causes add-guests permission error to display raw `forbidden: youdonothavepermission`

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:55–55`  ·  **Severity:** low  ·  **Judge confidence:** 0.86

**Why this is real.** The handler throws a TRPC error using a message string that is intended to be translated: `throw new TRPCError({ code: "FORBIDDEN", message: "youdonothavepermission" });` (reported at line 55). Client UI error handling commonly feeds `error.message` into i18n (e.g., `t(error.message)`); if `common.json` does not define a `youdonothavepermission` key, the UI will fall back to rendering the raw key (often prefixed by the error code), producing a user-visible string like `forbidden: youdonothavepermission` instead of a localized message.

**How to replicate.** 1) Use an account that can view a booking but does not have permission to modify it (e.g., not the organizer/host for the booking). 2) Trigger the UI flow that calls the `viewer.bookings.addGuests` mutation (Add Guests dialog). 3) Observe the error response path that executes the `FORBIDDEN` throw in `addguests.handler.ts`. Expected: a properly translated “You do not have permission …” message. Actual: the UI renders the literal key (e.g., `forbidden: youdonothavepermission`) because the translation key is missing from `common.json`.

**Found by** 1 cells (1 distinct report texts, 1 findings): sol: MRV·high

#### B48 — Add Guests button silently no-ops when all email rows are removed

**Location:** `apps/web/components/dialogs/AddGuestsDialog.tsx:49–51`  ·  **Severity:** medium  ·  **Judge confidence:** 0.62

**Why this is real.** The reports point to `handleAdd` in `addguestsdialog.tsx` lines 49-51 containing an early return when there are no email rows (e.g., `if (!emails.length) return;`). This makes the primary action (clicking “Add”) do nothing with no error message, toast, inline validation, or disabled button state, so users receive zero feedback. The PR diff does not include this file, so this verification relies on the reviewers’ line references and the described control flow.

**How to replicate.** Open the Add Guests dialog in the UI. Remove/delete all guest email rows so the list becomes empty, then click the “Add” button. Expected: the UI should either prevent the action (disable button) or show a validation message like “Please add at least one email.” Actual: the handler returns early and the dialog appears to do nothing (no feedback).

**Found by** 1 cells (1 distinct report texts, 1 findings): opus: van·high

#### B49 — Null eventType.teamId is coerced to 0, causing incorrect team lookup/authorization checks

**Location:** `packages/trpc/server/routers/viewer/eventTypes/get.handler.ts:128–136`  ·  **Severity:** medium  ·  **Judge confidence:** 0.38

**Why this is real.** The reported defect is that when `eventType.teamId` is `null` (personal event type), the code coerces it to `0` and then performs team-related logic against that value (e.g., `teamId: eventType.teamId || 0`). This changes the meaning of `null` (no team) into a concrete team id and can cause incorrect authorization/lookup behavior (checking membership/access against a non-existent team 0 instead of skipping team checks). The file is not part of this PR’s diff, so verification relies on locating this coercion pattern in the post-PR tree as described by the reports.

**How to replicate.** 1) Create/use a personal EventType where `teamId` is NULL in the DB (not a team event). 2) Hit the code path that performs a team authorization or team fetch for that EventType (e.g., fetch/update event type via the viewer eventTypes router). 3) Observe in logs/debugger that the team query/check uses `teamId = 0` rather than skipping team logic; expected behavior is that `null` teamId should bypass team membership/team fetch checks, but actual behavior performs them against team 0 and can incorrectly deny access or behave inconsistently.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: van·high

---

## PR 10967 — 55 distinct real bugs (6 goldens + 49 the goldens missed)
(<https://github.com/calcom/cal.com/pull/10967>)

### Bug index

| # | sev | location | title | found by (cells) |
|---|---|---|---|---|
| B1 | high | `packages/lib/CalendarService/googlecalendar.ts:280–335` | Google Calendar update/delete falls back to primary when externalCalendarId is missing, ignoring destination calendar | 66 |
| B2 | high | `packages/lib/CalendarService/BaseCalendarService.ts:225–245` | Collective event creation always targets destinationCalendar[0] instead of the calendar matching the active host credential | 58 |
| B3 | high | `packages/features/bookings/lib/handlenewbooking.ts:1078–1082` | Collective hosts' destination calendars are dropped when organizer has none due to optional-chained push on null array | 45 |
| B4 | high | `packages/core/eventmanager.ts:118–120` | Google Meet event creation can crash when destinationCalendar is missing/empty | 41 |
| B5 | high | `packages/features/bookings/lib/handlecancelbooking.ts:435–454` | Recurring collective cancellation deletes only the first calendar reference, leaving co-host events undeleted | 39 |
| B6 | high | `packages/core/eventmanager.ts:552–560` | Merge/reschedule cleanup deletes only one old calendar reference, leaving other hosts' events stale | 30 |
| B7 | high | `packages/features/bookings/lib/handlenewbooking.ts:1871–1879` | Collective bookings persist only destinationCalendar[0], dropping co-host destination calendars | 30 |
| B8 | high | `packages/core/eventmanager.ts:169–170` | Non-calendar (video) booking references lose credentialId due to ternary assigning undefined | 27 |
| B9 | high | `packages/core/eventmanager.ts:335–384` | Legacy no-credential destination path creates events without externalCalendarId, breaking later update/delete routing | 26 |
| B10 | critical | `packages/core/eventmanager.ts:517–545` | Unscoped credential lookup by ID allows cross-tenant calendar writes using another user’s OAuth credential | 24 |
| B11 | medium | `packages/app-store/googlecalendar/lib/calendarservice.ts:122–206` | Google Calendar events for non-first collective hosts incorrectly use destinationCalendars[0] as organizer | 18 |
| B12 | high | `packages/trpc/server/routers/viewer/organizations/create.handler.ts:150–156` | Organization slug assignment logic inverted, breaking non-billing org URLs and bypassing requestedSlug gate in billing mode | 16 |
| B13 | medium | `packages/features/bookings/lib/handlenewbooking.ts:722–762` | loadUsers wraps validation errors as 500 and leaks Prisma error messages as 400 | 14 |
| B14 | high | `packages/core/eventmanager.ts:505–545` | DB-fetched calendar credential missing app relation is silently skipped or passed as undefined, causing missing/failed calendar sync | 13 |
| B15 | high | `packages/core/eventmanager.ts:374–385` | Credential-less destinations fan out to all matching credentials, creating duplicate external calendar events | 13 |
| B16 | high | `packages/core/eventmanager.ts:590–607` | Reschedule calendar update errors are swallowed: catch returns [] when calendarReference is unset and logs were removed | 13 |
| B17 | high | `packages/app-store/googlecalendar/lib/calendarservice.ts:145–165` | Google createEvent falls back to 'primary' when destination calendar has null credentialId, ignoring configured externalId | 11 |
| B18 | high | `packages/types/calendar.d.ts:134–136` | Booking webhook payload breaks backward compatibility by changing destinationCalendar from object/null to array | 11 |
| B19 | high | `organizations/create.handler.ts:148–152` | Organization slug gating inverted by IS_TEAM_BILLING_ENABLED ternary, breaking slug/requestedSlug flow | 10 |
| B20 | high | `packages/core/eventmanager.ts:356–371` | Collective booking can report success while silently skipping co-host calendar creation when destination credential is missing | 10 |
| B21 | high | `apps/web/pages/api/bookings/[id]/cancel/handleCancelBooking.ts:418–470` | Recurring cancellation delete sweep runs once per calendar reference, causing redundant deleteEvent calls (O(n) duplicates/404s) | 9 |
| B22 | high | `packages/features/ee/payments/api/webhook.ts:207–229` | Paid collective bookings only create calendar event for a single host because payment webhooks rebuild destinationCalendar as a 1-element array | 7 |
| B23 | low | `packages/trpc/server/routers/viewer/bookings/requestreschedule.handler.ts:239–242` | requestReschedule handler drops user.destinationCalendar fallback, producing empty destinationCalendar array | 6 |
| B24 | high | `packages/lib/CalendarManager/eventmanager.ts:508–522` | updateAllCalendarEvents can call updateEvent with missing/stale credential, aborting updates for other references | 6 |
| B25 | high | `packages/trpc/server/routers/viewer/booking/eventmanager.ts:553–558` | Reschedule/merge deletes only the first calendar reference, orphaning events on other hosts’ calendars | 6 |
| B26 | high | `packages/lib/handleCancelBooking.ts:430–540` | Recurring cancellation deletion sweep runs inside calendarReference loop, causing duplicate deleteEvent calls per host/reference | 5 |
| B27 | high | `packages/features/bookings/lib/handlenewbooking.ts:724–763` | Public booking endpoint leaks raw Prisma error messages and misclassifies DB failures as HTTP 400 in loadUsers() | 5 |
| B28 | high | `apps/api/src/integrations/googlecalendar/calendarservice.ts:254–256` | Inverted ternary makes destination-calendar fallback dead, leaving calendarId undefined for update/delete | 4 |
| B29 | high | `eventmanager.ts:355–381` | Missing credentialId branch fans out over all credentials per destination, creating duplicate external calendar events | 4 |
| B30 | high | `apps/web/playwright/webhook.e2e.ts:119–125` | Webhook payload uses inconsistent types for destinationCalendar (null vs []) across booking triggers | 4 |
| B31 | high | `packages/core/eventmanager.ts:370–385` | Missing external calendar id when creating event without credentialId causes booking references to store undefined externalCalendarId | 4 |
| B32 | medium | `packages/lib/CalendarManager/eventmanager.ts:596–608` | updateAllCalendarEvents swallows exceptions (no log) and may return empty results indistinguishable from 'no calendars' | 3 |
| B33 | high | `packages/features/bookings/lib/handlenewbooking.ts:735–760` | Dynamic group booking loadUsers no longer selects organization.slug (and may return undefined users), breaking org-aware booker URLs | 3 |
| B34 | high | `packages/core/eventmanager.ts:339–365` | Duplicate calendar events when destination calendars contain duplicate (credentialId, externalId) entries | 3 |
| B35 | critical | `packages/lib/eventmanager.ts:341–530` | Cross-tenant OAuth credential loading by raw credentialId without ownership validation | 3 |
| B36 | high | `packages/core/calendarmanager.ts:249–249` | Calendar createEvent failure logs full CalendarEvent object including attendee PII and credential IDs | 3 |
| B37 | critical | `packages/core/eventmanager.ts:493–530` | Stale calendar credential reused across references in updateAllCalendarEvents loop | 2 |
| B38 | high | `packages/core/eventmanager.ts:595–607` | eventmanager.update swallows errors and returns [] when calendarReference is undefined | 2 |
| B39 | critical | `packages/lib/calendarClient.ts:262–266` | createEvent error logging serializes full calEvent and raw provider error (PII + OAuth token leak to logs) | 2 |
| B40 | high | `unknown (not in PR diff); search post-PR tree for `teamDestinationCalendars` and `users.slice(1)` in the collective booking calendar-routing code` | Collective booking destination calendars skip first host and may duplicate organizer due to users.slice(1) assumption | 2 |
| B41 | medium | `apps/web/pages/api/book/[...slug].ts:712–755` | loadUsers validation errors fall through to generic 500 instead of returning a 4xx | 2 |
| B42 | high | `eventmanager.ts:169–170` | Video booking references persist with undefined credentialId, breaking later cancel/update lookups | 2 |
| B43 | high | `packages/core/eventmanager.ts:336–408` | Uncaught prisma/calendar lookup error aborts createAllCalendarEvents loop, failing entire booking and orphaning already-created events | 2 |
| B44 | high | `packages/core/eventmanager.ts:496–586` | CRM `othercalendar` references updated twice due to overly broad calendar reference filter | 2 |
| B45 | high | `packages/features/bookings/lib/handlecancelbooking.ts:638–646` | Cancel booking fallback loads Credential without app slug/name, breaking getCalendar resolution | 2 |
| B46 | high | `packages/lib/EventManager.ts:520–545` | updateAllCalendarEvents swallows early errors by returning [] when calendarReference is uninitialized | 1 |
| B47 | high | `packages/core/eventmanager.ts:337–520` | Booking creation performs sequential awaits and N+1 credential lookups, making latency scale linearly with host/destination count | 1 |
| B48 | high | `packages/features/bookings/lib/handlenewbooking.ts:1078–1084` | Collective booking webhook payload leaks all hosts' destinationCalendar identifiers | 1 |
| B49 | high | `packages/app-store/googlecalendar/lib/CalendarService.ts:228–259` | Multi-host Google Meet bookings create different Meet links per host calendar event | 1 |
| B50 | high | `apps/web/lib/server/loadUsers.ts:70–115` | loadUsers no longer selects organization.slug, breaking org-aware routing/links | 1 |
| B51 | high | `packages/features/webhooks/lib/payloads/booking.ts:1–40` | Webhook payload breaks backward compatibility: `destinationcalendar` changed from object/null to array | 1 |
| B52 | high | `packages/features/bookings/lib/handlecancelbooking.ts:482–495` | handleCancelBooking builds deletion Promise array with undefined entries, risking skipped/duplicated external calendar deletions | 1 |
| B53 | high | `packages/core/eventmanager.ts:357–366` | Fallback credential construction ignores `invalid` flag and can use revoked/broken OAuth credentials | 1 |
| B54 | high | `packages/core/eventmanager.ts:542–570` | Reschedule can persist in DB even when some host calendar updates fail (no rollback/retry) | 1 |
| B55 | high | `packages/types/calendar.d.ts:171–190` | Calendar interface migration to destinationCalendar[] + credentialId is not enforced; unmigrated implementers still type-check | 1 |

### Verification cards

#### B1 — Google Calendar update/delete falls back to primary when externalCalendarId is missing, ignoring destination calendar

**Location:** `packages/lib/CalendarService/googlecalendar.ts:280–335`  ·  **Severity:** high  ·  **Judge confidence:** 0.68

**Why this is real.** The reported code path derives the target calendar from `externalcalendarid` using an identity lookup like `selectedcalendar = calendars.find((cal) => cal.externalid === externalcalendarid)?.externalid` and then calls the API with `calendarId: selectedcalendar ?? "primary"`. When `externalcalendarid` is falsy/absent, the `find(...)` predicate compares `cal.externalid` to `undefined`, yielding `undefined`, so the code falls through to `"primary"` instead of using the event’s configured destination calendar (the previous behavior described in the reports). This causes updates/deletes to be applied to the wrong calendar, which is a functional defect, not a style issue; the lookup is also a no-op because it returns the same `externalid` it searched for.

**How to replicate.** 1) Configure a Google integration where the destination calendar is a non-primary calendar (e.g., a secondary calendar). 2) Create an event that is stored/handled without `externalCalendarId` populated (e.g., legacy/migrated event record or any path that omits it). 3) Trigger an update or deletion of that event via the Cal.com UI/API. Expected: the update/delete request targets the configured destination calendar. Actual: the integration sends the request to Google Calendar with `calendarId` resolved as `"primary"`, so it updates/deletes in the user’s primary calendar (or fails to find the event if it only exists in the destination calendar).

**Found by** 66 cells (314 distinct report texts, 314 findings): fable: van·high, van·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium, van·xhigh; sonnet: CE·low, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; terra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, van·high, van·low, van·medium

#### B2 — Collective event creation always targets destinationCalendar[0] instead of the calendar matching the active host credential

**Location:** `packages/lib/CalendarService/BaseCalendarService.ts:225–245`  ·  **Severity:** high  ·  **Judge confidence:** 0.60

**Why this is real.** All clustered reports describe the same concrete logic error: during collective/multi-host event creation the code unconditionally selects the first destination calendar entry (e.g., `destinationCalendar[0]`) rather than selecting the destination calendar associated with the current credential/host being processed. This means when iterating through multiple hosts/credentials, every host attempts to create the event in the first host’s destination calendar, which is incorrect and can also fail with permissions. The PR diff does not include this file, so verification must be done by inspecting the current code in this area for a hard-coded/index-0 destination calendar selection.

**How to replicate.** 1) Configure a collective event type with 2+ hosts. 2) Connect different calendars for each host (Office 365 or Lark) and set different destination calendars per host (so host A’s destination differs from host B’s). 3) Create a booking for that event type. Expected: each host’s calendar event is created/targeted using that host’s own destination calendar. Actual (bug): the system uses destinationCalendar[0] for all hosts, so events get created in the first host’s calendar (or fail for other hosts due to lack of access to host A’s calendar).

**Found by** 58 cells (254 distinct report texts, 254 findings): fable: van·high, van·low, van·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·xhigh; sonnet: CE·high, CE·low, MRV·high, MRV·medium, van·high, van·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium; sol: CE·high, CE·medium, MRV·high, MRV·medium, van·high, van·medium, van·xhigh; terra: CE·high, CE·low, CE·medium, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; astra: CE·high, CE·low, MRV·high, MRV·low, van·high, van·low, van·medium

#### B3 — Collective hosts' destination calendars are dropped when organizer has none due to optional-chained push on null array

**Location:** `packages/features/bookings/lib/handlenewbooking.ts:1078–1082`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** At ~line 1078 the code appends collective/team calendars via an optional-chained mutation like `evt.destinationcalendar?.push(...teamdestinationcalendars)`. If `evt.destinationcalendar` is `null`/`undefined` (e.g., neither the event type nor the organizer has a destination calendar), the optional chaining makes this a silent no-op, so `teamdestinationcalendars` are never persisted onto `evt`. This is a functional defect (loss of intended delivery destinations), not a style issue; per the reports, this file/line is not in the PR diff, so this verification relies on the reported post-PR code snippet/line reference.

**How to replicate.** 1) Create a collective/team event type where the organizer has no destination calendar configured (and the event type itself does not specify one). 2) Add at least one cohost/team member who does have a destination calendar configured. 3) Create a booking for that collective event. Expected: the booking is written/synced to the cohost(s) destination calendar(s). Actual: no cohost destination calendars are attached because `evt.destinationcalendar` remains null and `evt.destinationcalendar?.push(...)` discards `teamdestinationcalendars`.

**Found by** 45 cells (155 distinct report texts, 155 findings): fable: van·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low; sonnet: CE·high, MRV·high, MRV·low, MRV·medium, van·high, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low, van·medium, van·xhigh; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high; sol: CE·high, MRV·high, MRV·medium, van·high, van·medium; terra: CE·medium, MRV·low, MRV·medium, van·xhigh; astra: MRV·low, van·high, van·low, van·medium

#### B4 — Google Meet event creation can crash when destinationCalendar is missing/empty

**Location:** `packages/core/eventmanager.ts:118–120`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** Multiple deduplicated reports point to a direct null/undefined dereference around lines 118–120, e.g. code effectively does `const destinationcalendar = calendarEvent.destinationCalendar[0];` and then accesses `destinationcalendar.integration` without guarding for `destinationCalendar` being undefined or an empty array. If `destinationCalendar` is optional (or can be empty), `destinationcalendar` becomes undefined and `.integration` throws a TypeError, aborting event creation before any intended fallback (e.g., to Cal Video) can run. The file is not in this PR’s diff per the prompt, so this verification relies on the consistent line-referenced reports.

**How to replicate.** 1) Configure an event type/location that uses Google Meet (or triggers Google Meet conferencing creation) but does not have a destination calendar selected/connected (destinationCalendar undefined or []). 2) Attempt to create a booking for that event type. Expected: booking proceeds and either creates Google Meet via a valid calendar integration or falls back to Cal Video when no destination calendar exists. Actual: runtime exception (TypeError) occurs when the code reads `destinationcalendar.integration`, preventing booking/event creation.

**Found by** 41 cells (92 distinct report texts, 92 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium; sonnet: CE·high, CE·low, MRV·high, MRV·low, MRV·medium, van·xhigh; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·low; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·high; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low; terra: CE·high, CE·low, CE·medium, MRV·high, MRV·low; astra: CE·high, CE·low, CE·medium

#### B5 — Recurring collective cancellation deletes only the first calendar reference, leaving co-host events undeleted

**Location:** `packages/features/bookings/lib/handlecancelbooking.ts:435–454`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple reports point to the same code pattern in this range: using `updbooking.references.find(...)` (i.e., selecting a single first matching reference) and relying on only the organizer’s credentials when deleting calendar events. Because collective bookings can create multiple `references` per occurrence (one per host/calendar), deleting only the first reference means additional hosts’ calendar events are never targeted and remain active after “cancel all remaining instances”. The PR diff does not include this file, so verification relies on reading the current code around lines ~435–454 and confirming it only picks one reference/credential instead of iterating all references/hosts.

**How to replicate.** 1) Create a Collective event type with 2+ hosts, where each host has an active connected calendar integration. 2) Book a recurring series (multiple future occurrences) so that each booking occurrence stores multiple calendar `references` (one per host) and creates events on each host’s calendar. 3) Trigger cancellation of “all remaining instances” for the series. 4) Expected: every occurrence is removed from every host’s external calendar. Actual: only the event corresponding to the first matched `references.find(...)` (typically the organizer/first host) is deleted; other hosts’ events remain on their calendars for the cancelled occurrences.

**Found by** 39 cells (88 distinct report texts, 88 findings): fable: van·high; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·xhigh; glm-flash: CE·high, CE·medium, MRV·high, van·high; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·high, van·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·medium, van·high, van·low, van·medium, van·xhigh; terra: CE·high, CE·low, MRV·low; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, van·high, van·low, van·medium

#### B6 — Merge/reschedule cleanup deletes only one old calendar reference, leaving other hosts' events stale

**Location:** `packages/core/eventmanager.ts:552–560`  ·  **Severity:** high  ·  **Judge confidence:** 0.66

**Why this is real.** Multiple independent reports pinpoint the same code region (~lines 552–554) where cleanup during merge/reschedule does `booking.references.find(...)` to locate an old calendar reference to delete. Using `find()` returns only the first matching reference, so the subsequent deletion only removes one calendar event even when `booking.references` contains multiple entries (e.g., one per collective/multi-host calendar). As noted in the prompt, this file was not part of the PR diff we can quote directly here, so this verification relies on the deduplicated reports’ consistent line references and described logic.

**How to replicate.** 1) Create a collective/multi-host event type where multiple hosts each have their own connected calendar and the booking creates multiple calendar references (one per host). 2) Book the event so `booking.references` has >1 calendar reference. 3) Trigger the merge/reschedule path that performs “old booking/calendar cleanup” (e.g., reschedule the booking, or merge bookings as implemented in eventmanager). 4) Inspect each host calendar: expected = all old events are deleted and only the new event remains; actual = only one host’s old calendar event is deleted (the one corresponding to the first match from `find()`), while the other host(s) keep stale/orphaned events and their old time slots remain blocked.

**Found by** 30 cells (72 distinct report texts, 72 findings): fable: van·high, van·low; opus: CE·high, CE·low, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·medium, MRV·high, MRV·low, van·high; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium, van·high, van·medium; sol: CE·high, CE·medium, MRV·high, van·high, van·low, van·medium, van·xhigh; terra: van·high, van·low, van·medium, van·xhigh; astra: CE·high

#### B7 — Collective bookings persist only destinationCalendar[0], dropping co-host destination calendars

**Location:** `packages/features/bookings/lib/handlenewbooking.ts:1871–1879`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** Multiple reports point to the same concrete code pattern in `handlenewbooking.ts` around ~1877: the booking persistence logic connects only `destinationCalendar[0]` (e.g., `destinationCalendar: { connect: destinationCalendar?.[0] ? { id: destinationCalendar[0].id } : undefined }`). This is a real functional defect for collective bookings because `destinationCalendar` is built as an array containing calendars for all hosts, but only the first element is written to the DB, so downstream flows that reconstruct the event from the stored booking can only “see” the organizer’s calendar. The PR does not modify this file per the prompt, so verification relies on reading the existing code at the referenced lines.

**How to replicate.** 1) Configure a collective event type with 2+ hosts, where each host has a different connected destination calendar (e.g., Google Calendar A for host1, Google Calendar B for host2). 2) Create a booking that is not immediately finalized (e.g., requires payment or organizer confirmation / deferred creation path). 3) Inspect the created Booking record (DB or API) and confirm it has only one `destinationCalendar` linked (the first/organizer). 4) Proceed with the deferred step (confirm booking or complete payment) and observe only one calendar event gets created / downstream cancellation & reminder flows only operate on that single calendar; expected behavior is events/operations for all hosts’ destination calendars.

**Found by** 30 cells (58 distinct report texts, 58 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, van·high, van·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·medium, van·high, van·low, van·medium; sol: CE·high, CE·medium, MRV·high, MRV·low, van·high; terra: MRV·low, van·medium; astra: MRV·low

#### B8 — Non-calendar (video) booking references lose credentialId due to ternary assigning undefined

**Location:** `packages/core/eventmanager.ts:169–170`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple independent reports point to the same post-PR code around lines 169-170 setting `credentialid` via a ternary like `credentialid: isCalendarType ? result.credentialid : undefined`. That logic overwrites/clears `credentialid` specifically for non-calendar integrations (e.g., video conferencing), even when `result.credentialid` exists, which breaks later flows that need the creating credential to update/delete the external meeting. The PR diff isn’t provided here, so this verification relies on the consistent, line-specific reports and can be confirmed by reading those lines in the post-PR tree.

**How to replicate.** 1) Configure a video integration that stores credentials (e.g., Zoom/Google Meet via integration) for a user/team. 2) Create a booking that generates a video meeting reference (a non-calendar reference). 3) Inspect the persisted booking references (DB/returned payload): expected `credentialid` to match the integration credential used, actual `credentialid` is `undefined` for the video reference. 4) Attempt an operation that updates/deletes the external meeting (reschedule/cancel): expected the system to locate the correct credential and update/delete the video meeting, actual failure/missing-credential behavior because the reference no longer carries the credential identifier.

**Found by** 27 cells (49 distinct report texts, 49 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·high, MRV·medium; glm-flash: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium, van·high; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium; sol: MRV·high, van·high, van·medium, van·xhigh; terra: van·high; astra: MRV·high, van·high, van·low, van·medium

#### B9 — Legacy no-credential destination path creates events without externalCalendarId, breaking later update/delete routing

**Location:** `packages/core/eventmanager.ts:335–384`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The reports point to a specific compatibility branch in `packages/core/eventmanager.ts` (around lines ~335–380) where, when a destination calendar has no `credentialId`, the code calls `createEvent(c, event)` (e.g., reported at ~line 371) instead of passing the destination calendar’s `externalId`/calendar identifier. In the other branch, the destination identifier is forwarded to the calendar service, but in this legacy branch it is omitted, which causes the created booking reference to persist `externalCalendarId` as `undefined` and/or creates the event in the provider’s “primary” calendar while the app thinks it targeted the selected destination. The PR diff does not include this file, so this verification relies on the reported line references and the described call-site mismatch.

**How to replicate.** 1) Configure a destination calendar entry that has an `externalId` (calendar id) but no `credentialId` (legacy/compat destination). 2) Create a booking that triggers `createAllCalendarEvents`/event creation for that destination. 3) Observe that the provider event is created in the default/primary calendar (or at least without the intended calendar id), and the persisted booking reference row has `externalCalendarId` missing/undefined. 4) Attempt to reschedule/cancel (update/delete) the booking: expected behavior is to route to the correct destination calendar event; actual behavior is failure to find the event or acting on the wrong calendar because the reference lacks a valid `externalCalendarId`.

**Found by** 26 cells (46 distinct report texts, 46 findings): opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium; glm-flash: CE·high, CE·medium, MRV·high, MRV·medium, van·high, van·medium, van·xhigh; glm-vis: CE·high, CE·low, MRV·high, MRV·low, MRV·medium, van·high; sol: van·high, van·low, van·medium; terra: MRV·high, van·medium, van·xhigh

#### B10 — Unscoped credential lookup by ID allows cross-tenant calendar writes using another user’s OAuth credential

**Location:** `packages/core/eventmanager.ts:517–545`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74  ·  ⚠️ `distinct=false` (cluster may span two bugs)

**Why this is real.** The reported code path around line ~517 performs an unscoped credential fetch like `await prisma.credential.findUnique({ where: { id: bookingReference.credentialId } })` (and similarly around ~344 for `destinationCalendar.credentialId`) and then uses that credential (including its key/token) to update/create external calendar events. There is no accompanying authorization check that the fetched credential belongs to a host of the booking/event type (or the same team) and no validation that the credential is not invalid/disabled. This is a real access-control bug: any flow that can cause `bookingReference.credentialId` / `destinationCalendar.credentialId` to point at a foreign credential will operate on external calendars with another tenant’s OAuth token.

**How to replicate.** 1) Obtain (or guess/leak) a victim user’s `credential.id` (calendar OAuth credential) in the same Cal.com deployment. 2) Create or modify a booking reference / destination calendar record so that `bookingReference.credentialId` (reschedule/update path) or `destinationCalendar.credentialId` (create path) equals the victim credential id. 3) Trigger the corresponding action: reschedule a booking (updateAllCalendarEvents), create a booking (create external event), or cancel a booking (delete external event in handleCancelBooking). Expected: the system should reject/ignore the foreign credential and only use credentials owned by an authorized host/team member. Actual: the system loads the victim credential by raw ID and performs the external calendar operation using the victim’s token.

**Found by** 24 cells (60 distinct report texts, 60 findings): fable: van·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·medium; sonnet: MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·medium, MRV·medium; terra: MRV·high

#### B11 — Google Calendar events for non-first collective hosts incorrectly use destinationCalendars[0] as organizer

**Location:** `packages/app-store/googlecalendar/lib/calendarservice.ts:122–206`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple reports point to createEvent/updateEvent constructing the Google event payload with the organizer attendee email always derived from the first destination calendar (e.g., using `destinationCalendars[0].externalId`), even when the code selects a different calendar by `credentialId`/`externalCalendarId` for insertion/update. This is a real functional defect: when writing the event into host B’s calendar, the payload still hardcodes host A’s calendar email as the organizer/primary attendee, so the event metadata in host B’s copy is wrong. The PR does not modify this file per the evidence pack note, so verification relies on the referenced lines in the existing post-PR tree as reported.

**How to replicate.** 1) Configure a collective/multi-host booking with at least two Google Calendar-connected hosts (Host A and Host B), each with their own destination calendar (different `externalId`/calendar email). 2) Create a booking that should be written to both hosts’ calendars (Cal.com will call Google createEvent per host credential). 3) Inspect the event created on Host B’s Google Calendar: expected organizer/organizer-attendee email should match Host B’s calendar/destination externalId; actual organizer/organizer-attendee email is Host A’s destination (`destinationCalendars[0].externalId`). 4) Reschedule/update the booking (triggering updateEvent): Host B’s event organizer is again rewritten to Host A due to the same index-0 logic.

**Found by** 18 cells (25 distinct report texts, 25 findings): fable: van·high; opus: CE·high, MRV·high, MRV·medium; sonnet: MRV·high, MRV·medium, van·xhigh; glm-flash: MRV·low, van·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; sol: van·low; terra: CE·low, MRV·medium, van·low

#### B12 — Organization slug assignment logic inverted, breaking non-billing org URLs and bypassing requestedSlug gate in billing mode

**Location:** `packages/trpc/server/routers/viewer/organizations/create.handler.ts:150–156`  ·  **Severity:** high  ·  **Judge confidence:** 0.90

**Why this is real.** In the organization create payload, the PR changed slug assignment from `...(!IS_TEAM_BILLING_ENABLED && { slug })` to `...(IS_TEAM_BILLING_ENABLED ? { slug } : {})`, while also setting `metadata` to `...(IS_TEAM_BILLING_ENABLED ? { requestedSlug: slug } : {})`. This inverts the prior behavior: when team billing is disabled, the organization is now created with no `slug` at all; when team billing is enabled, it sets the live `slug` immediately (and also sets `requestedSlug`), undermining any flow that relied on `requestedSlug` being a pending/approved slug before `slug` is applied. This is a functional behavior change (not style), because it directly changes persisted fields for org routing/lookup and billing/verification gating.

**How to replicate.** 1) Run a build/environment where `IS_TEAM_BILLING_ENABLED` is false (e.g., self-hosted config). 2) Call the org creation endpoint (tRPC viewer.organizations.create) with an input that includes a desired slug (e.g., "acme"). Expected (pre-PR): the created organization row has `slug="acme"` so `/org/acme` (or equivalent org resolution) works. Actual (post-PR): `slug` is omitted/empty because the spread uses `IS_TEAM_BILLING_ENABLED ? { slug } : {}`, so the org has no slug and URL resolution by slug fails.

For billing-enabled mode: 1) Set `IS_TEAM_BILLING_ENABLED` true. 2) Create an org with slug "acme". Expected: `metadata.requestedSlug="acme"` is stored and `slug` remains unset until billing/verification approves it. Actual: `slug` is set immediately due to `IS_TEAM_BILLING_ENABLED ? { slug } : {}`, allowing immediate use of the live slug even though `requestedSlug` indicates a pending slug flow.

**Found by** 16 cells (25 distinct report texts, 25 findings): opus: CE·high, CE·low, MRV·high, MRV·medium; sonnet: MRV·low, MRV·medium; glm-flash: CE·high, CE·medium; glm-vis: CE·high, CE·low, CE·medium; sol: CE·high; terra: MRV·high, MRV·low; astra: CE·high, CE·low

#### B13 — loadUsers wraps validation errors as 500 and leaks Prisma error messages as 400

**Location:** `packages/features/bookings/lib/handlenewbooking.ts:722–762`  ·  **Severity:** medium  ·  **Judge confidence:** 0.68

**Why this is real.** Based on the clustered reports (the file was not included in the PR diff, so verification is by reading the post-PR code around the referenced lines), `loadUsers` now throws plain `Error` for client-input validation such as an empty/missing `dynamicUserList` (e.g., `throw new Error(...)` around ~727) and then catches broadly and rethrows a generic 500 (e.g., `throw new HttpError({ statusCode: 500, message: "Unable to load users" })` around ~761-762). This loses the original message and misclassifies a client error (should be 4xx) as a server error (500). Additionally, the catch branch reportedly does `if (error instanceof Prisma.PrismaClientKnownRequestError) throw new HttpError({ statusCode: 400, message: error.message })`, which both misclassifies server-side DB failures as 400 and leaks internal Prisma error details to API clients.

**How to replicate.** 1) Find the booking API/code path that calls `loadUsers` in `handleNewBooking` with a "dynamic booking" configuration.
2) Trigger it with an empty or missing `dynamicUserList` (e.g., dynamic booking request where the selection yields zero users). Expected (pre-change/intended): a 4xx dynamic-booking error (often 404/400) indicating no users found/invalid selection. Actual (post-change): response becomes a 500 with a generic "Unable to load users" and the original validation message is lost.
3) Trigger a Prisma known request error inside `loadUsers` (e.g., malformed query inputs that produce a PrismaClientKnownRequestError). Expected: 5xx with sanitized message (server failure). Actual: 400 with the raw `error.message` from Prisma exposed in the response body.

**Found by** 14 cells (18 distinct report texts, 18 findings): fable: van·low; opus: CE·high, CE·medium; sonnet: MRV·medium, van·xhigh; glm-flash: MRV·high, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium, van·high, van·medium; sol: MRV·medium

#### B14 — DB-fetched calendar credential missing app relation is silently skipped or passed as undefined, causing missing/failed calendar sync

**Location:** `packages/core/eventmanager.ts:505–545`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** The code path described in the reports fetches a credential from the DB during multi-reference update/create flows but does not guarantee the related `app` is loaded, and then either (a) silently skips when `credential.app?.slug` is falsy or (b) still enqueues an update with an undefined credential. Reported offending logic includes the pattern “db-fetched credential with null `app.slug` is silently skipped — no error, no result entry” (createAllCalendarEvents around ~345–360) and “if `app?.slug` is falsy, `credential` stays undefined and `updateEvent(undefined, ...)` is pushed” (updateAllCalendarEvents around ~505–542), which then throws inside calendar instantiation (e.g., reading `credential.appname`) and can cause `Promise.all` to reject and discard other successful updates.

**How to replicate.** 1) Ensure an event has multiple calendar references (e.g., host + additional calendars) so `createAllCalendarEvents` / `updateAllCalendarEvents` iterates over more than one destination. 2) Make one referenced credential resolvable only via DB lookup and ensure it lacks the `app` relation/slug (e.g., DB row exists but `app` not joined/loaded or is null/invalid), so `credential.app?.slug` is falsy. 3a) Create a booking: expected = an event is created on every referenced calendar; actual = one destination is skipped with no log/result entry and booking succeeds but the calendar event is missing. 3b) Reschedule/update the booking: expected = other calendars still update even if one reference is invalid; actual = `updateEvent` is called with `undefined`, throws during calendar selection, `Promise.all` rejects, and the catch can drop/obscure other successful update results.

**Found by** 13 cells (21 distinct report texts, 21 findings): opus: CE·high, CE·low; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium, van·xhigh; glm-vis: CE·medium, MRV·high, MRV·medium, van·low

#### B15 — Credential-less destinations fan out to all matching credentials, creating duplicate external calendar events

**Location:** `packages/core/eventmanager.ts:374–385`  ·  **Severity:** high  ·  **Judge confidence:** 0.66

**Why this is real.** In `createAllCalendarEvents`, the code iterates `for (const destination of destinations)` and, when `destination.credentialId` is missing, falls back to something equivalent to: `const credentials = organizerCredentials.filter((c) => c.type === destination.integration); for (const credential of credentials) await createEvent(credential, ...)`. Because that fallback is inside the per-destination loop, multiple destination entries of the same integration type with no `credentialId` trigger `createEvent` once per (destination × credential), producing duplicate external events and wasting API calls. This is a behavioral defect (extra external events and wrong target calendars), not a style issue; the PR did not include the file diff, so this verification relies on the reported post-PR line region (~374–385).

**How to replicate.** 1) Configure an organizer with 2 credentials of the same calendar integration type (e.g., two Google Calendar credentials).
2) Create/modify an event type or booking flow so the computed `destinations` array contains 2 entries for that same integration type where `credentialId` is null/undefined (now possible per reports).
3) Trigger a booking that calls `createAllCalendarEvents`.
Expected: at most one external calendar event per intended destination calendar.
Actual: for each credential-less destination, the code creates events on *every* organizer credential of that integration, so you get 2(destinations) × 2(credentials) = 4 external events (often on the providers' default/primary calendars), and secondary-host destinations may not receive the intended event.

**Found by** 13 cells (18 distinct report texts, 18 findings): opus: CE·high, CE·low, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high; glm-flash: van·high; glm-vis: CE·medium, MRV·high, MRV·medium, van·medium; sol: MRV·medium, van·high

#### B16 — Reschedule calendar update errors are swallowed: catch returns [] when calendarReference is unset and logs were removed

**Location:** `packages/core/eventmanager.ts:590–607`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** Per the reported post-PR code around the reschedule/update block, the error handler does `catch (error) { ... return Promise.resolve(calendarReference?.map(...) ?? []) }`. This means if an exception occurs before `calendarReference` is assigned (e.g., a `prisma.booking.findFirst`/lookup throws), the function returns an empty array (`?? []`) and does not log (the prior `console.error(message)`/logger was removed), so callers observe “no results” rather than a failure signal. That is a functional behavior change (silent failure) rather than a style issue, and it can mask real calendar-sync outages.

**How to replicate.** 1) Trigger a reschedule path that calls this eventmanager reschedule/update routine. 2) Force an exception before `calendarReference` is computed/assigned (e.g., make the underlying booking lookup throw by using a non-existent booking ID or temporarily breaking DB connectivity). 3) Observe that the function resolves with `[]` and no error log output, so the caller/UI treats the operation as completed without calendar updates. Expected: a non-empty failure result (e.g., `[{ success: false, ... }]`) and/or logged/propagated error so the user can be warned and retries/alerts can occur.

**Found by** 13 cells (14 distinct report texts, 14 findings): fable: van·high, van·low; opus: CE·medium, van·xhigh; sonnet: CE·low, MRV·high; glm-flash: van·xhigh; glm-vis: CE·high, CE·medium; sol: CE·high, MRV·low, MRV·medium; astra: MRV·low

#### B17 — Google createEvent falls back to 'primary' when destination calendar has null credentialId, ignoring configured externalId

**Location:** `packages/app-store/googlecalendar/lib/calendarservice.ts:145–165`  ·  **Severity:** high  ·  **Judge confidence:** 0.67

**Why this is real.** Post-PR logic (per the reports) resolves the target calendar with a lookup like `destinationCalendars.find((cal) => cal.credentialId === credentialId)` and then uses `selectedCalendar || "primary"`. If a destination calendar row is in the legacy state where `credentialId` is null/undefined but `externalId` is set, the `find(...)` can never match any passed `credentialId`, so `selectedCalendar` becomes undefined and the code silently writes to Google’s "primary" calendar instead of the configured destination calendar. The issue is functional (wrong calendar + wrong stored reference), not a style nit; the reports note this file wasn’t part of the PR diff, so verification must be done by reading the current tree code around the referenced lines.

**How to replicate.** 1) Ensure a user has a Google Calendar destination configured with a non-null `externalId` (calendarId) but a null/empty `credentialId` (legacy/migrated row). 2) Create a booking that should create a Google event on that destination calendar. 3) Observe in Google Calendar API/UI that the event is created on the user’s primary calendar (actual) instead of the configured externalId calendar (expected). 4) If the system stores the booking’s external calendar reference based on the selected destination, attempt an update/cancel: it will fail to target the correct calendar because the booking reference will not contain the intended external calendar id.

**Found by** 11 cells (31 distinct report texts, 31 findings): opus: CE·high, MRV·high; glm-flash: CE·high, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium, van·high

#### B18 — Booking webhook payload breaks backward compatibility by changing destinationCalendar from object/null to array

**Location:** `packages/types/calendar.d.ts:134–136`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** Multiple reports point to a concrete contract change in the public calendar/webhook event type: `destinationcalendar?: destinationcalendar[] | null;` (previously described/used as a single object or null). This means webhook payloads that historically allowed consumers to read `payload.destinationcalendar.externalid` will now deliver an array (or `[]` from some producers), causing runtime failures/undefined values in existing unversioned webhook subscribers. The PR diff for this file is not provided here, so this verification relies on the referenced post-PR line and the downstream webhook producers cited in the reports.

**How to replicate.** 1) Configure a booking webhook endpoint (or use the repo’s e2e webhook snapshot tests) that expects the old shape, e.g., code that reads `payload.destinationcalendar.externalid`.
2) Create a booking that has a destination calendar selected (or trigger a booking event like confirmed/canceled/rejected).
3) Observe the emitted webhook JSON: `destinationcalendar` is now an array (e.g., `[{ externalid: ... }]`) rather than a single object, so `payload.destinationcalendar.externalid` is undefined/throws.
4) Also verify shape inconsistency across triggers: for some events it becomes `[]` when unset (rather than `null`), which breaks consumers that treat `null` as the only empty-case and/or have strict schema validation.

**Found by** 11 cells (11 distinct report texts, 11 findings): opus: CE·low, MRV·low, MRV·medium; sonnet: MRV·high; sol: CE·high, MRV·low, van·medium; terra: CE·low; astra: CE·high, CE·low, MRV·high

#### B19 — Organization slug gating inverted by IS_TEAM_BILLING_ENABLED ternary, breaking slug/requestedSlug flow

**Location:** `organizations/create.handler.ts:148–152`  ·  **Severity:** high  ·  **Judge confidence:** 0.86

**Why this is real.** The post-PR code now reads `...(IS_TEAM_BILLING_ENABLED ? { slug } : {})` while still adding `metadata: { ...(IS_TEAM_BILLING_ENABLED ? { requestedSlug: slug } : {}), ... }`. This inverts the previous behavior where the slug was only directly assigned when team billing was disabled (`...(!IS_TEAM_BILLING_ENABLED && { slug })`). As a result, billing-enabled deployments now immediately set a live `slug` (bypassing any “requestedSlug/approval” gating), while billing-disabled deployments stop setting `slug` entirely, which is a functional behavior change not explained by the patch context.

**How to replicate.** 1) In a deployment/config where `IS_TEAM_BILLING_ENABLED=false` (self-hosted/non-billing), create an organization with a slug (e.g., via the org creation endpoint/UI). Expected (pre-PR): the created organization has `slug` set to the provided value and is reachable by its org URL; Actual (post-PR): `slug` is omitted, so org URL routing/lookup by slug can fail.
2) In a deployment/config where `IS_TEAM_BILLING_ENABLED=true`, create an organization with a slug that may conflict with an existing org/user/team slug. Expected (pre-PR): slug is not written immediately; instead `metadata.requestedSlug` is recorded for gated/verified assignment; Actual (post-PR): `slug` is written immediately, potentially triggering a unique-constraint error (500) and allowing unverified/unpaid orgs to claim slugs right away.

**Found by** 10 cells (26 distinct report texts, 26 findings): glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, MRV·high, MRV·low, MRV·medium

#### B20 — Collective booking can report success while silently skipping co-host calendar creation when destination credential is missing

**Location:** `packages/core/eventmanager.ts:356–371`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** In createAllCalendarEvents, the code guards calendar event creation with an `if (credential) { ... }` block around ~369, but there is no corresponding `else` branch to record a failure result or log when the credential cannot be resolved (neither in-memory nor via `prisma.credential.findUnique`). As a result, when a destination has a dangling/invalid `credentialId` (e.g., deleted credential or `app?.slug` is null causing lookup to fail), that host/destination is simply skipped and nothing is pushed into `createdEvents`/results, so downstream checks can treat the overall booking as fully synced even though a co-host event was never created. The PR diff does not include this file, so this verification relies on the reported line references and the described control flow at ~356-371.

**How to replicate.** 1) Set up a collective event type with 2+ hosts/destinations that should each get a calendar event. 2) Ensure one destination references a credential that is no longer resolvable (e.g., delete/disconnect that credential row, or make its associated app have `slug = null` so lookup fails). 3) Create a booking. Expected: booking result should include an explicit failure for the affected host/destination (or fail the booking / at least log/report partial sync failure). Actual: booking completes successfully, but the skipped host has no calendar event and no failure entry/log indicating it was skipped.

**Found by** 10 cells (11 distinct report texts, 11 findings): opus: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high, MRV·medium; glm-vis: CE·high; sol: CE·high, MRV·low

#### B21 — Recurring cancellation delete sweep runs once per calendar reference, causing redundant deleteEvent calls (O(n) duplicates/404s)

**Location:** `apps/web/pages/api/bookings/[id]/cancel/handleCancelBooking.ts:418–470`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple independent reports point to the same structural defect: the recurring-event deletion branch (the block that iterates over all calendar credentials and all updated bookings/references to delete provider events) was moved inside a `for (const reference of bookingCalendarReference)` loop around lines ~418-470. With that nesting, the full recurring deletion sweep is re-executed once per calendar reference, even though the body already loops over all credentials × all updated bookings, producing m×n duplicate `deleteEvent` provider calls and subsequent 404/410 failures or rate limiting. The PR diff is not available here, so this verification relies on the consistent line references and described control-flow from the reports.

**How to replicate.** 1) Create a recurring booking with at least two calendar references (e.g., two hosts or one host + an additional integration reference) and ensure the involved user has multiple calendar credentials connected. 2) Call the cancel endpoint for the series (recurring cancellation) so it triggers the recurring-delete path. 3) Observe server logs/network traces: expected is one delete sweep per affected event/credential; actual is the same events being deleted repeatedly (once per bookingCalendarReference), with duplicate delete calls and follow-up provider errors (404/410) for already-deleted events and/or increased latency/rate-limit errors.

**Found by** 9 cells (10 distinct report texts, 10 findings): fable: van·medium; opus: van·high, van·low, van·medium, van·xhigh; glm-flash: CE·high, van·high; glm-vis: CE·high, CE·medium

#### B22 — Paid collective bookings only create calendar event for a single host because payment webhooks rebuild destinationCalendar as a 1-element array

**Location:** `packages/features/ee/payments/api/webhook.ts:207–229`  ·  **Severity:** high  ·  **Judge confidence:** 0.82

**Why this is real.** In the payment-success flow the event payload reconstructs destination calendars as a single-element array: `destinationCalendar: selectedDestinationCalendar ? [selectedDestinationCalendar] : [],` (around the reported lines 207-229). For collective/team events, `evt.destinationCalendar` is supposed to represent multiple hosts' selected calendars, but this code collapses it to only the single "selected" calendar (typically the organizer/first host), so downstream `eventManager.create(evt)` can only create one calendar event even when the booking has multiple hosts.

**How to replicate.** 1) Create a Collective/Team event type with 2+ hosts, and ensure each host has a different connected destination calendar selected. 2) Enable payments (Stripe) so the booking is only finalized after webhook payment success. 3) Book the event and complete payment. Expected: calendar events are created on each host's selected destination calendar. Actual: only one calendar (the organizer/first-host selectedDestinationCalendar) receives the created event; other hosts see no event on their calendars.

**Found by** 7 cells (7 distinct report texts, 7 findings): opus: CE·high, CE·low, MRV·high, MRV·medium; glm-vis: CE·high; astra: CE·high, MRV·high

#### B23 — requestReschedule handler drops user.destinationCalendar fallback, producing empty destinationCalendar array

**Location:** `packages/trpc/server/routers/viewer/bookings/requestreschedule.handler.ts:239–242`  ·  **Severity:** low  ·  **Judge confidence:** 0.80

**Why this is real.** In requestreschedule.handler.ts around lines 239-242, the code builds destination calendars from only the booking value (e.g., `destinationCalendar: bookingToReschedule?.destinationCalendar ? [bookingToReschedule?.destinationCalendar] : []`). This preserves the earlier copy/paste bug (`bookingToReschedule?.destinationCalendar || bookingToReschedule?.destinationCalendar`) by still never falling back to `user.destinationCalendar`. As a result, when a legacy booking has `destinationCalendar` null/undefined but the user has a configured destination calendar, this handler emits `[]` while sibling handlers use `booking.destinationCalendar || user.destinationCalendar`.

**How to replicate.** 1) Use (or seed) a user account with a configured `user.destinationCalendar`.
2) Ensure there exists a booking to reschedule whose `booking.destinationCalendar` is null/undefined (common for legacy rows or bookings created before destination calendars were stored per-booking).
3) Call the viewer bookings reschedule request endpoint (the `requestReschedule` TRPC mutation) for that booking.
Expected: the handler should pass the user's destination calendar (consistent with other booking handlers) so downstream event/booking logic has a calendar context.
Actual: `destinationCalendar` becomes an empty array (`[]`), losing the user's fallback and potentially causing the reschedule flow to select no destination calendar or behave inconsistently vs other handlers.

**Found by** 6 cells (9 distinct report texts, 9 findings): sonnet: MRV·medium; glm-flash: van·high; glm-vis: CE·high, CE·low, van·low, van·medium

#### B24 — updateAllCalendarEvents can call updateEvent with missing/stale credential, aborting updates for other references

**Location:** `packages/lib/CalendarManager/eventmanager.ts:508–522`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The reports consistently describe code in updateAllCalendarEvents/updateCalendarReferences where a loop-external `let credential` is reused and `updateEvent(credential, ...)` is invoked unconditionally. The offending pattern is: `let credential; for (const reference of calendarReferences) { credential = this.calendarCredentials.find(...); if (!credential && reference.credentialId) credential = await prisma.credential.findUnique(...); result.push(this.updateEvent(credential, ...)); }` — meaning if both the in-memory lookup and DB fallback return nothing, `credential` is `undefined` (or remains a stale value from the previous iteration) and is still passed to `updateEvent`, which then dereferences credential fields / destructures it and throws. Because the promises are awaited under a surrounding try/catch, a single missing credential causes a cascade failure (all references reported as failed), unlike the createAllCalendarEvents path which reportedly guards with `if (credential)`.

**How to replicate.** 1) Create a booking that generates multiple calendar references (e.g., multi-host or organizer+attendee calendars) with stored `credentialId`s. 2) Delete (or revoke) one host's calendar credential from the DB so that `prisma.credential.findUnique({ where: { id: reference.credentialId } })` returns null (or returns a credential missing `app.slug`). 3) Trigger the update/reschedule flow that calls updateAllCalendarEvents/updateCalendarReferences. Expected: references with valid credentials update successfully and missing-credential references are skipped/marked failed. Actual: the code calls `updateEvent(undefined, ...)` (or uses the previous iteration's credential), throwing a TypeError / calendar manager crash and causing the whole batch to report failure or update the wrong calendar.

**Found by** 6 cells (8 distinct report texts, 8 findings): glm-flash: CE·low, CE·medium, MRV·medium; glm-vis: CE·low, MRV·high, MRV·low

#### B25 — Reschedule/merge deletes only the first calendar reference, orphaning events on other hosts’ calendars

**Location:** `packages/trpc/server/routers/viewer/booking/eventmanager.ts:553–558`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** In the reschedule/merge ("newBookingId" / merge) path, the code reportedly selects a single old calendar reference via `booking.references.find((reference) => reference.type.includes("calendar"))` and deletes only that one event. Because collective/multi-destination bookings can have multiple calendar references (one per host/destination), using `.find(...)` removes just the first match and leaves the remaining old references/events untouched, producing stale/orphaned events on other hosts’ calendars. The PR diff does not include this file, so this verification relies on the reported post-PR line references and the cited offending expression.

**How to replicate.** 1) Create a collective booking with multiple hosts where the booking writes events to more than one calendar (multiple `booking.references` of type including "calendar"). 2) Trigger a reschedule that goes through the merge/newBookingId update path (i.e., replaces the booking and attempts to delete the old booking’s calendar events). 3) Observe: only one host’s old calendar event is removed; the other host(s) still have the original event on their calendars. Expected: all old calendar events for the old booking are deleted/updated across every calendar reference.

**Found by** 6 cells (7 distinct report texts, 7 findings): fable: van·medium; opus: van·xhigh; glm-flash: CE·high, CE·medium; glm-vis: CE·high, CE·low

#### B26 — Recurring cancellation deletion sweep runs inside calendarReference loop, causing duplicate deleteEvent calls per host/reference

**Location:** `packages/lib/handleCancelBooking.ts:430–540`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The reported issue is that a new `for (...)` loop over `booking.bookingCalendarReference` now encloses the recurring-cancellation deletion sweep (the fan-out over all user calendar credentials × all remaining/updated bookings). The offending structure is effectively: `for (const ref of booking.bookingCalendarReference) { ... if (booking.recurringEventId) { await Promise.all(updatedBookings.map(async (b) => Promise.all(credentials.map(async (c) => deleteEvent(...b.uid...))))); } }`—but the recurring deletion block does not use `ref` at all, so it executes once per reference and re-deletes the same events multiple times. This multiplies outbound provider API calls and turns subsequent iterations into predictable 404/410 failures (already-deleted events), producing spurious error logs and unnecessary latency; this is functional behavior, not a style nit.

**How to replicate.** 1) Create a collective (multi-host) event type where a single booking stores multiple BookingCalendarReference entries (e.g., hosts A/B each connect a Google/O365 calendar and you book a recurring series). 2) Book a recurring series so there are multiple future occurrences (updatedBookings > 1) and ensure each host has at least one calendar credential (credentials >= 1). 3) Cancel the series via the API/UI path that calls handleCancelBooking with the option to cancel remaining occurrences. 4) Observe provider API traffic/logs: expected is ~credentials×remainingBookings deleteEvent calls; actual is ~calendarReferences×credentials×remainingBookings calls, with the extra sweeps attempting to delete the same UIDs again, often yielding duplicate 404/410 responses and extra error logs.

**Found by** 5 cells (9 distinct report texts, 9 findings): glm-flash: MRV·high, MRV·low; glm-vis: CE·low, MRV·high, MRV·medium

#### B27 — Public booking endpoint leaks raw Prisma error messages and misclassifies DB failures as HTTP 400 in loadUsers()

**Location:** `packages/features/bookings/lib/handlenewbooking.ts:724–763`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The reports consistently point to the new loadUsers() try/catch around lines ~724-762 where Prisma errors are caught and re-thrown as an HttpError 400 using the original Prisma exception message (e.g., `catch (e) { if (e instanceof Prisma.PrismaClientKnownRequestError) throw new HttpError({ statusCode: 400, message: e.message }) ... }`). Returning `e.message` verbatim exposes internal DB/Prisma details (model/field/constraint names) to unauthenticated bookers, and mapping transient infrastructure/DB errors to 400 incorrectly signals a client fault and breaks 5xx-based alerting/retry semantics. Additionally, errors intentionally thrown inside the try (e.g., “dynamicUserList is ... empty”) are swallowed by the same catch and converted into a generic 500, changing behavior and obscuring root cause.

**How to replicate.** 1) Hit the public booking creation endpoint that executes handleNewBooking() with inputs that reach loadUsers(). 2) Trigger a Prisma known request error (e.g., violate a unique/foreign-key constraint via crafted booking payload, or force an invalid relation lookup) so Prisma throws PrismaClientKnownRequestError. 3) Observe the response: Actual = HTTP 400 with the raw Prisma error message in the body; Expected = sanitized client-facing error (no internal schema details) and correct status (typically 5xx for DB failures, or a controlled 4xx with a safe message for true validation errors). Optionally, simulate a transient DB failure (pool timeout/connection drop) and see it misreported as 400 rather than a retryable 5xx.

**Found by** 5 cells (7 distinct report texts, 7 findings): opus: CE·high, CE·medium, MRV·medium; glm-vis: CE·high, CE·medium

#### B28 — Inverted ternary makes destination-calendar fallback dead, leaving calendarId undefined for update/delete

**Location:** `apps/api/src/integrations/googlecalendar/calendarservice.ts:254–256`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The code around the update path is reported to gate the lookup backwards, e.g. `const destinationCalendar = !externalCalendarId ? event.destinationCalendar?.find((cal) => cal.externalId === externalCalendarId) : null;`. When `externalCalendarId` is falsy (the only time the fallback should run), the predicate compares `cal.externalId === undefined`, so it returns undefined; when `externalCalendarId` is truthy, the find is skipped entirely. This makes the fallback permanently ineffective and can leave the computed `calendarId` undefined, breaking updates/deletes that rely on legacy destination-calendar references; the PR diff does not include this file, so verification relies on reading the current post-PR code at the referenced lines.

**How to replicate.** 1) Ensure an event exists whose stored reference lacks `externalCalendarId` (legacy record) but does have a `destinationCalendar` array containing the correct target calendar `externalId`. 2) Trigger an update (or delete) via the GoogleCalendar service for that event so the code must derive `calendarId` from the destinationCalendar fallback. Expected: the service finds the matching destination calendar and calls Google API with that calendar id. Actual: the inverted ternary causes the find to compare against `undefined` and return undefined, so `calendarId` becomes undefined and the API call targets an undefined/incorrect calendar (typically resulting in a 404/failed update/delete or acting on the wrong calendar).

**Found by** 4 cells (7 distinct report texts, 7 findings): opus: van·low, van·medium, van·xhigh; glm-vis: CE·high

#### B29 — Missing credentialId branch fans out over all credentials per destination, creating duplicate external calendar events

**Location:** `eventmanager.ts:355–381`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple reviewers point to the same control-flow defect: in the per-`destinationCalendar` loop (around lines 355–381), the `else` branch for when `destinationCalendar.credentialId` is falsy gathers *all* credentials matching `destinationCalendar.integration` (e.g., via filtering/concatenating by integration type) and then proceeds to create events for each of those credentials. Because this `no-credentialId` branch is executed once per destination entry, two destinations with the same integration type but no credentialId will each iterate the same credential set, producing duplicated event creations (N destinations × M credentials). The PR diff isn’t provided here, so this verification relies on the consistent line-referenced reports describing the exact loop/branch placement and fan-out behavior.

**How to replicate.** 1) Configure a team/collective booking with multiple destination calendars that share the same integration type (e.g., two Google Calendar destinations) and ensure those destination entries do not specify a credentialId (collective/auto-selection case).
2) Ensure there are multiple credentials connected for that same integration type (e.g., two Google accounts connected to the team/hosts).
3) Create a booking that triggers event creation.
Expected: one event per intended destination/credential selection (no duplicates for the same booking).
Actual: the code’s no-credentialId branch runs for each destination and iterates all matching credentials each time, causing duplicated events on the same credential calendars (e.g., identical booking appears multiple times in Google Calendar).

**Found by** 4 cells (5 distinct report texts, 5 findings): opus: van·high, van·low, van·medium; sonnet: van·low

#### B30 — Webhook payload uses inconsistent types for destinationCalendar (null vs []) across booking triggers

**Location:** `apps/web/playwright/webhook.e2e.ts:119–125`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** The webhook E2E fixtures still assert different “no calendar selected” representations for the same (now array-typed) field. In `bookingcreated` (and similarly `bookingrequested` around line ~373) the expected payload includes `destinationCalendar: null`, while the `bookingrejected` fixture asserts `destinationCalendar: []`. This indicates (and effectively locks in) a real contract mismatch: webhook consumers will receive different JSON types for the same field depending on which booking trigger fired, which is a breaking behavioral inconsistency after the change to `destinationCalendar[]`.

**How to replicate.** 1) Run the webhook E2E tests or manually trigger webhook deliveries for the same event type with different flows: create/request a booking (bookingcreated/bookingrequested) and reject a booking (bookingrejected).
2) Inspect the delivered webhook JSON payloads.
Expected: `destinationCalendar` should always be an array (e.g., `[]` when none), matching the new multi-destination type.
Actual (per the fixtures and corresponding handlers): some triggers produce `destinationCalendar: null` while others produce `destinationCalendar: []`, yielding inconsistent payload types across triggers.

**Found by** 4 cells (4 distinct report texts, 4 findings): opus: MRV·high, van·medium; glm-flash: MRV·high, MRV·medium

#### B31 — Missing external calendar id when creating event without credentialId causes booking references to store undefined externalCalendarId

**Location:** `packages/core/eventmanager.ts:370–385`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** Multiple reviewers point to the same concrete call-site defect in event creation: in the no-credentialId path, the code calls `createevent(c, event)` without the (new/required) third `externalId` argument. Because later code writes booking references from the returned value (e.g., `externalcalendarid: result.externalid`), omitting the argument makes `result.externalid` undefined and the booking reference is persisted with `externalcalendarid: undefined`, so subsequent update/delete operations can no longer route to the correct destination calendar. The PR diff does not include this file, so this verification relies on the reported post-PR line references (~375 and ~378) and their described control-flow/assignments.

**How to replicate.** 1) Configure a destination calendar integration where the selected destination has no `credentialId` (the branch described around eventmanager.ts ~370). 2) Create a booking that triggers this branch; observe the booking reference persisted for that attendee/booking has `externalcalendarid` missing/undefined (instead of the destination calendar external id). 3) Attempt to reschedule/cancel the booking (or any flow that calls update/delete against the provider); expected: it updates/deletes the correct event on the chosen destination calendar; actual: the system cannot target the correct calendar/event reliably (often falling back to provider defaults like Google 'primary' or failing to find the event) because `externalcalendarid` was never recorded.

**Found by** 4 cells (4 distinct report texts, 4 findings): opus: van·high, van·xhigh; glm-flash: CE·high; astra: CE·high

#### B32 — updateAllCalendarEvents swallows exceptions (no log) and may return empty results indistinguishable from 'no calendars'

**Location:** `packages/lib/CalendarManager/eventmanager.ts:596–608`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72

**Why this is real.** The clustered reports all point to the same post-PR change around eventmanager.ts:596: the `catch` block in `updateAllCalendarEvents` no longer logs the exception because `console.error(message)` was removed, making failures silent. Additionally, the catch path returns an empty array (or otherwise synthesizes a non-throwing result), which is ambiguous when the exception happens before `calendarReference` is assigned—callers cannot distinguish 'there were no calendar references to update' from 'the update crashed'. The file is not present in this PR diff, so this verification relies on the reported post-PR lines; a human can confirm by inspecting the catch block at ~596 and noting the lack of logging and the empty/placeholder return.

**How to replicate.** 1) In a dev environment, configure at least one external calendar integration (e.g., Google/Microsoft) for a user. 2) Trigger the code path that calls `updateAllCalendarEvents` (e.g., update an event type or reschedule an event that would update existing calendar events). 3) Force the underlying calendar provider call to throw (disconnect the integration token, revoke access, or simulate network/provider error). Expected: the server logs contain the error/stack (or propagated error) clearly indicating the failure cause; Actual: no error is logged from `updateAllCalendarEvents`, and the caller receives an empty/placeholder result (e.g., `[]` / `success:false` with `appName: "none"`), making it look like nothing needed updating rather than an exception.

**Found by** 3 cells (3 distinct report texts, 3 findings): fable: van·medium; opus: van·medium, van·xhigh

#### B33 — Dynamic group booking loadUsers no longer selects organization.slug (and may return undefined users), breaking org-aware booker URLs

**Location:** `packages/features/bookings/lib/handlenewbooking.ts:735–760`  ·  **Severity:** high  ·  **Judge confidence:** 0.68

**Why this is real.** The reports indicate that in the rewritten `loadUsers` around lines ~735–755, the user selection for dynamic/group bookings dropped the previous `organization: { select: { slug: true } }` include, so later code that reads `user.organization.slug` (e.g., when building the booker URL) will now see `organization`/`slug` as missing. The same area also reportedly removed the prior `|| []` fallback, meaning `loadUsers` can return `eventType.users` as `undefined`, leading to downstream logic either generating a non-organization URL or throwing when iterating/accessing user fields. This is a functional regression (missing required data and possible undefined) rather than a style issue; the PR diff is not available here, so this verification relies on the consistent line-referenced reviewer reports.

**How to replicate.** 1) In code, open `packages/features/bookings/lib/handlenewbooking.ts` and inspect `loadUsers` near lines 735–755: confirm the Prisma select for users no longer includes `organization: { select: { slug: true } }` and that the function returns `eventType.users` without an `|| []` safeguard. 2) Run the app with an organization workspace and create a dynamic/group booking event type with organization members. 3) Create a booking for that event: when the booking flow constructs the booker URL (via `getBookerUrl`/equivalent), expected behavior is an org-aware URL containing the organization slug; actual behavior is a URL missing the org slug or a runtime error if user list is undefined.

**Found by** 3 cells (3 distinct report texts, 3 findings): opus: CE·low, van·low; sol: CE·high

#### B34 — Duplicate calendar events when destination calendars contain duplicate (credentialId, externalId) entries

**Location:** `packages/core/eventmanager.ts:339–365`  ·  **Severity:** high  ·  **Judge confidence:** 0.70

**Why this is real.** Around `createAllCalendarEvents` (report points to ~line 339), the code iterates over the provided destination calendars and invokes `createEvent` once per entry, but does not deduplicate destinations by `(credentialId, externalId)` (or any equivalent key) before looping. Because upstream booking code can combine organizer/team destinations via array concatenation (reported in `handlenewbooking.ts` ~1003-1010 and ~1085-1087) without removing duplicates, the same calendar can appear twice in the destinations list. That causes this loop to call `createEvent` twice against the same calendar, producing two identical external events rather than one.

**How to replicate.** 1) Configure an event type where the event-type destination calendar is a shared/team calendar (same underlying external calendar). 2) Add a collective host/teammate whose personal destination resolution points to that exact same calendar (same credential and same externalId). 3) Create a booking for that event type. Expected: one event is created on the shared calendar. Actual: two identical events are created on the same external calendar because `createAllCalendarEvents` processes both destination entries without deduplication.

**Found by** 3 cells (3 distinct report texts, 3 findings): opus: CE·medium; glm-flash: CE·medium; glm-vis: CE·high

#### B35 — Cross-tenant OAuth credential loading by raw credentialId without ownership validation

**Location:** `packages/lib/eventmanager.ts:341–530`  ·  **Severity:** critical  ·  **Judge confidence:** 0.72

**Why this is real.** The code path reported loads credentials purely by database primary key, e.g. `await prisma.credential.findUnique({ where: { id: destinationCalendar.credentialId } })`, and then uses the returned OAuth tokens to create/update/delete calendar events. There is no additional predicate/guard ensuring the credential row belongs to the booking organizer, host, or team (no `userId`/`teamId` match), so the trust boundary expands from “only use credentials already attached to this host/team” to “use any credential row if its id is provided”. The PR diff does not include this file, so this verification relies on the reported line ranges and the described code pattern.

**How to replicate.** 1) Identify (or create) two users: Victim (has a connected calendar credential, note its `credential.id`) and Attacker (can configure event type destination calendars or otherwise influence `destinationCalendar.credentialId`).
2) As Attacker, set the event type (or destination calendar record) to reference Victim’s `credential.id` (e.g., by tampering an API request / DB row / any upstream input path that populates `destinationCalendar.credentialId`).
3) Create a booking for Attacker’s event type (or cancel/reschedule one). Expected: the system rejects using a credential not owned by the booking’s organizer/team, failing closed. Actual: EventManager fetches Victim’s credential by raw id and uses Victim’s OAuth tokens to write/cancel events on Victim’s calendar.

**Found by** 3 cells (3 distinct report texts, 3 findings): glm-flash: CE·medium; glm-vis: CE·high, MRV·low

#### B36 — Calendar createEvent failure logs full CalendarEvent object including attendee PII and credential IDs

**Location:** `packages/core/calendarmanager.ts:249–249`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** At/around line 249 the code logs a calendar-creation failure with the full event payload: `log.error("createevent failed", JSON.stringify(error), calEvent)`. The `calEvent` object typically contains attendee/organizer names and emails, notes/custom form responses, timezones, and destination calendar metadata (including credential IDs), so emitting it to application logs leaks sensitive data whenever calendar creation fails. The PR diff reportedly does not change this line, but leaving it in place still constitutes a real information-disclosure bug; this verification relies on the reporters’ referenced line since the file is not part of the PR diff.

**How to replicate.** 1) Configure a booking with an integration/destination calendar that will fail to create events (e.g., revoke OAuth/invalid credential, or set an invalid destination calendar ID). 2) Create a booking with real attendee details (name/email) and optional notes/custom questions. 3) Trigger event creation (normal booking flow) so `createEvent` throws. 4) Check server/application logs: expected is an error message without sensitive payloads; actual is an error log entry containing the serialized error and the full `calEvent` object with attendee PII and destination calendar/credential identifiers (potentially repeated per host in collective bookings).

**Found by** 3 cells (3 distinct report texts, 3 findings): opus: CE·low, MRV·low; sonnet: MRV·high

#### B37 — Stale calendar credential reused across references in updateAllCalendarEvents loop

**Location:** `packages/core/eventmanager.ts:493–530`  ·  **Severity:** critical  ·  **Judge confidence:** 0.67

**Why this is real.** The bug is that a `credential` variable is declared outside the `for (const reference of calendarReference)` loop and only conditionally reassigned inside it. As reported, the code pattern is effectively `let credential; for (...) { credential = calendarCredentials.find(...) || (await prisma.credential.findFirst(...)); await updateEvent(credential, ...) }` without resetting `credential` when a reference’s credential lookup fails (e.g., deleted credential => DB returns null). This means a later iteration can retain the previous iteration’s credential and call `updateEvent` with the wrong user’s auth, causing incorrect calendar updates or 403/404s; this is a real state-leak bug, not a style issue. (The PR diff does not include this file, so this verification relies on the reported line range and described code structure.)

**How to replicate.** 1) Ensure an event has 2+ `calendarReference` entries (e.g., host A and host B) where each reference normally has its own `credentialId`.
2) Delete/disable host B’s credential record (so `reference.credentialId` exists but is no longer resolvable from `calendarCredentials` and the DB fetch returns null).
3) Trigger an update that calls `updateAllCalendarEvents` (e.g., edit the event title/time and save).
Expected: host A’s calendar updates, and host B’s reference is skipped/marked failed due to missing credential.
Actual: the loop reuses host A’s `credential` when processing host B’s reference, causing an update attempt on the wrong calendar (or a permission error) and potentially marking the wrong references failed or updating the wrong external calendar.

**Found by** 2 cells (3 distinct report texts, 3 findings): glm-flash: CE·medium; glm-vis: CE·medium

#### B38 — eventmanager.update swallows errors and returns [] when calendarReference is undefined

**Location:** `packages/core/eventmanager.ts:595–607`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** In `eventmanager.update`, the `catch` path returns `calendarReference?.map(...) ?? []` (per the reports around lines ~595-607). If an exception is thrown before `calendarReference` is assigned (e.g., during the booking lookup / prisma query), this expression evaluates to `[]`, which is indistinguishable from “there were no calendar references to update”. This silently converts a real update failure into a no-op result, whereas the prior behavior returned an explicit `{ success: false, ... }` result row.

**How to replicate.** 1) Read `packages/core/eventmanager.ts` and locate `update(...)`’s `try/catch` around ~595-607; confirm the `catch` returns `calendarReference?.map(...) ?? []`. 2) Find where `calendarReference` is assigned inside the `try` block after a booking lookup (e.g., `prisma.booking.findUnique/findFirst`). 3) Consider/force a failure before that assignment (e.g., DB unavailable or booking query throws). 4) Observe that the function resolves to `[]` rather than returning at least one failure result; any caller that checks `results.some(r => !r.success)` will treat `[]` as “no failures” and proceed as if the update succeeded, potentially leaving stale calendar events after a reschedule.

**Found by** 2 cells (3 distinct report texts, 3 findings): glm-vis: CE·high, CE·medium

#### B39 — createEvent error logging serializes full calEvent and raw provider error (PII + OAuth token leak to logs)

**Location:** `packages/lib/calendarClient.ts:262–266`  ·  **Severity:** critical  ·  **Judge confidence:** 0.66

**Why this is real.** In the createEvent failure path, the catch handler logs sensitive objects verbatim: `log.error("createevent failed", JSON.stringify(error), calEvent);`. `calEvent` typically includes attendee names/emails/phones and booking answers/notes, so any create-event failure emits booking PII into server logs. For Google Calendar failures, the thrown value is commonly a gaxios error whose `config.headers.Authorization` contains `Bearer <access_token>`, meaning `JSON.stringify(error)` can persist OAuth access tokens into logs as well.

**How to replicate.** 1) Configure a Google Calendar integration (or any provider) and ensure createEvent is invoked with at least one attendee containing name/email/phone and booking answers/notes. 2) Force the provider call to fail (e.g., revoke/expire the Google OAuth token or intentionally misconfigure credentials so the provider returns 401/403). 3) Trigger an event creation (book an appointment). 4) Inspect server logs / log aggregator output: actual behavior is that the log entry for "createevent failed" contains serialized attendee/booking data from `calEvent` and may include the provider error's request config including the `Authorization: Bearer ...` token; expected behavior is that logs are redacted/minimized and never include attendee PII or credentials.

**Found by** 2 cells (2 distinct report texts, 2 findings): glm-vis: MRV·high, MRV·medium

#### B40 — Collective booking destination calendars skip first host and may duplicate organizer due to users.slice(1) assumption

**Location:** `unknown (not in PR diff); search post-PR tree for `teamDestinationCalendars` and `users.slice(1)` in the collective booking calendar-routing code` (exact lines not in diff)  ·  **Severity:** high  ·  **Judge confidence:** 0.67

**Why this is real.** The reported code constructs `teamDestinationCalendars` from `users.slice(1)`, e.g. `const teamDestinationCalendars = users.slice(1).flatMap(...)`, while separately adding the base destination from `organizerUser` (e.g. `organizerUser.destinationCalendar`). This implicitly assumes `users[0] === organizerUser`, but nothing enforces that ordering; when the organizer is not the first host in `users`, the first host’s destination calendar is never added (skipped by `slice(1)` and absent from the organizer base), and the organizer’s destination can be added twice (once via organizer base, once via inclusion in `slice(1)`). This is a functional correctness bug (missing/duplicated calendar event creation), not a style issue; the file/line cannot be cited exactly because it is explicitly noted as not part of the PR diff, so it must be confirmed by locating the `users.slice(1)` usage in the post-PR code.

**How to replicate.** 1) Configure a collective/team event type with 3 hosts A, B, C, where the booking organizer is B, but the hosts list order returned/loaded is [A, B, C] (A first). 2) Set distinct destination calendars for A, B, and C (ideally Google calendars so duplicates are observable). 3) Create a booking for that event type. Expected: calendar events are created in A, B, and C exactly once each. Actual with the bug: A’s destination calendar is missing entirely, and B’s destination may be included twice (leading to two createEvent calls against the same credential/calendar), while C is included normally.

**Found by** 2 cells (2 distinct report texts, 2 findings): glm-flash: MRV·high, MRV·low

#### B41 — loadUsers validation errors fall through to generic 500 instead of returning a 4xx

**Location:** `apps/web/pages/api/book/[...slug].ts:712–755`  ·  **Severity:** medium  ·  **Judge confidence:** 0.66

**Why this is real.** In the post-PR code, `loadUsers` performs input validation and throws plain `Error` objects such as `throw new Error("dynamicUserList is not properly defined or empty.")` (reported around lines ~725/~744). The surrounding `catch` only treats `HttpError` (and Prisma known request errors) as client/expected errors; all other thrown errors fall through to the generic branch that returns a 500 (e.g., `return res.status(500).json({ message: "unable to load users" })`). Because these validation failures are user-controllable (empty/invalid dynamic user list, non-array `eventType.hosts`) and are not `instanceof HttpError`, the intended 4xx behavior is unreachable and clients incorrectly receive a 500.

**How to replicate.** 1) Create/obtain a dynamic group booking link (dynamic user list via URL/query). 2) Call the booking API endpoint with a dynamic link whose resolved `dynamicUserList` is empty (e.g., remove all hosts/usernames from the URL/query), OR craft an event type payload/state where `eventType.hosts` is not an array. 3) Observe the API response: actual is HTTP 500 with a generic body like `{ "message": "unable to load users" }`. Expected is a 4xx (400/404) indicating invalid/no valid users so the client can handle it as a user/input problem rather than an internal server error.

**Found by** 2 cells (2 distinct report texts, 2 findings): glm-vis: MRV·low, MRV·medium

#### B42 — Video booking references persist with undefined credentialId, breaking later cancel/update lookups

**Location:** `eventmanager.ts:169–170`  ·  **Severity:** high  ·  **Judge confidence:** 0.78

**Why this is real.** The reported post-PR code sets `credentialid` conditionally: `credentialid: isCalendarType ? result.credentialid : undefined`. This means for non-calendar references (e.g., Zoom/Teams/Meet video meeting references) the `credentialid` is explicitly dropped/serialized as null/undefined in the stored booking reference. Later flows that need to find/delete/update the external video meeting by matching `credentialid` (or selecting the correct credential when multiple exist) will fail because the booking no longer records which credential created the meeting; the PR diff for this file is not shown, so this verification relies on the reviewers' quoted lines.

**How to replicate.** 1) Connect two video provider credentials (e.g., two Zoom accounts) to the same Cal.com user/team. 2) Create an event type using that video integration and make a booking. 3) Inspect the created booking's stored references (DB row / API payload) and observe the video reference has `credentialid` missing/null/undefined (actual) instead of the creating credential id (expected). 4) Cancel the booking (or delete one of the credentials and trigger cleanup): expected behavior is the external meeting is deleted/updated using the recorded credential; actual behavior is the system cannot reliably look up the correct credential/meeting, leading to failed deletion, orphaned meetings, or using the wrong credential.

**Found by** 2 cells (2 distinct report texts, 2 findings): opus: van·xhigh; glm-vis: CE·medium

#### B43 — Uncaught prisma/calendar lookup error aborts createAllCalendarEvents loop, failing entire booking and orphaning already-created events

**Location:** `packages/core/eventmanager.ts:336–408`  ·  **Severity:** high  ·  **Judge confidence:** 0.74

**Why this is real.** In `createAllCalendarEvents` (reported around lines 336–408), the code performs per-host/per-destination work in a sequential loop and includes an awaited DB lookup like `await prisma.credential.findUnique(...)` (reported at ~line 344) without any surrounding `try/catch` at the per-destination level (or even the method level). Because the loop is sequential, any thrown exception (e.g., prisma timeout/connection error or downstream getCalendar failure) propagates out and aborts processing remaining hosts/destinations. The reports also note that events may already have been created in external calendars before the failure, but references are not saved if the function aborts, leaving those external events orphaned; this is a functional correctness issue, not a style nit. (The file is not in this PR’s diff per the prompt, so this verification relies on the reported line references and described control flow.)

**How to replicate.** 1) Configure a booking with multiple hosts and/or multiple destination calendars so `createAllCalendarEvents` iterates over >1 destination. 2) Induce a failure for exactly one destination during execution (e.g., simulate a transient Prisma failure for `prisma.credential.findUnique` via DB connection drop/timeout, or force one calendar integration’s `getCalendar`/API call to throw). 3) Make a booking request that triggers `EventManager.create()` → `createAllCalendarEvents`. Expected: only the failing destination is skipped/marked failed while other destinations still complete and the booking succeeds (or at least preserves references for already-created external events). Actual: the thrown error is uncaught, the entire booking-creation request fails, remaining destinations are not processed, and any external events created earlier in the loop are left without saved references (orphaned).

**Found by** 2 cells (2 distinct report texts, 2 findings): opus: CE·low; sonnet: MRV·high

#### B44 — CRM `othercalendar` references updated twice due to overly broad calendar reference filter

**Location:** `packages/core/eventmanager.ts:496–586`  ·  **Severity:** high  ·  **Judge confidence:** 0.95

**Why this is real.** The code reportedly changed to filter calendar-related references using `newBooking.references.filter((reference) => reference.type.includes("calendar"))` (and the same for `booking.references`). Because `"othercalendar".includes("calendar")` is true, CRM `othercalendar` references are picked up by this general “calendar” update loop and then updated a second time in the dedicated `othercalendar` loop later (reported around lines 567–586). This creates duplicate external lifecycle updates (two update calls for the same reference) during reschedule/location changes; the PR diff doesn’t include this file, so this verification relies on the reported post-PR code lines.

**How to replicate.** 1) Create a booking that has at least one reference with `type: "othercalendar"` (e.g., via a CRM/other-calendar integration that stores an external event reference). 2) Trigger an operation that updates external calendar events (reschedule the booking or change location). 3) Observe outgoing integration calls/logs: the same `othercalendar` reference will be updated twice—once by the general `includes("calendar")` loop and again by the dedicated `othercalendar` loop—where only one update is expected.

**Found by** 2 cells (2 distinct report texts, 2 findings): sol: CE·high, MRV·high

#### B45 — Cancel booking fallback loads Credential without app slug/name, breaking getCalendar resolution

**Location:** `packages/features/bookings/lib/handlecancelbooking.ts:638–646`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** In the DB fallback path, the code reportedly does `foundCalendarCredential = await prisma.credential.findUnique({ where: { id: credentialId } })` and then passes that object to `getCalendar(...)`. Unlike the parallel implementation in `packages/core/eventmanager.ts` (which explicitly selects `app: { select: { slug: true } }` and reconstructs `appname: app.slug`), this fallback does not attach `app.slug`/`appname`, so `getCalendar` can receive a credential missing the `appname` field it relies on to choose the calendar provider. This is a functional mismatch (not stylistic) and can cause cancellation to fail when the fallback path is taken; the PR diff is not available here, so this verification relies on the reported offending lines.

**How to replicate.** 1) Create a collective (multi-host) booking where attendee/cancellation triggers host calendar deletion, and ensure at least one host reference stores only a `credentialId` (so the code must fall back to `prisma.credential.findUnique`). 2) Cancel the booking (via UI or API) to trigger `handleCancelBooking`. 3) Observe that the cancellation workflow attempts to call `getCalendar` with the DB-fetched credential lacking `appname`/`app.slug`; expected: calendar events are deleted for each host; actual: `getCalendar` fails to resolve the calendar app/provider for that host (error or skipped deletion), leaving host events not removed.

**Found by** 2 cells (2 distinct report texts, 2 findings): sonnet: MRV·medium; glm-vis: CE·high

#### B46 — updateAllCalendarEvents swallows early errors by returning [] when calendarReference is uninitialized

**Location:** `packages/lib/EventManager.ts:520–545`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** Post-PR, the `catch` path reportedly changed to `return calendarReference?.map(...) ?? []` and removed the prior `console.error(message)` / explicit failure-row return. If an exception is thrown before `calendarReference` is assigned inside the `try` (e.g., during the Prisma lookup of the new booking at the top of the `try`), `calendarReference` is `undefined`, so the catch returns `[]`. Callers interpret `[]` as "no calendar references to update" rather than "calendar update failed", making the error silent and changing observable behavior compared to the pre-diff code which always emitted at least one failure result plus a log.

**How to replicate.** 1) Trigger a reschedule/update code path that calls `EventManager.updateAllCalendarEvents` (e.g., reschedule an existing booking that normally updates external calendars). 2) Force an error before `calendarReference` is set inside that function (e.g., make the Prisma query for the new booking fail by temporarily breaking DB connectivity or injecting a thrown error in that lookup). 3) Observe: function returns an empty array `[]` and no failure row/log is produced; upstream logic proceeds as if there were no calendar references to update, so the DB reschedule succeeds but external calendar events are not updated. Expected (pre-PR): a failure result entry (e.g., `{ success: false, ... }`) and a log line indicating the update failure, allowing the caller to detect/report the issue.

**Found by** 1 cells (3 distinct report texts, 3 findings): glm-vis: MRV·medium

#### B47 — Booking creation performs sequential awaits and N+1 credential lookups, making latency scale linearly with host/destination count

**Location:** `packages/core/eventmanager.ts:337–520`  ·  **Severity:** high  ·  **Judge confidence:** 0.66

**Why this is real.** Per the clustered reports, post-PR `createAllCalendarEvents` was changed to a sequential `for...of` loop that does `await createEvent(...)` inside the loop, and it also performs `await prisma.credential.findUnique(...)` per destination/reference inside those loops (reported around ~345 and ~510). This is a concrete performance defect: instead of batching independent work (via `Promise.all`) and fetching credentials once (via a single `findMany({ where: { id: { in: [...] } } })`), the code forces serialized network/db calls and repeats identical queries. The PR diff is not provided here, so this verification relies on the reviewers’ consistent line-specific reports; an engineer can confirm by opening the file at the referenced lines and observing the `for...of` + `await` pattern and the `findUnique` calls inside the loops.

**How to replicate.** 1) Configure a booking that triggers `createAllCalendarEvents` for multiple destinations/hosts (e.g., group/collective booking where N attendees/hosts each have a calendar destination). 2) Enable Prisma query logging (e.g., `DEBUG="prisma:query"`) and time the booking endpoint. 3) Increase N (e.g., 1 -> 5 -> 20) and re-run. Expected: roughly constant or sublinear overhead due to parallelization/batched queries. Actual: response time increases ~linearly with N and logs show repeated `prisma.credential.findUnique` queries (N+1 pattern) and serialized calendar event creation.

**Found by** 1 cells (2 distinct report texts, 2 findings): opus: van·xhigh

#### B48 — Collective booking webhook payload leaks all hosts' destinationCalendar identifiers

**Location:** `packages/features/bookings/lib/handlenewbooking.ts:1078–1084`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** Per the deduplicated reports, around line ~1078 the code for collective events “push[es] every collective host's destinationcalendar row (externalid, credentialid, userid) … into evt”, and `evt` is later spread into webhook/workflow/email payloads. That means a single booking’s event object includes *all* hosts’ `destinationCalendar` entries (including `externalId` which is often an email address), exposing other hosts’ calendar identifiers to any webhook subscriber for the booking/team. This is a concrete confidentiality bug (over-broad data inclusion), not a style issue; note that this file/region is not part of the PR diff, so verification requires reading the current post-PR code at/near the referenced lines.

**How to replicate.** 1) Configure a Collective event type with 2+ hosts, where each host has a Destination Calendar set (so `destinationCalendar` rows exist with `externalId`, `credentialId`, `userId`). 2) Add a webhook subscription for booking-created (or any workflow/webhook that receives the booking event payload) for that team/event type. 3) Create a new booking for that Collective event. Expected: webhook payload contains only the destination calendar relevant to the booking/organizer (or none). Actual (per reports): payload contains an array/list of destinationCalendar rows for *all* hosts, including other users’ `externalId`/`credentialId`/`userId`.

**Found by** 1 cells (2 distinct report texts, 2 findings): opus: CE·high

#### B49 — Multi-host Google Meet bookings create different Meet links per host calendar event

**Location:** `packages/app-store/googlecalendar/lib/CalendarService.ts:228–259`  ·  **Severity:** high  ·  **Judge confidence:** 0.58

**Why this is real.** The per-host calendar event creation calls Google Calendar `events.insert` with `conferenceDataVersion: 1` and a fresh `conferenceData.createRequest` for every host (e.g., `conferenceDataVersion: 1` together with `conferenceData: { createRequest: { requestId: uuidv4() } }`). Because this insert is executed independently for hosts 2..n, Google generates a new Meet for each host’s event, while the booking record/attendee invite keeps only the first returned conference link—so hosts 2..n see a different Meet URL than attendees. (This PR’s diff does not include the relevant file; this verification relies on the reports’ described offending lines/behavior.)

**How to replicate.** 1) Configure a team/collective event type with 2+ hosts, each connected to Google Calendar with Google Meet conferencing enabled. 2) Create a booking as an attendee for a time slot that includes all hosts. 3) Inspect the calendar event created on each host’s Google Calendar and the invite/booking details sent to the attendee. Expected: all parties share the same Google Meet link. Actual: host #1’s event matches the attendee link, while host #2..n’s calendar events contain different Meet URLs (distinct meetings).

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: MRV·high

#### B50 — loadUsers no longer selects organization.slug, breaking org-aware routing/links

**Location:** `apps/web/lib/server/loadUsers.ts:70–115`  ·  **Severity:** high  ·  **Judge confidence:** 0.60

**Why this is real.** The reports indicate the PR’s rewritten `loadUsers` Prisma `select` for the (non-eventtype) user lookup dropped `organization: { select: { slug: true } }`. With Prisma, any relation/field not explicitly selected is omitted from the returned object, so downstream code reading `user.organization.slug` will now get `undefined` even for users that belong to an org. Because the file/lines are not present in this PR diff, this must be confirmed by inspecting the post-PR `loadUsers` query’s `select` block and verifying `organization.slug` is no longer selected.

**How to replicate.** 1) In the post-PR code, locate `loadUsers` and inspect the Prisma query used when loading users not via an EventType (the “non-eventtype user query”). 2) Confirm the `select` does not include `organization: { select: { slug: true } }`. 3) Find a downstream consumer that uses `user.organization.slug` (e.g., org-aware routing/booking logic for dynamic collective links) and trace its input from `loadUsers`; it will now see `undefined`. Expected: loaded users include `user.organization.slug` when applicable; actual: `organization`/`organization.slug` is missing/undefined, causing misrouting or incorrect link generation.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-vis: MRV·low

#### B51 — Webhook payload breaks backward compatibility: `destinationcalendar` changed from object/null to array

**Location:** `packages/features/webhooks/lib/payloads/booking.ts:1–40`  ·  **Severity:** high  ·  **Judge confidence:** 0.55

**Why this is real.** The reports indicate the webhook payload field `payload.destinationcalendar` was changed from an object (or null) to an array (e.g., `destinationcalendar: [...]`). This is a real breaking change because existing external consumers that read `payload.destinationcalendar.externalid` (Zapier/Make/custom code) will now receive an array and throw or evaluate `undefined`, with no webhook versioning or opt-out noted. The PR diff provided in this benchmark evidence pack does not include the file/lines for this change, so verification requires locating the payload construction in-repo and confirming the type change directly in code.

**How to replicate.** 1) In the post-PR codebase, locate the booking webhook payload builder (search for `destinationcalendar` or `destinationCalendar` in `packages/features/webhooks`).
2) Confirm the payload assignment builds `destinationcalendar` as an array rather than an object/null.
3) Run the app and configure a webhook endpoint; create a booking/event type that uses a destination calendar integration.
4) Trigger a booking and inspect the delivered webhook JSON: expected (pre-change) `destinationcalendar` is an object with fields like `externalid`; actual (post-change) `destinationcalendar` is an array, causing integrations that access `payload.destinationcalendar.externalid` to fail.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: CE·high

#### B52 — handleCancelBooking builds deletion Promise array with undefined entries, risking skipped/duplicated external calendar deletions

**Location:** `packages/features/bookings/lib/handlecancelbooking.ts:482–495`  ·  **Severity:** high  ·  **Judge confidence:** 0.62

**Why this is real.** The deduped report indicates that around ~line 486 `handlecancelbooking` pushes “raw promises including undefined” into an `apideletes` array (e.g., an `apideletes.push(<maybePromiseOrUndefined>)` pattern inside a loop over calendar references). This is a real functional defect because `Promise.all(apideletes)` (or similar) will treat `undefined` as an already-resolved value, silently masking the fact that some intended deletions were never scheduled; additionally, pushing per-reference without de-duplication can multiply deletion attempts for the same external event, increasing the chance of missed cleanup/orphaned calendar events. The PR does not include this file in its diff, so verification must be done by directly inspecting the current code near the reported line.

**How to replicate.** 1) Read `handlecancelbooking.ts` around lines ~482–495 and locate where `apideletes` is populated (likely inside a loop over `calendarReferences` / attendees / destinations). 2) Confirm there is a `.push(...)` where the pushed expression can be `undefined` (conditional operator/short-circuit `&&`) or where the same external event deletion is pushed multiple times per calendar reference. 3) Run the app with an event that creates multiple calendar references (e.g., multiple destinations/calendars) and cancel the booking. 4) Observe logs/network: expected is exactly one successful deletion per external calendar event; actual is that some deletions are not attempted (because `undefined` is pushed) and/or duplicate deletion calls occur, leaving an external calendar event orphaned or producing inconsistent deletion results without an explicit failure.

**Found by** 1 cells (1 distinct report texts, 1 findings): glm-flash: CE·low

#### B53 — Fallback credential construction ignores `invalid` flag and can use revoked/broken OAuth credentials

**Location:** `packages/core/eventmanager.ts:357–366`  ·  **Severity:** high  ·  **Judge confidence:** 0.72

**Why this is real.** In the fallback path, the code manually re-creates a credential object from a DB row and explicitly copies the flag verbatim (e.g., `invalid: credentialFromDb.invalid`) but does not gate usage on it before passing the credential into calendar operations. The same file later hands that constructed credential directly to calendar integration calls (create/update/get calendar) without filtering out `invalid` credentials, unlike the normal user-credentials query path which typically excludes invalid ones. The PR diff does not include these files/lines, so this verification relies on the reported line ranges and the described object construction/usage pattern.

**How to replicate.** 1) Ensure a calendar OAuth credential is marked invalid/revoked in the DB (set the credential's `invalid` flag true, e.g., by revoking the token or toggling the DB field). 2) Trigger a code path that uses the fallback credential fetch/construction in `eventmanager.ts` (e.g., an event update/create that falls back to fetching a credential by ID rather than via the normal user credentials list). 3) Observe that the system still attempts calendar API calls with that credential (actual), leading to integration errors or unintended use of a revoked token; expected behavior is to reject/skip invalid credentials and fail early with a clear error or choose an alternative valid credential.

**Found by** 1 cells (1 distinct report texts, 1 findings): sonnet: MRV·medium

#### B54 — Reschedule can persist in DB even when some host calendar updates fail (no rollback/retry)

**Location:** `packages/core/eventmanager.ts:542–570`  ·  **Severity:** high  ·  **Judge confidence:** 0.66

**Why this is real.** The reported code around `eventmanager.ts:542` records per-host calendar update failures only as flags/results ("per-host update failures are only returned as flags") and then continues the reschedule flow without throwing or compensating. Because the DB reschedule write happens regardless, there is no rollback or retry mechanism when one host update fails, leaving some external host calendars at the old time while the booking is updated. This is a real consistency bug (partial failure handling) rather than a style issue; the PR does not touch this file in its diff, so verification requires reading the existing logic at/near the referenced lines.

**How to replicate.** 1) Create an event with multiple hosts (team/round-robin) where each host has a connected calendar. 2) Force one host calendar update to fail during a reschedule (e.g., revoke that host’s OAuth token, make their calendar read-only, or simulate a provider 401/5xx) while another host remains valid. 3) Reschedule the booking. Expected: reschedule should either fail atomically (DB not changed) or retry/compensate so all host calendars match. Actual: booking/reschedule is committed in the database, but the failing host’s calendar still shows the old time (or missing update), producing inconsistent state across hosts.

**Found by** 1 cells (1 distinct report texts, 1 findings): sol: CE·high

#### B55 — Calendar interface migration to destinationCalendar[] + credentialId is not enforced; unmigrated implementers still type-check

**Location:** `packages/types/calendar.d.ts:171–190`  ·  **Severity:** high  ·  **Judge confidence:** 1.00

**Why this is real.** Around line 171 in `packages/types/calendar.d.ts`, the PR’s migration is represented only as a type-level change on `export interface Calendar` (the reports indicate the interface now expects a `destinationCalendar` that is an array and credentialId-aware). TypeScript’s structural typing plus method-parameter bivariance means classes that `implements Calendar` can still compile even if their `createEvent`/similar methods keep the old `destinationCalendar` shape (or otherwise don’t actually consume the new array+credentialId semantics). As a result, `tsc` provides false confidence: the interface update compiles while at least three implementers (office365, lark, and a base service per the report) remain unmigrated and only manual inspection reveals the mismatch.

**How to replicate.** 1) In the post-PR tree, open `packages/types/calendar.d.ts` around line 171 and confirm the `Calendar` interface’s method signature(s) now require the new destinationCalendar representation (array + credentialId-aware). 2) Ripgrep for implementers: `rg "implements Calendar" -n` and inspect the Office365, Lark, and BaseCalendarService classes referenced in the reports. 3) Verify those classes still use the pre-migration destinationCalendar contract (e.g., expecting a single calendar id / not handling an array / not threading credentialId), yet the project still type-checks with `tsc`. 4) Optional runtime confirmation: invoke the code path that creates/syncs an event specifying multiple destination calendars or requiring credentialId disambiguation; expected behavior is correct selection/handling of the new array form, actual behavior in those unmigrated services is incorrect routing/selection or failure because they still assume the old shape.

**Found by** 1 cells (1 distinct report texts, 1 findings): sonnet: MRV·high
