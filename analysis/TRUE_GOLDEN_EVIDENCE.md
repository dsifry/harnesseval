# The True Golden Set — verified evidence pack (§10c)

**What this is.** Every confirmed-bug finding from the whole campaign (all models × frameworks ×
efforts; 2,416 healthy runs) on the six hardest PRs, taken through: (1) the adjudication gate
(hallucinations and important_non_bug excluded), (2) an LLM semantic merge of same-defect
paraphrases, (3) a stricter whole-PR re-merge with the same judge, (4) a **finding-level**
golden-overlap check — a cluster is a duplicate of a golden only if a single member finding is
that golden's exact defect — and (5) a strict tie-break of low-confidence overlaps.

**Verified set: 42 goldens + 211 additional real bugs = 253 distinct bugs.**
47 clusters were verified duplicates of a golden and are **excluded** from the additional set
(counting them would double-count: the golden is already in the denominator). Every additional bug
below carries a judge-produced verification card: location (`file:start–end`), a why-real
explanation quoting the code, replication steps, and the exact cells that found it. Bugs found by
**no harness cell** are called out — those are the blind spots, and they are a different class of
defect (performance, test quality, framework idioms) than the correctness/security bugs the lenses
target. Residual under-merge or mis-attribution is possible; the artifacts are the record.

**Provenance.** Judges: gpt-5.2, 2026-09-17. Artifacts: `analysis/exp_union_semantic_pilot_<pr>.json`
(semantic merge), `analysis/semantic_true_golden_verify_<pr>.json` (re-merge + first-pass overlap),
`analysis/semantic_overlap_finding_<pr>.json` (finding-level), `analysis/semantic_overlap_locked_<pr>.json`
(locked status), `analysis/semantic_true_golden_<pr>.json` (cards). Adjudication verdicts are the
frozen instruments and are untouched. LLM steps are not deterministic; the stored artifacts are the
record.

| PR | goldens | verified additional | verified universe | clusters merged | golden-duplicates removed |
|---|---|---|---|---|---|
| [11059](https://github.com/calcom/cal.com/pull/11059) | 9 | **24** | 33 | 35 | 11 |
| [4](https://github.com/ai-code-review-evaluation/discourse-graphite/pull/4) | 8 | **70** | 78 | 81 | 11 |
| [10](https://github.com/ai-code-review-evaluation/discourse-graphite/pull/10) | 7 | **32** | 39 | 37 | 5 |
| [8](https://github.com/ai-code-review-evaluation/discourse-graphite/pull/8) | 6 | **21** | 27 | 28 | 7 |
| [14740](https://github.com/calcom/cal.com/pull/14740) | 6 | **33** | 39 | 42 | 9 |
| [10967](https://github.com/calcom/cal.com/pull/10967) | 6 | **31** | 37 | 35 | 4 |
| **total** | **42** | **211** | **253** | 258 | 47 |

## Harness blind spots — 12 verified bugs no harness cell found

- **[4] Rails migration adds NOT NULL column with DEFAULT, causing full table rewrite and ACCESS EXCLUSIVE lock on PostgreSQL < 11** — `db/migrate/20131219203905addcookmethodtoposts.rb`:3–3 · 5 findings, 2 cells (vanilla only)
- **[4] Dead feed-modified cache key means PollFeed always re-downloads and reprocesses the full feed** — `app/jobs/scheduled/pollfeed.rb`:20–22 · 4 findings, 3 cells (vanilla only)
- **[4] RetrieveTopic job unnecessarily eager-loads mail stack via stray require_dependency** — `app/jobs/regular/retrievetopic.rb`:1–1 · 2 findings, 2 cells (vanilla only)
- **[4] Embed URL is constructed by naive string concatenation, breaking when discourseUrl lacks a trailing slash** — `N/A (not referenced in the deduplicated reports; not modified in PR #4 diff)` · 1 findings, 1 cells (vanilla only)
- **[4] Embed controller spec for missing embed_url is a false positive due to embeddable_host default failure** — `spec/controllers/embed_controller_spec.rb`:8–16 · 1 findings, 1 cells (vanilla only)
- **[4] Using `<<` to append to `contents` mutates the caller's String and can crash on frozen strings** — `lib/topicembed.rb`:13–13 · 1 findings, 1 cells (vanilla only)
- **[4] Cache miss on arbitrary URL triggers synchronous full RSS fetch+import (DoS vector)** — `topicretriever.rb`:41–48 · 1 findings, 1 cells (vanilla only)
- **[10] EmbeddableHost host format validation allows trailing newline due to end-anchor, creating broken allowlist entries** — `app/models/embeddablehost.rb`:2–3 · 3 findings, 3 cells (vanilla only)
- **[10] Embeddable hosts table header renders even when list is empty due to truthy empty array in Ember {{if}}** — `app/assets/javascripts/admin/templates/embedding.hbs`:1–12 · 1 findings, 1 cells (vanilla only)
- **[10] EmbeddableHost missing presence validation for non-null category_id causes DB NotNullViolation** — `app/models/embeddable_host.rb`:1–30 · 1 findings, 1 cells (vanilla only)
- **[14740] Null eventType.teamId is coerced to 0, causing incorrect team lookup/authorization checks** — `packages/trpc/server/routers/viewer/eventTypes/get.handler.ts`:128–136 · 1 findings, 1 cells (vanilla only)
- **[10967] Booking creation performs sequential awaits and N+1 credential lookups, making latency scale linearly with host/destination count** — `packages/core/eventmanager.ts`:337–520 · 2 findings, 1 cells (vanilla only)

---

## PR 11059 — 24 additional real bugs (9 goldens; 11 golden-duplicates removed)
(<https://github.com/calcom/cal.com/pull/11059>)

### Additional bugs (evidence cards)

#### A1 — Webhook secret validation uses non-constant-time string comparison (timing side-channel) and fragile header lookup

**Location:** `apps/web/pages/api/webhook/app-credential.ts:23–29`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  91 findings, 39 cells

**Why this is real.** The handler validates the webhook secret with a direct `!==` comparison: `req.headers[process.env.CALCOM_WEBHOOK_HEADER_NAME || "calcom-webhook-secret"] !== process.env.CALCOM_WEBHOOK_SECRET` (lines 24–26). In JavaScript/Node, string equality is not guaranteed to be constant-time, so an attacker can potentially infer the secret via timing differences across many requests. Additionally, `req.headers` keys are normalized to lowercase by Node/Next.js, so using a mixed-case `CALCOM_WEBHOOK_HEADER_NAME` can cause the lookup to return `undefined`, making the check behave incorrectly (e.g., always 403 even with the correct header present).

**How to replicate.** 1) Run the app locally with `APP_CREDENTIAL_SHARING_ENABLED=true`, set `CALCOM_WEBHOOK_SECRET` to a known value (e.g., `supersecret`). 2) Timing side-channel: send many POST requests to `/api/webhook/app-credential` varying the secret so it matches progressively longer prefixes of `supersecret` (e.g., `s`, `su`, `sup`, ...) and measure average response times; because the code uses `!==` on strings, observed latency can correlate with how many leading characters match (expected: constant-time behavior; actual: potentially variable timing). 3) Header-name fragility: set `CALCOM_WEBHOOK_HEADER_NAME=Calcom-Webhook-Secret` (mixed case) and send a request with header `Calcom-Webhook-Secret: supersecret`; because `req.headers` is lowercased, the lookup misses and the endpoint returns `403 Invalid webhook secret` even though the correct header/value were supplied.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A2 — Non-atomic findFirst-then-create in webhook can create duplicate app credentials under concurrent requests

**Location:** `apps/web/pages/api/webhook/app-credential.ts:62–88`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  46 findings, 36 cells

**Why this is real.** The handler does a non-atomic read-then-write: `const appCredential = await prisma.credential.findFirst({ where: { userId: reqBody.userId, appId: appMetadata.slug } ... })` and, if not found, proceeds to `await prisma.credential.create({ data: { ... userId: reqBody.userId, appId: appMetadata.slug ... } })`. Under concurrent first-time webhook deliveries for the same (userId, appId), both requests can observe no existing credential and both execute `create`, producing duplicate rows (or a unique-constraint error if one exists, which is not handled here). This is a real race condition because the check and insert are separate operations without a transaction/lock or an atomic upsert on a unique key.

**How to replicate.** 1) Ensure there is no existing `credential` row for a given `userId` and `appSlug` (mapped to `appMetadata.slug`). 2) Send two POST requests concurrently to `/api/webhook/app-credential` with identical JSON bodies `{ userId: X, appSlug: Y, keys: <valid encrypted payload> }` and valid webhook secret header. 3) Expected: exactly one credential exists for that user/app, and the request is idempotent. Actual: both requests can take the `findFirst` miss and both run `create`, resulting in two credentials for the same user/app (or one request failing with a DB unique constraint error/500 if uniqueness is enforced).

**Found by:** opus: CE·high, CE·low, MRV·low; sonnet: MRV·high, MRV·low; glm-flash: CE·high, CE·low, MRV·high, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; terra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A3 — Webhook API handler performs credential create/update without restricting HTTP method (missing POST-only guard)

**Location:** `apps/web/pages/api/webhooks/app-credential.ts:17–90`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  41 findings, 24 cells

**Why this is real.** The handler is defined as `export default async function handler(req, res)` and immediately starts processing auth/body (`const reqBody = appCredentialWebhookRequestBodySchema.parse(req.body);`) without any `req.method` validation. Later it performs writes unconditionally via `await prisma.credential.update(...)` and `await prisma.credential.create(...)`. Because there is no `if (req.method !== "POST") return res.status(405)...` guard, non-POST requests (GET/PUT/DELETE, etc.) that include the secret header can reach the same credential-mutation code path instead of being rejected.

**How to replicate.** 1) Ensure the deployed app has `APP_CREDENTIAL_SHARING_ENABLED` true and you know/configure `CALCOM_WEBHOOK_SECRET` and `CALCOM_WEBHOOK_HEADER_NAME` (or use default `calcom-webhook-secret`).
2) Send a non-POST request (e.g., PUT or GET) to the webhook route for this file with headers: `{<webhook-header-name>: <CALCOM_WEBHOOK_SECRET>, "Content-Type": "application/json"}` and a JSON body matching the schema: `{ "userId": <existing user id>, "appSlug": "<existing app slug>", "keys": "<encrypted string>" }`.
3) Observe the response is `200` with "Credentials created..." or "Credentials updated..." and the credential row is created/modified.
Expected behavior: non-POST methods should return `405 Method Not Allowed` and must not attempt to parse body or mutate credentials.

**Found by:** opus: CE·high, CE·medium; sonnet: CE·high; glm-flash: CE·low, CE·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·low, MRV·medium

#### A4 — Credential-sync token refresh request omits shared secret/Authorization header

**Location:** `packages/app-store/utils/oauth/refreshoauthtokens.ts:8–24`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74  ·  75 findings, 34 cells

**Why this is real.** In `refreshoauthtokens.ts` (around line 8 per the reports), the code performs an outbound `fetch` to the configured credential-sync endpoint with headers that include only a content type (e.g., `{"Content-Type":"application/json"}`) and a JSON body containing only identifiers like `calcomuserid` and `appslug`. There is no `Authorization` header or shared-secret/signature header included, so the receiving token-minting endpoint has no cryptographic way to authenticate that the caller is Cal.com. This is a real security defect (not style): if the credential-sync endpoint is reachable and trusts these parameters, an attacker can request tokens for arbitrary user IDs/app slugs, or operators cannot securely enforce caller authentication.

**How to replicate.** 1) Open `packages/app-store/utils/oauth/refreshoauthtokens.ts` and find the outbound `fetch`/HTTP call to the credential-sync endpoint (line ~8). 2) Verify the request headers: confirm it does not set `Authorization` and does not set any shared-secret header (e.g., `x-calcom-secret`, `x-webhook-secret`, etc.), and that the body contains only `calcomuserid` and `appslug` (or equivalent). 3) If you can run locally: point the credential-sync endpoint to a test server that logs requests; trigger OAuth token refresh so this function runs; observe the incoming request contains only the IDs and no authentication secret. Expected (secure) behavior: a configured secret/signature is always sent so the endpoint can verify the caller; actual behavior: unauthenticated request.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·medium, MRV·high, MRV·medium; terra: CE·high, CE·low, CE·medium

#### A5 — Salesforce calendarservice references `prisma` without importing it

**Location:** `packages/app-store/salesforce/lib/calendarservice.ts:96–105`  ·  **Severity:** critical  ·  **Judge confidence:** 0.78  ·  30 findings, 21 cells

**Why this is real.** Multiple independent reports point to post-PR line ~96 where the module calls into Prisma (e.g., a persistence/update call like `await prisma.<model>...`) but there is no corresponding `import prisma from ...` (or equivalent Prisma client initialization) at the top of `calendarservice.ts`. In TypeScript, this produces a compile-time error ("Cannot find name 'prisma'") and, if somehow emitted, a runtime `ReferenceError: prisma is not defined` when the refresh/persist path executes. The PR diff for this file is not provided here, so this verification relies on the consistent line-specific evidence from the deduplicated reports.

**How to replicate.** 1) Check out the PR branch/commit and open `packages/app-store/salesforce/lib/calendarservice.ts`.
2) Navigate to around line 96 and confirm there is a statement using `prisma` (e.g., `await prisma...`) while the top of the file lacks any import/definition for `prisma`.
3) Run a TypeScript build/typecheck for the repo or package (e.g., `pnpm -r build` or `pnpm -C packages/app-store/salesforce build`).
Expected: build succeeds. Actual: TypeScript fails with an error indicating `prisma` is undefined/unresolved in `calendarservice.ts`.
(If typechecking is bypassed, trigger the token refresh path in the Salesforce integration; execution will throw `ReferenceError: prisma is not defined` when that line runs.)

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·high, CE·medium, MRV·high, MRV·medium; glm-flash: CE·low; glm-vis: CE·medium; sol: CE·high, CE·low, MRV·medium; terra: CE·high, CE·low, MRV·high, MRV·low; astra: CE·high, MRV·medium

#### A6 — Webhook persists decrypted credential keys without validating per-app credential schema

**Location:** `apps/web/pages/api/webhook/app-credential.ts:49–85`  ·  **Severity:** high  ·  **Judge confidence:** 0.80  ·  52 findings, 27 cells

**Why this is real.** The handler decrypts and parses attacker-controlled JSON and writes it directly into the credential record: `const keys = JSON.parse(symmetricDecrypt(...))` (lines 50-52) and then `data: { key: keys }` in both the update (lines 69-75) and create (lines 79-85) paths. Although the request body is Zod-validated, only `keys` being a string is checked; there is no validation that the decrypted `keys` matches the selected app's expected credential shape. This can silently persist malformed credential objects that downstream app/provider code cannot consume, causing later runtime failures while this endpoint still returns 200.

**How to replicate.** 1) Ensure `APP_CREDENTIAL_SHARING_ENABLED` is true and set `CALCOM_WEBHOOK_SECRET`, `CALCOM_WEBHOOK_HEADER_NAME` (or use default `calcom-webhook-secret`), and `CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY`.
2) Pick an existing userId and an existing appSlug present in `appStoreMetadata`.
3) Send a POST request to `/api/webhook/app-credential` with the correct webhook secret header and a body where `keys` is a valid AES-encrypted JSON string that decrypts to an invalid shape for that app (e.g., `"not-an-object"`, `{}`, or missing required fields that the provider expects).
4) Observe the endpoint returns 200 and the credential row is created/updated with `credential.key` equal to the malformed decrypted value.
Expected: endpoint should reject (400) when decrypted keys don't match the app's credential schema. Actual: endpoint accepts and persists malformed keys, which later cause failures when the app integration tries to use/refresh the credential.

**Found by:** opus: CE·low, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high, MRV·low; glm-flash: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium; sol: CE·low, CE·medium; terra: CE·high, MRV·medium

#### A7 — Webhook updates an arbitrary credential when user has multiple credentials for the same app

**Location:** `apps/web/pages/api/webhook/app-credential.ts:62–80`  ·  **Severity:** high  ·  **Judge confidence:** 0.92  ·  49 findings, 27 cells

**Why this is real.** The handler locates an existing credential using `prisma.credential.findFirst({ where: { userId: reqBody.userId, appId: appMetadata.slug } })` (lines 62-70), which is non-unique when a user can connect multiple accounts for the same integration. Because there is no additional account/credential identifier and no deterministic `orderBy`, `findFirst` may return any matching row; the subsequent `prisma.credential.update({ where: { id: appCredential.id }, data: { key: keys } })` (lines 73-80) will overwrite whichever credential happened to be returned, potentially clobbering the wrong connected account's tokens.

**How to replicate.** 1) In the database, create (or via UI connect) two credentials for the same user and same app slug (same `userId` and same `appId`) but representing different connected accounts (two rows in `credential`).
2) Call this endpoint with a valid webhook secret header and body containing that `userId`, the app's `appSlug`, and `keys` for only one of the accounts.
3) Observe that exactly one existing credential row gets updated, but which row is updated is not guaranteed (depends on DB/prisma row selection); expected behavior would be to update the specific intended credential/account, while actual behavior can overwrite the other account's credential key and break its associations.

**Found by:** opus: CE·high, CE·medium, MRV·high; glm-flash: CE·low, CE·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high; sol: CE·high, CE·medium, MRV·high, MRV·medium; terra: MRV·high, MRV·medium; astra: CE·high, MRV·high, MRV·low, MRV·medium

#### A8 — .env.example suggests wrong-length AES-256 encryption key generation (24 bytes vs required 32)

**Location:** `.env.example:241–243`  ·  **Severity:** medium  ·  **Judge confidence:** 0.78  ·  18 findings, 13 cells

**Why this is real.** The .env.example comment around lines 241-243 reportedly states the key "must be 32 bytes for aes256" but then recommends generating it with `openssl rand -base64 24`. That command produces 24 random bytes (encoded to ~32 Base64 characters), which contradicts the stated 32-byte requirement and conflates bytes with Base64 string length. This is a real defect because it can lead users to configure an invalid/shorter-than-intended key for AES-256, weakening security or causing runtime key-length validation failures depending on how the application consumes the value.

**How to replicate.** 1) Open `.env.example` and locate the `CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY` (or similarly named) comment at ~lines 241-243. 2) Observe that it claims the key must be 32 bytes for AES-256 but suggests `openssl rand -base64 24`. 3) Run `openssl rand -base64 24 | base64 -d | wc -c` and observe the decoded byte count is 24 (actual) not 32 (expected per comment). 4) (If the app validates key length) set the env var to that generated value and start the app / trigger credential encryption; expected: accepts a 32-byte key; actual: either rejects due to length mismatch or silently uses a shorter-than-intended key.

**Found by:** opus: CE·medium; sonnet: MRV·medium; glm-flash: MRV·high, MRV·low, MRV·medium; glm-vis: MRV·medium

#### A9 — Webhook secret header lookup uses raw env header name, breaking auth due to lowercased req.headers keys

**Location:** `apps/web/pages/api/webhooks/app-credential.ts:24–27`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  21 findings, 13 cells

**Why this is real.** In `app-credential.ts` (not touched in this PR’s diff; verification relies on the clustered reports), the code indexes the header map with the raw environment value, e.g. `req.headers[process.env.calcomwebhookheadername]`, and then compares it directly to the configured secret. In Node/Next.js, incoming header names are normalized to lowercase in `req.headers`, so if `process.env.calcomwebhookheadername` contains any uppercase characters, the lookup always returns `undefined` and the handler always responds 403 even for valid requests. Additionally, `req.headers[...]` can be `string | string[]`, so repeated headers yield an array that will never strictly equal the secret string.

**How to replicate.** 1) Configure env: set `calcomwebhookheadername=CalCom-Webhook-Secret` (any mixed/upper-case) and `calcomwebhooksecret=shh123`.
2) Send a webhook request to the app-credential webhook endpoint with header `CalCom-Webhook-Secret: shh123`.
3) Observe: the handler reads `req.headers` keys lowercased (e.g. `calcom-webhook-secret`), so `req.headers['CalCom-Webhook-Secret']` is `undefined` and the endpoint returns 403 "invalid webhook secret".
4) Variant: send the same header twice so it becomes an array (e.g. via proxy); `req.headers[...]` becomes `string[]` and the strict comparison fails, also producing 403.
Expected behavior: correct secret in the configured header should authenticate; Actual: valid requests are rejected.

**Found by:** glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low; glm-vis: CE·high, CE·low, MRV·high, MRV·low, MRV·medium

#### A10 — Feature-flag constant evaluates to raw encryption-key string instead of boolean, risking secret leakage

**Location:** `packages/lib/constants.ts:92–92`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  17 findings, 10 cells

**Why this is real.** The constant is defined using a logical-AND of two environment variables, e.g. `export const appCredentialSharingEnabled = process.env.CALCOM_WEBHOOK_SECRET && process.env.CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY;`. In JavaScript/TypeScript, `a && b` evaluates to the last operand (`b`) when both are truthy, so this “enabled” flag becomes the *raw encryption key string* (or another string) rather than a boolean. This is a functional bug (strict boolean checks like `=== true` fail) and a security footgun because any logging/serialization of the exported flag leaks the encryption key; reports indicate this lives in a shared `constants.ts` module that also exports client-facing constants, increasing the blast radius.

**How to replicate.** 1) Set `CALCOM_WEBHOOK_SECRET=whsec_test` and `CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY=0123456789abcdef...` in the runtime env. 2) Import and print the constant (e.g. `console.log({ appCredentialSharingEnabled })`). 3) Observe actual output is the full encryption key string, not `true`. 4) Additionally, evaluate `appCredentialSharingEnabled === true` (or validate it with a boolean schema): expected `true` when both env vars are set, actual `false` because the value is a string.

**Found by:** glm-flash: CE·low, CE·medium, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, MRV·high, MRV·low, MRV·medium

#### A11 — Webhook auth fails open when CALCOM_WEBHOOK_SECRET is unset (undefined equals missing header)

**Location:** `apps/web/pages/api/webhook/app-credential.ts:23–27`  ·  **Severity:** critical  ·  **Judge confidence:** 0.92  ·  11 findings, 8 cells

**Why this is real.** The authentication check compares the incoming header directly to the env secret: `req.headers[process.env.CALCOM_WEBHOOK_HEADER_NAME || "calcom-webhook-secret"] !== process.env.CALCOM_WEBHOOK_SECRET`. If `process.env.CALCOM_WEBHOOK_SECRET` is unset (i.e., `undefined`) and the request omits the header, then `req.headers[...]` is also `undefined`, making the comparison `undefined !== undefined` false, so the code does NOT return 403 and proceeds to write credentials. This is a real authorization bypass triggered by a configuration edge case.

**How to replicate.** 1) Configure the app so `APP_CREDENTIAL_SHARING_ENABLED` is true. 2) Ensure `CALCOM_WEBHOOK_SECRET` is NOT set in the environment (unset/empty so it becomes `undefined` at runtime). 3) Send a POST request to `/api/webhook/app-credential` with a valid JSON body (userId/appSlug/keys) but do NOT include the `calcom-webhook-secret` header (or whatever `CALCOM_WEBHOOK_HEADER_NAME` would be). Expected: request should be rejected with 403 due to missing/invalid secret. Actual: the secret check passes (undefined equals undefined) and the handler continues, allowing credential create/update for the specified userId.

**Found by:** sol: CE·high, CE·low, CE·medium, MRV·low, MRV·medium; terra: CE·high, CE·low, CE·medium

#### A12 — Instance-wide shared webhook secret allows overwriting any user's app credentials (no per-user binding/replay protection)

**Location:** `apps/web/pages/api/webhook/app-credential.ts:23–90`  ·  **Severity:** critical  ·  **Judge confidence:** 0.93  ·  11 findings, 8 cells

**Why this is real.** Authorization is only `req.headers[... ] !== process.env.CALCOM_WEBHOOK_SECRET` (lines 24-29), i.e., a single instance-wide shared secret. The target `userId` is taken directly from the request body (`const reqBody = ...parse(req.body)` then `where: { id: reqBody.userId }` and later `where: { userId: reqBody.userId, appId: ... }`) and is used to update/create credentials, so any caller who knows/leaks the shared secret can choose an arbitrary userId and overwrite that user's stored OAuth/app keys. There is also no nonce/timestamp/event-id/revision check, so a captured valid request can be replayed to roll credentials back to older keys.

**How to replicate.** 1) Ensure `APP_CREDENTIAL_SHARING_ENABLED` is true and the server has `CALCOM_WEBHOOK_SECRET` configured. 2) Send a POST request to `/api/webhook/app-credential` with header `calcom-webhook-secret: <CALCOM_WEBHOOK_SECRET>` (or the name in `CALCOM_WEBHOOK_HEADER_NAME`) and JSON body `{ "userId": <victimUserId>, "appSlug": "<existing-app-slug>", "keys": "<valid AES256 encrypted blob>" }`. 3) Observe response `200 Credentials created/updated for userId: <victimUserId>` and that the victim user's `credential` row for that app is created/updated with attacker-supplied `key`. 4) Replay the exact same request later (or after the victim rotates credentials) and observe it still succeeds and overwrites the credential again (no timestamp/nonce/revision guard). Expected: webhook authorization should be scoped to the intended user/app and reject replays/stale updates; actual: any holder of the shared secret can overwrite any user's credentials and replays are accepted indefinitely.

**Found by:** opus: CE·medium, MRV·high, MRV·low; sonnet: MRV·high, MRV·medium; glm-vis: CE·low, MRV·low; sol: MRV·high

#### A13 — parseRefreshTokenResponse throws on schema mismatch and can crash calendar operations when callers don’t catch it

**Location:** `packages/app-store/utils/oauth/parseRefreshTokenResponse.ts:19–21`  ·  **Severity:** high  ·  **Judge confidence:** 0.66  ·  8 findings, 8 cells

**Why this is real.** Post-PR, the helper unconditionally throws on parse failure (reports cite lines 19–21): `throw new Error("invalid refreshed tokens were returned")`. Several callers (notably the Salesforce calendar service connection/client construction path) still treat the function as returning a `{ success: boolean, ... }` result and do not wrap the call in a try/catch, so a non-conforming but otherwise recoverable refresh response (e.g., missing optional fields like `scope`) will now propagate as an unhandled exception/rejection and abort calendar operations. This is a behavioral change from a non-throwing parse-result API and is a functional defect, not a style concern.

**How to replicate.** 1) Set up an integration that refreshes OAuth tokens via this helper (e.g., Salesforce calendar). 2) Force a refresh-token response that fails the Zod schema (common case from reports: Salesforce refresh responses omit `scope` or other fields the schema requires). 3) Trigger any codepath that builds an authed API client/connection and calls `parseRefreshTokenResponse` without a surrounding try/catch (e.g., concurrent booking sync or webhook-driven calendar fetch). Expected: refresh failure is handled (typed error/HTTP error path) and the caller can retry or surface a controlled auth error. Actual: the thrown `Error("invalid refreshed tokens were returned")` bubbles up as an unhandled exception/rejection, causing the calendar operation to fail hard.

**Found by:** opus: CE·low, CE·medium, MRV·high, MRV·low; sonnet: MRV·low

#### A14 — Webhook credential sync updates key but does not clear previously set invalid flag

**Location:** `apps/web/pages/api/webhook/app-credential.ts:72–80`  ·  **Severity:** high  ·  **Judge confidence:** 0.80  ·  3 findings, 4 cells

**Why this is real.** In the update path, the handler only writes the decrypted key back to the existing credential: `data: { key: keys, }` (lines 77-79). If the credential record had previously been marked `invalid=true` (as described by the reports), this endpoint never resets that flag, so even after receiving fresh valid tokens the credential can remain disabled/invalid in the database. This is a functional state bug (missing state transition), not a style issue.

**How to replicate.** 1) In DB, ensure a credential exists for (userId, appId=appMetadata.slug) with `invalid=true` and some old/expired `key` content (or reproduce by letting an integration mark the credential invalid). 2) Send a POST request to `/api/webhook/app-credential` with correct webhook secret header and a body containing the same `userId`, `appSlug`, and `keys` holding newly valid encrypted credentials. 3) Observe the handler returns 200 "Credentials updated" and the `key` field changes, but `invalid` remains true. Expected: a successful credential refresh/sync should also clear `invalid` (and re-enable the integration); actual: integration remains disabled because the invalid flag is never updated.

**Found by:** sol: CE·low; terra: CE·high; astra: MRV·high

#### A15 — Some OAuth integrations refresh via refreshOAuthTokens but persist the raw sync response without parseRefreshTokenResponse normalization

**Location:** `packages/app-store/lark/lib/getAccessToken.ts:1–120`  ·  **Severity:** high  ·  **Judge confidence:** 0.58  ·  2 findings, 2 cells

**Why this is real.** The reports describe that certain providers (e.g., lark, hubspot, webex, msteams/office365video) call `refreshOAuthTokens(...)` and then persist the returned JSON directly into `credential.key` without running it through `parseRefreshTokenResponse(...)`, while other providers (google/zoom/office365/salesforce) do apply the parser. This is a real functional defect because the sync endpoint can return provider-specific shapes (e.g., `expiresIn` vs `expires_in`, refresh token placeholders, or extra required fields) and without normalization/validation the app stores an incompatible object verbatim, silently corrupting credentials and breaking future API calls. The PR does not include these files in the diff, so verification is by inspecting the current post-PR tree for the missing `parseRefreshTokenResponse(...)` step after `refreshOAuthTokens(...)` in the affected provider call sites.

**How to replicate.** 1) Enable/force “sync mode” so token refreshes go through the sync endpoint (the code path that uses `refreshOAuthTokens`). 2) Stub/misconfigure the sync endpoint to return a token response missing provider-specific fields (e.g., for Lark omit/rename `refreshToken` and `expire`, or for Webex omit `expiresIn`). 3) Trigger a refresh (wait for expiry or explicitly invoke the provider’s token refresh path). Expected: the response is normalized/validated (via `parseRefreshTokenResponse`) and stored in a consistent schema, preserving required fields/placeholders. Actual: the raw response is saved into `credential.key` as-is, leading to broken subsequent API calls or refresh attempts.

**Found by:** glm-flash: MRV·high; glm-vis: MRV·low

#### A16 — parseRefreshTokenResponse now throws on Zod safeParse failure, turning previously-graceful token refresh degradation into a hard failure

**Location:** `packages/lib/integrations/oauth/parseRefreshTokenResponse.ts:18–33`  ·  **Severity:** critical  ·  **Judge confidence:** 0.60  ·  4 findings, 3 cells

**Why this is real.** The function reportedly changed from returning/continuing on `schema.safeParse(...)` failure (logging the Zod error + MS response and letting the caller use `tokenResponse.success && tokenResponse.data`) to instead hard-throwing: `if (!tokenResponse.success) throw new Error("invalid refreshed tokens were returned")`. That converts a recoverable/observable parse mismatch (e.g., Office365 returning an unexpected/partial refresh payload) into an exception that aborts `refreshAccessToken`, so any downstream booking flow depending on refresh now fails outright. The evidence pack notes this file is not in the PR diff; verification requires reading post-PR code for this function and confirming the throw replaced the previous non-throwing branch.

**How to replicate.** 1) In an environment with Office365 (or any provider using this shared refresh helper), force a refresh-token response that is missing/renamed fields (e.g., simulate an MS response missing `refresh_token` or with additional/unexpected shape so the strict schema fails). 2) Trigger any code path that calls `refreshAccessToken` during a booking (e.g., attempt to book a meeting that requires creating a calendar event while the access token is expired). Expected (pre-change): the Zod error is logged and the system proceeds with whatever usable fields were present (or at least does not crash the whole request). Actual (post-change): `parseRefreshTokenResponse` throws "invalid refreshed tokens were returned", bubbling up as an unhandled error and the booking/event creation request fails.

**Found by:** glm-flash: MRV·medium; glm-vis: MRV·low

#### A17 — Google OAuth refresh persists unvalidated credential.key (schema validation bypass) in credential-sharing mode

**Location:** `unknown (not in PR diff); search in Google OAuth refresh/credential update code for `parseRefreshTokenResponse(` and `credential.update({ data: { key: ... } })``  ·  **Severity:** high  ·  **Judge confidence:** 0.66  ·  1 findings, 1 cells

**Why this is real.** The clustered reports indicate the refresh flow now writes `credential.key` using `parseRefreshTokenResponse(googleCredentials, ...)` directly, instead of validating the full stored object via something like `GoogleCredentialSchema.parse(googleCredentials)` before persisting. This is a real behavioral regression because `parseRefreshTokenResponse` is typically a minimal/partial parser for the token response (or a merge helper), not a strict validator of the entire credential key shape, so arbitrary/unvalidated fields present on the mutated `googleCredentials` object (and potentially token-response fields) can be persisted into the database. The file/line numbers are not available in the provided evidence (the affected file is not part of the PR diff), but a reader can confirm by locating where refresh tokens are handled and comparing what expression is assigned to `data: { key: ... }` in the credential update.

**How to replicate.** 1) Enable/enter "credential sharing" mode (shared credential object reused across users/workspaces). 2) Ensure a Google credential exists whose in-memory `googleCredentials` object contains extra/unexpected properties (e.g., inject an additional field via a prior mutation point, or simulate by editing the stored JSON if possible). 3) Trigger a token refresh (e.g., call an endpoint that forces Google access token refresh or wait for expiry and perform an action that refreshes). 4) Inspect the persisted `Credential.key` JSON in the DB: expected behavior is that only fields allowed by the strict Google credential schema remain after refresh; actual behavior is that unvalidated/extra fields survive or new unexpected fields are written because the refresh path persists the merged/minimally-parsed object without strict schema.parse validation.

**Found by:** glm-vis: MRV·low

#### A18 — Zoho CRM token expiry adds 3600ms instead of 1 hour, causing near-immediate expiration

**Location:** `packages/app-store/zoho-crm/lib/credentials.ts:84–88`  ·  **Severity:** high  ·  **Judge confidence:** 0.58  ·  1 findings, 1 cells

**Why this is real.** The reported code computes expiry as `Math.round(Date.now() + 60 * 60)` (or equivalent `Date.now() + 60 60`), which adds 3600 to a millisecond timestamp—i.e., ~3.6 seconds—not one hour. Because `Date.now()` is in milliseconds, the intended “1 hour” TTL must be `60 * 60 * 1000`. This makes stored Zoho CRM credentials appear expired almost immediately after refresh, forcing a refresh on every subsequent operation. (The file/lines were not part of the PR diff; this verification relies on the aggregated reviewer report snippet.)

**How to replicate.** 1) In the Zoho CRM integration, trigger an access-token refresh (e.g., revoke/expire the token, then perform any calendar/CRM operation that refreshes it). 2) Inspect the persisted credential fields right after refresh (e.g., `expiresAt`/`expiryDate`). Expected: expiry timestamp ~now + 3600000ms (~1 hour). Actual with the bug: expiry ~now + 3600ms (~3.6s). 3) Perform a second operation a few seconds later; observe the integration treats the token as expired and refreshes again every time (extra refresh requests, repeated OAuth calls, potential rate limiting).

**Found by:** glm-flash: MRV·high

#### A19 — Cross-instance credential sync incorrectly trusts req.body.userId, attaching credentials to the wrong local user

**Location:** `UNKNOWN (not in PR diff) — locate the sync handler that reads req.body.userId and queries the local User table`  ·  **Severity:** critical  ·  **Judge confidence:** 0.60  ·  2 findings, 1 cells

**Why this is real.** The reported handler "resolves reqbody.userid — the calling instance's user id — directly against the local user table" (e.g., a lookup like `where: { id: req.body.userId }`) with no cross-instance identity mapping/scoping beyond a shared secret. In a multi-instance setup where local DB user IDs do not match the parent instance’s ID space, this causes the synced calendar/video credentials to be persisted under whatever local user happens to have that numeric ID. This is a functional mis-association bug (not a style issue): credentials can be silently linked to an unrelated local account, routing meetings/bookings through the wrong external calendar/video provider.

**How to replicate.** 1) Set up two Cal.com instances (Parent and Child) that share the credential-sync shared secret but have different user-id spaces (e.g., on Child, create a user so that local `id=1` belongs to Alice; on Parent, `userId=1` is Bob).
2) From Parent, trigger the credential-sync request to Child with `req.body.userId` set to Parent's user id (e.g., 1) and include valid credential payload.
3) Observe in Child DB that the new credential row is attached to local `userId=1` (Alice) rather than to a mapped identity for Bob.
Expected: Child should map Parent user identity to the correct local user (or reject if unmapped). Actual: Child attaches credentials to the local user with the same numeric ID, causing calendar/video actions for Alice to use Bob’s synced credentials (or vice versa).

**Found by:** glm-flash: MRV·high

#### A20 — Sync-endpoint fetch has no timeout/abort and no fallback, allowing hangs to stall all calendar/video ops

**Location:** `UNKNOWN (sync-endpoint fetch call site not included in PR #11059 diff; reports provided no file/line refs)`  ·  **Severity:** critical  ·  **Judge confidence:** 0.42  ·  1 findings, 1 cells

**Why this is real.** The clustered reports describe a specific control-flow defect: the code path that calls the new/central “sync endpoint” uses a plain `fetch(...)` without an AbortController/timeout and without a try/catch fallback to the prior local `refresh...` function when the endpoint errors or stalls. In Node/undici, `fetch` can wait indefinitely (or until long socket-level timeouts), so a slow/hung sync endpoint can block requests that require token refresh/sync, effectively stalling bookings touching the affected apps. The PR diff itself doesn’t include the relevant file, and the reports include no file/line references, so a reviewer must locate the sync-endpoint fetch wrapper in the post-PR tree and confirm the absence of `signal`/timeout and fallback logic.

**How to replicate.** 1) Configure the deployment to use the sync endpoint (whatever env/config flag points token refresh/sync at the parent endpoint) and set it to a host that accepts connections but never responds (e.g., an nginx location that sleeps/hangs).
2) Trigger an operation that requires calendar/video app sync/refresh (e.g., create a booking that writes to Google/Microsoft calendar or uses a video provider that needs token refresh).
3) Observe the server request: it hangs for a long time (until OS/TCP timeout) instead of failing fast; downstream calendar/video operations do not proceed.
Expected: request fails quickly with a controlled error and/or falls back to refreshing directly against the provider (pre-PR behavior). Actual: the entire flow stalls waiting on the sync-endpoint fetch.

**Found by:** glm-vis: MRV·high

#### A21 — API route default-imports zod, making `z` undefined and crashing on module load

**Location:** `apps/web/pages/api/webhook/app-credential.ts:1–12`  ·  **Severity:** critical  ·  **Judge confidence:** 0.78  ·  1 findings, 1 cells

**Why this is real.** The route reportedly begins with a default import (`import z from "zod"`) and then calls into it early (e.g., `z.object(...)` around line 9). In this repo, other files consistently use `import { z } from "zod"` because zod does not provide a stable default export in the runtime configuration used here; as a result, `z` can be `undefined` and `z.object(...)` throws `TypeError: Cannot read properties of undefined (reading 'object')` when the module is first evaluated. This is a functional crash (not a style issue) because it prevents the handler from loading at all; the PR diff is not provided here, so this verification relies on the clustered reports’ quoted lines and the repository’s established import pattern.

**How to replicate.** 1) Checkout the PR branch and open `apps/web/pages/api/webhook/app-credential.ts`; confirm it contains `import z from "zod"` and later uses `z.object(...)` near the top-level. 2) Start the app (e.g., `pnpm dev`) and send a POST request to `POST /api/webhook/app-credential` with any JSON body. 3) Observe the server logs show a `TypeError` during module load (`...reading 'object'`) and the endpoint returns HTTP 500 instead of processing the webhook.

**Found by:** glm-vis: MRV·medium

#### A22 — Webhook secret check has no rate limiting, enabling unlimited online guessing/brute force

**Location:** `apps/web/pages/api/webhook/app-credential.ts:18–26`  ·  **Severity:** medium  ·  **Judge confidence:** 0.80  ·  2 findings, 2 cells

**Why this is real.** The handler authenticates requests solely by comparing a header value to an environment secret: `req.headers[process.env.CALCOM_WEBHOOK_HEADER_NAME || "calcom-webhook-secret"] !== process.env.CALCOM_WEBHOOK_SECRET` and immediately returns `res.status(403)` on mismatch. There is no rate limiting, lockout, IP throttling, or other brute-force protection anywhere in this endpoint, so an unauthenticated caller can send unlimited guesses against the webhook secret. That makes the secret effectively an online password and weak/short secrets become practically guessable over time.

**How to replicate.** 1) Deploy/run the app with `APP_CREDENTIAL_SHARING_ENABLED=true` and set `CALCOM_WEBHOOK_SECRET` to some value. 2) Send repeated POST requests to `/api/webhook/app-credential` with an invalid `calcom-webhook-secret` header (or the configured header name), varying the header each time. 3) Observe that every request is processed and returns `403 {"message":"Invalid webhook secret"}` without any backoff, throttling headers, temporary bans, or increasing delay—allowing high-rate brute force attempts. Expected: requests should be rate-limited/blocked after some threshold to prevent online guessing.

**Found by:** sonnet: MRV·high

#### A23 — Webhook app-credential sync updates keys but leaves credential type stale

**Location:** `apps/web/pages/api/webhook/app-credential.ts:78–92`  ·  **Severity:** medium  ·  **Judge confidence:** 0.62  ·  1 findings, 1 cells

**Why this is real.** At the update site (around line 78 per the report), the handler updates the existing AppCredential row with the new secret payload (e.g., `key: keys`) but does not also update the row's discriminator/type (i.e., it omits something like `type: appMetadata.type`). This means an AppCredential that was created under an older app type (or whose integration type changed over time) can be successfully synced (keys updated) while still retaining an outdated `type` value in the DB. Any later resolution logic that routes by `credential.type` will then select the wrong integration despite the keys being current.

**How to replicate.** 1) In the DB, create (or pick) an existing app credential row whose `type` is the legacy/old integration type but whose `appId`/slug corresponds to an app whose `appMetadata.type` has changed (or simulate by editing `type` to an old value). 2) Call the webhook endpoint that hits `pages/api/webhook/app-credential.ts` to sync/update that credential (same credential id/app linkage), providing new `keys` so the update path is taken (not create). 3) Observe in the DB after the request: `key`/payload is updated, but `type` remains the old value. 4) Trigger any code path that loads and dispatches integration behavior based on `credential.type`; expected: it uses the app’s current integration type, actual: it routes using the stale stored `type` and behaves as the wrong integration.

**Found by:** sol: MRV·low

#### A24 — (untitled)

**Location:** `?`  ·  **Severity:** ?  ·  **Judge confidence:** 0.00  ·  1 findings, 1 cells

**Found by:** glm-vis: CE·high

### Golden-duplicates removed (would double-count)

- **duplicate of golden #4** — “When the sync endpoint path is used, res is a fetch Response and has no .data; res?.data will be undefined and token.access_token will throw at runtime. This re…”
  - cluster: OAuth refresh in credential-sync returns a raw fetch Response but callers treat it as a token object (.data/fields), causing runtime failures and bad persistence (`packages/app-store/googlecalendar/lib/calendarservice.ts`), 170 findings, 40 cells
- **duplicate of golden #4** — “When the sync endpoint path is used, res is a fetch Response and has no .data; res?.data will be undefined and token.access_token will throw at runtime. This re…”
  - cluster: OAuth token refresh can hang indefinitely because credential-sync fetch has no timeout/abort (`packages/app-store/utils/oauth/refreshoauthtokens.ts`), 180 findings, 42 cells
- **duplicate of golden #6** — “The Salesforce integration checks `response.statusText` instead of `response.ok` when handling OAuth token refresh responses. This can lead to unreliable behavi…”
  - cluster: Salesforce token refresh incorrectly checks response.statusText instead of response.ok, causing false failures (`packages/app-store/salesforce/lib/calendarservice.ts`), 129 findings, 48 cells
- **duplicate of golden #2** — “parseRefreshTokenResponse returns a Zod safeParse result ({ success, data, error }), not the credential key object. Persisting that as key stores the wrapper in…”
  - cluster: Google Calendar refresh flow persists Zod safeParse wrapper ({success,data}) as credential key (`packages/app-store/googlecalendar/lib/calendarservice.ts`), 97 findings, 31 cells
- **duplicate of golden #1** — “The Zod schema in parseRefreshTokenResponse uses computed property keys [z.string().toString()] and [z.string().optional().toString()] in minimumTokenResponseSc…”
  - cluster: Refresh-token response Zod schema uses computed keys that become a single literal "[object Object]", so dynamic/provider fields are stripped or parsing fails (`parseRefreshTokenResponse.ts`), 203 findings, 43 cells
- **duplicate of golden #8** — “The `appCredentialWebhookRequestBodySchema.parse` function can throw on invalid payloads, resulting in 500 Internal Server Errors instead of the expected 400 Ba…”
  - cluster: Unhandled Zod/decrypt/JSON parse exceptions in webhook handler cause 500s instead of returning 4xx (`apps/web/pages/api/webhook/app-credential.ts`), 80 findings, 34 cells
- **duplicate of golden #0** — “The parseRefreshTokenResponse function incorrectly sets refresh_token to the hardcoded string 'refresh_token' when it's missing from the OAuth refresh token res…”
  - cluster: parseRefreshTokenResponse overwrites missing refresh token with literal "refreshtoken" sentinel (`packages/app-store/utils/oauth/parserefreshtokenresponse.ts`), 53 findings, 23 cells
- **duplicate of golden #5** — “The `refreshOAuthTokens` function is passed `credentialId` instead of `userId`, which breaks the credential sync functionality by causing incorrect user lookups…”
  - cluster: Zoho Bigin refreshOAuthTokens called with credentialId instead of userId (calcomuserid mismatch) (`packages/app-store/zoho-bigin/lib/calendarservice.ts`), 45 findings, 11 cells
- **duplicate of golden #0** — “The parseRefreshTokenResponse function incorrectly sets refresh_token to the hardcoded string 'refresh_token' when it's missing from the OAuth refresh token res…”
  - cluster: Refresh token response is parsed with sync/minimal schema based on global sharing flags, corrupting provider-native credentials (e.g., Salesforce instanceUrl lost) (`packages/app-store/utils/oauth/parserefreshtokenresponse.ts`), 24 findings, 16 cells
- **duplicate of golden #0** — “The parseRefreshTokenResponse function incorrectly sets refresh_token to the hardcoded string 'refresh_token' when it's missing from the OAuth refresh token res…”
  - cluster: Missing refresh_token from sync response overwrites stored Office365 refresh token, permanently breaking credentials (`packages/app-store/office365calendar/lib/calendarservice.ts`), 20 findings, 15 cells
- **duplicate of golden #6** — “The Salesforce integration checks `response.statusText` instead of `response.ok` when handling OAuth token refresh responses. This can lead to unreliable behavi…”
  - cluster: Salesforce token refresh misclassifies successful responses by checking `response.statusText !== "ok"` instead of `response.ok` (`apps/api/lib/integrations/salesforce/lib/calendarservice.ts`), 35 findings, 15 cells

---

## PR 4 — 70 additional real bugs (8 goldens; 11 golden-duplicates removed)
(<https://github.com/ai-code-review-evaluation/discourse-graphite/pull/4>)

### Additional bugs (evidence cards)

#### A1 — absolutize_urls treats protocol-relative URLs (//...) as root-relative and rewrites them to the article host

**Location:** `app/models/topicembed.rb:58–65`  ·  **Severity:** high  ·  **Judge confidence:** 0.70  ·  116 findings, 48 cells

**Why this is real.** Multiple reports point to `app/models/topicembed.rb` around lines 64–65 where the URL-rewriting logic uses a check like `href.start_with?('/')` and then prefixes the article URI host/scheme (e.g. `href = "#{uri.scheme}://#{uri.host}#{href}"`). Because protocol-relative URLs begin with `//`, they satisfy `start_with?('/')` and are incorrectly rewritten as if they were root-relative paths on the article host, yielding a broken URL such as `https://article-host//cdn.example.com/img.png` instead of preserving `//cdn.example.com/img.png` or converting it to `https://cdn.example.com/img.png`. The file is not part of this PR’s diff, so verification is based on the consistent line references and described control flow in the deduplicated reports.

**How to replicate.** 1) Locate the method in `app/models/topicembed.rb` that rewrites `<a href>`/`<img src>` attributes (the reports cite ~58–65). 2) Confirm it has a branch that checks `start_with?('/')` and then builds an absolute URL by concatenating the embed/article URI scheme+host with the original string. 3) Consider an embedded article URL like `https://example.com/blog/post.html` containing HTML `<img src="//cdn.example.com/img.png">`. Expected: the rewritten `src` should remain protocol-relative (`//cdn.example.com/img.png`) or be absolutized to `https://cdn.example.com/img.png`. Actual per the code path: it matches the leading `/` branch and becomes `https://example.com//cdn.example.com/img.png` (or otherwise incorrectly points at the article host), breaking the link/image.

**Found by:** fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; terra: CE·medium, MRV·low, MRV·medium; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A2 — Embed requests are wrongly rejected due to strict/unnormalized Referer host check (and requiring Referer)

**Location:** `app/controllers/embedcontroller.rb:21–27`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  123 findings, 42 cells

**Why this is real.** The controller enforces embedding access by requiring a Referer and then doing an exact host string compare, e.g. `uri(request.referer || '').host != SiteSetting.embeddable_host` (and/or a preceding `request.referer` presence check). This is a real functional bug because `URI(...).host` is normalized differently than the admin setting (scheme/path/port/case/www variants), so legitimate embeds can be denied with 403 even when coming from the intended site. Additionally, some legitimate browser/referrer-policy situations omit Referer entirely for iframe requests, causing embeds to be rejected even when the request is otherwise valid.

**How to replicate.** 1) In admin settings, set the embeddable host to a value an operator might reasonably enter, e.g. `https://example.com/` or `Example.com` (mixed case), or set it to `example.com:8080` (includes port).
2) Add an embed on a page served from `https://example.com` (or `https://www.example.com` if you set `example.com`) that loads the Discourse embed endpoint in an iframe.
3) Observe: the iframe request returns 403/InvalidAccess (blank embed) because `URI(request.referer).host` yields just `example.com` (no scheme/path/port, typically downcased) and therefore will not equal the unnormalized `embeddable_host` string, or because the Referer header is missing.
4) Expected: legitimate embeds from the configured site should be accepted despite harmless formatting differences (scheme/trailing slash/case/www) and should not hard-fail solely due to Referer stripping by the browser/policy.

**Found by:** fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·low, MRV·medium; sonnet: CE·medium, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium

#### A3 — Unbounded open-uri fetch in TopicEmbed can hang jobs or exhaust Sidekiq memory

**Location:** `app/models/topicembed.rb:48–52`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  101 findings, 49 cells

**Why this is real.** The code at/around the reported location performs a remote fetch using open-uri and reads the entire response into memory (e.g., `open(url).read`). This call is made without explicit open/read timeouts and without a maximum byte limit, so a slow/stalled origin can tie up the worker indefinitely and a very large response can be fully buffered into memory, potentially OOM-killing the Sidekiq process. This is a functional reliability/security defect (resource exhaustion), not a style issue; the evidence here relies on the deduplicated reports because the PR diff for this file is not provided.

**How to replicate.** 1) Configure/trigger the code path that fetches an embed/article/feed URL through TopicEmbed (use a URL that TopicEmbed will fetch).
2) Point the URL to (a) an endpoint that never finishes sending data (slowloris/chunked stream) or sleeps for a long time before responding, and (b) an endpoint that returns a very large body (e.g., hundreds of MB).
3) Run the Sidekiq job/process that performs the fetch.
Expected: the job times out quickly and/or stops after a bounded number of bytes.
Actual: with `open(url).read`, the job can hang for a long time (no timeout) or memory usage grows until the worker is killed or becomes unstable (no response-size cap).

**Found by:** fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·low, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A4 — Destructive `force: true` in create_table migration can drop existing data

**Location:** `db/migrate/20131223171005createtoptopics.rb:3–3`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  82 findings, 42 cells

**Why this is real.** The migration’s `create_table` call includes `force: true` (reported at line 3), i.e., `create_table :toptopics, force: true do |t| ...`. In Rails, `force: true` drops the table if it already exists before recreating it. That turns a normally safe/failed re-run (which would raise if the table exists) into silent, irreversible data loss if the migration is ever replayed against a DB where `toptopics` already exists.

**How to replicate.** 1) In a Rails console or via SQL, create/populate a `toptopics` table with at least one row. 2) Ensure the migration is considered pending (e.g., delete its version row from `schema_migrations` while keeping the table). 3) Run `rails db:migrate`. Expected: migration should fail because the table already exists (preventing accidental overwrite). Actual: with `force: true`, the existing `toptopics` table is dropped and recreated, and the row(s) are lost.

**Found by:** fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·low, MRV·high, MRV·medium; glm-flash: CE·high, CE·low, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; astra: CE·medium, MRV·high, MRV·low

#### A5 — Disqus importer silently drops --category/-c support and no longer assigns imported topics to the requested category

**Location:** `lib/tasks/disqus.thor:114–152`  ·  **Severity:** high  ·  **Judge confidence:** 0.86  ·  87 findings, 44 cells

**Why this is real.** In the post-PR code, the CLI option is removed (the options list no longer includes `method_option :category, aliases: '-c'`), and the category lookup/assignment code is deleted. The import path now calls `post = TopicEmbed.import_remote(user, t[:link], title: t[:title])`, which does not take or apply a category ID, whereas the pre-change code explicitly did `PostCreator.new(..., category: category_id)`. This is a behavioral regression: existing automation that passes `--category/-c` will fail (unknown option) and imports can no longer be directed into a chosen category, forcing them into the default/uncategorized behavior.

**How to replicate.** 1) In a Discourse instance with this PR applied, run the Thor task as previously documented/used: `bundle exec thor disqus:import --post_as admin --category "Support" ...` (or `-c Support`).
2) Expected (pre-PR): the task accepts `--category/-c` and imported topics are created in the "Support" category.
3) Actual (post-PR): Thor rejects the invocation with an unknown option error (since `:category` is no longer defined), and even if invoked without the flag, the created topic comes from `TopicEmbed.import_remote(...)` with no category assignment, so imports are not placed into the intended category.

**Found by:** fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·medium, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium; sol: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; terra: MRV·medium; astra: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A6 — Redis throttle key can become permanent due to non-atomic SETNX + EXPIRE

**Location:** `lib/topicretriever.rb:27–28`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  74 findings, 41 cells

**Why this is real.** In `lib/topicretriever.rb` around lines 27–28, the throttle/lock is implemented as two separate Redis commands: `redis.setnx(throttle_key, 1)` followed by `redis.expire(throttle_key, THROTTLE_SECONDS)` (or equivalent). Because these are not atomic, a process crash/kill between the `setnx` and `expire` leaves the key present with no TTL. Subsequent runs see the key and treat the URL as throttled forever, so retrieval for that embed URL is permanently suppressed.

**How to replicate.** 1) Configure a Redis instance and run the code path that triggers the embed URL throttle (the one guarded by the SETNX/EXPIRE pair). 2) Instrument or pause execution right after `setnx` returns success (e.g., add a `sleep` between the `setnx` and `expire` lines), then kill the worker/process before `expire` executes. 3) Verify in Redis: `TTL <throttle_key>` returns -1 (no expiry) while the key exists. 4) Trigger the same URL retrieval again: expected behavior is that the throttle expires after the intended window and retrieval resumes; actual behavior is that retrieval continues to be skipped indefinitely because the key never expires.

**Found by:** fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·medium, MRV·high; glm-flash: CE·high, CE·medium, MRV·high, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; sol: CE·high, MRV·high; terra: CE·high, CE·medium; astra: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium

#### A7 — Redirect-based SSRF: only initial URL host is validated while open-uri follows redirects

**Location:** `lib/topicretriever.rb:14–53`  ·  **Severity:** critical  ·  **Judge confidence:** 0.78  ·  69 findings, 44 cells

**Why this is real.** The reports consistently describe code in lib/topicretriever.rb that validates only the initial hostname (e.g., parsing the input URL and checking `uri.host`) and then fetches content via open-uri (e.g., `open(url).read`). open-uri follows HTTP redirects by default, so if validation occurs only before the first request and the redirect destination is not re-checked (host/scheme/IP range), an attacker can use an allowed/whitelisted host that 30x-redirects to `127.0.0.1`, RFC1918 ranges, or `169.254.169.254` and the server will fetch it. The PR diff does not include this file, so this verification relies on the line references and behavior described in the reports rather than a patch hunk.

**How to replicate.** 1) Find where TopicRetriever is invoked (e.g., a feature that fetches/embeds remote topic content) and confirm it accepts a user-supplied URL.
2) Choose an allowed domain (one that passes the hostname allowlist) that can issue a redirect, or use any allowed domain with an open-redirect endpoint.
3) Provide a URL like `https://allowed.example/redirect?to=http://169.254.169.254/latest/meta-data/` (or to `http://127.0.0.1:PORT/`).
4) Observe server-side behavior: expected is the fetch should be rejected once it redirects off the approved host / into private or link-local address space; actual is the request follows the redirect and retrieves internal/metadata content because the redirect destination is not revalidated.

**Found by:** fable: CE·low; opus: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·medium, MRV·high, MRV·low, MRV·medium; glm-flash: MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·medium, MRV·high; astra: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A8 — TopicEmbed re-import crashes when the embedded post was deleted (embed.post is nil)

**Location:** `app/models/topic_embed.rb:23–34`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  68 findings, 24 cells

**Why this is real.** The code path that updates an existing embed assumes the associated Post still exists, e.g. it calls `PostRevisor.new(embed.post)` / `post_revisor = PostRevisor.new(post)` without checking for nil. If the embedded post has been deleted/trashed, `embed.post` will return nil (association can’t find the record due to deletion/default scope), so `PostRevisor.new(nil).revise!` raises (typically a NoMethodError inside PostRevisor) and the poll/import request aborts with a 500. This is a functional crash scenario, not a style issue; the reports indicate these exact lines but the PR diff does not include this file, so verification relies on reading the current file at the referenced lines.

**How to replicate.** 1) Create an embed so a TopicEmbed row exists and is linked to a created Post (initial import works). 2) Delete/trash that Post (or delete the Topic/Post in a way that leaves the TopicEmbed row behind). 3) Trigger the embed update path again (e.g., hit the embed poll/import endpoint for the same embed URL so it tries to revise the existing post). Expected: the system should recreate the post or clean up the embed and re-import. Actual: it attempts `PostRevisor.new(embed.post).revise!` with embed.post == nil and raises, returning a 500 and preventing further re-import attempts.

**Found by:** fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·medium; glm-flash: CE·high, CE·low, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A9 — Race condition: non-atomic exists?/create! on TopicEmbed causes RecordNotUnique under concurrent imports

**Location:** `lib/topicretriever.rb:36–37`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  72 findings, 46 cells

**Why this is real.** The code performs a check-then-act sequence on the unique embedurl: it does `topicembed.where(embedurl: embedurl).exists?` (around line 36) and then later does `topicembed.create!(embedurl: embedurl, ...)` (around line 37). Under concurrency, two workers can both observe `exists? == false` and both attempt `create!`; the database unique index on `embedurl` makes one raise `ActiveRecord::RecordNotUnique`, which (per the reports) is not handled, aborting the retrieval/import flow. The PR diff does not include this file, so this verification relies on the reported line references and the known uniqueness constraint behavior.

**How to replicate.** 1) Ensure `topicembeds.embedurl` has a UNIQUE index (as implied by the reports). 2) Pick an `embedurl` not yet present. 3) Trigger two imports for the same `embedurl` concurrently (e.g., run a staff-triggered "retrieve topic" that bypasses throttling at the same time as the hourly `PollFeed` job, or start two retrieve jobs in parallel). 4) Expected: one TopicEmbed is created and the other path no-ops cleanly. Actual: both paths pass the `exists?` precheck, the loser hits the UNIQUE constraint during `create!`, raising `ActiveRecord::RecordNotUnique` and causing the job/request to fail and potentially abandon remaining feed items.

**Found by:** fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·medium, MRV·high, MRV·low; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·low, CE·medium, MRV·high, MRV·low; sol: CE·high, MRV·medium; terra: CE·low, MRV·high, MRV·low; astra: MRV·high, MRV·medium

#### A10 — Embed loading page reloads forever with no terminal failure state

**Location:** `app/views/embed/loading.html.erb:8–10`  ·  **Severity:** high  ·  **Judge confidence:** 0.82  ·  66 findings, 34 cells

**Why this is real.** The view unconditionally schedules a page reload every 30 seconds: `setTimeout(function() { document.location.reload(); }, 30000);`. There is no conditional check, retry cap, or error/timeout UI, so if the underlying retrieval can never succeed (invalid URL, network failure, misconfiguration), the client will reload indefinitely and keep hitting the server forever. This is functional behavior (infinite polling loop), not a style concern.

**How to replicate.** 1) Configure/trigger an embed retrieval that will never become ready (e.g., embed an invalid/unreachable URL or simulate retrieval failure). 2) Load the embed/iframe so it renders `app/views/embed/loading.html.erb`. 3) Observe the browser reloading the same loading page every ~30 seconds indefinitely. Expected: after some number of failed attempts or a timeout, the page should stop polling and display an error state (and ideally stop generating repeated server requests/jobs); Actual: it reloads forever.

**Found by:** fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·medium, MRV·low; glm-flash: CE·high, CE·low, CE·medium, MRV·high; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high; terra: CE·low; astra: CE·medium, MRV·high

#### A11 — Embed URL lookup uses exact, unnormalized string match, allowing duplicate topics for equivalent URLs

**Location:** `app/models/topicembed.rb:79–82`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72  ·  42 findings, 26 cells

**Why this is real.** The code (per the aggregated reports; this file is not part of the PR diff) performs an exact lookup on the stored embed URL, e.g. `TopicEmbed.where(embed_url: embed_url).first` / `find_by(embed_url: embed_url)` at/around line 79. Because the input is used verbatim (no canonicalization such as stripping fragments, normalizing trailing slashes, or normalizing query strings/host casing), logically equivalent URLs (like `https://site/a` vs `https://site/a/` vs `https://site/a#x`) will not match the existing record and can cause creation of separate TopicEmbed/Topic records for the same resource. This is a functional correctness bug (duplicate discussions / split history), not a style issue.

**How to replicate.** 1) Enable/confirm Discourse embedding is set up for a host and can create topics from an `embed_url`.
2) Trigger an embed for a URL, e.g. request the embed endpoint (or run the embed creation path) with `embed_url=https://example.com/article` and observe a topic created and a TopicEmbed row stored with that exact string.
3) Trigger embedding again for a semantically equivalent variant, e.g. `https://example.com/article/` (trailing slash) or `https://example.com/article#comments` (fragment) or `https://EXAMPLE.com/article` (host case).
Expected: the existing embedded topic is found and reused. Actual: the lookup misses and a new topic/topicembed is created, resulting in duplicate topics for the same article (and potentially bypassing any per-URL throttling keyed on the raw string).

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·medium; glm-flash: MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium; sol: CE·high, MRV·high, MRV·medium; terra: MRV·low, MRV·medium; astra: MRV·high, MRV·low, MRV·medium

#### A12 — Unrescued inline feed poll aborts HTTP fallback on embed cache miss

**Location:** `lib/topicretriever.rb:41–43`  ·  **Severity:** high  ·  **Judge confidence:** 0.70  ·  35 findings, 23 cells

**Why this is real.** The reported code path around `lib/topicretriever.rb:41` calls `Jobs::Pollfeed.new.execute({})` synchronously inside the retrieval flow (e.g., in/near `performretrieve`) and does not rescue exceptions from that call. Because the poll runs inline and unhandled errors propagate, any feed-level failure (network error, malformed RSS) aborts the method before it can reach the direct `fetchhttp` fallback, so otherwise reachable articles are never retrieved and embeds remain stuck. This file is not part of the PR diff per the prompt, so verification relies on reading the referenced lines in the post-PR tree to confirm the inline call and lack of exception handling/ensure around it.

**How to replicate.** 1) Configure an embed URL that is not yet cached (clear the plugin/cache store). 2) Point the RSS/feed source used by `Jobs::Pollfeed` to an unavailable/malformed endpoint (e.g., invalid host or serve broken XML). 3) Trigger retrieval for the uncached embed (load a post containing the embed or call the retriever method). Expected: the code should fall back to a direct HTTP fetch and still retrieve the target article. Actual: the inline `Pollfeed.execute` raises, the exception propagates, and the HTTP fallback is skipped, leaving the embed/article unresolved (often a perpetual loading state).

**Found by:** fable: CE·low; opus: CE·high, CE·medium, MRV·low, MRV·medium; glm-flash: CE·high; glm-vis: CE·low, CE·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low; terra: CE·high, MRV·medium; astra: CE·high, CE·low, MRV·high, MRV·medium

#### A13 — TopicEmbed advances contentsha1 even when post revision fails, permanently skipping future re-syncs

**Location:** `app/models/topicembed.rb:34–37`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  37 findings, 29 cells

**Why this is real.** In `app/models/topicembed.rb` around lines 34–37, the code path calls the revisor (e.g., `revisor.revise!(...)`) but does not check its return value / persistence success before updating the embed’s checksum (e.g., `update_column(:contentsha1, new_sha1)` or equivalent). This means a rejected/failed revision (validation/callback/permission) can still advance `contentsha1`, making the system believe the new content was imported even though the post body did not change. Because subsequent sync checks compare the current content’s SHA to `contentsha1`, the failed update will never be retried and the embedded topic content can remain stale indefinitely (reports indicate the file is not modified in this PR, so verification relies on the current code in that file).

**How to replicate.** 1) Locate the import/update method in `TopicEmbed` that computes a new content SHA and then revises the first post via `PostRevisor` (or similar) followed by an unconditional `contentsha1` write.
2) Create a scenario where `revisor.revise!` fails/returns false (e.g., make the target post/topic non-editable, trigger a validation/callback rejection, or otherwise cause the revisor save to fail).
3) Run the embed import/update with changed remote content so a new SHA is computed.
Expected: if the revision fails, `contentsha1` should remain unchanged so a later run retries.
Actual: `contentsha1` is updated despite the failed revision; the post content remains old, and later runs skip updating because the stored SHA now matches the new remote content.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·low; glm-flash: CE·low, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·low; sol: CE·high, MRV·high, MRV·low, MRV·medium; terra: CE·high; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A14 — TopicEmbed embedurl column defaults to varchar(255), causing failures for valid long URLs during imports/polling

**Location:** `db/migrate/20131217174004createtopicembeds.rb:6–10`  ·  **Severity:** high  ·  **Judge confidence:** 0.70  ·  33 findings, 17 cells

**Why this is real.** Multiple reports pinpoint the migration line defining the column as a default-length string (e.g., `t.string :embedurl`), which in Rails maps to `varchar(255)` unless a larger `:limit` is specified. Real-world article/feed URLs (especially with tracking/query params) can exceed 255 characters; when such a URL is inserted into `topic_embeds.embedurl`, Postgres raises a "value too long"/`StatementInvalid` error, aborting the import/poll job. The file is not part of this PR's diff, so this verification relies on the reported offending line reference (`:6`) and standard Rails schema behavior for `t.string`.

**How to replicate.** 1) Ensure the migration has been applied and `topic_embeds.embedurl` is a `varchar(255)` (e.g., `\d topic_embeds` in psql). 2) Attempt to create a TopicEmbed (or run the feed import/poll job) with an embed URL longer than 255 chars, e.g. `TopicEmbed.create!(embedurl: 'http://example.com/?' + 'a'*300, topic_id: some_topic_id)`. 3) Expected: record is created and job continues. Actual: database insert fails with a length/statement error and the import/polling process aborts or partially processes then crashes.

**Found by:** fable: CE·low; opus: CE·medium, MRV·high, MRV·medium; sonnet: CE·low, CE·medium; glm-flash: CE·high, CE·medium, MRV·high; glm-vis: MRV·high, MRV·medium; astra: MRV·high

#### A15 — EmbedController spec expects synchronous TopicRetriever call but controller enqueues async :retrieve_topic job

**Location:** `spec/controllers/embed_controller_spec.rb:44–49`  ·  **Severity:** high  ·  **Judge confidence:** 0.82  ·  34 findings, 26 cells

**Why this is real.** In the controller spec around lines 44-49, the test sets Mocha expectations like `TopicRetriever.expects(:new)` and `retriever.expects(:retrieve)`, asserting the controller directly instantiates and runs the retriever. But the controller implementation (reported at `app/controllers/embed_controller.rb` around line 15) calls `Jobs.enqueue(:retrieve_topic, ...)` (or `:retrievetopic` per reports) instead of calling `TopicRetriever` synchronously, so the spec’s mocked collaborator is never invoked and the example fails with unsatisfied expectations (or, worse, tests the wrong contract). This is a real behavioral mismatch between test and code, not a style issue.

**How to replicate.** 1) Check `app/controllers/embed_controller.rb` (around line 15) and confirm the action enqueues `Jobs.enqueue(:retrieve_topic, embed_url: ..., user_id: ...)` rather than calling `TopicRetriever.new(...).retrieve`.
2) Open `spec/controllers/embed_controller_spec.rb` lines ~44-49 and confirm it expects `TopicRetriever.expects(:new)` and `retriever.expects(:retrieve)`.
3) Run `bundle exec rspec spec/controllers/embed_controller_spec.rb` with Sidekiq/Jobs not running inline; observe the failing example due to Mocha expectations never being satisfied. Expected (per spec): retriever is called; actual: only a background job is enqueued.

**Found by:** opus: CE·low, CE·medium, MRV·low, MRV·medium; sonnet: CE·high; glm-flash: CE·low; glm-vis: CE·low, CE·medium, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·high, CE·medium, MRV·high; astra: CE·high

#### A16 — embed.js throws when #discourse-comments container is missing (null appendChild)

**Location:** `app/assets/javascripts/embed.js:5–12`  ·  **Severity:** high  ·  **Judge confidence:** 0.93  ·  42 findings, 25 cells

**Why this is real.** The script assigns `var comments = document.getElementById('discourse-comments')` and then unconditionally calls `comments.appendChild(iframe);`. If the host page includes this embed script but does not define an element with id `discourse-comments`, `getElementById` returns null and `appendChild` throws a TypeError, aborting the IIFE before the `message` listener is registered.

**How to replicate.** 1) Include the generated `embed.js` on any HTML page but omit `<div id="discourse-comments"></div>`. 2) Load the page and open the browser console. Expected: the script should no-op or fail gracefully. Actual: it throws (e.g., "Cannot read properties of null (reading 'appendChild')"), and the rest of the embed initialization (including `window.addEventListener('message', ...)`) never runs.

**Found by:** fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·low, MRV·medium; sonnet: MRV·high; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; glm-vis: MRV·medium; sol: CE·low, CE·medium

#### A17 — disqus:import regresses to live HTTP fetch per thread with no error handling (and drops -c category option), causing imports to abort or mis-categorize

**Location:** `lib/tasks/disqus.rake:25–62`  ·  **Severity:** high  ·  **Judge confidence:** 0.62  ·  20 findings, 10 cells

**Why this is real.** The reports consistently describe that the importer’s main loop was changed to call `TopicEmbed.import_remote(user, t[:link], ...)` inside `parser.threads.each`, performing network I/O (via open-uri) for every thread. Because this call is not wrapped in any `begin/rescue`, a single `OpenURI::HTTPError`, timeout, redirect error, or nil/invalid `t[:link]` will raise and abort the entire import mid-run, leaving a partial import. The same change set also removed the documented `--category/-c` option and category lookup from the task, so existing invocations now fail with an unknown-option error and/or imported topics lose intended category placement; the PR diff for `TopicEmbed.import_remote` is not included here, so this verification relies on the deduplicated reports’ quoted call sites and behavior.

**How to replicate.** 1) Prepare a Disqus export where at least one thread has a dead/unreachable permalink in `link` (e.g., `https://example.invalid/missing`). 2) Run the task in the PR’s post-merge tree (e.g., `bundle exec rake disqus:import[/path/to/export.xml]`). Expected (pre-regression): importer creates topics/posts from the export data without requiring live HTTP, completing the run. Actual (post-regression): the run performs a live fetch per thread; when it hits the dead URL it raises (e.g., `OpenURI::HTTPError`/timeout) and stops, leaving only earlier threads imported. 3) Additionally, run the previously-documented invocation with category (e.g., `bundle exec rake disqus:import[/path/to/export.xml] -c mycat` or equivalent Thor option): expected is successful import into the specified category; actual is an unknown-option failure or topics going to the default category because the option/lookup was removed.

**Found by:** glm-flash: CE·high, CE·low, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium

#### A18 — Throttle key is acquired before successful fetch and uses non-atomic setnx+expire, causing skipped retries or permanent lockout

**Location:** `lib/topicretriever.rb:27–35`  ·  **Severity:** critical  ·  **Judge confidence:** 0.72  ·  18 findings, 15 cells

**Why this is real.** Multiple reports point to code around lines 27–35 that (a) records the throttle before the retrieval succeeds and (b) implements the throttle with `$redis.setnx(...)` followed by a separate `$redis.expire(...)`. If the fetch fails and Sidekiq retries within the TTL window, the worker can see the throttle key already set and return early "success" without re-attempting the failed work. Separately, because `setnx` and `expire` are not atomic, a process crash between them can leave the key without a TTL (TTL = -1), permanently blocking future retrieval for that URL; this is a functional correctness bug, not a style issue. (The file is not in this PR diff, so this is verified based on the consistent line-referenced reports.)

**How to replicate.** 1) Skipped retry path: enqueue the job that calls TopicRetriever for a given URL; force the actual fetch/parsing to raise (e.g., network failure/timeout) after the throttle key has been set. Observe Sidekiq schedules a retry; when it runs within ~60s, the code hits the throttle early-return (because the key already exists) and exits without fetching; expected: the retry should re-attempt the fetch and only throttle after a successful completion.
2) Permanent lockout path: run two Redis commands as the code does—first `SETNX retrieved:<url> 1`, then kill the process before `EXPIRE retrieved:<url> 60` executes. In Redis, `TTL retrieved:<url>` returns -1 (no expiry); subsequent runs will always see the key present and never retrieve that URL again; expected: throttle key should always have an expiry (atomic `SET ... NX EX 60` or Lua).

**Found by:** opus: MRV·high, MRV·low; glm-flash: CE·high, CE·low; glm-vis: CE·high, CE·medium; sol: CE·high, CE·low, CE·medium, MRV·low, MRV·medium; terra: MRV·low, MRV·medium; astra: MRV·low

#### A19 — TopicEmbed import mutates caller-owned contents via `<<`, causing duplicate footers and FrozenError on frozen strings

**Location:** `app/models/topicembed.rb:12–14`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  16 findings, 13 cells

**Why this is real.** The code appends the imported-from footer using in-place mutation: `contents << "\n<hr>..."` (reports point to lines ~12–14). Using `<<` modifies the caller-provided String object, so if the same `contents` instance is reused (retries/re-imports) the footer accumulates repeatedly. If `contents` is frozen (e.g., from `# frozen_string_literal: true` or explicitly `.freeze`), `<<` raises `FrozenError`, making this a functional bug rather than a style issue; the PR diff does not include this file, so this is based on the referenced post-PR line locations in the reports.

**How to replicate.** 1) In a Rails console, create a reusable string: `c = "Hello"`; call the import method (e.g., `TopicEmbed.import(url, title, c, user_id, ...)`) twice with the same `c` object. Expected: imported footer appears once per stored post; actual: `c` is mutated and the second call appends a second footer (and any downstream SHA1/validation based on `contents` changes as a side effect).
2) Trigger frozen input: `c = "Hello".freeze` (or use a frozen string literal in code) and call the same import path. Expected: import succeeds; actual: raises `FrozenError` at the `contents << "\n<hr>..."` line.

**Found by:** fable: CE·low; opus: CE·medium, MRV·high; glm-flash: CE·low; sol: CE·high; astra: CE·low, MRV·high

#### A20 — Existing TopicEmbed updates ignore title-only changes, leaving topic titles stale

**Location:** `app/models/topicembed.rb:34–37`  ·  **Severity:** medium  ·  **Judge confidence:** 0.85  ·  18 findings, 13 cells

**Why this is real.** In the existing-embed update branch (around lines 34–37), the code gates updates on the body checksum (e.g., `if contentsha1 != embed.contentsha1`) and, when it does update, it revises only the post raw via a call like `revisor.revise!(user, absolutizeurls(url, contents), ...)` and then stores the new `contentsha1`. There is no corresponding update of the topic/title field in this path, so when an upstream feed/article title is corrected but the body content remains the same, the condition is false and the title is never propagated. This is a functional defect (stale topic titles after successful re-polls), not a style issue; the PR diff does not include this file, so this verification relies on the reported line references and described code.

**How to replicate.** 1) Import/embed a feed item/article into Discourse so a TopicEmbed/topic is created with title T1 and body B. 2) Change the upstream title to T2 but keep the body exactly B (so the body SHA1 remains unchanged). 3) Trigger the embed refresh/poll that calls TopicEmbed’s update logic for existing records. Expected: the existing Discourse topic title updates to T2. Actual: the topic title remains T1 because the update path only checks `contentsha1` (derived from body) and only revises the post body, never applying the new title.

**Found by:** opus: MRV·high, MRV·low, MRV·medium; glm-flash: MRV·medium; glm-vis: MRV·high, MRV·medium; sol: MRV·high; terra: MRV·high; astra: MRV·high, MRV·low, MRV·medium

#### A21 — TopicEmbed URL guard uses line-anchored regex and later calls URI() without rescue, allowing malformed/multiline URLs to crash imports

**Location:** `app/models/topicembed.rb:11–58`  ·  **Severity:** high  ·  **Judge confidence:** 0.68  ·  12 findings, 12 cells

**Why this is real.** Multiple reports point to a scheme/prefix check like `url =~ /^https?\:\/\//` around line 11 and later parsing like `URI(url)` inside `absolutize_urls` around lines 57–58. In Ruby, `^` is line-anchored (matches after newlines), so a multiline string such as `"javascript:...\nhttp://x"` can pass the `^https?://` gate even though the overall value is not a safe/valid URL. Separately, the guard only checks a prefix, so malformed values (e.g., containing spaces) can still pass and then `URI(url)` can raise `URI::InvalidURIError`; if not rescued, that exception aborts the feed/import job.

**How to replicate.** 1) Locate `app/models/topicembed.rb` and confirm there is a URL scheme check around line ~11 using a regex anchored with `^` (e.g., `/^https?:\/\//`) rather than `\A`.
2) Confirm `absolutize_urls` (around lines ~57–58) calls `URI(url)` / `URI.parse(url)` without a `rescue URI::InvalidURIError`.
3) Trigger: provide a feed item/link (or stored embed URL) that passes the prefix regex but is not a valid URI, e.g. `"http:// bad"` (space) or a multiline value `"javascript:alert(1)\nhttp://example.com"`.
4) Run the code path that processes links (the feed polling/import job that calls `absolutize_urls`).
Expected: invalid URLs are rejected/skipped without killing the job.
Actual: `URI::InvalidURIError` is raised from `URI(url)` and the import/polling job crashes/aborts; multiline input can also bypass the intended scheme validation.

**Found by:** fable: CE·low; opus: CE·high, CE·medium, MRV·high, MRV·low; sonnet: CE·high, MRV·high; glm-flash: CE·high, CE·low

#### A22 — Embed/topic retrieval synchronously runs full feed poll (Jobs::PollFeed) on cache miss, coupling embeds to feed health and enabling resource exhaustion

**Location:** `lib/topicretriever.rb:44–47`  ·  **Severity:** critical  ·  **Judge confidence:** 0.78  ·  11 findings, 9 cells

**Why this is real.** In `perform_retrieve`, the code calls `Jobs::PollFeed.new.execute({})` inline (reported at `lib/topicretriever.rb:44-47`). Because this executes the entire feed fetch/parse/import synchronously inside the embed retrieval path, any slow/hanging feed blocks the worker and any exception in `PollFeed` aborts the retrieval before the normal HTTP fetch path runs. This is a functional defect (availability/behavior change) rather than a style issue: embed retrieval becomes dependent on external feed polling success and can be repeatedly triggered by cache-miss requests.

**How to replicate.** 1) In a dev instance, enable the site setting that causes `perform_retrieve` to run feed polling (e.g., `feed_polling_enabled = true`) and set `feed_polling_url` to an unreachable host (or a server that accepts connections but never responds). 2) Trigger an embed retrieval cache miss (e.g., request `/embed/best?url=https://example.com/some/new/path` or whatever endpoint enqueues/executes `TopicRetriever#perform_retrieve` for an unknown URL). 3) Observe that the job blocks or fails while executing `Jobs::PollFeed.new.execute({})`, and the normal per-URL HTTP retrieval does not proceed; subsequent requests for different URLs repeat the whole-feed poll again, tying embed availability/performance to the feed server.

**Found by:** glm-flash: MRV·high, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium

#### A23 — TopicEmbed uses open(url) without requiring open-uri, causing URL opens to be treated as local files

**Location:** `app/models/topicembed.rb:46–48`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  12 findings, 12 cells

**Why this is real.** The reports consistently point to `importremote` calling `open(url).read` (e.g., `Readability::Document.new(open(url).read, ...)`) in `app/models/topicembed.rb` around lines 46–48, but this model file only requires Nokogiri and does not `require 'open-uri'`. In Ruby, `open("http://...")` only gains URL-handling behavior when open-uri is loaded; otherwise `Kernel#open` treats the string as a local path, leading to `Errno::ENOENT` for URLs. This creates a real load-order coupling where it only works if some other file (notably `app/jobs/scheduled/pollfeed.rb`) happened to require `open-uri` first.

**How to replicate.** 1) Ensure `app/jobs/scheduled/pollfeed.rb` (or any other file requiring `open-uri`) is not loaded first (e.g., Rails console in development with lazy autoloading, or run the import task path that loads TopicEmbed directly). 2) Invoke the code path that calls `TopicEmbed#importremote` with an HTTP(S) URL (e.g., via the Disqus import thor task mentioned in the reports, or directly in a console if the method is accessible). 3) Expected: it fetches the remote page content over HTTP and parses it. Actual: Ruby attempts to open a local file literally named like `http://example.com/...` and raises `Errno::ENOENT (No such file or directory)`.

**Found by:** fable: CE·low; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low; sonnet: MRV·high, MRV·medium; glm-flash: MRV·high, MRV·low; glm-vis: CE·high

#### A24 — Readability import sanitizer preserves javascript: URLs in whitelisted href/src attributes (stored XSS on click)

**Location:** `lib/import_remote/readability.rb:45–92`  ·  **Severity:** high  ·  **Judge confidence:** 0.62  ·  8 findings, 6 cells

**Why this is real.** In the readability import sanitization, the tag/attribute allowlist keeps URL-bearing attributes like `a[href]` and `img[src]` but does not restrict allowed URL schemes (e.g., no `protocols`/scheme validation for `href`/`src`). As a result, values such as `href="javascript:alert(1)"` survive unchanged through sanitization. Additionally, the URL “absolutize” logic only rewrites relative paths (e.g., those starting with `/`), so `javascript:` URLs are not touched and remain in the cooked/imported HTML.

**How to replicate.** 1) Host an HTML page containing something like `<article><a href="javascript:alert(document.domain)">click</a></article>`.
2) In Discourse (this plugin/app), use the "import remote" / readability-based import path to import that page into a topic (same path used for embedding/importing remote articles).
3) Inspect the resulting cooked HTML/topic content: the `<a>` tag remains and still has `href="javascript:..."`.
4) Click the link as a normal viewer: expected behavior is that the sanitizer strips or neutralizes the unsafe URL; actual behavior is script execution in the forum origin context upon click (stored XSS vector for anyone viewing imported content).

**Found by:** glm-flash: CE·high, CE·low, CE·medium, MRV·high; glm-vis: CE·medium, MRV·high

#### A25 — PollFeed specs for missing URL/username are vacuous because feedpollingenabled? is never set true

**Location:** `spec/jobs/pollfeedspec.rb:18–30`  ·  **Severity:** medium  ·  **Judge confidence:** 0.82  ·  8 findings, 3 cells

**Why this is real.** In the examples around lines 18–30, the spec stubs only the individual setting under test (e.g., `SiteSetting.stubs(:feedpollingurl).returns(nil)` / `SiteSetting.stubs(:embedbyusername).returns(nil)`) but never stubs `SiteSetting.feedpollingenabled?` to `true`. If `execute` is implemented as a guard chain like `return unless feedpollingenabled? && feedpollingurl.present? && embedbyusername.present?`, the default `feedpollingenabled? == false` short-circuits before URL/username are even evaluated, so these tests would still pass even if the URL/username guard checks were deleted. The PR does not modify this file in its diff, so this verification relies on the reported line references and typical Discourse guard logic.

**How to replicate.** 1) Open `spec/jobs/pollfeedspec.rb` and confirm the 'requires feedpollingurl' and 'requires embedbyusername' examples stub only `feedpollingurl` or `embedbyusername` but do not stub `feedpollingenabled?` to true. 2) Confirm `pollfeed` is stubbed/spied such that `execute` is expected not to call it. 3) Temporarily edit the job implementation to remove the URL (or username) presence check from `execute` (leave `feedpollingenabled?` as the only guard). 4) Run the spec suite: the two examples still pass, demonstrating the tests never exercised those guards and are therefore defective.

**Found by:** sol: MRV·high

#### A26 — Embed layout references standalone embed assets that are not added to assets.precompile, breaking production

**Location:** `app/views/layouts/embed.html.erb:4–5`  ·  **Severity:** high  ·  **Judge confidence:** 0.80  ·  7 findings, 7 cells

**Why this is real.** The embed layout includes a new standalone stylesheet bundle via `<%= stylesheet_link_tag 'embed' %>` (reported at embed.html.erb:4-5), but the PR adds `app/assets/stylesheets/embed.css.scss` / `app/assets/javascripts/embed.js` without any corresponding change to `config.assets.precompile`. In Rails 4 + sprockets-rails (typical Discourse setup), only `application.(js|css)` and explicitly precompiled bundles are available when `config.assets.compile = false`, so this reference will raise an `AssetNotPrecompiledError` or produce a missing `/assets/embed-<digest>.css` request in production.

**How to replicate.** 1) In a production-like environment set `config.assets.compile = false` and run `RAILS_ENV=production bundle exec rake assets:precompile`. 2) Boot the app in production mode and request an embed page that uses this layout (e.g., `/embed/best?embed_url=https%3A%2F%2Fexample.com%2Fpost`). 3) Expected: embed page loads with styles and the third-party embed works. Actual: the response errors with an `AssetNotPrecompiled` for `embed.css` (or the browser requests `/assets/embed-<digest>.css` and gets 404), leaving the embedded widget unstyled/broken.

**Found by:** opus: MRV·medium; glm-flash: MRV·high, MRV·medium; glm-vis: CE·high, MRV·high

#### A27 — Embed topic retrieval can crash or silently no-op when embedbyusername is blank/missing, leaving embeds stuck on infinite “loading”

**Location:** `lib/topicretriever.rb:49–50`  ·  **Severity:** critical  ·  **Judge confidence:** 0.93  ·  7 findings, 7 cells

**Why this is real.** The reported code at lib/topicretriever.rb:49-50 uses the configured embedding username without validation: `user = user.where(usernamelower: sitesetting.embedbyusername.downcase).first` followed by `return if user.blank?`. If `embedbyusername` is the shipped default empty string (or nil), calling `.downcase` can raise (NoMethodError), causing the job to fail repeatedly; if it does not raise (e.g., empty string), `return if user.blank?` silently exits without importing/creating a topic and without surfacing an error. In both cases, the embed request never transitions out of the loading state, which is functional breakage rather than a style issue. (The file/lines are not in this PR’s diff; this verification relies on the reports’ cited lines.)

**How to replicate.** 1) Configure a site with the default/blank embedding import username (embedbyusername = ''), or set it to a username that does not exist/deleted. 2) Hit an embed endpoint/page that triggers topic retrieval (an embedded discussion for a valid URL). 3) Observe: the embed shows the loading frame/page and keeps reloading/re-enqueuing retrieval. Expected: either a topic is created and the embed loads normally, or a clear configuration/error message is returned/logged. Actual: the job either crashes on `.downcase` (if nil) or returns early on `user.blank?`, so no topic is created and the embed remains stuck on “loading” indefinitely with no actionable error.

**Found by:** opus: MRV·medium; sol: CE·low, MRV·high, MRV·low, MRV·medium; terra: MRV·high; astra: MRV·low

#### A28 — Gemfile updated with new gems but default Gemfile.lock not regenerated, breaking frozen/deployment bundler installs

**Location:** `Gemfile:209–211`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  6 findings, 4 cells

**Why this is real.** In the PR, `Gemfile` adds new dependencies around lines 209–211 (e.g., `gem 'ruby-readability'` and `gem 'simple-rss'`). However, per the evidence pack/reports, only `gemfilerails4.lock` was regenerated while the repository’s default `Gemfile.lock` was left unchanged (the PR contains no diff updating `Gemfile.lock`). This creates a real Gemfile/lockfile mismatch: on the default (non-rails4) lockfile path, Bundler detects the lock is out of sync with the Gemfile and aborts in frozen/deployment mode.

**How to replicate.** 1) Check out the PR branch/merge commit.
2) Ensure you are using the default lockfile path (do not point bundler to the rails4 lockfile).
3) Run `bundle install --deployment` (or set `BUNDLE_FROZEN=true` and run `bundle install`, or run `bundle check`).
Expected: Bundler installs using the committed `Gemfile.lock`.
Actual: Bundler errors that `Gemfile.lock` is out of date with `Gemfile` (because `ruby-readability`/`simple-rss` are in `Gemfile` but not reflected in the default lockfile), forcing a lockfile regeneration and breaking CI/deploy flows that require frozen locks.

**Found by:** glm-flash: MRV·high, MRV·low; glm-vis: MRV·high

#### A29 — Redis throttle key is set before retrieval succeeds, suppressing retries after failures

**Location:** `lib/topicretriever.rb:32–55`  ·  **Severity:** high  ·  **Judge confidence:** 0.62  ·  5 findings, 5 cells

**Why this is real.** Per the reports, `retrievedrecently?` writes the 60s throttle marker using `$redis.setnx(...)` followed by `$redis.expire(..., 60)` before `performretrieve` is executed. Because the key is committed before the actual retrieval/import work, any exception or early-return in `performretrieve` leaves the marker in Redis for its full TTL. Subsequent retries within 60 seconds hit `retrievedrecently?` and return without attempting work, so the job can “succeed” while no topic is created and no error is surfaced. (The PR diff for this file isn’t available here; this verification relies on the consistent, matching reports.)

**How to replicate.** 1) Configure/enqueue a retrieval for an embed URL that will reliably fail in `performretrieve` (e.g., a URL that times out, returns 404, or triggers a parsing/readability failure).
2) Run the job once: it will set the Redis throttle key via `setnx+expire`, then raise during `performretrieve`.
3) Immediately retry the same job (or let Sidekiq retry) within 60 seconds.
Expected: the retry should attempt the retrieval again (or at least surface the prior failure).
Actual: the retry returns early due to the existing throttle key and does no work; no topic is created, and the failure is effectively masked until the TTL expires.

**Found by:** glm-flash: MRV·high, MRV·low, MRV·medium; glm-vis: MRV·high

#### A30 — Rails migration adds NOT NULL column with DEFAULT, causing full table rewrite and ACCESS EXCLUSIVE lock on PostgreSQL < 11

**Location:** `db/migrate/20131219203905addcookmethodtoposts.rb:3–3`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  5 findings, 2 cells · ⚠️ **no harness cell found this**

**Why this is real.** The migration reportedly contains `add_column :posts, :cookmethod, :integer, default: 1, null: false` (line 3 per the reports). On PostgreSQL versions prior to 11, adding a column with both a non-null DEFAULT and `null: false` forces a full table rewrite and takes an `ACCESS EXCLUSIVE` lock for the duration, blocking reads/writes on `posts`. This is a well-known operational hazard in production on large tables; since this file was not part of the PR diff, this verification relies on the consistent line-referenced reports.

**How to replicate.** 1) Use PostgreSQL 9.6 or 10 (or any < 11) and create a large `posts` table (e.g., millions of rows). 2) Run the migration containing `add_column :posts, :cookmethod, :integer, default: 1, null: false`. 3) In a second session, attempt any `SELECT/UPDATE/INSERT` on `posts` while the migration runs and/or inspect `pg_locks`/`pg_stat_activity`. Expected: schema change should be near-instant and not block normal traffic; Actual: migration holds an ACCESS EXCLUSIVE lock and can take minutes due to table rewrite, blocking application traffic and causing downtime.

**Found by:** **no harness cell** — vanilla only: opus, sol

#### A31 — Embed best view renders imported post HTML as raw, enabling XSS from untrusted imported content

**Location:** `app/views/embed/best.html.erb:18–25`  ·  **Severity:** critical  ·  **Judge confidence:** 0.62  ·  5 findings, 5 cells

**Why this is real.** In the embed rendering template, the post body is output using Rails' raw helper (e.g., `<%= raw post.cooked %>`), which bypasses HTML escaping. If `post.cooked` can contain attacker-controlled HTML from `TopicEmbed.import`/remote feeds, that HTML will be emitted verbatim in `/embed/best`, enabling script injection. The clustered reports all point to this same mechanism and note there are no specs asserting sanitization/escaping of imported content, so the unsafe branch is not guarded by tests.

**How to replicate.** 1) Configure Discourse embedding for a host you control. 2) On that host, serve an embeddable page whose imported content includes a payload like `<img src=x onerror=alert(1)>` (or `<script>alert(1)</script>` if allowed by the importer). 3) Trigger the embed import (visit the page with the Discourse embed script or run the embed retrieval job), then open `/embed/best?embed_url=<that page URL>` (or the equivalent embed best endpoint for the imported URL). Expected: imported HTML is sanitized/escaped so no JS runs. Actual: because the template renders `post.cooked` via `raw`, the payload is reflected and executes in the embed page context.

**Found by:** glm-vis: CE·low

#### A32 — Embeddable host validation uses strict string equality, rejecting valid hosts with different casing or with a scheme included

**Location:** `lib/topicretriever.rb:14–15`  ·  **Severity:** high  ·  **Judge confidence:** 0.86  ·  4 findings, 4 cells

**Why this is real.** The host gate is implemented as a direct string comparison (reported as `SiteSetting.embeddablehost != URI(@embedurl).host`). This is a real correctness bug because DNS hostnames are case-insensitive, so `Example.com` and `example.com` should match but won’t with a case-sensitive `!=` check. Additionally, if an admin enters a full URL like `https://example.com` into the setting, it will never equal `URI(@embedurl).host` (which is just `example.com`), effectively rejecting all embeds for that site.

**How to replicate.** 1) Configure the application setting `embeddablehost` to either (a) `Example.com` (different casing) or (b) `https://example.com` (includes scheme). 2) Attempt an embed retrieval using an embed URL like `https://example.com/some/path`. 3) Expected: host validation passes and the topic is retrievable/embeddable. Actual: validation fails because the code compares the raw setting string to `URI(embedurl).host` with strict equality, so it rejects the request.

**Found by:** glm-flash: CE·low; sol: CE·high, CE·medium; astra: MRV·medium

#### A33 — Migration backfills posts.cookmethod to rawhtml, causing all existing posts to bypass cooking/sanitization

**Location:** `db/migrate/20131219203905_add_cookmethod_to_posts.rb:3–3`  ·  **Severity:** critical  ·  **Judge confidence:** 0.90  ·  4 findings, 4 cells

**Why this is real.** The migration reportedly adds the column with `add_column :posts, :cookmethod, :integer, default: 1, null: false` (line 3). In Rails/ActiveRecord, adding a NOT NULL column with a DEFAULT backfills all existing rows to that default, so every historical post gets `cookmethod = 1`. If enum value `1` corresponds to `rawhtml`, the rendering logic will take the raw/unsafe branch and skip the normal cooking + sanitization pipeline, making this a functional and security-impacting defect (the file was not in the PR diff, so this relies on the reports’ cited line).

**How to replicate.** 1) Start with a database containing at least one existing Post whose raw contains Markdown/HTML (e.g., `<script>alert(1)</script>` or `**bold**`). 2) Deploy/apply the migration `20131219203905_add_cookmethod_to_posts`. 3) Query the DB: `SELECT id, cookmethod FROM posts LIMIT 5;` — observe existing rows now have `cookmethod = 1`. 4) Load a topic containing an old post in the UI (or hit the post serializer endpoint). Expected: historical posts remain cooked/sanitized (Markdown converted, unsafe HTML stripped). Actual: posts render using the rawhtml path (raw source returned as trusted cooked HTML), bypassing cooking/sanitization and potentially executing user-supplied HTML/JS.

**Found by:** sol: MRV·low; terra: MRV·medium

#### A34 — Dead feed-modified cache key means PollFeed always re-downloads and reprocesses the full feed

**Location:** `app/jobs/scheduled/pollfeed.rb:20–22`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72  ·  4 findings, 3 cells · ⚠️ **no harness cell found this**

**Why this is real.** The job computes a cache key (reported around lines 20-22) like `feedkey = "feed-modified:" + Digest::SHA1.hexdigest(...)` but never reads from or writes to it. Because `feedkey` is unused, there is no conditional GET (no If-Modified-Since/ETag) and no early-exit based on cached "last modified" state, so each hourly run necessarily downloads and parses the entire feed again. The PR does not include this file in its diff, so this verification relies on the reported line references and the fact that the computed variable is dead code in the current post-PR tree.

**How to replicate.** 1) Configure the app with a feed URL that rarely changes and enable/run the scheduled PollFeed hourly job. 2) Run the job twice (manually trigger twice or wait two hourly intervals) without changing the upstream feed content. 3) Observe via logs/HTTP proxy that both runs fetch the full feed (200 with full body) rather than using a conditional request (304 Not Modified / If-Modified-Since / ETag) and that the job proceeds to parse/import again. Expected: the second run should skip download/parse when unchanged by using the computed cache key to store/check last-modified/etag; actual: it always re-downloads and re-processes because the cache key is never used.

**Found by:** **no harness cell** — vanilla only: fable, opus, sol

#### A35 — (untitled)

**Location:** `?`  ·  **Severity:** ?  ·  **Judge confidence:** 0.00  ·  4 findings, 4 cells

**Found by:** opus: CE·low, MRV·high

#### A36 — (untitled)

**Location:** `?`  ·  **Severity:** ?  ·  **Judge confidence:** 0.00  ·  3 findings, 2 cells

**Found by:** glm-flash: MRV·low

#### A37 — Disqus importer now live-fetches thread URLs via TopicEmbed, skipping unreachable/non-http threads and losing original created_at/permalink body

**Location:** `lib/tasks/disqus.thor:148–154`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  3 findings, 3 cells

**Why this is real.** At the reported location the importer was changed to create the first post via a remote-embed path, e.g. `post = topicembed.importremote(user, t[:link], title: t[:title])`, instead of directly creating a post with the Disqus thread metadata (`raw: "[[permalink](#{t[:link]})]"` and `created_at: Date.parse(t[:createdat])`). This is a functional contract change: `TopicEmbed.import_remote` performs a live HTTP fetch of `t[:link]` (and returns nil for non-http(s) or failed fetches), which means some Disqus threads are silently skipped (and thus their comments never import) and the original thread `created_at` is no longer applied (topics get import-time timestamps). The PR diff for `topicembed.importremote` is not in this PR, so verification relies on reading the post-PR `lib/tasks/disqus.thor` around line 148 and confirming it delegates to `TopicEmbed.import_remote` rather than `PostCreator` with explicit `raw`/`created_at`.

**How to replicate.** 1) Prepare a Disqus export containing at least two threads: (a) one with `link` set to a non-http(s) URL (e.g. `mailto:test@example.com` or a relative/invalid URL) or an http(s) URL that is unreachable from the importer host; (b) one normal reachable http(s) URL. 2) Run the Disqus import task (the Thor task implemented in `lib/tasks/disqus.thor`). 3) Observe results: expected behavior (pre-change) is that both threads are created with a first post containing a permalink markdown body and the topic/post timestamps matching the Disqus `createdAt`. Actual behavior (post-change) is that the unreachable/non-http thread is skipped entirely (no topic, no comments) because `importremote` returns nil, and imported topics use the current import time rather than honoring `t[:createdat]` and no longer include the explicit permalink body.

**Found by:** fable: CE·low; opus: CE·medium, MRV·medium

#### A38 — Disqus importer is no longer idempotent: reruns duplicate all replies when TopicEmbed.import_remote returns an existing post

**Location:** `lib/tasks/disqus.thor:148–163`  ·  **Severity:** high  ·  **Judge confidence:** 0.82  ·  3 findings, 3 cells

**Why this is real.** Post-PR, the importer replaces `PostCreator.new(...).create` with `post = TopicEmbed.import_remote(user, t[:link], title: t[:title])` and then unconditionally appends replies via `t[:posts].each do |p| ...` whenever `post.present?`. `TopicEmbed.import_remote` is designed to return an already-existing embedded topic/post when the same remote URL was imported before, so re-running the task will re-enter the same topic and re-create every Disqus comment again, producing duplicates (no check for already-imported replies, no upsert key, no idempotency guard).

**How to replicate.** 1) Run the Thor task to import a Disqus export containing at least one thread with multiple comments (e.g., `bundle exec thor disqus:import path/to/disqus.xml --post-as someuser`). 2) Run the exact same import command a second time. Expected: the importer should detect the thread/topic and comments are already imported and skip them. Actual: `TopicEmbed.import_remote` returns the existing topic post for the same `t[:link]`, and the following `t[:posts].each` loop re-creates all replies, resulting in a second copy of each Disqus comment under the existing topic. (Variant: include one thread whose `t[:link]` is invalid/unreachable so the first run aborts mid-way; rerunning then duplicates replies for the threads that were already imported before the abort.)

**Found by:** opus: CE·high, MRV·high; sol: MRV·high

#### A39 — Poll feed processing calls `String#scrub` via `stringscrub`, crashing on Ruby 2.0 (requires Ruby >= 2.1)

**Location:** `lib/pollfeed.rb:35–35`  ·  **Severity:** high  ·  **Judge confidence:** 0.70  ·  3 findings, 2 cells

**Why this is real.** The reports consistently point to `pollfeed.rb:35` invoking `stringscrub`/`scrub` during feed item processing. `String#scrub` is a Ruby 2.1+ API, and the `stringscrub` gem itself requires Ruby >= 2.1, so under the Ruby 2.0 runtime used by Discourse at the time this code would raise `NoMethodError` (or fail to load the gem) even for otherwise valid strings. The PR diff is not available here, so this verification relies on the line reference and the documented Ruby version incompatibility mechanism.

**How to replicate.** 1) Run the app/plugin under Ruby 2.0 with the Gemfile/Gemfile.lock corresponding to this code. 2) Trigger the poll feed job/endpoint that processes feed items (the code path that executes `lib/pollfeed.rb`, line 35). 3) Observe that when a feed item is handled, execution hits the `scrub` call and raises an exception (`NoMethodError: undefined method 'scrub' for String` or a gem load/version error), causing the poll/feed processing to crash instead of returning/recording results.

**Found by:** glm-flash: CE·high; glm-vis: CE·medium

#### A40 — Disqus importer drops original topic/OP created_at by switching to TopicEmbed.import_remote without forwarding created_at

**Location:** `script/import_scripts/disqus.rb:118–132`  ·  **Severity:** critical  ·  **Judge confidence:** 0.66  ·  3 findings, 2 cells

**Why this is real.** Per the reports, the PR rewrites the Disqus thread import from `PostCreator.new(..., created_at: Date.parse(t[:createdAt]), category: category_id)` to `TopicEmbed.import_remote(user, t[:link], title: t[:title])`. `TopicEmbed.import_remote` (and the underlying TopicEmbed import path) does not accept/forward `created_at`, so the created time of the imported OP/topic will default to the import run time. This creates a real data-integrity bug in migrations: topics appear “new” and can even end up with an OP dated after its replies (which still use the original Disqus timestamps).

**How to replicate.** 1) Prepare a Disqus export where a thread has `createdAt` far in the past and at least one reply with its own old `createdAt`.
2) Run the Disqus import task in this repo (the code path calling `TopicEmbed.import_remote(user, t[:link], title: t[:title])`).
3) In the resulting Discourse instance, inspect the imported topic: the topic/first post timestamp will match the import run time ("now"), while imported replies retain the original Disqus timestamps.
Expected: the topic/OP created_at matches the Disqus thread createdAt and sorts correctly chronologically; Actual: topic/OP is timestamped at import time and can sort as brand-new, with replies appearing older than the OP.

**Found by:** glm-vis: MRV·medium

#### A41 — Embed source hash includes localized footer, causing false-positive content changes on locale/footer updates

**Location:** `app/models/topicembed.rb:12–16`  ·  **Severity:** medium  ·  **Judge confidence:** 0.64  ·  2 findings, 2 cells

**Why this is real.** The reported lines indicate the model appends a localized footer (via I18n/site text) to the imported embed content and then computes a SHA1 over that final string (e.g., content is modified with a translated footer and then `Digest::SHA1.hexdigest(...)` is computed). Because the footer text is presentation/locale-dependent rather than part of the upstream source, any change to locale or footer translation changes the hash even when the remote page content is identical, so the code will incorrectly detect a change and create needless post revisions. The PR diff does not include this file, so verification relies on inspecting the post-PR tree at the referenced lines.

**How to replicate.** 1) Configure/enable embedding/import so a remote URL is imported into a Discourse topic using TopicEmbed. 2) Import a URL once, ensuring the topic is created and its stored embed hash reflects the initial import. 3) Change the site locale (or modify the translation string used for the embed footer / the footer text itself) without changing the remote URL content. 4) Re-run the embed import/sync for the same URL. Expected: no update/revision since upstream content is unchanged. Actual: the computed SHA1 differs solely due to the localized footer, so the system thinks the content changed and revises/updates the post(s).

**Found by:** sol: CE·high

#### A42 — Disqus import passes untrusted thread <link> to importremote/open without URI validation (SSRF/LFI/RCE)

**Location:** `lib/tasks/disqus.thor:148–148`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74  ·  2 findings, 2 cells

**Why this is real.** At lib/tasks/disqus.thor:148 the task calls `topicembed.importremote(user, t[:link], ...)`, where `t[:link]` comes directly from the imported Disqus XML `<link>` field. The reports indicate `importremote` ultimately uses `open(...)`/`Kernel.open` to fetch the URL and that any `^https?` validation happens only after the fetch, meaning a crafted export can drive an arbitrary fetch (SSRF/LFI) and potentially command execution on some Ruby versions/configs if `open` is invoked on a string starting with `|`.

**How to replicate.** 1) Inspect `lib/tasks/disqus.thor` around line 148 and confirm the Disqus thread link `t[:link]` is passed directly into `topicembed.importremote(...)` without any `URI.parse` + scheme/host allowlist validation. 2) Inspect `TopicEmbed.import_remote` (or similarly named method) and confirm it calls `open(url)`/`Kernel.open(url)` (or `URI.open`) before any `http/https` scheme checks. 3) Create a Disqus export XML where a thread's `<link>` is `file:///etc/passwd` (LFI) or an internal URL like `http://127.0.0.1:3000/admin` (SSRF), then run the Disqus import Thor task as an admin; observe the importer reads/fetches that resource and embeds its content into the created topic (actual), whereas expected behavior is to reject non-http(s) schemes and disallow internal/localhost targets before any fetch. (If `Kernel.open` is used unsafely, also test `<link>|touch /tmp/pwned` to see whether a shell command is executed; expected is that it is rejected as an invalid URL.)

**Found by:** opus: MRV·high; sonnet: MRV·high

#### A43 — Migration uses `force: true`, risking silent table drop and data loss on re-run

**Location:** `migrations/createtoptopics.rb:3–3`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74  ·  3 findings, 3 cells

**Why this is real.** Automated reports consistently flag that `migrations/createtoptopics.rb:3` uses `force: true` on `create_table` (i.e., `create_table ..., force: true do |t|`). In Rails migrations, `force: true` drops an existing table before recreating it, which can silently destroy production data if the migration is re-run (e.g., via `db:migrate:redo`/`rollback`/rebuild workflows). The PR diff for this file is not shown here, so this verification relies on the reported line-level evidence rather than an hunk header.

**How to replicate.** 1) Create a database and run migrations so the `top_topics` table exists and contains rows. 2) Re-run the migration (e.g., `rails db:migrate:redo VERSION=<the createtoptopics migration version>` or rollback then migrate up again). 3) Observe that the table is dropped/recreated due to `force: true`, causing existing rows to be lost; expected behavior is that rerunning should not silently drop data (or should require an explicit `drop_table`/safety mechanism).

**Found by:** glm-flash: CE·low; glm-vis: MRV·high

#### A44 — `skip_validations` allows saving posts/topics with invalid or unsafe data (validations fully bypassed)

**Location:** `lib/post_revisor.rb:85–90`  ·  **Severity:** high  ·  **Judge confidence:** 0.66  ·  2 findings, 2 cells

**Why this is real.** Around lib/post_revisor.rb:85 the PR introduces a `skip_validations`/`skipvalidations` option that leads to saving a post with ActiveRecord validations disabled (i.e., a `save`/`save!` call with `validate: false` when the flag is set). That means required-field checks (e.g., title presence) and safety checks implemented as validations/callback validations can be bypassed for attacker-influenced imported content. This is not a style issue: it changes persistence semantics so invalid records can be committed (e.g., nil/blank titles when both `opts[:title]` and the imported document title are nil).

**How to replicate.** 1) In Rails console (or the code path used by `importremote`), construct a revise/create call that passes the new option: `skip_validations: true` (or `skipvalidations: true`, per the importer) while providing invalid data (e.g., missing/blank title and/or content that normally fails spam/host/content validations).
2) Ensure both the explicit title option and the imported document's title are nil/blank.
3) Run the import/revise.
Expected: the save is rejected by validations (e.g., title can't be blank, spam/host rules trigger) and the record is not persisted.
Actual: the record is persisted because the save path disables validations when `skip_validations` is true, allowing topics/posts with nil/blank titles or otherwise invalid/unsafe content.

**Found by:** opus: CE·high; glm-flash: CE·low

#### A45 — Stored XSS: Post.cook returns raw HTML unchanged when cook_method=raw_html, bypassing sanitization/filtering

**Location:** `app/models/post.rb:128–136`  ·  **Severity:** critical  ·  **Judge confidence:** 0.88  ·  3 findings, 3 cells

**Why this is real.** In Post#cook, the new logic explicitly skips the normal cooking/sanitization pipeline: `return raw if cook_method == Post.cook_methods[:raw_html]`. This returns user-controlled HTML verbatim and also bypasses `Plugin::Filter.apply(:after_post_cook, ...)`, which is where downstream filters/sanitizers would normally run. Any code path that sets `cook_method` to `:raw_html` and persists `raw`/`cooked` can therefore store and later render arbitrary HTML/JS (stored XSS).

**How to replicate.** 1) Ensure there is a code path that creates/updates a Post with `cook_method` set to `Post.cook_methods[:raw_html]` (the PR comment mentions RSS/imported posts). 2) Supply `raw` content containing executable HTML/JS, e.g. `<img src=x onerror=alert(document.domain)>` (or `<script>...</script>`). 3) Cause the post to be cooked/saved and then rendered (e.g., view the topic page or any embed template that outputs cooked HTML). Expected: HTML should be sanitized/escaped and JS should not execute. Actual: because `cook` returns `raw` unchanged for `:raw_html`, the payload is stored and executed in the viewer’s browser (stored XSS).

**Found by:** glm-vis: CE·medium, MRV·medium

#### A46 — (untitled)

**Location:** `?`  ·  **Severity:** ?  ·  **Judge confidence:** 0.00  ·  2 findings, 2 cells

**Found by:** glm-vis: CE·high, MRV·medium

#### A47 — TopicEmbed import uses non-atomic exists?/create! allowing concurrent duplicates and unhandled RecordNotUnique

**Location:** `app/models/topic_embed.rb:21–34`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  2 findings, 2 cells

**Why this is real.** The import logic is a classic check-then-create race: it first checks something like `TopicEmbed.exists?(embed_url: url)` and then later does `TopicEmbed.create!(embed_url: url, topic_id: topic.id)`. Under concurrency, two workers can both pass the `exists?` check and the loser hits the DB unique constraint, raising `ActiveRecord::RecordNotUnique`. Because the exception is not rescued around `create!`, the job fails after side effects (topic/post creation, enqueued work), producing inconsistent state and the reported stuck/infinite-loading behavior. (The PR diff does not include this file; this verification relies on the line reference and behavior described in the reports.)

**How to replicate.** 1) Ensure the `topic_embeds` table has a unique index on `embed_url` (or equivalent).
2) Trigger two concurrent imports/embeds for the exact same URL (e.g., enqueue the same TopicEmbed import Sidekiq job twice, or hit the endpoint that creates embedded topics twice in parallel).
3) Observe: both workers pass the `exists?` guard, one succeeds, the other raises `ActiveRecord::RecordNotUnique` from `TopicEmbed.create!`.
Expected: the second import should be idempotent (find-or-create) and not fail; Actual: one job fails with an uncaught exception, potentially leaving the UI waiting (infinite loading) or leaving partially-created records/queued jobs.

**Found by:** glm-flash: CE·low

#### A48 — poll_feed job processes unbounded RSS items, creating/enqueuing work for every entry in a single run

**Location:** `app/jobs/regular/poll_feed.rb:18–56`  ·  **Severity:** high  ·  **Judge confidence:** 0.64  ·  1 findings, 1 cells

**Why this is real.** The poller fetches the remote feed and then iterates every entry without any limit, e.g. `rss = Feedjira.parse(URI.open(url).read)` followed by `rss.items.each do |item|` (or `rss.entries.each`) and then invokes `PostCreator`/enqueues per-item processing inside that loop. Because there is no cap (no `take(n)`, no `break` after N items, no pagination/backoff), a feed with thousands of items will be fully processed in one job execution, leading to multi-hour job runtime and flooding Sidekiq with thousands of enqueued post/topic jobs. The PR diff referenced in the prompt does not include this file/hunk, so this verification relies on the reported code path description; a human can confirm by locating the unbounded `each` over `rss.items` in `poll_feed.rb` and observing there is no bounding logic anywhere on that path.

**How to replicate.** 1) Point the plugin/site setting that defines the polled RSS feed URL to a test RSS feed containing thousands of `<item>` entries (or a real feed with a very large history). 2) Run the poll job manually (e.g., from Rails console `Jobs.enqueue(:poll_feed, ...)` or by triggering the scheduled job) and watch the Sidekiq dashboard/logs. Expected: poller should process a bounded number of new items per run (and/or defer the rest). Actual: the job iterates the entire `rss.items` collection, creates topics/posts for each, and enqueues per-post processing jobs for all entries in one poll, causing excessive runtime and a surge in queued jobs/topics.

**Found by:** glm-vis: MRV·high

#### A49 — ERB syntax error: invalid `end if` terminator breaks embed best template rendering

**Location:** `app/views/embed/best.html.erb:6–6`  ·  **Severity:** high  ·  **Judge confidence:** 0.86  ·  2 findings, 2 cells

**Why this is real.** The template closes an ERB `if` block with `<%- end if %>` (line 6). In ERB/Ruby, `end if` is not valid syntax for closing a block; the correct terminator is just `end`. When this template is rendered, Rails will attempt to compile it and raise an `ActionView::SyntaxError`, causing the embed page to fail at runtime.

**How to replicate.** 1) Run the app with this PR applied. 2) Hit the route/action that renders `embed/best` (e.g., request the embed "best" view in a browser). Expected: the embed page renders with a header and posts list. Actual: the request errors during template compilation with an ERB/Ruby syntax error pointing at the line `<%- end if %>`.

**Found by:** glm-vis: MRV·high

#### A50 — Migrations add posts.cookmethod and topic_embeds table but schema dump is not regenerated (schema drift)

**Location:** `db/schema.rb:1–1`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  1 findings, 1 cells

**Why this is real.** The reports indicate this PR introduces a migration adding a `posts.cookmethod` column and creating a `topic_embeds` table, but the diff contains no corresponding update to the tracked schema dump (`db/schema.rb` or `db/structure.sql`). That is a functional defect because environments that build the database from the committed schema dump (e.g., `db:schema:load`, `db:reset`, CI test DB setup) will not have the new column/table even though application code (e.g., post cooking logic) expects `cookmethod` to exist, leading to runtime errors or incorrect behavior. This is an omission bug (missing file update), so there are no “offending lines” in the diff to quote beyond the absence of the schema changes.

**How to replicate.** 1) Checkout the PR branch/commit. 2) Create a fresh database using the schema dump instead of migrations (e.g., `RAILS_ENV=test bundle exec rake db:drop db:create db:schema:load` or `bundle exec rake db:reset`). 3) Boot the app or run a code path that cooks a post (or run a spec that triggers post cooking). Expected: cooking succeeds and TopicEmbed-related queries work. Actual: errors such as missing column `posts.cookmethod` and/or missing table `topic_embeds` (e.g., `ActiveRecord::StatementInvalid: PG::UndefinedColumn` / `PG::UndefinedTable`) because the schema dump lacked the PR’s migration changes.

**Found by:** glm-vis: MRV·medium

#### A51 — EmbedController enqueues RetrieveTopic job but spec expects synchronous TopicRetriever call

**Location:** `app/controllers/embedcontroller.rb:16–16`  ·  **Severity:** medium  ·  **Judge confidence:** 0.78  ·  1 findings, 1 cells

**Why this is real.** The controller code (per the report) enqueues an async job at `app/controllers/embedcontroller.rb:16` (e.g., a `Jobs::RetrieveTopic` enqueue), meaning topic retrieval happens later/out-of-band. However, the controller spec (reported at `spec/controllers/embedcontrollerspec.rb:43`) asserts `TopicRetriever.new` is invoked synchronously during the request, which cannot be true if the controller only enqueues a job. This is a real contract mismatch between shipped behavior and the test, so the test does not (and cannot) validate the actual behavior the controller implements.

**How to replicate.** 1) Open `app/controllers/embedcontroller.rb` around line 16 and confirm the action enqueues `Jobs::RetrieveTopic` (or equivalent) instead of directly calling `TopicRetriever.new`/`TopicRetriever#retrieve`. 2) Open `spec/controllers/embedcontrollerspec.rb` around line 43 and confirm it expects `TopicRetriever.new` to be called during the controller action. 3) Run the controller spec: expected (per test) is an immediate `TopicRetriever.new` call; actual (per controller) is only a job enqueue, so either the spec fails or it passes only because of incorrect stubbing, meaning it doesn't assert the real behavior.

**Found by:** opus: MRV·low

#### A52 — RetrieveTopic job unnecessarily eager-loads mail stack via stray require_dependency

**Location:** `app/jobs/regular/retrievetopic.rb:1–1`  ·  **Severity:** low  ·  **Judge confidence:** 0.60  ·  2 findings, 2 cells · ⚠️ **no harness cell found this**

**Why this is real.** The report indicates the file begins with an unrelated `require_dependency 'email/sender'` at line 1. This is a genuine defect because it forces the job worker to load the email delivery subsystem even though RetrieveTopic should not depend on sending email, increasing boot time/memory and potentially triggering mail-specific initialization/side effects. The PR does not modify this file, so verification must be done by directly opening the post-PR code and confirming that this require is present and unused.

**How to replicate.** 1) Open `app/jobs/regular/retrievetopic.rb` on the PR branch and confirm it contains `require_dependency 'email/sender'` at the top.
2) Search within the same file for any references to `Email::Sender` (or other constants from `email/sender`)—expected: none.
3) Run the job worker (or Rails runner to execute the job) with minimal config and enable load/require tracing (e.g., instrument `ActiveSupport::Dependencies` or use `RUBYOPT='--enable-frozen-string-literal'` plus logging) to observe that `email/sender` (and its transitive mail stack) gets loaded when `RetrieveTopic` is loaded—expected: it should not be loaded for this job; actual: it is loaded due to the top-level require.

**Found by:** **no harness cell** — vanilla only: fable, opus

#### A53 — `require_dependency 'nokogiri'` can raise `LoadError` in Rails development due to `:load` dependency mechanism

**Location:** `app/models/topicembed.rb:1–1`  ·  **Severity:** high  ·  **Judge confidence:** 0.76  ·  1 findings, 1 cells

**Why this is real.** The file begins with `require_dependency 'nokogiri'` (reported at `app/models/topicembed.rb:1`). In Rails development (`cache_classes=false`), `ActiveSupport::Dependencies` may use `mechanism = :load`, causing `require_dependency` to ultimately call `Kernel#load` rather than `require`; `load` does not resolve extension-less feature names the way `require` does (and will not properly load native extensions like Nokogiri), leading to `LoadError` and preventing the `TopicEmbed` model from being loaded at all. This is a functional runtime failure, not a style issue; the PR diff does not include this file, so verification is based on the reported code location/behavior.

**How to replicate.** 1) Run the app in Rails development mode with `config.cache_classes = false` (default in development). 2) Ensure Nokogiri is present in the bundle (Gemfile includes `nokogiri`). 3) Boot the app (or open a Rails console) and trigger autoload of `TopicEmbed` (e.g., reference `TopicEmbed` or hit any request path that loads the model). Expected: the model loads normally. Actual: Rails raises `LoadError` for `nokogiri` while loading `app/models/topicembed.rb`, breaking boot/autoload in development.

**Found by:** sonnet: MRV·high

#### A54 — TopicEmbed stores redundant topic_id that can go stale when an embedded post is moved to another topic

**Location:** `app/models/topicembed.rb:25–35`  ·  **Severity:** medium  ·  **Judge confidence:** 0.55  ·  1 findings, 1 cells

**Why this is real.** The model persists both a `topic_id` and a `post_id` for the same embed record even though `topic_id` is derivable from `post.topic_id`. Because controller-side lookups/updates are reported to use only `topic_id` (not `post_id`), if Discourse moves the post to a different topic, `topicembed.topic_id` can remain pointing to the original topic while the `post_id` now belongs to a different topic. This creates a real data-integrity bug: the embed record can reference the wrong topic and subsequent operations can target inconsistent resources. (This file is not part of the PR diff, so this verification relies on the reported code behavior and the referenced line location.)

**How to replicate.** 1) Create an embedded post that results in a `TopicEmbed` row with both `post_id` and `topic_id` populated. 2) Use Discourse’s post-moving feature to move that post to a different topic (so `posts.topic_id` changes). 3) Trigger whatever controller action updates/reads the embed (the report indicates it identifies the embed by `topic_id` only). Expected: the embed follows the moved post/new topic consistently. Actual: the embed lookup/update still uses the stale `topic_id`, so it continues to associate with the old topic while the referenced post now belongs to the new topic, causing incorrect embed behavior.

**Found by:** opus: MRV·high

#### A55 — Embedded iframe height is posted only on load, causing clipped content after resize/wrap

**Location:** `app/views/layouts/embed.html.erb:8–16`  ·  **Severity:** high  ·  **Judge confidence:** 1.00  ·  1 findings, 1 cells

**Why this is real.** The embed layout sets a one-shot handler like `window.onload = function() { ... parent.postMessage(... height ...) ... }`, which only reports the iframe height a single time at load. When the host page is resized (or fonts/images load later) the embedded discussion height can increase due to text reflow, but no further height messages are sent; combined with the typical `scrolling="no"` iframe usage, the additional content becomes inaccessible. The file is not part of this PR’s diff, so this verification relies on the reported code location/behavior.

**How to replicate.** 1) Load a Discourse embed page (using this layout) inside a host page `<iframe ... scrolling="no">` that listens for the posted height and sets the iframe’s CSS height. 2) Ensure the embed contains enough text/comments to wrap differently. 3) After the iframe finishes loading, narrow the host page/iframe width (e.g., resize the browser window or change a responsive container width). Expected: the iframe height updates to fit the newly wrapped/taller content. Actual: the iframe height stays fixed (only set on initial load) and the bottom of the discussion is clipped with no scrolling available.

**Found by:** astra: MRV·high

#### A56 — New /embed/best route is unnamed and unconstrained, so it has no URL helper and accepts unintended formats

**Location:** `config/routes.rb:245–245`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  1 findings, 1 cells

**Why this is real.** The PR adds `get 'embed/best' => 'embed#best'` with no `as:` option and no format constraint/defaults. In Rails, omitting `as:` means no named route helper (e.g., `embed_best_path`) will be generated, which can cause runtime errors anywhere the app tries to build this URL via helpers. Omitting a format constraint/default (e.g., JSON-only) also means the same action will be routed for HTML requests (`/embed/best`) as well as `/embed/best.json`, which is incorrect if `embed#best` is intended to be JSON-only or to have a separate HTML route.

**How to replicate.** 1) After applying the PR, run `bin/rails routes | grep -n "embed/best"` and observe the route exists but has no named prefix (no helper name shown). 2) In a Rails console (or any view/controller), attempt to call `embed_best_path` (or `embed_best_url`); expected: helper exists for the new endpoint; actual: `NoMethodError` because the route is unnamed. 3) Send requests to both `/embed/best` and `/embed/best.json`; expected (for a JSON-only embed endpoint): `/embed/best` should not match or should be rejected/404, while `/embed/best.json` should be the only accepted format; actual: both route to `embed#best` because the route has no format constraint.

**Found by:** opus: CE·medium

#### A57 — Embed URL is constructed by naive string concatenation, breaking when discourseUrl lacks a trailing slash

**Location:** `N/A (not referenced in the deduplicated reports; not modified in PR #4 diff)`  ·  **Severity:** medium  ·  **Judge confidence:** 0.58  ·  1 findings, 1 cells · ⚠️ **no harness cell found this**

**Why this is real.** The clustered reports indicate the code builds the request URL by concatenating a configured `discourseUrl` with a relative path like `"embed/best?..."`. If `discourseUrl` does not end with `/`, the resulting string becomes `https://forum.example.comembed/best?...`, which is an invalid endpoint and fails silently unless the host page (or configuration) happens to include a trailing slash. This is a functional correctness bug (bad URL construction), not a style issue; however, the exact offending lines cannot be quoted because the reports include no file/line references and the PR diff does not touch the relevant code.

**How to replicate.** 1) Find where the embed URL is formed (search the repo for `embed/best` or for concatenation with `discourseUrl`). 2) Configure/set `discourseUrl` to a value without a trailing slash (e.g., `https://discourse.example.com`). 3) Trigger whatever code path loads the embed/best content. Expected: request goes to `https://discourse.example.com/embed/best?...`. Actual: request URL becomes `https://discourse.example.comembed/best?...` (or otherwise malformed), causing 404/network failure and a broken embed unless `discourseUrl` ends with `/`.

**Found by:** **no harness cell** — vanilla only: opus

#### A58 — Missing presence check before calling `downcase` on `SiteSetting.embed_by_username` can raise NoMethodError

**Location:** `lib/discourse_graphite/topic_retriever.rb:17–17`  ·  **Severity:** medium  ·  **Judge confidence:** 0.58  ·  1 findings, 1 cells

**Why this is real.** The same lookup logic is duplicated in multiple places, but with different guards. In `pollfeed.rb` the report indicates it is guarded (e.g., checking `SiteSetting.embed_by_username.present?` before doing `SiteSetting.embed_by_username.downcase`), while `topic_retriever.rb` reportedly calls `SiteSetting.embed_by_username.downcase` directly inside `User.where(usernamelower: SiteSetting.embed_by_username.downcase).first`. If the setting is blank/nil, the unguarded `.downcase` will crash at runtime with `NoMethodError`, making this a functional bug (not just style/duplication).

**How to replicate.** 1) In the running app/plugin environment, ensure `SiteSetting.embed_by_username` is unset or set to an empty value. 2) Trigger the code path that uses `TopicRetriever` (the code that fetches/embeds content and performs `User.where(usernamelower: SiteSetting.embed_by_username.downcase).first`). 3) Expected: it should safely behave as “no embed user configured” and proceed without error. Actual: it raises `NoMethodError: undefined method 'downcase' for nil:NilClass` (or for an empty non-string value), because `.downcase` is called without a presence check.

**Found by:** glm-vis: CE·medium

#### A59 — embedurl param not type-checked allows non-String, causing unrescued TypeError in URI parsing and Sidekiq retry churn

**Location:** `app/controllers/embed_controller.rb:9–16`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  1 findings, 1 cells

**Why this is real.** The controller reads the URL via something equivalent to `@embedurl = params.require(:embedurl)` (per the report’s embedcontroller.rb:9-16). In Rails, `require` enforces presence but not type, so a request like `?embedurl[]=x` yields an Array/Hash instead of a String; later code passes this value into URI parsing in TopicRetriever, where `URI(@embedurl)` (topicretriever.rb:15-18) raises `TypeError` for non-String inputs. The rescue only catches `URI::InvalidURIError`, so this TypeError escapes and crashes the enqueued job, leading to repeated Sidekiq retries/job churn. (embed_controller.rb is not in this PR’s diff; this verification relies on the reported line ranges and the described control/data flow.)

**How to replicate.** 1) Find the controller action in app/controllers/embed_controller.rb around lines 9-16 that does `params.require(:embedurl)` and enqueues a background job (directly or indirectly) using that value. 2) Find TopicRetriever (topicretriever.rb around lines 15-18) calling `URI(@embedurl)` inside a `rescue URI::InvalidURIError`. 3) Trigger the endpoint anonymously with a non-scalar embedurl, e.g. `GET /<embed-endpoint>?embedurl[]=http://example.com` (or send JSON with `embedurl: []`/`{}`), and observe: expected behavior is a 4xx validation error without enqueuing; actual behavior is the job is enqueued, then fails with `TypeError` (not caught by the rescue) and is retried by Sidekiq repeatedly (visible in Sidekiq/rails logs).

**Found by:** glm-vis: CE·medium

#### A60 — Unescaped request.referer interpolated into JS string breaks postMessage targetOrigin (and can enable injection)

**Location:** `app/views/layouts/embed.html.erb:11–11`  ·  **Severity:** high  ·  **Judge confidence:** 0.88  ·  2 findings, 2 cells

**Why this is real.** The template embeds server-controlled data directly into a JavaScript string literal: `parent.postMessage(..., '<%= request.referer %>');`. ERB’s default escaping is for HTML, not JavaScript, so characters like a trailing backslash (or a single quote) in the Referer header can escape/break the closing quote and make the inline script syntactically invalid. When that happens, the `postMessage` call never executes, so the expected resize message is not sent.

**How to replicate.** 1) Serve the embed page that uses this layout. 2) Request it while forcing a Referer header that ends with a backslash or contains a single quote, e.g. via curl: `curl -H "Referer: https://evil.test/\\" http://localhost:3000/.../embed` (or `Referer: https://evil.test/'`). 3) Open the response in a browser/inspect the rendered HTML: the generated JS contains an unterminated/broken string for the second `postMessage` argument. Expected: page posts `{type:'discourse-resize', ...}` to the parent; Actual: browser console shows a JS syntax error and no resize postMessage is sent.

**Found by:** glm-flash: CE·high; glm-vis: CE·low

#### A61 — Invalid or wrong-host embed URLs are treated as successful retrieval, causing infinite loading loop

**Location:** `lib/topicretriever.rb:9–9`  ·  **Severity:** high  ·  **Judge confidence:** 1.00  ·  1 findings, 1 cells

**Why this is real.** At lib/topicretriever.rb:9 the control flow is reported as `performretrieve unless (invalidhost? || retrievedrecently?)`. This means that when `invalidhost?` is true (malformed/wrong-host URL), the method skips `performretrieve` and can still return as if background work completed, rather than surfacing a 4xx/invalid-input result. The result is a real behavioral defect: the controller/view that polls for completion never receives an error state, so it keeps reloading indefinitely. (This file is not part of the PR diff, so verification relies on inspecting the referenced line in the post-PR tree.)

**How to replicate.** 1) In the UI or API endpoint that triggers topic retrieval via an embed URL, submit an embed URL with an unsupported host or malformed URL (so `invalidhost?` would be true). 2) Observe the subsequent "loading"/polling behavior (page reloads or repeated status checks). Expected: request should fail with a 4xx (invalid input / unsupported host) and stop polling. Actual: the system appears to accept the job but never progresses (keeps reloading/polling forever) because no retrieval is performed and no error is returned.

**Found by:** sol: MRV·high

#### A62 — OpenURI follows redirects, bypassing host allowlist when fetching embedded topic HTML

**Location:** `lib/topicembed.rb:48–52`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  1 findings, 1 cells

**Why this is real.** The code reportedly fetches remote HTML with `open(url)` (e.g., `html = open(url).read`) at topicembed.rb:48. Ruby's OpenURI follows HTTP 3xx redirects by default, so even if TopicRetriever/TopicEmbed performs a host check on the *original* `url`, the actual content fetched can come from a different host after a redirect. This makes the host/embeddable-domain constraint ineffective and allows an embeddable site with an open redirect to supply attacker-controlled HTML to the importer (amplifying downstream XSS/URL-injection issues).

**How to replicate.** 1) Find the code path where an embed request provides a URL that is validated against an allowed host/domain before calling `open(url)` in lib/topicembed.rb (~line 48). 2) Configure an allowed/embeddable host A that returns `302 Location: https://attacker.example/payload.html` for a chosen path. 3) Trigger the embed/import for `https://A.example/redirect` (whatever controller/job calls TopicEmbed/TopicRetriever). Expected: fetch is constrained to A.example only; Actual: OpenURI follows the redirect and fetches attacker.example content, which is then parsed/imported as if it came from A.example.

**Found by:** glm-vis: CE·medium

#### A63 — Feed item URL fallback uses entry.id (often not a URL), causing items to be silently skipped

**Location:** `pollfeed.rb:1–1`  ·  **Severity:** medium  ·  **Judge confidence:** 0.50  ·  1 findings, 1 cells

**Why this is real.** The deduplicated report indicates `pollfeed.rb` "falls back to i.id" when a feed entry has no URL. In many feed formats, `id` is a GUID/opaque identifier (e.g., `tag:example.com,2024:post-123`), not an HTTP(S) URL; if downstream code assumes a real URL (for normalization, fetching, or deduping), this fallback makes valid entries appear invalid and they get skipped. The report also notes there is no logging on the skip path, making the failure silent; this is a behavioral defect (missed content) rather than a style nit. (The PR diff does not include this file, so this verification relies on the report and must be confirmed by locating the `url = i.url || i.id`-style line in `pollfeed.rb` in the post-PR tree.)

**How to replicate.** 1) In `pollfeed.rb`, find the code path that derives an entry URL (commonly something like `url = entry.url || entry.id`). 2) Provide a feed where an item has no `<link>`/URL but does have an `<id>` that is not an http(s) URL (e.g., an Atom `<id>tag:example.com,2024:abc</id>`). 3) Run the poller against that feed. Expected: the item is processed (or at least a warning is logged that it cannot be processed due to missing URL). Actual: the item is skipped/dropped because the derived "url" is not a valid URL, and there is no log message explaining the drop.

**Found by:** glm-flash: CE·low

#### A64 — Embed endpoint trusts spoofable Referer/embedurl and uses Referer as postMessage targetOrigin

**Location:** `app/controllers/embedcontroller.rb:28–28`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  1 findings, 1 cells

**Why this is real.** The embed implementation relies on `request.referer` (a client-controlled header) and the client-supplied `embedurl` to decide what origin is allowed. As reported (this file is not part of the PR diff, so verification is by reading the current tree), the referer check at/around line 28 is effectively a weak host equality check and can be bypassed via crafted Referer/embedurl values (e.g., case/format variations), letting an attacker-origin pass validation. The corresponding view then uses the Referer-derived value as the `postMessage` targetOrigin, so a spoofed Referer can cause messages intended for a legitimate parent to be sent to an attacker-controlled origin.

**How to replicate.** 1) Inspect `app/controllers/embedcontroller.rb` around line 28 and confirm it compares/derives the allowed origin from `request.referer` and/or `params[:embedurl]` without strict, normalized origin parsing and verification.
2) Inspect `app/views/layouts/embed.html.erb` around line 9 and confirm it does `window.parent.postMessage(..., <%= request.referer %>)` (or equivalent), using the Referer as targetOrigin.
3) Run the app locally and request the embed endpoint (e.g., `/embed`) while setting a forged `Referer: https://attacker.example/` header and an `embedurl` parameter that passes the controller check.
Expected: the embed response should refuse/deny or only postMessage to the canonical, verified origin.
Actual: the endpoint renders and the embedded page posts messages with targetOrigin derived from the spoofed Referer, enabling redirecting/embed messaging to attacker origins.

**Found by:** glm-vis: CE·low

#### A65 — Embed controller spec for missing embed_url is a false positive due to embeddable_host default failure

**Location:** `spec/controllers/embed_controller_spec.rb:8–16`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72  ·  1 findings, 1 cells · ⚠️ **no harness cell found this**

**Why this is real.** The example around line 8 (e.g., `it 'is 404 without an embed_url' do ... get ... expect(response.status).to eq(404) end`) passes even when the controller’s `params.require(:embed_url)` logic is never exercised. With the default/empty `embeddable_host` configuration, the controller fails earlier in `ensure_embeddable` (host not allowed/blank), returning/raising before Rails can raise the expected missing-parameter error. This is a genuine defect in the spec: it claims to test “missing param” behavior but actually tests “embeddable host misconfiguration returns 404,” so regressions in `params.require` would not be caught (the controller patch is not in this PR diff; this conclusion follows directly from the report’s described control flow).

**How to replicate.** 1) Open `spec/controllers/embed_controller_spec.rb` and find the test named like `is 404 without an embed_url` (around line 8). 2) Check whether the spec sets an allowed/non-empty embeddable host; if it does not, the request will be rejected by `ensure_embeddable` before `params.require(:embed_url)` is reached. 3) Confirm by temporarily configuring `embeddable_host` to a valid allowed value for the test (or stubbing `ensure_embeddable` to pass) and re-running that example: it should no longer return 404; instead it should raise `ActionController::ParameterMissing` / return 400 (depending on how the controller rescues), demonstrating the current expectation is asserting the wrong behavior.

**Found by:** **no harness cell** — vanilla only: opus

#### A66 — (untitled)

**Location:** `?`  ·  **Severity:** ?  ·  **Judge confidence:** 0.00  ·  1 findings, 1 cells

**Found by:** glm-vis: CE·medium

#### A67 — Scheduled and inline poll can run concurrently and duplicate work when inline poll exceeds throttle TTL

**Location:** `N/A (not referenced in reports; affected file not included in this PR diff)`  ·  **Severity:** high  ·  **Judge confidence:** 0.55  ·  1 findings, 1 cells

**Why this is real.** The clustered reports describe two entry points (a scheduled poll job and an inline poll path) that both trigger the same polling work, guarded only by a 60s throttle/TTL. Without a shared mutex/lock across both code paths, if the inline poll takes longer than the throttle TTL, a second invocation (e.g., the scheduled job) can re-enter while the first is still running, duplicating the poll and any side effects. This is a real concurrency bug (duplicate execution) rather than a style issue; however, the exact offending lines and line numbers cannot be quoted because the relevant file was not part of this PR’s diff and the reports did not include file/line references.

**How to replicate.** 1) Identify the two call sites in the codebase: (a) the scheduled job that runs the poll periodically and (b) the inline/request-triggered poll endpoint/method. 2) Modify or instrument the poll implementation to take >60s (e.g., insert a sleep or use a slow upstream) and ensure the throttle TTL is 60s. 3) Trigger the inline poll, then while it is still running, wait until the TTL expires and let the scheduled job fire (or trigger the inline poll again after 60s). Expected: second invocation should be prevented until the first completes. Actual: a second poll starts concurrently, duplicating work/requests/state updates.

**Found by:** glm-vis: CE·medium

#### A68 — Using `<<` to append to `contents` mutates the caller's String and can crash on frozen strings

**Location:** `lib/topicembed.rb:13–13`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72  ·  1 findings, 1 cells · ⚠️ **no harness cell found this**

**Why this is real.** The code at/around line 13 reportedly does `contents << ...` (e.g., appending a suffix/prefix directly onto the `contents` String). In Ruby, `String#<<` mutates the receiver in-place, so if `contents` is a String provided by the caller, this unexpectedly changes the caller’s object. Additionally, if `contents` is frozen (common when passed as a frozen literal or explicitly `.freeze`d), `<<` raises `FrozenError`, turning what should be normal processing into a runtime exception; the PR diff doesn’t include this file, so this verification relies on the report’s cited line.

**How to replicate.** 1) Find the method in `lib/topicembed.rb` that takes/uses a `contents` String and locate line 13 where it does `contents << ...`. 2) In a Rails console (or unit test), call that method with a frozen String, e.g. `contents = "abc".freeze` and pass it as the `contents` argument. 3) Expected: method returns processed output without mutating the input and without crashing. Actual: raises `FrozenError: can't modify frozen String` (and even when not frozen, the original `contents` object will be modified, observable by checking it after the call).

**Found by:** **no harness cell** — vanilla only: fable

#### A69 — Cache miss on arbitrary URL triggers synchronous full RSS fetch+import (DoS vector)

**Location:** `topicretriever.rb:41–48`  ·  **Severity:** high  ·  **Judge confidence:** 0.66  ·  1 findings, 1 cells · ⚠️ **no harness cell found this**

**Why this is real.** The deduplicated reports all point to `topicretriever.rb:41` where the URL lookup path treats a miss as a reason to synchronously run a full RSS “fetch-and-import” of the entire feed. This is a real defect because any caller that can cause lookups for previously unseen URLs can force repeated expensive network+parsing+DB work in the request path (i.e., attacker-triggerable amplification/DoS). Note: this file is not part of the PR diff, so verification is by inspecting the post-PR tree at/around the referenced line and confirming the miss path directly invokes the RSS import routine instead of deferring/queuing/caching it.

**How to replicate.** 1) Locate the method in `topicretriever.rb` responsible for resolving a topic by URL (around line ~41) and confirm that when the URL is not found in cache/DB it immediately calls the RSS fetch+import routine for the whole feed.
2) Run the service in dev and identify an endpoint/action that calls this resolver with a URL parameter.
3) Send repeated requests with distinct, never-before-seen URL values (e.g., add a unique querystring each time) so the lookup always misses.
Expected: misses should be cheap (e.g., return not-found, or enqueue a background refresh at most once per interval).
Actual: each miss performs a full RSS fetch/import synchronously, causing high latency and rapidly increasing CPU/IO/DB load.

**Found by:** **no harness cell** — vanilla only: fable

#### A70 — Embed loading page auto-reloads every 30s, amplifying unauthenticated request/job flooding risk

**Location:** `app/views/embed/loading.html.erb:7–11`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  1 findings, 1 cells

**Why this is real.** The new template adds an unconditional reload loop: `setTimeout(function() { document.location.reload(); }, 30000);`. This causes any client that reaches the embed loading page to repeatedly re-request the same embed route forever (every 30 seconds) with no user interaction. If the embed request path enqueues background work per request (as reported), this view turns a single visit into an ongoing stream of requests/jobs, magnifying DoS potential rather than being a style issue.

**How to replicate.** 1) Load the embed loading page in a browser (the route that renders `embed/loading.html.erb`). 2) Open DevTools -> Network and observe the page automatically re-requesting itself every ~30 seconds (repeated GETs without clicks). 3) In parallel, monitor Sidekiq/Redis (queue size, enqueued jobs, Redis memory) while the page runs; expected: a single request/one-time load, actual: infinite periodic requests that (if the controller enqueues per request) continuously enqueue jobs and grow Redis/Sidekiq load.

**Found by:** glm-vis: CE·high

### Golden-duplicates removed (would double-count)

- **duplicate of golden #4** — “The TopicEmbed.import method is susceptible to a NoMethodError if the contents parameter is nil when attempting to append a string, and an XSS vulnerability due…”
  - cluster: Stored XSS: RSS/Atom item HTML is imported and rendered as raw HTML without sanitization (`app/models/topic_embed.rb`), 205 findings, 65 cells
- **duplicate of golden #4** — “The TopicEmbed.import method is susceptible to a NoMethodError if the contents parameter is nil when attempting to append a string, and an XSS vulnerability due…”
  - cluster: XSS via unescaped feed-supplied URL in TopicEmbed imported-from footer (`app/models/topicembed.rb`), 46 findings, 29 cells
- **duplicate of golden #6** — “Calling `i.content.scrub` assumes that `i.content` is always populated. However, many RSS feeds do not provide a `content` field, leading to a potential nil poi…”
  - cluster: Pollfeed aborts entire feed import on first bad item (no per-item rescue) (`app/jobs/scheduled/pollfeed.rb`), 68 findings, 29 cells
- **duplicate of golden #0** — “The PollFeed job calls open(SiteSetting.feed_polling_url) without validating the URL, allowing an attacker who controls the feed_polling_url site setting to mak…”
  - cluster: PollFeed uses Kernel.open on an unvalidated admin setting, allowing pipe-prefixed command execution (admin-to-RCE) (`app/jobs/scheduled/pollfeed.rb`), 19 findings, 15 cells
- **duplicate of golden #1** — “The current origin validation using indexOf is insufficient and can be bypassed. An attacker could use a malicious domain like evil-discourseUrl.com to pass thi…”
  - cluster: postMessage origin validation uses substring match, allowing spoofed origins to resize the embed iframe (`app/assets/javascripts/embed.js`), 21 findings, 17 cells
- **duplicate of golden #5** — “The ERB block closes with end if, which is invalid Ruby/ERB and will raise at render; it should just be end to close the if block.…”
  - cluster: Malformed ERB terminator `<%- end if %>` breaks or miscompiles the header conditional (`app/views/embed/best.html.erb`), 16 findings, 7 cells
- **duplicate of golden #6** — “Calling `i.content.scrub` assumes that `i.content` is always populated. However, many RSS feeds do not provide a `content` field, leading to a potential nil poi…”
  - cluster: Feed polling crashes on Ruby 2.0/1.9 when calling String#scrub on RSS item content (`app/jobs/scheduled/pollfeed.rb`), 11 findings, 11 cells
- **duplicate of golden #3** — “The code sets X-Frame-Options: ALLOWALL which completely disables clickjacking protection. The referer validation can be bypassed (referer headers are easily sp…”
  - cluster: Invalid X-Frame-Options value (`allowall`) is ignored by browsers, weakening framing protection (`app/controllers/embedcontroller.rb`), 5 findings, 5 cells
- **duplicate of golden #6** — “Calling `i.content.scrub` assumes that `i.content` is always populated. However, many RSS feeds do not provide a `content` field, leading to a potential nil poi…”
  - cluster: PollFeed job crashes on RSS items without a content field (nil.scrub) (`jobs/pollfeed.rb`), 2 findings, 2 cells
- **duplicate of golden #4** — “The TopicEmbed.import method is susceptible to a NoMethodError if the contents parameter is nil when attempting to append a string, and an XSS vulnerability due…”
  - cluster: Topic embed import crashes when Readability returns nil content (`lib/topic_embed/importer.rb`), 1 findings, 1 cells
- **duplicate of golden #5** — “The ERB block closes with end if, which is invalid Ruby/ERB and will raise at render; it should just be end to close the if block.…”
  - cluster: embed/best.html.erb can call @topicview.topic when @topicview is nil due to malformed conditional/end modifier (`app/views/embed/best.html.erb`), 1 findings, 1 cells

---

## PR 10 — 32 additional real bugs (7 goldens; 5 golden-duplicates removed)
(<https://github.com/ai-code-review-evaluation/discourse-graphite/pull/10>)

### Additional bugs (evidence cards)

#### A1 — Migration interpolates embeddable host strings into raw SQL, breaking on quotes and enabling SQL injection

**Location:** `db/post_migrate/*_backfill_embeddable_hosts.rb:23–27`  ·  **Severity:** high  ·  **Judge confidence:** 0.62  ·  171 findings, 56 cells

**Why this is real.** The reports consistently point to a post-migration that builds an INSERT with raw string interpolation, e.g. `execute("INSERT INTO embeddable_hosts ... VALUES ('#{h}', ...)")` around line ~23. Because `h` comes from the legacy embeddable-hosts setting, any value containing an apostrophe will terminate the SQL string literal and cause a syntax error (or worse, allow crafted SQL to be executed). This is a functional correctness and safety issue, not a style nit; it can crash the migration or insert corrupted data during upgrade/backfill.

**How to replicate.** 1) Before running the backfill migration, set the legacy embeddable hosts setting to include a host with a quote, e.g. `example.com` and `evil'host.com` (or a value like `a'); DELETE FROM embeddable_hosts; --`). 2) Run the migration/backfill (e.g. `bundle exec rake db:migrate` / `db:post_migrate`). 3) Observe the migration failing with a SQL syntax error near the quote, or (with a crafted payload) executing unintended SQL. Expected: hosts are inserted safely regardless of characters; actual: the raw-interpolated SQL breaks or becomes injectable.

**Found by:** fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; opus: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·high, CE·low, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, MRV·high, MRV·low; terra: CE·low, CE·medium, MRV·low; astra: CE·high, CE·low, CE·medium

#### A2 — Plural *_ids hydration blindly calls .map on null/undefined and can drop unresolved relationship ids

**Location:** `app/services/store.js.es6:192–202`  ·  **Severity:** high  ·  **Judge confidence:** 0.86  ·  122 findings, 48 cells

**Why this is real.** In the plural branch introduced by the patch, the code does `const hydrated = obj[k].map(function(id) { ... });` and then `delete obj[k];` unconditionally. If `obj[k]` is `null`, `undefined`, or a scalar (possible for nullable/optional relationships or inconsistent serializers), calling `.map` throws a TypeError. Even when `obj[k]` is an array, `_lookupSubType(...)` can return falsy for missing referenced records, producing `[record, null, ...]` while still deleting the original `*_ids`, silently losing the original id list needed to preserve the relationship.

**How to replicate.** 1) Ensure a model payload contains a nullable plural relationship key like `comment_ids: null` (or omit it, leaving `obj[k]` undefined) and run the store hydration path that calls `_hydrateEmbedded`. Expected: hydration should tolerate null/absent ids and leave the object usable; Actual: it throws `TypeError: Cannot read properties of null/undefined (reading 'map')` at the plural branch.
2) Send a partial REST response where `topic_ids: [1,2]` but only record `1` is included in `root` (id `2` missing). Expected: either keep `topic_ids` intact or avoid inserting nulls so the relationship can be resolved later; Actual: `obj[pluralized]` becomes `[<record 1>, null]` and `topic_ids` is deleted, losing the unresolved id.

**Found by:** fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high; glm-flash: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, MRV·low, MRV·medium; astra: MRV·low

#### A3 — Embeddable hosts saved with a port never match because lookup drops the port

**Location:** `app/models/embeddablehost.rb:17–35`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  143 findings, 61 cells

**Why this is real.** The model allows saving hosts that include a port (e.g. via a permissive host format/validation that does not reject `example.com:8080`), but the runtime lookup uses `uri(url).host` (or equivalent) which returns only the hostname without the port. As a result, code that compares the stored `host` string to the parsed URL host (e.g., `recordforhost`/`hostallowed?` comparing against `urihost(url)`) can never match when the stored value includes `:PORT`, making such configurations ineffective. The reports all describe the same mechanism; the PR diff itself is not shown here, so this verification relies on the reported line reference (`embeddablehost.rb:17`) and the described use of `uri.host`.

**How to replicate.** 1) In Rails console, create an allowed host record with a port: `EmbeddableHost.create!(host: 'example.com:8080')` (it is accepted by validation per report). 2) Call the allow-check with a URL including that port, e.g. `EmbeddableHost.hostallowed?('http://example.com:8080/some/path')` (or whatever entrypoint checks embedding). 3) Expected: returns true / embedding is allowed. Actual: returns false / embedding is rejected because the parsed URL host is `example.com` (port dropped) and does not equal the stored `example.com:8080`.

**Found by:** fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; opus: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·low; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A4 — EmbeddableHost hostname validation regex rejects valid hosts (long gTLDs, localhost/IP) and is inconsistent about ports

**Location:** `app/models/embeddablehost.rb:2–6`  ·  **Severity:** medium  ·  **Judge confidence:** 0.64  ·  89 findings, 43 cells

**Why this is real.** Multiple reviewers point to the model-level format validation in `app/models/embeddablehost.rb` (reported around line 2) using a hostname regex that caps the TLD length to 2–5 letters (e.g., a fragment like `\.[a-z]{2,5}`) and requires an alphabetic TLD. That mechanism necessarily rejects legitimate modern gTLDs such as `.technology`/`.photography` as well as common non-DNS hosts used in embedding setups like `localhost` and raw IPv4 addresses. Reports also indicate the regex permits `:port` while downstream host extraction (e.g., `URI#host`/`urihost`) drops ports, making saved `example.com:3000` impossible to match later—this is a functional mismatch, not a style nit.

**How to replicate.** 1) Open `app/models/embeddablehost.rb` and find the `validates ... format: { with: /.../ }` for the host field; confirm it contains an alphabetic TLD restriction with a `{2,5}` quantifier (and likely an optional `:\d+` port segment).
2) In a Rails console, attempt to create records:
   - `EmbeddableHost.create!(host: "example.photography")` (or `.technology`, `.museum`) => expected: valid host saved; actual: validation error.
   - `EmbeddableHost.create!(host: "localhost")` and `EmbeddableHost.create!(host: "192.168.0.1")` => expected: allowed for local/private embedding; actual: validation error.
3) If the regex allows ports, save `EmbeddableHost.create!(host: "example.com:3000")`, then exercise the lookup path that compares against `URI.parse(url).host` (or `urihost`) for `http://example.com:3000/...` => expected: match; actual: mismatch because lookup uses `example.com` (port stripped) while the stored value includes `:3000`.

**Found by:** fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; opus: CE·medium, MRV·high; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·medium, MRV·high, MRV·medium; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A5 — EmbeddableHost allows duplicate host mappings, making lookup via `.first` nondeterministic

**Location:** `app/models/embeddable_host.rb:15–30`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  88 findings, 52 cells

**Why this is real.** The underlying defect is that the host-to-category mapping is not enforced as unique (neither case-insensitively in the model nor via a DB unique index per the reports), while the lookup logic selects an arbitrary matching row. In the model method typically written like `where("lower(host) = ?", host.downcase).first`, `.first` has no `ORDER BY`, so if multiple rows exist for the same host (e.g., different categories), the returned record/category is unspecified and can vary depending on query plan/row order. The PR diff does not include this file, so this verification relies on the consistent reports pointing to the lack of uniqueness enforcement plus unordered `.first` selection.

**How to replicate.** 1) Insert two EmbeddableHost rows with the same hostname differing only by case (or identical) but different `category_id` (e.g., `host='Example.com', category_id=1` and `host='example.com', category_id=2`). 2) Trigger the host lookup used by embedding (e.g., call `EmbeddableHost.record_for_host('example.com')` or hit the embed endpoint that resolves the host). 3) Observe that the chosen category is whichever row happens to be returned first by the DB; it may flip after deletes/inserts/vacuum/restart because there is no uniqueness constraint and no deterministic ordering. Expected: host resolves to a single, well-defined category; actual: arbitrary category selection or inconsistent behavior.

**Found by:** fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; opus: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, MRV·high, MRV·low, MRV·medium; glm-vis: CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·medium, MRV·high, MRV·low, MRV·medium; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A6 — Delete action swallows destroyRecord() failures (no popupAjaxError catch)

**Location:** `app/assets/javascripts/admin/components/embeddable-host.js.es6:43–51`  ·  **Severity:** medium  ·  **Judge confidence:** 0.88  ·  75 findings, 51 cells

**Why this is real.** In the delete action, the code calls `this.get('host').destroyRecord().then(() => { ... });` but never attaches a rejection handler (e.g. `.catch(popupAjaxError)`). If the DELETE request fails, the promise rejects and no UI error is shown; additionally `deleteHost` is only sent in the `.then(...)`, so the row is never removed and the admin gets no feedback about the failure.

**How to replicate.** 1) Go to the admin UI where embeddable hosts are listed (the table row rendered by this component). 2) Click the delete button and confirm. 3) Force the delete request to fail (e.g., DevTools -> Network -> Offline, or mock the endpoint to return 500/403). Expected: an error popup via `popupAjaxError` and clear feedback that deletion failed. Actual: no error popup/feedback; the row remains because `deleteHost` is never called, and the rejection may surface only as an unhandled promise rejection in the console.

**Found by:** fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; opus: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A7 — Creating an embeddable host with no category overwrites server-assigned Uncategorized on the client until reload

**Location:** `assets/javascripts/discourse/components/embeddable-host.js:63–76`  ·  **Severity:** low  ·  **Judge confidence:** 0.62  ·  62 findings, 41 cells

**Why this is real.** All reports point to the success handler for saving a new host assigning the host's category from the (still null) UI selection, e.g. `host.set('category_id', this.get('categoryId'));` followed by `host.set('category', this.site.categories.findBy('id', host.get('category_id')));`. When no category is selected, `categoryId` remains null, so `findBy('id', null)` yields undefined and the component overwrites the association the backend defaulted to Uncategorized. This is a real state bug (UI becomes inconsistent with persisted data) rather than a style issue; the file wasn’t part of the PR diff, so this verification relies on the consistent mechanism described in the deduplicated reports.

**How to replicate.** 1) In the UI where embeddable hosts are created/edited (the component using `embeddable-host.js`), add a new host and leave the category unselected/blank. 2) Click Save. 3) Observe: the host row shows no category (blank/undefined badge) immediately after save. 4) Reload the page (or re-fetch hosts from the server). Expected: it should show Uncategorized immediately after save (since backend defaults it). Actual: it only shows Uncategorized after reload because the client overwrote `host.category` using `findBy('id', null)`.

**Found by:** fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; opus: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, MRV·high, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: MRV·high, MRV·medium; terra: CE·medium; astra: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium

#### A8 — EmbeddableHost persists arbitrary categoryid without verifying category exists or is accessible

**Location:** `app/controllers/admin/embeddablehostscontroller.rb:24–26`  ·  **Severity:** medium  ·  **Judge confidence:** 0.68  ·  43 findings, 24 cells

**Why this is real.** Multiple reports point to the same assignment in this controller (around line 24): `host.categoryid = params[:embeddablehost][:categoryid]` followed by saving the record, with no check like `Category.exists?(...)` or authorization/visibility validation. Because the `categoryid` value is taken directly from params and persisted, a nonexistent/deleted (or read-restricted) category id can be stored, creating a dangling relationship that is later used when importing/creating embedded topics. The PR diff does not include this file, so this verification relies on the reported line reference and the described behavior in code paths that later use `host.categoryid` during import/topic creation.

**How to replicate.** 1) In the admin UI (or via HTTP), create or update an EmbeddableHost and set `embeddablehost[categoryid]` to a non-existent category id (e.g., a large integer), or to an id of a category that will be deleted after saving.
2) Save succeeds (actual), because the controller/model does not validate that the category exists/is allowed.
3) Trigger an embed import for that host (e.g., by embedding a page that causes `TopicEmbed.import` / topic creation).
Expected: the system should reject the invalid category id at save-time (or coerce to nil/default) with a clear error.
Actual: import/topic creation fails or routes content to an unintended/private category because the stored `categoryid` is invalid or unauthorized.

**Found by:** fable: CE·low, CE·medium, MRV·high, MRV·low; opus: CE·high, CE·low, CE·medium, MRV·low, MRV·medium; sonnet: MRV·low; glm-flash: MRV·high, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, MRV·low, MRV·medium; astra: MRV·high, MRV·medium

#### A9 — Irreversible destructive data migration in `change` permanently deletes site settings on rollback

**Location:** `db/migrate/20150818190757_create_embeddable_hosts.rb:31–40`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  49 findings, 31 cells

**Why this is real.** The migration reportedly performs raw SQL data operations inside `def change`, including `execute "DELETE FROM site_settings WHERE name IN ('embeddablehosts','embedcategory')"` (report points to line ~31). Because these deletes are not reversible and there is no explicit `def down` that re-inserts the deleted `site_settings` rows, rolling back the migration drops the new table but cannot restore the deleted configuration, causing permanent data loss. The PR diff isn’t provided here, so this verification relies on the consistent line-level description from the deduplicated reports.

**How to replicate.** 1) In a DB with existing `site_settings` rows for names `embeddablehosts` and `embedcategory` (populate them with non-empty values). 2) Run `rails db:migrate` to apply `20150818190757_create_embeddable_hosts`. 3) Confirm the settings rows were deleted (and hosts inserted into the new table if applicable). 4) Run `rails db:rollback STEP=1`. Expected: original `site_settings` rows restored (or rollback fully reversible). Actual: rollback cannot restore the deleted `site_settings` rows; embedding configuration is lost even though the schema rollback drops the embeddable hosts table.

**Found by:** fable: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; opus: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·low, MRV·high, MRV·low; glm-flash: CE·high, CE·low, MRV·high, MRV·low; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high; terra: MRV·high, MRV·medium; astra: CE·low, MRV·high, MRV·low

#### A10 — Migration uses create_table force: true causing silent drop/recreate and data loss

**Location:** `db/migrate/20150818190757_create_embeddable_hosts.rb:3–3`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74  ·  24 findings, 16 cells

**Why this is real.** The migration reportedly calls `create_table :embeddable_hosts, force: true` (referenced at line 3 in multiple reports). In Rails migrations, `force: true` issues a DROP TABLE (if it exists) before creating the table, which silently deletes any existing `embeddable_hosts` table and all its rows. That makes the migration destructive on re-runs or if the table already exists (e.g., created manually or by a plugin), and it masks partial-failure states instead of failing loudly.

**How to replicate.** 1) In a database where an `embeddable_hosts` table already exists (e.g., create it manually) and insert at least one row. 2) Run the migration `20150818190757_create_embeddable_hosts.rb` (or re-run it in a reset/test environment). Expected: migration should fail or no-op if the table exists, preserving existing data. Actual: the existing table is dropped and recreated, and the previously inserted row(s) are lost.

**Found by:** fable: CE·medium, MRV·medium; opus: CE·low, CE·medium; sonnet: MRV·low, MRV·medium; glm-flash: MRV·high, MRV·low; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium

#### A11 — PUT /admin/customize/embedding update is a no-op that returns 200 without persisting changes

**Location:** `app/controllers/admin/embeddingcontroller.rb:9–12`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  23 findings, 17 cells

**Why this is real.** Multiple reports point to `app/controllers/admin/embeddingcontroller.rb:9` where the `update` action does not read any request params nor call any persistence method; it simply re-renders the current `@embedding` (e.g., `render_serialized(@embedding, EmbeddingSerializer)`). Because the action returns a successful response while performing no mutation, any client "save" request will appear to succeed (HTTP 200) even though nothing is updated. This is a functional contract bug (misleading endpoint behavior), not a style issue; the controller method effectively discards the request body.

**How to replicate.** 1) Send a PUT request to `/admin/customize/embedding` with a JSON body that changes a setting (any field the UI intends to save). 2) Observe the response is 200 and returns the serialized embedding. 3) Reload the page or re-fetch the embedding; expected: the updated value persists. Actual: the value is unchanged because `update` ignores params and performs no save/update call.

**Found by:** opus: CE·low, CE·medium; glm-flash: CE·high, CE·low, MRV·high, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; sol: MRV·high, MRV·medium

#### A12 — expandable_first_post? no longer gated by configured embeddable hosts, causing regression when hosts are cleared

**Location:** `app/models/topic.rb:869–875`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  21 findings, 15 cells

**Why this is real.** The reports indicate that in the post-PR code around `app/models/topic.rb:869`, `expandable_first_post?` was changed to only check something equivalent to `SiteSetting.embed_truncate? && has_topic_embed?`, and the prior guard requiring configured embeddable hosts (e.g., `SiteSetting.embeddable_hosts.present?` or an `EmbeddableHost.exists?` check) was removed. That means once a topic has an embed record (`has_topic_embed?`), enabling `embed_truncate` will keep `expandable_first_post?` true even if all allowed embedding hosts are later deleted/cleared, silently changing the previous behavior where clearing hosts disabled this feature. This is a behavioral regression (logic bug), not a style issue, because it changes feature enablement conditions and can expose expandable/truncated behavior when the admin has effectively disabled embedding by removing all hosts.

**How to replicate.** 1) Ensure embedding is enabled at least once so an embedded topic exists (create an embedded topic while at least one EmbeddableHost/embeddable host entry is configured). 2) Enable the setting controlling truncation (e.g., `SiteSetting.embed_truncate = true`). 3) Delete all allowed embedding hosts (remove all EmbeddableHost rows / clear the embeddable hosts setting so there are zero configured hosts). 4) Fetch the topic JSON or view the topic; observe `expandable_first_post?` behavior (e.g., an `expandable_first_post` field or UI expander remains active) because the method still returns true due to `embed_truncate && has_topic_embed?`. Expected: once no embeddable hosts are configured, expandable/truncated embed behavior should be off (method returns false), matching the prior host-gated semantics.

**Found by:** fable: CE·high, MRV·high; opus: MRV·high, MRV·low, MRV·medium; sonnet: MRV·high, MRV·low; glm-flash: CE·low, CE·medium, MRV·high, MRV·medium; glm-vis: MRV·high, MRV·low

#### A13 — Migration skips importing legacy embeddable hosts by using cmdtuples on a SELECT, then deletes the only copy of the config

**Location:** `db/migrate/20150818190757createembeddablehosts.rb:18–31`  ·  **Severity:** critical  ·  **Judge confidence:** 0.95  ·  13 findings, 12 cells

**Why this is real.** The migration gates the import on `if embeddablehosts && embeddablehosts.cmdtuples > 0`, but `cmdtuples` is the affected-row count for DML; for PostgreSQL `SELECT` results it is 0, so this condition is never true even when rows are returned. As a result, the insert loop never runs and the subsequent unconditional `delete from site_settings where name in ('embeddablehosts', 'embedcategory')` removes the legacy settings, permanently losing all configured embeddable hosts on upgrade. (The PR diff does not include this file; this verification relies on the reported offending lines.)

**How to replicate.** 1) In a PostgreSQL-backed environment, create legacy rows in `site_settings`: one with `name='embeddablehosts'` and a non-empty host list value, and optionally `name='embedcategory'`.
2) Run the migration `20150818190757createembeddablehosts.rb` (e.g., `rake db:migrate`).
3) Observe that the `embeddable_hosts` table remains empty (no imported rows) while the `site_settings` rows for `embeddablehosts`/`embedcategory` are deleted.
Expected: hosts are copied into `embeddable_hosts` before deleting legacy settings. Actual: import block is skipped and settings are deleted, disabling previously configured embedding.

**Found by:** opus: CE·medium, MRV·low; sonnet: MRV·high; glm-flash: CE·high, MRV·high; glm-vis: MRV·high, MRV·low, MRV·medium; sol: MRV·low, MRV·medium; terra: MRV·medium

#### A14 — Feed-polled TopicEmbed imports can lose category and land in Uncategorized when no EmbeddableHost matches

**Location:** `app/models/topicembed.rb:36–43`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  14 findings, 10 cells

**Why this is real.** The reported post-PR code derives category solely from a per-host lookup: `eh = EmbeddableHost.record_for_host(url)` followed by `category: eh.try(:category_id)` (or equivalent). When `record_for_host(url)` returns nil (no matching embeddable host row, or host mismatch like www vs bare), `eh.try(:category_id)` becomes nil and the created topic has no category, silently falling back to Uncategorized. This is a real behavioral regression because the former site-wide fallback (`SiteSetting.embed_category`) was removed, and feed polling paths can call `TopicEmbed.import` without first ensuring/validating an EmbeddableHost exists.

**How to replicate.** 1) Configure a Discourse instance with RSS/Atom feed polling enabled (so `Jobs::PollFeed` runs) and set the old embed default category to a non-default category (pre-PR behavior baseline). 2) Ensure there is NO `EmbeddableHost` row matching the host of the feed item link URLs (e.g., feed is on example.com but item links are on www.example.com or a different domain). 3) Trigger `Jobs::PollFeed` (or run it manually) so it calls `TopicEmbed.import` for feed entries. Expected (pre-PR): imported topics go into the configured embed category; Actual (post-PR): `record_for_host(url)` is nil, `category` becomes nil, and topics are created in Uncategorized with no warning/error.

**Found by:** fable: CE·medium, MRV·high, MRV·low, MRV·medium; opus: MRV·high; sonnet: MRV·high; glm-flash: CE·high

#### A15 — Routes expose REST actions for embeddable_hosts that the controller doesn't implement (ActionNotFound on GET)

**Location:** `config/routes.rb:153–153`  ·  **Severity:** medium  ·  **Judge confidence:** 0.86  ·  10 findings, 9 cells

**Why this is real.** The PR adds `resources :embeddable_hosts, constraints: AdminConstraint.new` (config/routes.rb:153). In Rails, `resources` without an `only:`/`except:` generates the full REST set (index/show/new/edit/create/update/destroy). If `Admin::EmbeddableHostsController` only defines mutating actions (create/update/destroy) and does not define `index`, `show`, `new`, or `edit`, then GET requests to the generated routes will dispatch to missing actions and raise `AbstractController::ActionNotFound` (500) instead of being unroutable or handled.

**How to replicate.** 1) In the post-PR code, run `bin/rails routes | grep embeddable_hosts` and observe routes like `GET /admin/embeddable_hosts(.:format) admin/embeddable_hosts#index` and `GET /admin/embeddable_hosts/:id(.:format) admin/embeddable_hosts#show` are present.
2) Open `app/controllers/admin/embeddable_hosts_controller.rb` and confirm it does not implement `index/show/new/edit` (only create/update/destroy).
3) As an admin (or with an authenticated admin session), request `GET /admin/embeddable_hosts.json` (or `GET /admin/embeddable_hosts/1`).
Expected: no route exists (404) or a valid index/show response. Actual: Rails raises `AbstractController::ActionNotFound` for the missing action, resulting in a 500 error.

**Found by:** fable: CE·high, CE·medium; opus: CE·medium; sonnet: CE·high, MRV·high, MRV·low; glm-flash: CE·high

#### A16 — Pretender /fruits/:id handler ignores requested id and always returns fruits[0], making store.find('fruit', 2) test assert the wrong record

**Location:** `test/javascripts/helpers/create-pretender.js.es6:226–229`  ·  **Severity:** low  ·  **Judge confidence:** 0.80  ·  7 findings, 6 cells

**Why this is real.** The Pretender route for single-fruit fetch is defined as `this.get('/fruits/:id', function() { ... return { fruit: fruits[0] }; })` (around lines 226-229), which never reads `request.params.id` and always serves the first fixture. As a result, any call like `store.find('fruit', 2)` receives the payload for fruit id=1 (apple), so downstream tests that assert apple’s data under an id=2 request are validating a fixture quirk rather than correct find-by-id behavior. This is a functional defect in the test server/mock, not a style issue.

**How to replicate.** 1) Inspect `test/javascripts/helpers/create-pretender.js.es6` and locate the `this.get('/fruits/:id', ...)` handler; note it returns `fruits[0]` unconditionally. 2) In `test/javascripts/models/store-test.js.es6` (the updated "find embedded" test), observe it calls `store.find('fruit', 2)` but asserts properties matching apple (e.g., colors ids [1,2]) rather than banana (colorids [3]). 3) To observe behavior concretely, temporarily log/inspect the response for GET /fruits/2 (or change the handler to select by `request.params.id`); expected: response fruit.id == 2, actual (current): response fruit.id == 1, and once fixed the test assertions will fail because banana has different embedded colors.

**Found by:** glm-flash: CE·high, MRV·high; glm-vis: CE·high, MRV·high

#### A17 — EmbeddingSerializer emits only embeddable_host_ids (no sideloaded embeddable_hosts), breaking client hydration

**Location:** `app/serializers/embeddingserializer.rb:3–3`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  4 findings, 4 cells

**Why this is real.** The reports consistently point to `app/serializers/embeddingserializer.rb:3` defining the association like `has_many :embeddable_hosts, ... embed: :ids` (notably without `include: true`). In AMS-style serializers, `embed: :ids` alone produces only an `embeddable_host_ids` array and does not emit a root/side-loaded `embeddable_hosts` collection. The frontend store code path described in the reports (`lookupSubType` for each id) requires those host records to exist in a top-level side-load array; because the payload never includes them, hydration resolves to missing/undefined records and the admin list renders empty. The PR diff does not include this file, so this verification relies on the reported offending line and the known serializer behavior.

**How to replicate.** 1) Load the admin embedding UI that fetches embeddings (e.g., navigate to `/admin/customize/embedding`).
2) Inspect the network response for the embeddings endpoint (e.g., GET `/admin/customize/embedding.json` or equivalent).
3) Actual: the JSON includes something like `embeddable_host_ids: [..]` but no side-loaded/top-level `embeddable_hosts: [...]` array of host objects.
4) Expected: when the client hydrates `embedding.embeddable_hosts` by id, the response should also include the full embeddable host records in a root collection so `lookupSubType` can resolve them; otherwise the table/list shows blank/empty entries despite ids being present.

**Found by:** opus: CE·medium; sonnet: CE·high; glm-flash: MRV·high, MRV·low

#### A18 — Embed host lookup uses lower(host) without a supporting functional index, causing sequential scans on embed requests

**Location:** `app/models/embeddablehost.rb:17–20`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  3 findings, 3 cells

**Why this is real.** In `EmbeddableHost.ensure_embeddable` the lookup is performed with a case-insensitive predicate like `where("lower(host) = ?", host.downcase)` (reported at line 17). The accompanying migration `createembeddablehosts.rb` (reported lines 3-7) creates the table but does not add an index on `host`, and even a plain index on `host` would not be used by `lower(host)` anyway; without a functional index on `lower(host)` (or normalized storage), this forces a table scan for each embed request. This is a real performance bug on a hot path (public embeds), not a style issue, because it changes the query pattern from a cached/in-memory check to an uncached DB lookup that cannot be indexed as written.

**How to replicate.** 1) Ensure the PR is applied and the `embeddable_hosts` table exists (run migrations). 2) Add enough rows to `embeddable_hosts` to make scans noticeable (e.g., thousands of distinct hosts). 3) Trigger an embed request path (e.g., request the public `/embed/comments` endpoint for some host/domain). 4) Observe the SQL generated includes `lower(host) = ...` and run `EXPLAIN (ANALYZE, BUFFERS)` for that query: expected behavior is an index scan for host lookup, but actual behavior will be a sequential scan (or otherwise non-indexed scan) due to the missing functional index, leading to increased latency and DB load per request.

**Found by:** sol: CE·high

#### A19 — EmbeddableHost host format validation allows trailing newline due to end-anchor, creating broken allowlist entries

**Location:** `app/models/embeddablehost.rb:2–3`  ·  **Severity:** low  ·  **Judge confidence:** 0.67  ·  3 findings, 3 cells · ⚠️ **no harness cell found this**

**Why this is real.** The reported code in `app/models/embeddablehost.rb` validates `host` with a regex anchored using an end-of-string anchor that can match *before* a trailing newline (reported as `\z`/`\Z`), e.g. `validates :host, format: { with: /\A...\Z/ }`. In Ruby, `\Z` (and similarly `$`) will match before a final newline, so an input like `"example.com\n"` can pass format validation and be persisted with the newline intact. Later, lookups comparing `lower(host)` to a parsed URI host (which will be `"example.com"` without the newline) will not match, producing a silently broken allowlist entry; the reports note nothing strips the newline server-side and this is reachable via API.

**How to replicate.** 1) Find the `EmbeddableHost` model validation in `app/models/embeddablehost.rb` (around line 2) and confirm the host format regex uses an end anchor that matches before a trailing newline (e.g., `\Z` or `$`) rather than a strict end anchor (`\z`) and/or does not normalize/strip whitespace.
2) Create an allowlist entry via the API/console with a trailing newline, e.g. `EmbeddableHost.create!(host: "example.com\n")` (or the corresponding endpoint payload).
3) Observe: the record is accepted and stored containing `\n` (actual behavior). Expected: validation should reject or normalize such input so that stored host equals `"example.com"`.
4) Attempt to use/resolve an embed for `https://example.com/...` and observe the allowlist lookup fails (because `lower(host)` in DB includes the newline while `uri.host` does not), so the allowlisted host is not recognized.

**Found by:** **no harness cell** — vanilla only: glm-vis, opus, sonnet

#### A20 — REST adapter only replaces first underscore in type name, breaking admin routing for multi-underscore models

**Location:** `app/assets/javascripts/discourse/adapters/rest.js.es6:22–22`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  2 findings, 2 cells

**Why this is real.** At/around line 22 the adapter normalizes the Ember Data type with a single-string replace (reported as `type.replace('_', '-')`). In JavaScript, `String.prototype.replace` with a string argument replaces only the first match, so a type like `foo_bar_baz` becomes `foo-bar_baz` instead of `foo-bar-baz`. Any later lookup/comparison that expects fully hyphenated types (e.g., for admin route selection or identity-map keys) will silently miss, causing wrong URL selection; this is a functional defect, not a style nit. (The PR diff isn’t provided here; verification is by inspecting the post-PR file at the reported line.)

**How to replicate.** 1) Open `app/assets/javascripts/discourse/adapters/rest.js.es6` and locate the type normalization around line 22 (`type = type.replace('_', '-')` or equivalent).
2) Identify the code path that decides whether a request goes to an admin endpoint (e.g., comparing the normalized `type` against an allowlist of admin types / choosing `/admin/` vs `/`).
3) Trigger a request for a model whose type contains multiple underscores (e.g., `foo_bar_baz`) through the adapter’s URL building (e.g., `adapter.buildURL('foo_bar_baz', ...)` or by interacting with a route that loads that type).
Expected: all underscores are converted (`foo-bar-baz`) so the admin-type match succeeds and the request targets the correct admin path.
Actual: only the first underscore is converted (`foo-bar_baz`), the admin match fails, and the adapter routes to the non-admin path (e.g., `/` instead of `/admin/`) or uses a mismatched type key for caching/hydration.

**Found by:** opus: MRV·high

#### A21 — EmbeddableHost destroy action always reports success even when destroy fails

**Location:** `app/controllers/admin/embeddablehostscontroller.rb:16–18`  ·  **Severity:** medium  ·  **Judge confidence:** 0.78  ·  2 findings, 2 cells

**Why this is real.** The destroy action calls `host.destroy` but does not check its return value and then unconditionally renders a success payload (e.g., `host.destroy` followed by `render json: success_json`). In Rails, `destroy` can fail (returning false / leaving the record persisted) when callbacks abort the destroy or when the database rejects it (e.g., FK constraints). Because the result is ignored, the controller can return 200/success even though the host was not deleted; this is a functional correctness bug, not a style issue. (This file was not part of the PR diff per the report, so verification relies on inspecting the current post-PR source at the referenced lines.)

**How to replicate.** 1) Create an EmbeddableHost record. 2) Ensure destruction will fail: add/enable a `before_destroy` callback that throws `:abort`, or create dependent rows with a restrictive foreign key so the DB rejects delete. 3) Call the admin destroy endpoint for that host (DELETE request to the controller action). Expected: non-success response (e.g., 422/500) and an error JSON; Actual: success JSON is returned while the record still exists when you reload/check the database.

**Found by:** opus: CE·medium; sol: MRV·medium

#### A22 — EmbedController authorization can be bypassed by forging the Referer header

**Location:** `app/controllers/embedcontroller.rb:61–75`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  2 findings, 2 cells

**Why this is real.** The controller’s embeddable gate is implemented by checking only a client-supplied header: `embeddable_host.host_allowed?(request.referer)` (per the report, in/around `ensure_embeddable`). Since `Referer` is not an authenticated signal and can be freely set by non-browser HTTP clients (curl/requests/Postman), an attacker can bypass the intended “only allowed hosts may embed” restriction simply by sending a forged `Referer: https://<allowed-host>/`. The same area is also described as CSRF-exempt (`skip_before_filter :verify_authenticity_token`), which removes an additional browser-side safeguard and makes header-forgery exploitation straightforward.

**How to replicate.** 1) Configure Discourse embedding with at least one allowed embeddable host (e.g., `allowed.example`). 2) From any machine, use curl to call the embed endpoints directly (e.g., the topic comments/count endpoint under `EmbedController`) while forging the header: `curl -H 'Referer: https://allowed.example/' 'https://<forum-host>/<embed-endpoint>?topic_id=<id-or-slug>'`. 3) Expected: request is rejected when not actually originating from an allowed embed host context. Actual: request is authorized and returns embed content (comments/count) solely because the forged Referer passes `host_allowed?`, enabling anyone who knows an allowed hostname to read embed content without controlling that host.

**Found by:** sonnet: MRV·low; glm-vis: MRV·medium

#### A23 — Failed host.save leaves rejected buffered edits applied locally (no rollback on save error)

**Location:** `assets/javascripts/discourse/controllers/admin-graphite-hosts.js.es6:86–121`  ·  **Severity:** high  ·  **Judge confidence:** 0.62  ·  1 findings, 1 cells

**Why this is real.** The reported code path calls `host.save(props)` where `props` are the buffered edit values, which (in Ember Data) assigns those attributes onto the live record before the request is resolved. The `.catch(...)` handler only shows an alert and does not call `host.rollbackAttributes()`/restore the pre-edit state, so after a 422/failed save the record remains mutated in memory. When the user later clicks “cancel” (which rolls back only the buffer), the UI re-renders from the already-mutated record and shows the rejected values as if they persisted.

**How to replicate.** 1) In the admin UI for Graphite hosts, edit an existing host row (change host to an invalid format that the backend rejects) and click Save. 2) Ensure the server responds with a validation error (e.g., HTTP 422). 3) Observe that an error/alert is shown but the row’s displayed host/category values are now the attempted (invalid) edits. 4) Click Cancel: expected behavior is that the row returns to the original saved values; actual behavior is that it continues to display the rejected edits because the underlying record was mutated by `host.save(props)` and never rolled back on failure.

**Found by:** glm-vis: MRV·high

#### A24 — Admin embedding route calls store.find without an id, causing findAll-style parsing and an empty model

**Location:** `assets/javascripts/discourse/routes/admin-embedding.js.es6:6–9`  ·  **Severity:** high  ·  **Judge confidence:** 0.58  ·  1 findings, 1 cells

**Why this is real.** The route’s model hook loads the record via a call equivalent to `return this.store.find('embedding');` (no id). In Discourse’s store implementation, a `find` without an id is routed to the `findAll` code path, which extracts results from the plural root key (e.g. `embeddings`). However the backend `show` endpoint returns a singleton under the singular root key (`embedding`), so the store resolves the model as empty/undefined and downstream template checks like `{{if embedding.embeddablehosts}}` never become truthy.

**How to replicate.** 1) In the browser, navigate to the plugin’s admin embedding page (the route that uses `admin-embedding.js.es6`). 2) Observe in the network tab that the request hits the singleton `show` endpoint and returns JSON shaped like `{ "embedding": { ... } }`. 3) Despite the response, the page never renders the embeddable hosts table/section because the route’s model resolves to an empty result (it was parsed as a collection expecting `{ "embeddings": [...] }`). Expected: the embedding record loads and `embedding.embeddablehosts` drives the table; Actual: model stays empty and the table never appears.

**Found by:** glm-flash: MRV·high

#### A25 — Admin /admin/customize/embedding route crashes because it queries an unregistered Ember model type

**Location:** `app/assets/javascripts/discourse/app/routes/admin-customize-embedding.js:7–9`  ·  **Severity:** high  ·  **Judge confidence:** 0.62  ·  1 findings, 1 cells

**Why this is real.** The new admin route calls Ember Data with an unknown type, e.g. `model() { return this.store.find('embedding'); }`. Discourse's store resolves model classes via container lookup (`model:<type>`), and this PR does not add a corresponding `embedding` model file (e.g. `app/assets/javascripts/discourse/app/models/embedding.js`) or any registration, so the lookup fails and the route throws instead of rendering an empty page/tab. The file containing the store implementation is not in this PR’s diff, so verification relies on the reported behavior plus checking that no `embedding` model is added in the PR tree.

**How to replicate.** 1) Apply the PR and boot the app in development. 2) Log in as an admin and navigate directly to `/admin/customize/embedding` (or click the new Embedding tab under Admin > Customize if present). 3) Observe the route transition fails with a JS exception about missing/unknown model type `embedding` (container cannot resolve `model:embedding`). Expected: the page loads (even if empty) without throwing; Actual: the admin tab is unreachable due to the exception.

**Found by:** glm-flash: MRV·low

#### A26 — Delete action can fire multiple concurrent destroyRecord requests (no in-flight guard)

**Location:** `app/assets/javascripts/admin/components/embeddable-host.js.es6:43–51`  ·  **Severity:** medium  ·  **Judge confidence:** 0.78  ·  1 findings, 1 cells

**Why this is real.** In the `delete()` action, the code unconditionally calls `this.get('host').destroyRecord().then(...)` inside the confirm callback: `if (result) { this.get('host').destroyRecord().then(() => { ... }); }`. There is no state flag/check (e.g., `isDeleting`), no promise reuse, and no disabling of the delete control, so repeated clicks/confirms before the first request resolves can enqueue multiple `destroyRecord()` calls for the same record. This can lead to duplicate DELETE requests, inconsistent UI state, and avoidable backend errors (e.g., 404 on the second delete).

**How to replicate.** 1) In the admin UI where this component is used (embeddable host row), click the delete control for a host. 2) Before the first DELETE request finishes, trigger delete again (e.g., double-click the delete button quickly and confirm both bootbox dialogs, or click delete repeatedly if the UI allows). 3) Observe in the browser network panel that multiple DELETE requests are sent for the same host. Expected: once deletion is initiated, subsequent delete attempts are blocked/disabled until completion; Actual: multiple concurrent deletions can be initiated, potentially causing errors or double-remove logic.

**Found by:** sonnet: MRV·low

#### A27 — Unhandled promise rejection when saving admin embedding settings (update promise not handled)

**Location:** `app/assets/javascripts/admin/controllers/admin-embedding.js.es6:6–7`  ·  **Severity:** medium  ·  **Judge confidence:** 0.62  ·  1 findings, 1 cells

**Why this is real.** The reported code calls `embedding.update({ ... })` (around line 6) but does not return it or attach any `.then(...)`/`.catch(...)`/`await` handling. If the update request fails (e.g., server returns 4xx/5xx or the network errors), the promise rejection is unhandled and the controller never shows an error to the user. The PR diff was not provided for this file, so this verification relies on the reviewers' referenced line and the described missing promise handling at that call site.

**How to replicate.** In the admin UI page that uses `admin-embedding` controller, attempt to save embedding settings while forcing the request to fail (e.g., temporarily break the endpoint, return 500, or go offline in DevTools). Expected: the UI shows an error/flash explaining the save failed and no console errors. Actual: a console "Unhandled Promise Rejection" occurs and the user receives no clear failure feedback (save appears to silently fail).

**Found by:** opus: CE·medium

#### A28 — Embeddable hosts table header renders even when list is empty due to truthy empty array in Ember {{if}}

**Location:** `app/assets/javascripts/admin/templates/embedding.hbs:1–12`  ·  **Severity:** low  ·  **Judge confidence:** 0.74  ·  1 findings, 1 cells · ⚠️ **no harness cell found this**

**Why this is real.** The template reportedly guards the embeddable-hosts table with `{{#if embedding.embeddablehosts}} ... {{/if}}`. In Ember/Handlebars, an empty array is still truthy, so when `embedding.embeddablehosts` is `[]` (hydrated but empty), the block renders, showing the table/header with no rows. The PR diff does not include this file, so this verification relies on the reported code path and Ember truthiness semantics.

**How to replicate.** 1) Ensure the Embeddable Hosts list is empty (no hosts configured) but the property is present as an empty array (typical after hydration). 2) Navigate to the admin embedding page that uses `admin/templates/embedding.hbs`. 3) Actual: the embeddable-hosts table header/structure renders with no rows underneath. Expected: the entire table (including header) should be hidden when there are zero hosts (e.g., using `{{#if embedding.embeddablehosts.length}}` or an `{{#each}}`-based empty state).

**Found by:** **no harness cell** — vanilla only: glm-flash

#### A29 — Embed allowlist check does not scope requested topic/embed_url to the referer host's permitted category

**Location:** `app/controllers/embedcontroller.rb:61–75`  ·  **Severity:** high  ·  **Judge confidence:** 0.63  ·  1 findings, 1 cells

**Why this is real.** The reported issue is that `hostallowed?` only validates that the request `Referer` matches an allowed/embeddable host, but does not verify that the requested `embed_url`/`topic_id` belongs to a topic/category configured for that specific host. As a result, once any host is on the allowlist, it can request embeds for topics associated with other embeddable hosts/categories (authorization bypass via mismatched scoping). This verification is based on the report because `embedcontroller.rb` is not included in this PR’s diff, so the exact lines must be confirmed by inspecting the post-PR file around line ~61.

**How to replicate.** 1) Configure Discourse embedding with at least two allowed embeddable hosts (e.g., hostA.com -> Category A, hostB.com -> Category B) and ensure both are enabled. 2) On hostA.com, create an embed request pointing to a topic in Category B (or directly request the embed endpoint with `topic_id`/`embed_url` for a Category B topic while sending a `Referer: https://hostA.com/...`). 3) Expected: the controller rejects the request because hostA is not authorized for that topic/category. Actual (per report): the request succeeds because only the referer host is checked; the topic/embed_url is not constrained to hostA’s category mapping.

**Found by:** opus: CE·medium

#### A30 — (untitled)

**Location:** `?`  ·  **Severity:** ?  ·  **Judge confidence:** 0.00  ·  1 findings, 1 cells

**Found by:** fable: CE·medium

#### A31 — Migration splits embeddable host list on newlines instead of pipe delimiter, losing hosts

**Location:** `db/migrate/20150818190757createembeddablehosts.rb:22–31`  ·  **Severity:** high  ·  **Judge confidence:** 0.60  ·  1 findings, 1 cells

**Why this is real.** The migration reads the existing SiteSetting value and splits it using a newline delimiter (e.g., `...split("\n")` around line 22), but Discourse list-type settings are persisted pipe-delimited (per `app/models/sitesetting.rb` using `setting.split('|')`). If the stored value is `a.com|b.com`, splitting on `\n` produces a single element `"a.com|b.com"`, so only one EmbeddableHost row is created with an invalid host string. The migration then deletes/clears the original setting value (reported at line 31), making the data loss permanent after the migration runs.

**How to replicate.** 1) Before running the migration, set the `embeddable_hosts` site setting through the list editor to two hosts (e.g., enter `a.com` and `b.com`), which persists as `a.com|b.com`.
2) Run the migration that creates EmbeddableHost records.
3) Inspect the created rows: expected two rows (`a.com` and `b.com`), but actual is one row with `host = "a.com|b.com"`.
4) Verify that embedding for either `a.com` or `b.com` no longer matches, and that the original `embeddable_hosts` setting has been cleared/removed so the original list cannot be recovered automatically.

**Found by:** fable: MRV·medium

#### A32 — EmbeddableHost missing presence validation for non-null category_id causes DB NotNullViolation

**Location:** `app/models/embeddable_host.rb:1–30`  ·  **Severity:** medium  ·  **Judge confidence:** 0.62  ·  1 findings, 1 cells · ⚠️ **no harness cell found this**

**Why this is real.** The reports indicate the `embeddable_hosts.category_id` column is defined with `null: false` at the database level, but the `EmbeddableHost` model does not validate presence of `category_id` (e.g., it may validate other fields like `host` but lacks `validates :category_id, presence: true`). This mismatch means that creation/update paths that bypass controller strong-params (e.g., Rails console, seeds, background jobs, tests, or any code doing `EmbeddableHost.create!(host: ...)` without `category_id`) will raise an `ActiveRecord::NotNullViolation` instead of returning a clean model validation error. The file is not part of this PR’s diff, so verification relies on reading the current model validations and the schema/migration for the `embeddable_hosts` table.

**How to replicate.** 1) Open a Rails console in the app. 2) Run `EmbeddableHost.create!(host: "example.com")` (omit `category_id`). 3) Actual: the save hits the DB and raises `ActiveRecord::NotNullViolation` (or similar) because `category_id` is NULL. 4) Expected: `EmbeddableHost` should fail validation with an error on `category_id` (e.g., `embeddable_host.errors[:category_id]` includes "can't be blank") and not raise a database exception.

**Found by:** **no harness cell** — vanilla only: opus

### Golden-duplicates removed (would double-count)

- **duplicate of golden #1** — “The update and destroy methods in Admin::EmbeddableHostsController do not validate the existence of the EmbeddableHost record retrieved by ID. If EmbeddableHost…”
  - cluster: Admin::EmbeddableHostsController update/destroy nil-dereference on missing record or params causes 500 (`app/controllers/admin/embeddable_hosts_controller.rb`), 139 findings, 46 cells
- **duplicate of golden #6** — “The migration accesses execute(...)[0]['id'] without checking if the query returned any rows, which causes a crash when no embed_category setting exists. This c…”
  - cluster: Migration assumes site_settings rows exist and dereferences execute(...)[0], crashing on nil (`db/migrate/20150818190757createembeddablehosts.rb`), 119 findings, 40 cells
- **duplicate of golden #3** — “Because this migration inserts embeddable_hosts rows with raw SQL, any existing embeddable_hosts values that include http:// or /https:// or path segments won’t…”
  - cluster: Migration backfills embeddable hosts verbatim (including schemes/paths), breaking hostname-only lookups (`db/migrate/20150818190757createembeddablehosts.rb`), 41 findings, 21 cells
- **duplicate of golden #0** — “The EmbeddableHost model's before_validation callback calls self.host.sub! to strip http://, https://, and path segments, but if self.host is nil, this raises N…”
  - cluster: before_validation mutates host with sub! causing NoMethodError when host is nil (`app/models/embeddablehost.rb`), 22 findings, 15 cells
- **duplicate of golden #2** — “record_for_host compares lower(host) = ? but does not normalize the parameter’s case, so mixed‑case referer hosts may fail to match even though comparison inten…”
  - cluster: EmbeddableHost lookup is case-sensitive because only DB side is lowercased (`app/models/embeddablehost.rb`), 7 findings, 4 cells

---

## PR 8 — 21 additional real bugs (6 goldens; 7 golden-duplicates removed)
(<https://github.com/ai-code-review-evaluation/discourse-graphite/pull/8>)

### Additional bugs (evidence cards)

#### A1 — Updating a group without `visible` param unintentionally flips visibility to false

**Location:** `app/controllers/admin/groups_controller.rb:170–175`  ·  **Severity:** high  ·  **Judge confidence:** 0.62  ·  150 findings, 53 cells

**Why this is real.** The update logic reportedly assigns visibility unconditionally: `group.visible = params[:visible] == "true"`. When `params[:visible]` is absent (nil), this expression evaluates to `false`, so any PATCH/PUT that updates other fields will silently set `group.visible` to false. This is a functional behavior change (state corruption) compared to guarded assignments used for other optional params.

**How to replicate.** 1) Pick an existing group that is currently visible (public). 2) Send `PATCH /admin/groups/:id.json` with a payload that updates some other attribute (e.g., `{ "name": "new-name" }`) and omit the `visible` parameter entirely. 3) Expected: visibility remains unchanged. Actual: the group becomes invisible because `params[:visible]` is nil and the controller sets `visible` to false.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·medium, MRV·high, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·low, CE·medium, MRV·high, MRV·medium; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A2 — Unvalidated limit/offset in GroupsController#members allows negative SQL OFFSET and unbounded LIMIT

**Location:** `app/controllers/groups_controller.rb`  ·  **Severity:** high  ·  **Judge confidence:** 0.62  ·  147 findings, 55 cells

**Why this is real.** The clustered reports consistently describe `members` reading pagination directly from request params (e.g., `limit = params[:limit].to_i` and `offset = params[:offset].to_i`) and passing them straight into an ActiveRecord query via `.limit(limit).offset(offset)` with no clamping/validation. A negative `offset` is then sent to PostgreSQL as `OFFSET -1`, which raises a SQL error and yields a 500 response; similarly, an arbitrarily large `limit` can force huge queries/serialization. The PR diff does not include this file, so exact line numbers cannot be cross-checked here; verification requires opening the post-PR `GroupsController#members` implementation and confirming the unvalidated param-to-query flow.

**How to replicate.** 1) Run the app and ensure there is a group with members. 2) Send a request to the members endpoint (e.g., `GET /groups/<group_id>/members.json?offset=-1`). 3) Observe actual behavior: the request triggers a server error (500) due to invalid SQL OFFSET. Expected behavior: the controller should reject invalid pagination (400) or clamp offset to 0. 4) Also test `GET /groups/<group_id>/members.json?limit=1000000` and observe excessive query/serialization time or resource usage; expected behavior is enforcing a reasonable maximum limit.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; astra: CE·low

#### A3 — Admin::GroupsController#add_members splits usernames without trimming, causing spaced names to be skipped while still returning success

**Location:** `app/controllers/admin/groups_controller.rb:71–86`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  51 findings, 27 cells

**Why this is real.** The add_members action (reported at ~line 71) takes the raw string and does `params[:usernames].split(",")` and then looks up each entry via an exact-match finder (e.g., `User.find_by_username(username)`), but it does not `strip` or reject blanks. As a result, input like "bob, alice" produces a second token " alice" (leading space), which will not match any real username and is silently skipped; the action still returns a success JSON response, giving no indication that one or more requested users were not added. The PR diff does not include this file, so this verification relies on the reviewers’ consistent line-referenced reports; a human can confirm by reading the add_members loop and observing the missing `strip`/blank filtering and unconditional success response.

**How to replicate.** 1) In the admin UI or via HTTP, call the group member add endpoint (e.g., POST /admin/groups/:id/add_members) with params user names string set to `"bob, alice"` (note the space after the comma).
2) Ensure both users exist with usernames exactly `bob` and `alice`.
3) Observe: only `bob` is added; `alice` is not added because the lookup is performed on the literal token `" alice"`.
4) The controller still returns a success JSON response (no error/warning), so the UI/API consumer cannot detect the partial failure from the response.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·medium; glm-flash: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, MRV·low, MRV·medium; terra: MRV·high; astra: MRV·high

#### A4 — Admin group creation drops submitted aliaslevel and saves default instead

**Location:** `app/controllers/admin/groups_controller.rb:22–35`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  48 findings, 29 cells

**Why this is real.** In the `create` action, the new group is instantiated using only `params[:name]` and `params[:visible]` (e.g., `Group.new(name: params[:name], visible: params[:visible])` / equivalent assignments) and then saved, but there is no read/assignment of `params[:aliaslevel]`. As a result, even if the client submits a non-default alias level, it is silently ignored and the persisted record retains the model/database default after save/reload. The PR diff for this file is not present in the provided patch, so this verification relies on the reported line reference and the described controller behavior.

**How to replicate.** 1) In the admin UI (or via HTTP), create a new group and set a non-default alias level in the form.
2) Submit the create request; ensure the request payload includes `aliaslevel=<non-default>`.
3) After creation, reload the group (or fetch it via API/admin page) and compare the saved alias level.
Expected: the group’s alias level matches the submitted value. Actual: the alias level is the default (the submitted `aliaslevel` was ignored during creation).

**Found by:** opus: CE·medium, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium; astra: CE·low

#### A5 — PATCH updates unintentionally hide groups when `visible` param is omitted (and legacy membership changes are ignored)

**Location:** `app/controllers/admin/groupscontroller.rb:34–36`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  96 findings, 38 cells

**Why this is real.** Multiple reports point to an unconditional assignment in the update path around line 34: `group.visible = params[:visible] == "true"`. When a PATCH request omits the `visible` key (common for partial updates and legacy membership PATCHes), `params[:visible]` is nil so the expression evaluates to false, silently flipping an existing visible group to invisible; the same legacy requests may include `changes.add`/`changes.delete`, which the ordinary update handler does not process, so membership changes are dropped while the request still succeeds. The PR diff is not available here, so this verification relies on the consistent line-specific reports.

**How to replicate.** 1) Ensure an existing group has `visible = true`. 2) Send `PATCH /admin/groups/:id` with a body that updates something other than visibility (e.g., name) and omit `visible` entirely (or send a legacy membership payload like `{ changes: { add: ["user1"] } }` without `visible`). 3) Observe: expected behavior is that visibility remains unchanged (and membership changes apply for the legacy payload). Actual behavior is that `visible` becomes false (group is hidden) and, for the legacy payload, membership does not change even though the response indicates success.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; sonnet: MRV·high, MRV·low; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; terra: CE·medium, MRV·high; astra: CE·low, MRV·high, MRV·low

#### A6 — Admin group add/remove member actions drop the AJAX promise, making failures silent and leaving stale UI state

**Location:** `app/assets/javascripts/admin/controllers/admin-group.js.es6:56–75`  ·  **Severity:** medium  ·  **Judge confidence:** 0.77  ·  35 findings, 25 cells

**Why this is real.** In the new actions, the controller triggers the mutation but does not return or handle the promise: inside `removeMember` it calls `self.get("model").removeMember(member);`, and in `addMembers` it calls `this.get("model").addMembers(this.get("usernames"));` without `return` or any `.catch(...)`/error handling. If the underlying AJAX request rejects (e.g., 422/404), the rejection is unhandled and no error feedback is shown, so the admin cannot tell the operation failed and the member list can remain unchanged/stale despite the UI action having been invoked.

**How to replicate.** 1) In the admin UI, open a group where membership mutations can fail (e.g., an automatic group, or attempt to remove a user who is not actually a member). 2) Click “Remove member” (confirm the bootbox) or use “Add members” with a username that triggers a server-side validation error. 3) Observe that no error is displayed to the admin and the UI provides no failure indication; the membership list remains unchanged even though the action was executed. Expected: the action should surface the failure (and/or only update/reload the member list after the promise resolves), and failures should be catchable/handled by callers.

**Found by:** opus: CE·high, CE·medium, MRV·low, MRV·medium; sonnet: MRV·high, MRV·medium; glm-flash: MRV·high, MRV·medium; glm-vis: MRV·high, MRV·medium; sol: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; terra: MRV·high, MRV·low, MRV·medium; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A7 — Admin::GroupsController#remove_member deletes association with userid (integer) and persists removal before save, causing exceptions or partial failures

**Location:** `app/controllers/admin/groupscontroller.rb:73–82`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  28 findings, 22 cells

**Why this is real.** The controller code reportedly calls `group.users.delete(userid)` inside the member-removal action (around lines 73–82). In ActiveRecord, `has_many` association `delete` is intended to take model instances (or relation), and passing a raw integer id can raise `ActiveRecord::AssociationTypeMismatch` instead of removing the user. Additionally, the removal via `group.users.delete(...)` is applied immediately to the join table, but the action then uses `group.save` as the success signal—so if `group.save` fails (422), the membership may already have been removed, creating an inconsistent/partial update.

**How to replicate.** 1) Find the admin endpoint/action in `Admin::GroupsController` responsible for removing a member (the one containing `group.users.delete(userid)` and checking `group.save`). 2) Trigger it with a request where `userid` is an integer param (e.g., remove a real user from a real group). Expected: member is removed cleanly (200/204) and counters/callbacks remain consistent. Actual: (a) it may raise `ActiveRecord::AssociationTypeMismatch` and return 500, or (b) if `group.save` fails validations, the request returns 422 even though the membership was already deleted from the join table.

**Found by:** opus: CE·high, CE·low, CE·medium; sonnet: MRV·high, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·medium; glm-vis: CE·high, CE·medium, MRV·medium; sol: MRV·low, MRV·medium

#### A8 — Remove-member link wrongly shown for automatic groups due to `automatic` resolving in member item context

**Location:** `app/assets/javascripts/admin/templates/groupmember.hbs:1–6`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  26 findings, 19 cells

**Why this is real.** The template guards the remove link with `{{unless automatic}} ... {{action removemember this}} ... {{/unless}}`. In this template the rendering context is a single group member (a user), not the group itself, so `automatic` is not a property on the current context and resolves to `undefined`/falsey; as a result the `unless` condition always passes and the remove link renders even for automatic groups. This is functional breakage (wrong UI state and a failing action), not a style concern; the PR diff does not include this file, so this conclusion relies on the reported template contents and Ember/Handlebars context resolution rules.

**How to replicate.** 1) In the admin UI, open an automatic group (e.g., a system/automatic group) and navigate to its Members list. 2) Observe that each member row shows a “remove” control/link even though automatic groups should not allow manual removals. 3) Click the remove control: expected behavior is that no remove option is available (or it is disabled/hidden) for automatic groups; actual behavior is that the UI offers removal and the request fails (commonly a 422 from the server) because automatic group membership cannot be removed.

**Found by:** opus: CE·low, MRV·low; sonnet: CE·high, CE·low, MRV·low; glm-flash: CE·high, CE·low, CE·medium; glm-vis: CE·low, MRV·low, MRV·medium

#### A9 — add_members crashes with 500 when `usernames` param is an array (calls `.split` on Array)

**Location:** `app/controllers/admin/groups_controller.rb:71–71`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  22 findings, 17 cells

**Why this is real.** The `add_members` action calls `params.require(:usernames).split(",")` (as referenced by multiple reports at/around line 71). `params.require(:usernames)` can legitimately be an Array when the client submits `usernames[]=a&usernames[]=b` (or JSON `{"usernames":[...]}`), and Arrays do not implement `split`, causing a `NoMethodError` and an unhandled 500 instead of a validation error (400/422). The PR diff provided here does not include this file, so this verification relies on the consistent line-referenced evidence from the reports.

**How to replicate.** 1) Locate `app/controllers/admin/groups_controller.rb` and find the `add_members` (or similarly named) action near line 71. Confirm it does `params.require(:usernames).split(",")`.
2) Trigger the endpoint as an admin (route typically resembles POST `/admin/groups/:id/members` or `/admin/groups/:id/add-members`; use the controller action name to confirm the exact path).
3) Send `usernames` as an array (e.g., form-encoded `usernames[]=alice&usernames[]=bob` or JSON body `{ "usernames": ["alice", "bob"] }`).
Expected: request is handled or rejected with 400/422 and a helpful message about invalid parameter type.
Actual: Rails raises `NoMethodError: undefined method 'split' for Array` and returns 500.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·low; sonnet: CE·medium; glm-flash: CE·high, CE·low, MRV·high, MRV·low, MRV·medium; glm-vis: CE·medium, MRV·medium; astra: MRV·low

#### A10 — Admin group addMembers leaves usernames input uncleared, causing stale re-submissions (even after switching groups)

**Location:** `app/assets/javascripts/admin/controllers/admin-group.js.es6:61–66`  ·  **Severity:** medium  ·  **Judge confidence:** 0.86  ·  20 findings, 16 cells

**Why this is real.** In the new `addMembers` action the controller never resets the `usernames` property after a successful add: `// TODO: should clear the input` followed by `this.get("model").addMembers(this.get("usernames"));` with no subsequent `this.set("usernames", ...)` or other clearing logic. Because `usernames` is now a simple controller field (`usernames: null`) rather than being recomputed from `members`, its value persists across actions and potentially across group changes, so the same stale usernames can be re-submitted unintentionally.

**How to replicate.** 1) In the admin group UI, enter one or more usernames in the add-members input (bound to `usernames`). 2) Click "Add" and wait for the request to succeed. 3) Observe the input still contains the same usernames (expected: it should clear/reset). 4) Click "Add" again (or navigate/switch to another group and click "Add"): actual behavior re-sends the same usernames again; expected behavior is that the field would be empty, preventing accidental duplicate or cross-group additions.

**Found by:** opus: MRV·high; glm-flash: CE·high, MRV·high; glm-vis: CE·high, CE·low, CE·medium, MRV·high; sol: CE·high, CE·medium

#### A11 — Group members reload/pagination uses live-edited group name, breaking after unsaved rename

**Location:** `app/assets/javascripts/discourse/models/group.js:23–52`  ·  **Severity:** high  ·  **Judge confidence:** 0.82  ·  10 findings, 9 cells

**Why this is real.** In `findMembers`, the members URL is built from the mutable, two-way-bound `name` field: `Discourse.ajax('/groups/' + this.get('name') + '/members.json', ...)`. However membership mutations use the persisted numeric id (`/admin/groups/` + `this.get('id')` + `/members.json`) and then call `self.findMembers();` to refresh. If an admin edits the group name in the UI but hasn’t saved yet, `this.get('name')` no longer matches the server’s current group slug, so the refresh/pagination request targets the wrong (or non-existent) group and fails or shows another group’s members.

**How to replicate.** 1) Go to the admin group editor for an existing group that has members. 2) In the name field, type a new name but do NOT click Save. 3) Add a member (or remove an existing member). 4) Observe network requests: the add/remove hits `/admin/groups/<id>/members.json` successfully, then the UI triggers a reload via `findMembers()` which requests `/groups/<unsaved-new-name>/members.json?limit=...&offset=...`. Expected: refreshed member list for the original group. Actual: 404 / empty list / or members from a different group if the unsaved name matches another group, leaving the UI stale or misleading.

**Found by:** opus: CE·high; glm-flash: MRV·high; glm-vis: CE·medium; astra: CE·high, CE·medium, MRV·high, MRV·low

#### A12 — Admin::GroupsController specs hardcode group id=1, implicitly depending on seeded automatic group

**Location:** `spec/controllers/admin/groups_controller_spec.rb:38–125`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  7 findings, 5 cells

**Why this is real.** The new/modified specs issue requests like `xhr :put, :addmembers, groupid: 1, usernames: "l77t"` and also directly reference `Group.find(1)` / params `id: 1`, assuming the group with id 1 exists and is an automatic group. This makes the tests depend on seed/fixture ordering: on a DB where id 1 is missing (or not automatic), the controller will raise/return not found or take a different code path, so the asserted 422 behavior is either never reached or the spec can pass/fail for the wrong reason. This is a real correctness bug in the test suite (nondeterministic/fixture-coupled), not a style issue; the evidence comes from the clustered reports since the relevant lines are in the spec file rather than the PR’s main code changes.

**How to replicate.** 1) Inspect `spec/controllers/admin/groups_controller_spec.rb` around the referenced lines and confirm the hardcoded `groupid: 1` / `id: 1` and any `Group.find(1)` usage in the "automatic group" related examples.
2) Run only this spec file in an environment where the test DB is not pre-seeded with an automatic group at id=1 (e.g., disable seeds/fixtures, or truncate then create a non-automatic group first so it gets id=1).
Expected: the spec should deterministically exercise the automatic-group guard and assert 422.
Actual: the request will 404/raise `ActiveRecord::RecordNotFound` (no id=1), or it will hit the non-automatic path (id=1 exists but isn’t automatic), making the asserted 422 either fail or be meaningless.

**Found by:** opus: MRV·high; glm-flash: MRV·low

#### A13 — Admin group addmembers accepts unbounded comma-separated usernames, causing N+1 queries and long-running request

**Location:** `app/controllers/admin/groupscontroller.rb:71–86`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  5 findings, 5 cells

**Why this is real.** The addmembers action reportedly does `params.require(:usernames).split(",")` and then iterates the resulting array, doing a per-username lookup (e.g., `User.find_by_username(...)`) and then a per-username add/insert (e.g., `@group.add(user)`), with no cap on the number of elements. Because there is no length limit on the `usernames` param, a single request containing thousands of comma-separated names triggers thousands of sequential DB operations in one controller action, which can tie up a web worker and database. Reports also note usernames are not stripped (e.g., " bob"), leading to missed lookups and silent skipping; this is input-handling logic, not a style issue. (The file is not in this PR diff, so verification relies on the reported code pattern at/around line 71.)

**How to replicate.** 1) As an authenticated admin, send a POST/PUT request to the group add-members endpoint that hits `Admin::GroupsController#addmembers` with `usernames` set to a very large comma-separated list (e.g., 10,000 entries like `user1,user2,...`). 2) Observe in logs/APM that the request runtime grows linearly and executes one user lookup plus one group-membership insert per username (thousands of queries/operations). Expected: the controller should reject or cap overly large lists (and normalize/strip whitespace) to prevent a single request from consuming excessive time/resources; actual: it attempts to process the entire list serially and may skip whitespace-padded usernames.

**Found by:** opus: CE·medium, MRV·medium; glm-flash: CE·medium; glm-vis: CE·low

#### A14 — Admin::GroupsController spec regression: removed coverage for add/remove member edge cases and paginated members meta shape

**Location:** `spec/controllers/admin/groups_controller_spec.rb:74–130`  ·  **Severity:** medium  ·  **Judge confidence:** 0.66  ·  5 findings, 4 cells

**Why this is real.** The reports point to a deletion in `spec/controllers/admin/groups_controller_spec.rb` around lines 74-130 where existing examples asserting "silent success" when adding non-existent usernames and removing non-members were removed and not replaced with equivalent specs for the new add/remove endpoints or the new paginated members response shape. This leaves key controller branches (unknown usernames, removing a non-member, adding an already-present member) and the `members + meta(total/limit/offset)` contract untested, so regressions in those code paths will not be caught by CI. This is a real, concrete test-suite defect (loss of assertions) rather than a style concern; it directly reduces coverage of behavior that the client pagination logic depends on.

**How to replicate.** 1) Open the post-PR `spec/controllers/admin/groups_controller_spec.rb` and inspect the section around lines ~74-130; confirm the prior examples covering (a) adding non-existent users and (b) removing non-members are no longer present, and that there are no new examples asserting the `members` response includes `meta.total`, `meta.limit`, and `meta.offset`.
2) Confirm by running `RAILS_ENV=test bundle exec rspec spec/controllers/admin/groups_controller_spec.rb` and noting there are no failing tests despite missing assertions.
3) Demonstrate impact: temporarily modify the controller to (a) error on unknown usernames or (b) omit `meta.total/limit/offset` from the members response; re-run the spec file—expected: tests should fail; actual: they will not (or will fail only for unrelated reasons), proving the behavior is currently unprotected.

**Found by:** glm-vis: MRV·medium

#### A15 — Group name is stripped on create but not on update, allowing whitespace-padded names

**Location:** `app/controllers/admin/groups_controller.rb:40–45`  ·  **Severity:** medium  ·  **Judge confidence:** 0.78  ·  4 findings, 4 cells

**Why this is real.** In the create path the controller normalizes the incoming name with `(params[:name] || '').strip`, but in the update path it assigns the raw parameter: `group.name = params[:name]` (no `strip`). This inconsistency means an admin can rename an existing group to `' bob '` and the update endpoint will attempt to persist the whitespace-padded name, either storing a dirty value or causing confusing validation failures. This is a real behavioral bug (inconsistent normalization between endpoints), not a style issue; the PR diff doesn’t include this file, so this verification relies on the reported code lines.

**How to replicate.** 1) Create a group via the admin UI/API with name `' bob '`; creation normalizes to `'bob'` due to `.strip`, so it succeeds with name `bob`.
2) Edit/rename that same group via the update endpoint, submitting name `' bob '` (leading/trailing spaces).
Expected: update behaves like create (normalizes to `bob`) and round-trips consistently.
Actual: update does not strip whitespace (`group.name = params[:name]`), so the group may be saved as `' bob '` or the update may fail validation with an error that doesn’t match create behavior, breaking consistency and potentially downstream features that assume normalized group names.

**Found by:** glm-vis: CE·high, CE·medium, MRV·low

#### A16 — Admin group edit form implicitly submits on Enter, causing full page reload and lost unsaved changes

**Location:** `app/assets/javascripts/discourse/templates/admin/group.hbs:1–53`  ·  **Severity:** high  ·  **Judge confidence:** 0.84  ·  4 findings, 4 cells

**Why this is real.** The template wraps editable inputs in a plain HTML form (`<form class="form-horizontal">`, line 1) but does not attach any submit handler (e.g., no `{{action ... on="submit"}}`) to prevent native submission. Inside that form are text inputs like `{{text-field name="name" ...}}` (line 8) and `{{user-selector ...}}` (line 28); pressing Enter in these fields triggers the browser’s implicit form submit to the current URL, causing a full page reload. The buttons also omit explicit `type="button"` (e.g., ` <button {{action "save"}} ...>` on line 47), so the form has no safe default behavior for submission via keyboard.

**How to replicate.** 1) Go to the Admin → Groups page and open an existing group for editing. 2) Change the group name in the name text field (or type a username in the add-members selector). 3) Press Enter while focused in that input. Expected: Ember handles the action (or at least no navigation occurs) and the page remains in-place. Actual: the browser performs a native form submission (GET to the current URL), the page reloads, and any unsaved edits (name/visibility/alias level) are discarded.

**Found by:** glm-vis: CE·high, CE·medium, MRV·high

#### A17 — Admin addmembers can re-add existing user and raise RecordNotUnique, leaving partial membership updates

**Location:** `app/controllers/admin/groups_controller.rb:-1–-1`  ·  **Severity:** high  ·  **Judge confidence:** 0.66  ·  1 findings, 1 cells

**Why this is real.** The clustered reports consistently describe `addmembers` iterating over a comma-separated username list and calling `group.add(user)` unconditionally (i.e., without checking whether the user is already a member). In Discourse-like schemas the group membership join table has a uniqueness constraint (e.g., `group_id,user_id`), so calling `group.add(user)` for an existing member attempts a duplicate insert and raises `ActiveRecord::RecordNotUnique`, producing a 500. Because this happens mid-loop, earlier usernames may already have been inserted, causing a partially-applied update with no clear admin feedback. The referenced code is not included in this PR diff, so verification is by inspecting the current `addmembers` implementation for an unconditional `group.add(user)` inside the usernames loop and lack of rescue/transactionality.

**How to replicate.** 1) In the admin UI/API, pick a group that already contains user A. 2) Trigger the add-members action (e.g., POST to the addmembers endpoint) with `usernames` including A (optionally along with other valid users like `A,B`). 3) Observe that the request returns HTTP 500 (from `ActiveRecord::RecordNotUnique`) when it hits A if `group.add(user)` tries to insert a duplicate join row; if multiple usernames were provided, users earlier in the list may have been added successfully before the failure. Expected behavior is idempotent adds (no error when adding an existing member) and/or an all-or-nothing update with a clear response.

**Found by:** glm-vis: MRV·medium

#### A18 — Label `for="name"` does not match the Ember `text-field` input id, breaking label-to-input association

**Location:** `N/A (template containing the new form markup is not present in the provided PR diff; issue is identified from the report only)`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  1 findings, 1 cells

**Why this is real.** The reported template adds a label like `<label for="name">` but renders the field with `{{text-field name="name"}}`. In Ember/Discourse, `text-field` does not automatically set the DOM `id` from the `name` attribute; it typically generates an auto id (e.g., `ember123`). This means the label’s `for="name"` references no element id, so clicking the label won’t focus the input and assistive tech cannot programmatically associate them.

**How to replicate.** 1) Navigate to the page/dialog that contains the new form.
2) Inspect the rendered DOM: find the `<label for="name">` and the `<input ...>` produced by `{{text-field name="name"}}`.
3) Observe the input has an auto-generated `id` (e.g., `emberNNN`) rather than `id="name"`.
4) Click the “Name” label: expected focus moves to the corresponding input; actual behavior is no focus change because the `for` target id does not exist.

**Found by:** glm-vis: MRV·high

#### A19 — Admin groups API no longer exposes GET /admin/groups/:id/users (route removed without read replacement)

**Location:** `config/routes.rb:1–1`  ·  **Severity:** high  ·  **Judge confidence:** 0.42  ·  1 findings, 1 cells

**Why this is real.** The clustered reports indicate that the admin group routing previously included a read endpoint like `get "users"` under `/admin/groups/:id/...`, but post-PR it has been removed and replaced only with write routes for membership (e.g., `put "members"` / `delete "members"`). With no remaining GET route for the member list, any existing client calling `/admin/groups/:id/users` will now hit a routing failure (404) even though it previously returned the group’s users. The PR evidence pack notes the relevant file/lines are not present in the PR diff, so verification requires inspecting the post-PR `config/routes.rb` directly for the missing `get "users"` route under the admin/groups resource.

**How to replicate.** 1) In the post-PR code, open `config/routes.rb` and locate the `namespace :admin` / `resources :groups` block. 2) Confirm there is no `get "users"` member route (or equivalent) for groups, and only `put/delete "members"` exist. 3) Run the app (or use `rails routes`) and request `GET /admin/groups/<id>/users.json` (or the non-json variant used previously). Expected (pre-PR): 200 with list of users in the group. Actual (post-PR): 404 / no route matches.

**Found by:** glm-flash: MRV·medium

#### A20 — Admin group template bypasses userCountDisplay and renders raw zero user_count

**Location:** `admin/templates/group.hbs:14–14`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  1 findings, 1 cells

**Why this is real.** The model defines a dedicated presentation helper `userCountDisplay` with the explicit intent to hide ugly zeros: `// don't display zero its ugly` and `if (c > 0) { return c; }` (group.js around lines 12-16 in the PR). However, the admin group template reportedly renders the raw count via `{{usercount}}` (admin/templates/group.hbs:14) instead of using `userCountDisplay`, so groups with `user_count = 0` will display “(0)” and any UI derived from that raw value (like pagination labels) can show “0/0”. This creates two divergent display paths for the same datum (template vs. computed property), making the zero-hiding logic ineffective in the admin view and prone to drift.

**How to replicate.** 1) In the admin UI, create or open a group that has no members (user_count == 0). 2) Navigate to the admin group detail page that uses `admin/templates/group.hbs`. 3) Observe the member count / pagination area: expected behavior (per `userCountDisplay`) is to show nothing for the count when it is zero; actual behavior is that the template shows the raw `{{usercount}}` value, displaying “(0)” and potentially “0/0” pagination.

**Found by:** glm-vis: CE·medium

#### A21 — (untitled)

**Location:** `?`  ·  **Severity:** ?  ·  **Judge confidence:** 0.00  ·  1 findings, 1 cells

**Found by:** glm-vis: CE·high

### Golden-duplicates removed (would double-count)

- **duplicate of golden #3** — “The `totalPages` calculation using `Math.floor(user_count / limit) + 1` produces an extra page when `user_count` is an exact multiple of `limit`, leading to inc…”
  - cluster: Admin group members pagination creates a phantom extra page when member count is an exact multiple of page size (`app/assets/javascripts/admin/controllers/admin-group.js.es6`), 63 findings, 26 cells
- **duplicate of golden #0** — “ The findMembers() call is now asynchronous and unhandled. The controller may not have member data immediately available, creating a race condition.…”
  - cluster: Out-of-order findMembers() responses can overwrite newer pagination state and show the wrong member page (`app/assets/javascripts/discourse/models/group.js`), 44 findings, 29 cells
- **duplicate of golden #1** — “In the next action, capping the next offset at user_count can produce an empty page (e.g., total equal to limit results in offset == total, showing 2/2 with no …”
  - cluster: Removing the only member on the last page reloads members with a stale, now-out-of-range offset and shows an empty page (`app/assets/javascripts/discourse/models/group.js`), 42 findings, 29 cells
- **duplicate of golden #0** — “ The findMembers() call is now asynchronous and unhandled. The controller may not have member data immediately available, creating a race condition.…”
  - cluster: Group members fetch is fired-and-forgotten in route, so errors are silently swallowed and UI can show empty/stale members (`app/assets/javascripts/discourse/routes/group-members.js.es6`), 30 findings, 22 cells
- **duplicate of golden #4** — “Expected to return a value at the end of function - code paths without explicit returns will return undefined…”
  - cluster: group.findMembers returns undefined on empty name instead of a promise (`app/assets/javascripts/discourse/models/group.js`), 2 findings, 2 cells
- **duplicate of golden #5** — “The route provides the group's ID in params[:id], but the code attempts to read it from params[:group_id], causing the action to fail. This results in a broken …”
  - cluster: Admin group addmembers route passes :id but controller requires :groupid, causing 400 ParameterMissing (`config/routes.rb`), 1 findings, 1 cells
- **duplicate of golden #1** — “In the next action, capping the next offset at user_count can produce an empty page (e.g., total equal to limit results in offset == total, showing 2/2 with no …”
  - cluster: `next` pagination can set offset to `user_count`, yielding an empty/out-of-range page (`app/assets/javascripts/admin/controllers/admin-group.js.es6`), 1 findings, 1 cells

---

## PR 14740 — 33 additional real bugs (6 goldens; 9 golden-duplicates removed)
(<https://github.com/calcom/cal.com/pull/14740>)

### Additional bugs (evidence cards)

#### A1 — Calendar sync uses requesting user's credentials instead of the booking organizer's

**Location:** `packages/trpc/server/routers/viewer/bookings.ts`  ·  **Severity:** high  ·  **Judge confidence:** 0.62  ·  141 findings, 55 cells

**Why this is real.** All deduplicated reports describe the same concrete defect: the calendar update path constructs an EventManager (or equivalent calendar client) from `ctx.user` (the authenticated caller) rather than from `booking.user` (the organizer/owner of the calendar event). That means calendar writes execute with the attendee’s OAuth credentials (or none), which either targets the wrong calendar account or fails authorization when trying to update the organizer’s existing event. The PR diff/line refs were not provided in the evidence pack, so this verification relies on the consistent cross-tool reports pointing to the `ctx.user` vs `booking.user` construction as the offending code.

**How to replicate.** 1) Create a booking where the organizer has a connected calendar integration (e.g., Google) and the attendee does not (or has a different Google account). 2) As the attendee (authenticated), call the booking update flow that triggers calendar synchronization (e.g., edit booking details / update attendees / reschedule, depending on the route used in the PR). 3) Observe that the server attempts to update the external calendar event using the attendee’s credentials; expected: organizer’s calendar event is updated via organizer credentials. Actual: the update fails with an auth/permissions error or updates/looks for an event in the attendee’s calendar account, leaving the organizer’s event unchanged while DB rows may already be updated.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; terra: MRV·high, MRV·low, MRV·medium; astra: MRV·high, MRV·low, MRV·medium

#### A2 — Non-atomic guest/attendee persistence causes DB/calendar divergence on calendar sync failure

**Location:** `unknown (reports did not include a file path; PR diff not provided in evidence pack)`  ·  **Severity:** high  ·  **Judge confidence:** 0.62  ·  130 findings, 55 cells

**Why this is real.** All deduplicated reports describe the same concrete defect mechanism: the code persists new booking attendees/guests to the database first, then performs an external calendar update/sync afterward, without a wrapping DB transaction and without any rollback/compensation if the calendar step fails. This creates a partial-success state where the DB is permanently mutated but the calendar event is not updated, and subsequent retries are rejected as duplicates because the DB already contains the guests. Because the evidence pack does not include the actual file/line references (and the relevant file is not in this PR’s diff), a human verifier must confirm by locating the handler/service that adds booking guests and checking that the DB write occurs before the provider calendar update and that failures in the calendar update do not revert the DB change.

**How to replicate.** 1) Find the API/handler that adds guests/attendees to an existing booking and triggers calendar synchronization. 2) Call it to add one or more new guest emails while ensuring the calendar provider update fails (e.g., revoke provider credentials, force the provider client to throw, or simulate a 5xx/network error). 3) Observe: request fails (or returns an error), but the booking’s guests/attendees are present in the database afterward. 4) Retry the same request with the same emails: expected behavior is a successful retry (or idempotent success) that results in calendar+DB consistency; actual behavior is rejection as “already present/duplicate” while the calendar event remains missing those attendees/notifications.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·medium, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; astra: CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A3 — addGuests input schema allows unbounded guests array (email/DB fan-out DoS vector)

**Location:** `apps/web/server/routers/viewer/bookings/addGuests.schema.ts:10–22`  ·  **Severity:** high  ·  **Judge confidence:** 0.62  ·  104 findings, 50 cells

**Why this is real.** The reported issue is that the Zod input schema defines `guests` as an array but does not apply any upper-bound constraint (no `.max(...)`). In practice this looks like `guests: z.array(...)` (or equivalent) without a length cap, meaning a single authenticated request can submit thousands of guest emails. Even though this PR’s diff does not include the file, a human can confirm by opening the schema and verifying there is no `.max()` on the `guests` array, enabling unbounded downstream inserts/calendar payload growth and outbound email fan-out.

**How to replicate.** 1) Locate the add-guests mutation that uses `addGuests.schema.ts` (server-side) and confirm `guests` is accepted as an array from the client.
2) Send a single authenticated request to that mutation with `guests` containing a very large list (e.g., 5,000–20,000 unique email strings).
3) Observe actual behavior: the request is accepted/validated, and the server attempts to process all guests (DB inserts, calendar attendee updates, and/or outbound invitation emails) rather than rejecting with a validation error.
Expected behavior: schema validation rejects overly large guest lists (e.g., `guests.max(N)`) and returns a 4xx error without performing fan-out work.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·high, CE·low, MRV·high, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·high, CE·low, CE·medium, MRV·high; astra: CE·low, CE·medium, MRV·medium

#### A4 — AddGuestsDialog leaves stale `isInvalidEmail` (and email input) state on success/close, showing old validation banner when reopened

**Location:** `apps/web/components/dialogs/AddGuestsDialog.tsx:29–50`  ·  **Severity:** medium  ·  **Judge confidence:** 0.62  ·  84 findings, 35 cells

**Why this is real.** Multiple independent reports point to the same state bug in `addguestsdialog.tsx` around lines ~29–50: `isInvalidEmail` is set when validation fails (e.g., via a `setIsInvalidEmail(true)` path), but there is no corresponding reset (`setIsInvalidEmail(false)`) on successful submit, on dialog close (`onOpenChange`), or when the user edits the email input. This means the component can re-render/reopen with `isInvalidEmail` still true, so the warning banner persists even after the input is corrected or the dialog is reopened. The PR patch does not include this file, so this verification relies on the consistent reports describing missing reset logic in that component.

**How to replicate.** 1) Open the Add Guests dialog. 2) Enter an invalid email (e.g., `foo@`) and trigger validation/submission so the invalid-email banner appears. 3) Now either (a) correct the email to a valid one and submit successfully, or (b) close the dialog (ESC/overlay) and reopen it. Expected: the invalid-email banner (and any partially typed invalid multi-email value) should be cleared once input is fixed, after successful add, or when reopening the dialog. Actual: the invalid banner and/or previous input reappears because `isInvalidEmail` (and possibly the multi-email value) was never reset.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·medium

#### A5 — Authorization bypass: any attendee can add arbitrary guests to a booking and trigger organizer calendar invites

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:52–53`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74  ·  124 findings, 47 cells

**Why this is real.** All deduped reports point to the same authorization guard at ~L52–53 where being an attendee (`isAttendee` / `isattendee`) is treated as sufficient permission to proceed (e.g., a check equivalent to “allow if organizer OR isAttendee”). That means an invitee (not the organizer/host) can call the `addguests` handler to mutate the booking and cause calendar updates/invitation emails to be sent to arbitrary third-party emails, leaking full event details (including meeting links) without organizer consent. The PR diff does not include this file, so verification relies on reading the post-PR handler around the referenced lines and confirming the permission condition includes `isAttendee` as an authorization grant rather than an informational role.

**How to replicate.** 1) Create a booking with Organizer O and invite Attendee A (A is a valid attendee on the booking).
2) Log in as Attendee A (not as Organizer O).
3) Call the TRPC endpoint backing `viewer.bookings.addGuests` (or the corresponding HTTP request) with the booking identifier (uid/id) and a list of arbitrary external guest emails (e.g., attacker-controlled addresses).
4) Observe actual behavior: the call succeeds and new guests are added; calendar updates and/or invitation emails (ICS) are sent containing full event details (location/video URL/password).
5) Expected behavior: only the organizer/host (or authorized team/admin roles) should be able to add new guests; an attendee should get an authorization error and no invitations/updates should be sent.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low; terra: CE·high, CE·low, CE·medium, MRV·medium; astra: CE·medium

#### A6 — add-guests handler emails raw guests list instead of filtered uniqueGuests, causing duplicate/wrong notifications

**Location:** `addguests.handler.ts:160–175`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  77 findings, 36 cells

**Why this is real.** Multiple reviewers point to the same concrete control-flow bug in `addguests.handler.ts` around ~line 168: the handler computes a filtered list like `uniqueGuests` (excluding already-attending/duplicate/rejected guests) and uses that list when persisting updates, but then calls the mailer with the original unfiltered input, e.g. `sendAddGuestsEmails({ guests, ... })` instead of `sendAddGuestsEmails({ guests: uniqueGuests, ... })`. This means the email-sending logic classifies pre-existing attendees as “newly added” and can pick the wrong template (e.g., scheduled-event email) or re-email guests that were intentionally filtered out. The PR diff does not include this file, so this verification relies on the consistent line-level references and described call-site behavior in the reports.

**How to replicate.** 1) Find an existing booked event with at least one attendee already on it (e.g., alice@example.com).
2) Call the “add guests” endpoint/handler with a payload that includes both the existing attendee (alice@example.com) and a truly new email (bob@example.com), possibly also including a duplicate address or an address previously rejected.
3) Observe emails sent: expected behavior is that only the newly added/unique guests receive an “added to event” style email, and existing/rejected/duplicate guests receive nothing.
4) Actual behavior (due to passing the raw `guests` array into `sendAddGuestsEmails`) is that alice@example.com (and possibly duplicates/rejected entries) also receives an email, potentially using the wrong template (e.g., a scheduled-event confirmation).

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·low; glm-flash: CE·high, CE·low; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·medium, MRV·high, MRV·medium; terra: CE·high, CE·low, CE·medium; astra: CE·low, CE·medium

#### A7 — addGuests crashes with unhandled Prisma P2025 when booking.userId is null (id coerced to 0)

**Location:** `packages/trpc/server/routers/viewer/bookings/addGuests.handler.ts:82–88`  ·  **Severity:** high  ·  **Judge confidence:** 0.70  ·  59 findings, 29 cells

**Why this is real.** The handler performs an organizer lookup using Prisma with a coerced fallback ID: `prisma.user.findFirstOrThrow({ where: { id: booking.userId || 0 } })` (line range reported as ~82–88). When `booking.userId` is `null`, this becomes `id: 0`, which will not match any real user and causes `findFirstOrThrow` to throw a Prisma error (typically P2025). Because this exception is not converted to a typed `TRPCError`, it bubbles up as an unhandled 500 with a raw Prisma error payload.

**How to replicate.** 1) Ensure there exists a Booking record where `userId` is NULL (e.g., an imported/legacy booking or any flow that can create bookings without an assigned user).
2) Call the tRPC endpoint that uses `addGuests.handler.ts` ("add guests" booking mutation) for that booking.
3) Observe the server response: expected is a clean, handled error (e.g., TRPCError NOT_FOUND/BAD_REQUEST stating organizer/user missing), but actual behavior is a 500 with an unhandled Prisma `findFirstOrThrow`/P2025 error because `userId` was coerced to 0.

**Found by:** opus: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high; terra: MRV·high

#### A8 — AddGuestsDialog error toast fallback is unreachable; users see raw error codes/undefined prefix

**Location:** `apps/web/components/dialog/addguestsdialog.tsx:43–47`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72  ·  57 findings, 35 cells

**Why this is real.** Automated reports consistently point to apps/web/components/dialog/addguestsdialog.tsx around line 43 building the toast message as a template string (e.g. something like ``const message = `${err?.data?.code}: ${t(err?.message)}`;``) and then calling `showToast(message || t("unabletoaddguests"), ...)`. Because a template literal always produces a string (even when interpolations are `undefined`, yielding e.g. `"undefined: ..."`), `message` is always truthy and the `|| t("unabletoaddguests")` fallback is dead/unreachable. This results in user-visible toasts containing raw server codes/i18n keys and even `undefined:` prefixes instead of the intended localized fallback; the PR diff is not provided here, so this verification relies on the repeated line-specific reports.

**How to replicate.** 1) In the web app UI, open the Add Guests dialog. 2) Trigger an error path while adding guests (e.g., enter an invalid email, or simulate a server failure/response without `err.data` such as a 500 or network error). 3) Observe the toast: Actual behavior shows a string like `undefined: <raw error key/code>` or a non-localized message, because the constructed template string is always used. Expected behavior is a localized generic fallback message (e.g., `t("unabletoaddguests")`) when structured error data/message is missing or not translatable.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·medium, MRV·low, MRV·medium; astra: CE·low, CE·medium

#### A9 — Add-guests endpoint can overbook seat-limited events by appending attendees without enforcing seatsPerTimeSlot

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:44–90`  ·  **Severity:** high  ·  **Judge confidence:** 0.64  ·  46 findings, 19 cells

**Why this is real.** The deduplicated reports consistently describe that this handler appends new guests by directly updating `booking.attendees` (via a Prisma `booking.update` / nested `attendees.create*`) and does not validate capacity for seated events (`seatsPerTimeSlot`). In particular, the handler is reported to read/possess `seatsPerTimeSlot` context but never checks `booking.attendees.length + uniqueGuests.length <= seatsPerTimeSlot` and does not create/update any seat-tracking records (e.g., BookingSeat) used by the seated-booking flow. Because the PR diff does not include this file, this verification relies on the reported code behavior/line references: guests are appended unconditionally, so seat-limited bookings can be overfilled.

**How to replicate.** 1) Create an event type configured as a seated/seat-limited event with `seatsPerTimeSlot = 2` (or any small number). 2) Create a booking for a specific timeslot with 2 attendees (fully booked). 3) Call the viewer bookings add-guests endpoint (the TRPC procedure backed by `addguests.handler.ts`) to add 1+ additional guests to that booking. Expected: request should be rejected (or only add up to remaining seats) and/or use the seated-booking seat allocation logic; Actual: guests are appended as attendees successfully, resulting in `attendees.count > seatsPerTimeSlot` (overbooked slot) and no corresponding seat-allocation records if the system uses a separate seat table/flow.

**Found by:** opus: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium

#### A10 — Team-member add-guest notification branch is unreachable because CalendarEvent.team is never populated by callers

**Location:** `packages/emails/email-manager.ts:522–553`  ·  **Severity:** high  ·  **Judge confidence:** 0.67  ·  45 findings, 26 cells

**Why this is real.** The new implementation tries to notify team hosts via `if (calendarEvent.team?.members) { for (const teamMember of calendarEvent.team.members) { ... } }` but this relies on `CalendarEvent` having a `team` object with `members`. In the surrounding codebase, the `CalendarEvent` object passed into email-manager is typically constructed as a literal from booking/event data; when that construction omits `team` (as the reports indicate), `calendarEvent.team` is `undefined` and the loop never executes, making team-host notifications for team bookings silently skip.

**How to replicate.** 1) Create a Team event type with at least two team members (A and B) as hosts. 2) Book the event so it is a team booking (both hosts are associated with the booking). 3) Use the UI/API flow that adds guests to an existing booking (triggering `sendAddGuestsEmails`). 4) Expected: both organizer A and the other team host(s) (e.g., B) receive an "OrganizerAddGuests" email. Actual: only the primary organizer email is sent; other team members are not emailed because `calendarEvent.team?.members` is missing and the loop never runs.

**Found by:** opus: CE·high, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium; sol: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; terra: MRV·high; astra: MRV·high

#### A11 — Add-guests email send failure is swallowed (no error context) and request still succeeds

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:167–170`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  29 findings, 21 cells

**Why this is real.** Multiple deduplicated reports point to a catch block around the add-guests email dispatch that is written as `catch (err) { console.log("error sending addguestsemails") }` (reported at ~lines 167–170). This discards the actual `err` object and uses a bare console.log, so production logs lack any actionable failure details. Because the error is swallowed (no rethrow/return error), the handler can still return success after persisting guests, leading callers/UI to believe notifications were sent when they were not.

**How to replicate.** 1) Create or open an existing booking that supports adding guests and use the UI/API route that invokes `viewer.bookings.addGuests` (or equivalent) to add one or more new guest emails. 2) Force the email send to fail (e.g., misconfigure SMTP/SendGrid credentials, block outbound email network calls, or set an invalid mail provider config in a dev/staging environment). 3) Observe: the request completes successfully and the guest list persists/updates, but no guest notification emails are delivered. 4) Check server logs: only a fixed message like `error sending addguestsemails` appears with no stack trace/error object, making the failure undiagnosable and preventing easy retry since guests are already saved.

**Found by:** opus: MRV·high, MRV·low; glm-flash: CE·medium, MRV·high, MRV·low; glm-vis: MRV·high, MRV·low, MRV·medium; sol: CE·low, MRV·high, MRV·low; terra: MRV·low, MRV·medium; astra: MRV·high, MRV·low, MRV·medium

#### A12 — Race condition in addGuests allows duplicate attendee rows (check-then-insert without transaction/unique constraint)

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:74–101`  ·  **Severity:** high  ·  **Judge confidence:** 0.67  ·  18 findings, 18 cells

**Why this is real.** The reported code path performs a read of existing attendees and then conditionally writes new attendees via `booking.update(... createMany ...)` based on an in-memory dedupe/filter. Because the read (duplicate check) and the subsequent `createMany` are not wrapped in a database transaction and there is no unique constraint on (bookingId,email), two concurrent requests can both observe "not present" and both insert the same attendee. The PR diff does not include this file, so verification relies on the consistent line-referenced reports pointing to this non-atomic read-then-write flow around lines ~74–101.

**How to replicate.** 1) Pick an existing booking with no attendee for email `dup@example.com`. 2) From two clients (or one script), send two addGuests requests concurrently to the same booking, both including `dup@example.com` (e.g., fire both requests without awaiting the other). 3) Observe that both requests succeed and the booking ends up with two attendee records for `dup@example.com` (or duplicated guest entries in the UI). Expected: only one attendee row per (booking,email); Actual: duplicates appear due to the race in the check-then-insert logic.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·low, MRV·medium; sonnet: MRV·high; glm-vis: MRV·low; sol: CE·high, CE·medium; terra: CE·low, MRV·low

#### A13 — Add-guests flow persists new guest attendees with empty name (blank greetings/ICS CN)

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:83–90`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  15 findings, 10 cells

**Why this is real.** Multiple reviewers point to the same concrete code pattern in this file/region: new guest attendees are created with an explicit empty string for the display name (e.g. `name: ""`) while filling other fields like email (and often organizer-derived `timeZone`/`locale`). Persisting `name: ""` is not a harmless placeholder: downstream email templates and ICS attendee rendering commonly use the attendee name as the display name/greeting and as the CN parameter, which becomes blank ("hi ,", `CN=""`, or `To:  <email>`). This is a functional defect (bad user-facing output and incorrect attendee identity data), not a style issue; the PR diff is not provided here, so this verification relies on the consistent line-referenced reports.

**How to replicate.** 1) Create a booking with an organizer and at least one existing attendee. 2) Call the add-guests endpoint/handler for that booking with a guest email that does not yet exist as an attendee (so the handler creates a new attendee record). 3) Observe the created attendee row: its `name` is persisted as an empty string. 4) Trigger sending of guest/organizer emails and/or download the ICS for the booking: expected is the guest addressed by a name or at least the email as display name; actual is blank name in greeting/headers (e.g., "hi ," / " <guest@email>") and ICS attendee has empty CN (e.g., `CN=""`).

**Found by:** opus: MRV·high, MRV·medium; sonnet: MRV·high; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium

#### A14 — Organizer add-guests email sets Reply-To to all attendee emails, leaking roster and risking oversized headers

**Location:** `packages/emails/templates/organizer-add-guests-email.ts:25–25`  ·  **Severity:** high  ·  **Judge confidence:** 0.87  ·  14 findings, 12 cells

**Why this is real.** The Nodemailer payload explicitly sets `replyTo: [this.calEvent.organizer.email, ...this.calEvent.attendees.map(({ email }) => email)]` (line 25). This means every recipient of this organizer/team-member notification receives an email whose Reply-To header contains the full attendee email list, disclosing addresses to each recipient and allowing unbounded growth of the header as attendees increase. For large bookings or repeated guest additions, the Reply-To header can exceed provider limits and cause message rejection/truncation, turning the notification into a silent/partial failure depending on upstream handling.

**How to replicate.** 1) Create a booking/event with an organizer and multiple attendees (or use a seats/large-attendee event), then trigger the 'add guests' flow so `OrganizerAddGuestsEmail` is sent. 2) Inspect the delivered email headers (in a mail catcher like MailHog/Mailpit or your SMTP provider logs): Expected: Reply-To should be a single address (e.g., organizer or a controlled alias) or otherwise privacy-preserving; Actual: `Reply-To` contains the organizer plus every attendee email. 3) Increase attendees to dozens/hundreds (or repeatedly add guests) and resend: Expected: email still delivers reliably; Actual: some providers reject/truncate due to excessive header size, and recipients may not receive the organizer notification.

**Found by:** opus: CE·medium, MRV·high; glm-flash: MRV·high, MRV·medium; glm-vis: CE·low, MRV·high, MRV·low, MRV·medium; sol: MRV·low; terra: MRV·high, MRV·medium; astra: MRV·low

#### A15 — MultiEmail list items keyed by array index cause stale/shifted input values after middle-row removal

**Location:** `packages/ui/form/multiemail.tsx:26–35`  ·  **Severity:** medium  ·  **Judge confidence:** 0.70  ·  13 findings, 10 cells

**Why this is real.** Multiple reports point to the component rendering a removable list of email inputs using an array-index React key (e.g., a map rendering items with `key={index}` around lines ~26–31) while removing items via splice/filter from the middle. In React, using the array index as the key on a mutable list causes DOM/component instances to be reused for different logical items after a deletion, so the input state/value/focus can appear to “move” to the wrong row. This is a functional correctness issue (wrong displayed values / state association), not a style nit; the PR diff does not include this file, so verification is based on the reports’ cited lines.

**How to replicate.** 1) Open any UI that uses the MultiEmail component (a form that lets you add multiple email rows). 2) Add at least three rows and type distinct values (e.g., a@a.com, b@b.com, c@c.com). 3) Delete the middle row (b@b.com). Expected: remaining rows keep their own values (a@a.com, c@c.com). Actual with `key={index}`: React may reuse the DOM node for the next item, causing the value/focus/IME state to appear to shift—e.g., c@c.com row may display b@b.com’s input state or vice versa.

**Found by:** glm-flash: MRV·low; glm-vis: CE·low

#### A16 — Organizer add-guests email subject crashes on empty attendees due to unguarded attendees[0].name access

**Location:** `packages/emails/templates/organizer-add-guests-email.ts:28–31`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  8 findings, 8 cells

**Why this is real.** In `packages/emails/templates/organizer-add-guests-email.ts` the subject template reads from the first attendee without any guard, e.g. `name: this.calevent.attendees[0].name` (reported at ~L28-29). If `this.calevent.attendees` is an empty array (or undefined), `this.calevent.attendees[0]` is `undefined` and `.name` throws a runtime `TypeError`, which can abort email payload construction/sending. This is a functional correctness bug (runtime exception) rather than a style issue; the PR diff didn’t include this file, so this verification relies on the reports’ line references.

**How to replicate.** 1) Find the code in `packages/emails/templates/organizer-add-guests-email.ts` where the subject is built and confirm it directly accesses `this.calevent.attendees[0].name` without optional chaining/fallback.
2) Trigger the template with a `calevent` object where `attendees: []` (e.g., in a unit test, or by invoking the email-sending path with an event that has no attendees).
Expected: email subject renders with a safe fallback (or email still sends).
Actual: subject construction throws `Cannot read properties of undefined (reading 'name')`, causing the email send/payload generation to fail (and potentially rejecting a batch `Promise.all` send).

**Found by:** opus: CE·medium, MRV·low; glm-flash: CE·low, MRV·low

#### A17 — Add-guests mutation silently drops blacklisted/already-attending emails yet returns success (and misleading 'emailsmustbeuniquevalid' when all dropped)

**Location:** `unknown (not referenced in the clustered reports and not present in PR #14740 diff; likely the server-side add-guests mutation/handler for bookings/attendees)`  ·  **Severity:** medium  ·  **Judge confidence:** 0.62  ·  8 findings, 4 cells

**Why this is real.** Per the deduplicated reports, the handler filters the requested guest list to a reduced `uniqueGuests` set (dropping blacklisted addresses and/or emails already present as attendees) but still returns a success response (e.g., a 'guests added' message) without indicating which inputs were skipped. The evidence is the specific behavior around the hardcoded error key/message `'emailsmustbeuniquevalid'`: when filtering removes every submitted email, the code throws BadRequest with `'emailsmustbeuniquevalid'`, even though the input emails can be valid/unique and were excluded for other reasons (blacklist/existing attendee). This is a functional correctness bug (silent partial application + incorrect error reporting), not a style issue, because it causes the UI to claim invitations were added when they were not and misleads users during retries.

**How to replicate.** 1) Configure the blacklist env var mentioned in reports (e.g., `BLACKLISTED_GUEST_EMAILS` / similar) to include `blocked@example.com`.
2) Create or open an event/booking where adding guests is supported.
3) Call the add-guests flow with a mixed list: `['ok1@example.com', 'blocked@example.com']`.
Expected: API/UI should either reject with a clear validation error identifying the blacklisted email, or return a response listing which guests were added vs skipped.
Actual (per reports): UI shows success ('guests added') but `blocked@example.com` is silently not added (no attendee row / no email).
4) Now submit only filtered-out emails, e.g., `['blocked@example.com']` (or an email already an attendee).
Expected: error like 'guest is blacklisted' / 'already invited'.
Actual (per reports): server returns BadRequest with message/key `'emailsmustbeuniquevalid'`, which misstates the real cause.

**Found by:** glm-flash: MRV·high, MRV·medium; glm-vis: CE·high, MRV·low

#### A18 — Remove-email tooltip is hardcoded in English instead of using i18n

**Location:** `packages/ui/form/multiemail.tsx:48–48`  ·  **Severity:** low  ·  **Judge confidence:** 0.74  ·  7 findings, 4 cells

**Why this is real.** Multiple reviewers point to the same line in `packages/ui/form/multiemail.tsx` where the tooltip for the remove action is a literal English string (e.g., `content="remove email"`) rather than using the existing `t(...)` translation function used elsewhere in the component (e.g., for the adjacent “add another” label). This is a real functional i18n defect: in any non-English locale, the tooltip will remain English while surrounding UI strings are localized. The file wasn’t part of this PR’s diff here, so this verification relies on the consistent line-referenced reports.

**How to replicate.** 1) Set the app language/locale to a non-English language (e.g., French). 2) Navigate to a UI that uses the shared MultiEmail control (e.g., the Add Guests dialog where you can add multiple emails). 3) Add at least one guest email so a remove (X/trash) button appears. 4) Hover the remove button: expected a translated tooltip; actual tooltip text is the English literal “remove email”.

**Found by:** glm-flash: MRV·high; glm-vis: MRV·high

#### A19 — addGuests mutation allows adding guests even when the EventType disables/blocks guests

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:44–80`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  6 findings, 6 cells

**Why this is real.** The add-guests handler proceeds with adding invitees to a booking without any guard that checks the associated EventType’s guest policy (e.g., `disableGuests` / “guests hidden/disabled” settings). Multiple reports pinpoint that around lines ~44 and ~74 the code updates/creates guests but never rejects bookings whose `eventType` forbids guests, meaning a caller can bypass the organizer’s configuration purely via this mutation. The PR diff does not include this file, so verification is by reading the current handler around the referenced lines and confirming there is no conditional returning an error when the EventType disallows guests.

**How to replicate.** 1) Create or pick an Event Type where guest additions are disabled/hidden (e.g., `disableGuests` enabled / guests turned off in settings). 2) Create a booking for that Event Type. 3) Call the viewer bookings addGuests mutation (the one implemented by `addguests.handler.ts`) with one or more guest emails for that booking. Expected: the mutation should fail (e.g., forbidden/bad request) because guests are disabled for the Event Type. Actual: the mutation succeeds and the guests are added/associated with the booking despite the Event Type’s no-guests setting.

**Found by:** opus: CE·medium; sol: CE·high

#### A20 — addGuests loads booking by raw id (with heavy includes) before authorization, enabling cross-tenant probing/enumeration

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:26–56`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  4 findings, 4 cells

**Why this is real.** The handler first loads the booking using an unscoped lookup like `prisma.booking.findFirst({ where: { id: bookingId }, include: { attendees: true, references: true, eventType: true, user: { include: { credentials: true }}}})` (reports cite addguests.handler.ts ~26-56 / 43-49), i.e., it does not constrain the query by the requester’s user/team. The authorization check happens only after this fetch, and the code path reportedly throws NOT_FOUND when `!booking` before throwing FORBIDDEN, so an authenticated attacker can (a) force materialization of sensitive relations for arbitrary booking IDs and (b) distinguish “exists vs not exists” by observing NOT_FOUND vs FORBIDDEN (or different timing), which is a real access-control/data-leak bug rather than a style issue. The PR diff does not include this file, so this verification relies on the reported code locations.

**How to replicate.** 1) Sign in as User A (any authenticated account). 2) Obtain/guess a bookingId belonging to User B (different org/team) and call the tRPC mutation that hits `viewer.bookings.addGuests` with that bookingId. 3) Observe that the server performs a heavy booking fetch (attendees/references/eventType/organizer credentials) before failing auth; compare responses for (a) an existing чужой bookingId vs (b) a random non-existent bookingId—expected: both should return FORBIDDEN (or identical behavior) without loading unrelated data; actual: NOT_FOUND is returned for non-existent IDs while existing чужие IDs take the auth branch (FORBIDDEN) after doing the full include query, making existence enumerable and causing unnecessary cross-tenant data access in the DB layer.

**Found by:** sonnet: MRV·medium; glm-flash: CE·high, MRV·low

#### A21 — Add-guests email path bypasses hideCalendarNotes redaction and can leak additional notes to attendees

**Location:** `packages/emails/email-manager.ts:541–549`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  4 findings, 4 cells

**Why this is real.** In the new add-guests sender, attendee emails are constructed with the full formatted event object: `return sendEmail(() => new AttendeeScheduledEmail(calendarEvent, attendee));` / `return sendEmail(() => new AttendeeAddGuestsEmail(calendarEvent, attendee));`. Unlike the existing scheduled-email flow (which explicitly sanitizes/redacts booking notes when `hideCalendarNotes` is enabled), this path never applies that redaction before passing `calendarEvent` into the templates, so any sensitive fields present on `calendarEvent` (e.g., `additionalNotes`) can be included in emails sent to newly added guests despite the hide-notes privacy setting.

**How to replicate.** 1) Create a booking/event with `hideCalendarNotes` enabled and set a non-empty `additionalNotes`/private notes field on the CalendarEvent. 2) Use the “add guests” feature so `sendAddGuestsEmails(calEvent, newGuests)` runs with the new guest email in `newGuests`. 3) Observe the email received by the newly added guest: expected behavior is that private notes are omitted/redacted (same as scheduled-email privacy behavior), but actual behavior is that the attendee email template receives the unredacted `calendarEvent` and can render those notes.

**Found by:** terra: MRV·medium; astra: MRV·high, MRV·low, MRV·medium

#### A22 — MultiEmail leaf module imports @calcom/ui barrel, creating a circular dependency via index re-export

**Location:** `packages/ui/form/multiemail.tsx:2–2`  ·  **Severity:** medium  ·  **Judge confidence:** 0.74  ·  3 findings, 3 cells

**Why this is real.** The reports indicate that `packages/ui/form/multiemail.tsx` (a leaf module) imports UI primitives from its own package barrel (e.g., `import { ... } from "@calcom/ui";` at/near line 2). Because the `@calcom/ui` entrypoint (`index.tsx`) re-exports `MultiEmail` (directly or indirectly), that import path forms a cycle: `multiemail.tsx -> @calcom/ui (index) -> re-export MultiEmail -> multiemail.tsx`. This is a real dependency bug (not style): circular imports can yield undefined exports or initialization-order issues depending on the bundler/optimizer and can also break tree-shaking and increase coupling. The PR diff does not include this file, so verification must be done by inspecting the post-PR code tree as referenced by the reports.

**How to replicate.** 1) In the post-PR tree, open `packages/ui/form/multiemail.tsx` and confirm it imports from the package barrel: `from "@calcom/ui"` (or an equivalent internal barrel path).
2) Open `packages/ui/index.tsx` (or the barrel entry used by `@calcom/ui`) and confirm it re-exports `MultiEmail` (e.g., `export * from "./form/multiemail"` or similar).
3) Run a build that bundles `@calcom/ui` (e.g., `pnpm -F @calcom/ui build` or the repo build) and inspect output for circular-dependency warnings, or exercise a page/component that uses `MultiEmail` and observe potential runtime failures (e.g., some imported primitives resolve as `undefined` due to initialization order). Expected: no circular dependency; Actual: barrel import creates a cycle through the re-export.

**Found by:** opus: CE·high; sol: CE·medium

#### A23 — MultiEmail label htmlFor references missing input id, breaking label/control association

**Location:** `packages/ui/form/multiemail.tsx:21–21`  ·  **Severity:** medium  ·  **Judge confidence:** 0.72  ·  2 findings, 2 cells

**Why this is real.** Automated reviewers report that `multiemail.tsx` contains a `<label htmlFor="emails">` (around line 21) but there is no element rendered with `id="emails"`. That makes the label-to-control association dead: clicking the label will not focus the intended field and assistive technologies cannot correctly map the label to an input. The PR diff does not include this file, so this verification relies on the reported line reference and the post-PR tree code.

**How to replicate.** 1) Open `packages/ui/form/multiemail.tsx` and locate the `<label htmlFor="emails">` around line 21. 2) Search within the component render for any element with `id="emails"` (e.g., `<input id="emails" ...>`); confirm none exists. 3) Run the app and navigate to any form that uses this MultiEmail component; click the label text: expected focus moves to the corresponding email input, actual focus does not (and an accessibility checker will flag 'label has no associated control').

**Found by:** opus: CE·high

#### A24 — Add-guests on a recurring booking updates only one occurrence but sends a series-wide calendar invite

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:138–155`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  2 findings, 2 cells

**Why this is real.** The reported code at/around line 138 adds new attendees via a `createMany` tied to the single `booking` being edited (one occurrence), while the event payload used for notifications/ICS is based on the recurring series (e.g., carries `recurringEvent` / `recurringEventId`). This creates a mismatch: the database has the guest on only one occurrence, but the generated calendar invite represents the whole series, so the guest is invited to all instances while follow-up flows (cancel/reschedule/reminders) that read per-occurrence attendees will not include them for the other occurrences. This file was not modified in the PR diff provided, so verification relies on the reviewers’ shared line-specific reports rather than a patch hunk.

**How to replicate.** 1) Create a recurring event type and book a recurring series (multiple occurrences). 2) Call the add-guests endpoint/mutation for one occurrence in the series (the booking being edited has a `recurringEventId` linking it to the series). 3) Observe: the new guest receives an ICS/invite that applies to the entire recurring series (calendar shows all occurrences). 4) Check data/behavior: only that one occurrence has a booking-attendee row for the new guest; other occurrences in the same `recurringEventId` do not. 5) Trigger a reminder/cancel/reschedule for a different occurrence in the same series: expected the new guest is included; actual they are skipped because they are not attached in the DB for those other occurrences.

**Found by:** opus: CE·high, MRV·high

#### A25 — Concurrent add-guests requests can overwrite calendar attendees with stale snapshot (lost updates)

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:164–170`  ·  **Severity:** high  ·  **Judge confidence:** 0.70  ·  2 findings, 2 cells

**Why this is real.** The reports point to lines ~164–165 where the handler performs a provider update by sending the full attendee list derived from the current request's local snapshot, rather than applying a merge/append or any version/ETag check. Because the external calendar write is an unversioned full "replace attendees" operation, two concurrent add-guest calls can race: the later-finishing request can push an older/smaller attendee list and effectively delete guests added by the other request. This is a real lost-update concurrency bug; the PR provides no patch hunk for this file, so verification must rely on inspecting these lines in the post-PR tree for a full-list attendee replacement without concurrency control.

**How to replicate.** 1) Use a booking with a connected calendar provider (Google/Microsoft) so attendee updates sync externally. 2) Fire two add-guests requests concurrently against the same booking (e.g., two clients adding different guests A and B at nearly the same time). 3) Observe the external calendar event attendees after both requests succeed: expected attendees include both A and B; actual attendees intermittently include only one set (whichever request performed the last provider "replace attendees" write), demonstrating lost updates due to racing full-list writes.

**Found by:** sol: CE·high

#### A26 — addGuests throws BAD_REQUEST when all submitted emails already attendees, enabling email probing and breaking retry/idempotency

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:80–86`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  2 findings, 1 cells

**Why this is real.** Multiple reviewers flag logic around line ~80 that filters the submitted guest emails against existing attendees and then throws a distinct `BAD_REQUEST` when the filtered list is empty (i.e., every submitted address is already an attendee). This creates an observable behavioral difference: the endpoint succeeds when at least one email is new, but fails when all are already present, which lets a caller infer whether a specific email is on the booking. The same branch also makes the operation non-idempotent: after a mid-flight failure where attendees were created but downstream side effects (calendar/email) didn’t complete, a retry will hit the “no new guests” path and permanently prevent recovery.

**How to replicate.** 1) Find/seed a booking with a known attendee email (E1) and another email not on the booking (E2). 2) Call the addGuests endpoint with only [E1]. Observe it returns a `BAD_REQUEST` (or otherwise distinct error) because all submitted emails were filtered out as already-attendees. 3) Call addGuests with [E2] (or [E1,E2]) and observe it succeeds, demonstrating email membership probing. 4) For retry-safety: trigger a partial failure after attendees are persisted but before invites/calendar updates (e.g., temporarily break SMTP/calendar provider or force an exception after DB write). Retry the exact same request; observe it now fails with `BAD_REQUEST` due to all guests already existing, and side effects remain missing.

**Found by:** opus: CE·medium

#### A27 — Guest email blacklist is undocumented/missing from .env.example and can be bypassed via email case differences

**Location:** `apps/web/pages/api/book/[...slug].ts:74–78`  ·  **Severity:** medium  ·  **Judge confidence:** 0.60  ·  1 findings, 1 cells

**Why this is real.** The code introduces an operator-configured guest blacklist via an environment variable (e.g., `process.env.BLACKLISTED_GUEST_EMAILS`) but the report indicates there is no corresponding `.env.example` entry or documentation in the PR, so self-hosted operators cannot discover or correctly configure it (feature ships effectively inert by default). Additionally, the check at lines ~74–78 compares raw strings (e.g., `blacklistedGuestEmails.includes(guest.email)` after a simple `split(',')`), meaning `Guest@Example.com` will not match a blacklist entry `guest@example.com`, allowing a trivial case-variant bypass. This is functional/security behavior, not style: it changes access-control outcomes based on string casing and undiscoverable configuration.

**How to replicate.** 1) Deploy the post-PR code without adding any new env var (as would happen for a self-host following `.env.example`): create a booking with any guest email; observe no blacklist enforcement because the feature is not configurable/discoverable. 2) Now set the env var to include a lowercased email (e.g., `BLACKLISTED_GUEST_EMAILS=guest@example.com`) and restart. 3) Attempt to create a booking with guest email `Guest@Example.com` (case changed). Expected: booking rejected due to blacklist. Actual: booking succeeds because the code performs a case-sensitive `includes` check on un-normalized strings.

**Found by:** glm-vis: MRV·medium

#### A28 — Organizer gets duplicate “guests added” email for team bookings because organizer isn’t excluded from team member loop

**Location:** `packages/features/emails/sendAddGuestsEmails.ts:34–73`  ·  **Severity:** medium  ·  **Judge confidence:** 0.62  ·  1 findings, 1 cells

**Why this is real.** The function sends an organizer notification once (e.g., a call like `await organizerAddGuestsEmail({ ... , teamMember: undefined })`) and then iterates `for (const member of calendarEvent.team.members) { await organizerAddGuestsEmail({ ..., teamMember: member }) }` without excluding the organizer when they are included in `calendarEvent.team.members`. If the organizer is also a team member (common in team bookings), they match one of the looped `member`s and receive the same email a second time. This is a behavioral defect (duplicate notifications), not a style issue; the evidence here relies on the deduplicated reports since the relevant file is not part of this PR’s diff.

**How to replicate.** 1) Create a team event type where the organizer is also present in the team membership list used to populate `calendarEvent.team.members`. 2) Book the event and then add a guest (triggering `sendAddGuestsEmails`). 3) Observe the organizer’s inbox: expected is one “guest added” email; actual is two emails for the same guest addition (one from the standalone organizer send, one from the team-members loop).

**Found by:** glm-vis: MRV·low

#### A29 — UI shows “Additional guests / Add members” action to users who are always forbidden by the backend

**Location:** `unknown (not included in PR diff; reports did not provide a path)`  ·  **Severity:** medium  ·  **Judge confidence:** 0.46  ·  1 findings, 1 cells

**Why this is real.** The reports describe a concrete permission mismatch: the dropdown menu appends an “Add members / Additional guests” entry with no permission gating, but the submit handler/API explicitly denies everyone except the organizer, an attendee, and (admin && owner). This creates a reachable UI action for ordinary team members that can never succeed and predictably results in a Forbidden error toast after valid input. Because the relevant file is not part of this PR’s diff and no line refs were provided, this verification relies on the reported behavior/logic mismatch rather than a specific hunk in the patch.

**How to replicate.** 1) Log in as a regular team member (not organizer/attendee of the booking; not admin+owner). 2) Navigate to a team booking details page where the actions dropdown is available. 3) Open the dropdown and click “Additional guests” / “Add members”. 4) Enter valid email(s) and submit. Expected: action hidden/disabled for this role, or request succeeds. Actual: the dialog is available, but submission fails with a Forbidden error toast because backend permission checks reject the user.

**Found by:** glm-vis: MRV·medium

#### A30 — tRPC input allows non-integer bookingId, causing Prisma Int validation error and 500 response

**Location:** `packages/trpc/server/routers/viewer/bookings.ts:1–1`  ·  **Severity:** medium  ·  **Judge confidence:** 0.55  ·  1 findings, 1 cells

**Why this is real.** The reports describe a tRPC input schema that validates `bookingId` as `z.number()` (no `.int()` or positivity/range constraint). Because Prisma expects an `Int` for the corresponding column, a request like `bookingId: 1.5` passes Zod validation but then fails at the Prisma client boundary with a validation error ("expected int, provided float"), which surfaces as an InternalServerError (500) instead of a client input error (400). The PR diff does not include the file/lines for this schema, so this verification relies on the reports and can be confirmed by locating the procedure that takes `bookingId` and checking whether it uses `z.number()` without `.int()`.

**How to replicate.** 1) Find the tRPC procedure that accepts `bookingId` (likely a booking read/update/cancel endpoint) and confirm its input schema uses `bookingId: z.number()` (without `.int()`). 2) Invoke the procedure (via the app UI devtools, tRPC client, or direct HTTP request) with `bookingId` set to a float, e.g. `1.5`. 3) Observe: Zod validation passes, Prisma throws a client validation error about expecting an int, and the server returns a 500. Expected: input validation rejects the request with a 4xx (e.g., 400) before reaching Prisma.

**Found by:** glm-vis: MRV·medium

#### A31 — Newly added booking attendees are not synced to the existing external calendar event (stale attendee list passed to updateCalendarAttendees)

**Location:** `packages/core/EventManager.ts:1–1`  ·  **Severity:** high  ·  **Judge confidence:** 0.58  ·  1 findings, 1 cells

**Why this is real.** This issue is reported in the deduplicated reviewer notes, but the relevant code is not present in this PR diff, so it must be confirmed by inspecting the post-PR tree directly. The defect mechanism described is: the booking is updated via Prisma using an `attendee.createMany(...)`/similar write, but the in-memory event/booking attendee list used for `eventManager.updateCalendarAttendees(...)` is not refreshed/merged to include the newly created attendee emails. As a result, the calendar update call can rebuild/update the external calendar event with an attendee list that omits the just-added guests (or mis-reconciles ordering), producing a real data-sync bug rather than a style issue.

**How to replicate.** 1) Use a booking type connected to a writable external calendar (e.g., Google Calendar) so a calendar event is created. 2) Create a booking with at least one attendee/guest so the calendar event has attendees. 3) Update/edit the booking to add one or more new attendee emails (the flow that performs `createMany` for attendees and then calls `eventManager.updateCalendarAttendees`). 4) Observe: the DB shows the new attendee rows, but the external calendar event attendees do not include the newly added guests (or the attendee list is inconsistent), indicating the update used a stale attendee list rather than re-reading/merging attendees before calling the calendar update.

**Found by:** glm-flash: MRV·low

#### A32 — Missing i18n key causes add-guests permission error to display raw `forbidden: youdonothavepermission`

**Location:** `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:55–55`  ·  **Severity:** low  ·  **Judge confidence:** 0.86  ·  1 findings, 1 cells

**Why this is real.** The handler throws a TRPC error using a message string that is intended to be translated: `throw new TRPCError({ code: "FORBIDDEN", message: "youdonothavepermission" });` (reported at line 55). Client UI error handling commonly feeds `error.message` into i18n (e.g., `t(error.message)`); if `common.json` does not define a `youdonothavepermission` key, the UI will fall back to rendering the raw key (often prefixed by the error code), producing a user-visible string like `forbidden: youdonothavepermission` instead of a localized message.

**How to replicate.** 1) Use an account that can view a booking but does not have permission to modify it (e.g., not the organizer/host for the booking). 2) Trigger the UI flow that calls the `viewer.bookings.addGuests` mutation (Add Guests dialog). 3) Observe the error response path that executes the `FORBIDDEN` throw in `addguests.handler.ts`. Expected: a properly translated “You do not have permission …” message. Actual: the UI renders the literal key (e.g., `forbidden: youdonothavepermission`) because the translation key is missing from `common.json`.

**Found by:** sol: MRV·high

#### A33 — Null eventType.teamId is coerced to 0, causing incorrect team lookup/authorization checks

**Location:** `packages/trpc/server/routers/viewer/eventTypes/get.handler.ts:128–136`  ·  **Severity:** medium  ·  **Judge confidence:** 0.38  ·  1 findings, 1 cells · ⚠️ **no harness cell found this**

**Why this is real.** The reported defect is that when `eventType.teamId` is `null` (personal event type), the code coerces it to `0` and then performs team-related logic against that value (e.g., `teamId: eventType.teamId || 0`). This changes the meaning of `null` (no team) into a concrete team id and can cause incorrect authorization/lookup behavior (checking membership/access against a non-existent team 0 instead of skipping team checks). The file is not part of this PR’s diff, so verification relies on locating this coercion pattern in the post-PR tree as described by the reports.

**How to replicate.** 1) Create/use a personal EventType where `teamId` is NULL in the DB (not a team event). 2) Hit the code path that performs a team authorization or team fetch for that EventType (e.g., fetch/update event type via the viewer eventTypes router). 3) Observe in logs/debugger that the team query/check uses `teamId = 0` rather than skipping team logic; expected behavior is that `null` teamId should bypass team membership/team fetch checks, but actual behavior performs them against team 0 and can incorrectly deny access or behave inconsistently.

**Found by:** **no harness cell** — vanilla only: glm-flash

### Golden-duplicates removed (would double-count)

- **duplicate of golden #3** — “uniqueGuests filters out existing attendees and blacklisted emails but does not deduplicate duplicates within the input; createMany can insert duplicate attende…”
  - cluster: Attendee/guest dedupe uses case-sensitive email comparisons, allowing duplicate attendees and false negatives (`apps/web/server/lib/email-manager.ts`), 204 findings, 45 cells
- **duplicate of golden #1** — “The logic for checking team admin/owner permissions is incorrect. This condition uses AND (&&) which requires both isTeamAdmin AND isTeamOwner to be true, but i…”
  - cluster: Team admin authorization check wrongly requires user to be both admin and owner (&& instead of ||) (`packages/trpc/server/routers/viewer/bookings/addGuests.handler.ts`), 94 findings, 26 cells
- **duplicate of golden #0** — “The addGuests.handler.ts blacklist check uses blacklistedGuestEmails.includes(guest) after lowercasing the blacklist but not the input guest emails, allowing at…”
  - cluster: addguests input schema allows empty guests array, leading to misleading BAD_REQUEST message (`packages/trpc/server/routers/viewer/bookings/addguests.schema.ts`), 24 findings, 14 cells
- **duplicate of golden #3** — “uniqueGuests filters out existing attendees and blacklisted emails but does not deduplicate duplicates within the input; createMany can insert duplicate attende…”
  - cluster: Server-side addGuests input allows duplicate guest emails in one request (`packages/trpc/server/routers/viewer/bookings/addGuests/addguests.schema.ts`), 17 findings, 9 cells
- **duplicate of golden #1** — “The logic for checking team admin/owner permissions is incorrect. This condition uses AND (&&) which requires both isTeamAdmin AND isTeamOwner to be true, but i…”
  - cluster: New add-guests handler ships with zero test coverage (permission matrix/filtering/email flow unverified) (`UNKNOWN (no test file path referenced in the reports; issue is the absence of tests in the PR diff)`), 10 findings, 6 cells
- **duplicate of golden #2** — “The sendAddGuestsEmails function in email-manager.ts passes the full calendarEvent.attendees array when determining which attendees receive AttendeeScheduledEma…”
  - cluster: sendAddGuestsEmails sends the wrong attendee template for newly-added guests (and uses a case-sensitive O(n×m) membership check) (`packages/emails/email-manager.ts`), 8 findings, 7 cells
- **duplicate of golden #4** — “Starting with an array containing an empty string may cause validation issues. Consider starting with an empty array [] and handling the empty state in the Mult…”
  - cluster: Add Guests dialog mishandles empty MultiEmail rows, causing silent no-op or persistent invalid-email errors (`apps/web/components/dialog/addguestsdialog.tsx`), 7 findings, 7 cells
- **duplicate of golden #2** — “The sendAddGuestsEmails function in email-manager.ts passes the full calendarEvent.attendees array when determining which attendees receive AttendeeScheduledEma…”
  - cluster: add-guests email notification is sent to all attendees on every call, enabling spam/harassment via repeated addGuests (`packages/lib/emails/sendAddGuestsEmails.ts`), 2 findings, 2 cells
- **duplicate of golden #5** — “The `sendAddGuestsEmails` function does not check the `disableStandardEmails` flags in the `EventType` metadata, which may result in sending emails to hosts/att…”
  - cluster: Attendee opt-out flag ignored when sending guest-change/new-invite emails (`packages/emails/email-manager.ts`), 1 findings, 1 cells

---

## PR 10967 — 31 additional real bugs (6 goldens; 4 golden-duplicates removed)
(<https://github.com/calcom/cal.com/pull/10967>)

### Additional bugs (evidence cards)

#### A1 — Collective bookings persist only destinationCalendar[0], dropping co-host destination calendars

**Location:** `packages/features/bookings/lib/handlenewbooking.ts:1871–1879`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  336 findings, 61 cells

**Why this is real.** Multiple reports point to the same concrete code pattern in `handlenewbooking.ts` around ~1877: the booking persistence logic connects only `destinationCalendar[0]` (e.g., `destinationCalendar: { connect: destinationCalendar?.[0] ? { id: destinationCalendar[0].id } : undefined }`). This is a real functional defect for collective bookings because `destinationCalendar` is built as an array containing calendars for all hosts, but only the first element is written to the DB, so downstream flows that reconstruct the event from the stored booking can only “see” the organizer’s calendar. The PR does not modify this file per the prompt, so verification relies on reading the existing code at the referenced lines.

**How to replicate.** 1) Configure a collective event type with 2+ hosts, where each host has a different connected destination calendar (e.g., Google Calendar A for host1, Google Calendar B for host2). 2) Create a booking that is not immediately finalized (e.g., requires payment or organizer confirmation / deferred creation path). 3) Inspect the created Booking record (DB or API) and confirm it has only one `destinationCalendar` linked (the first/organizer). 4) Proceed with the deferred step (confirm booking or complete payment) and observe only one calendar event gets created / downstream cancellation & reminder flows only operate on that single calendar; expected behavior is events/operations for all hosts’ destination calendars.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·high, CE·low, MRV·high, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; terra: CE·high, CE·low, CE·medium, MRV·low, MRV·medium; astra: CE·high, CE·low, MRV·high, MRV·low

#### A2 — Collective hosts' destination calendars are dropped when organizer has none due to optional-chained push on null array

**Location:** `packages/features/bookings/lib/handlenewbooking.ts:1078–1082`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  155 findings, 45 cells

**Why this is real.** At ~line 1078 the code appends collective/team calendars via an optional-chained mutation like `evt.destinationcalendar?.push(...teamdestinationcalendars)`. If `evt.destinationcalendar` is `null`/`undefined` (e.g., neither the event type nor the organizer has a destination calendar), the optional chaining makes this a silent no-op, so `teamdestinationcalendars` are never persisted onto `evt`. This is a functional defect (loss of intended delivery destinations), not a style issue; per the reports, this file/line is not in the PR diff, so this verification relies on the reported post-PR code snippet/line reference.

**How to replicate.** 1) Create a collective/team event type where the organizer has no destination calendar configured (and the event type itself does not specify one). 2) Add at least one cohost/team member who does have a destination calendar configured. 3) Create a booking for that collective event. Expected: the booking is written/synced to the cohost(s) destination calendar(s). Actual: no cohost destination calendars are attached because `evt.destinationcalendar` remains null and `evt.destinationcalendar?.push(...)` discards `teamdestinationcalendars`.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·high, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, MRV·high, MRV·medium; terra: CE·medium, MRV·low, MRV·medium; astra: MRV·low

#### A3 — Google Meet event creation can crash when destinationCalendar is missing/empty

**Location:** `packages/core/eventmanager.ts:118–120`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  91 findings, 41 cells

**Why this is real.** Multiple deduplicated reports point to a direct null/undefined dereference around lines 118–120, e.g. code effectively does `const destinationcalendar = calendarEvent.destinationCalendar[0];` and then accesses `destinationcalendar.integration` without guarding for `destinationCalendar` being undefined or an empty array. If `destinationCalendar` is optional (or can be empty), `destinationcalendar` becomes undefined and `.integration` throws a TypeError, aborting event creation before any intended fallback (e.g., to Cal Video) can run. The file is not in this PR’s diff per the prompt, so this verification relies on the consistent line-referenced reports.

**How to replicate.** 1) Configure an event type/location that uses Google Meet (or triggers Google Meet conferencing creation) but does not have a destination calendar selected/connected (destinationCalendar undefined or []). 2) Attempt to create a booking for that event type. Expected: booking proceeds and either creates Google Meet via a valid calendar integration or falls back to Cal Video when no destination calendar exists. Actual: runtime exception (TypeError) occurs when the code reads `destinationcalendar.integration`, preventing booking/event creation.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·high, CE·low, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·low; terra: CE·high, CE·low, CE·medium, MRV·high, MRV·low; astra: CE·high, CE·low, CE·medium

#### A4 — Reschedule/merge deletes only the first calendar reference, orphaning events on other hosts’ calendars

**Location:** `packages/trpc/server/routers/viewer/booking/eventmanager.ts:553–558`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  165 findings, 47 cells

**Why this is real.** In the reschedule/merge ("newBookingId" / merge) path, the code reportedly selects a single old calendar reference via `booking.references.find((reference) => reference.type.includes("calendar"))` and deletes only that one event. Because collective/multi-destination bookings can have multiple calendar references (one per host/destination), using `.find(...)` removes just the first match and leaves the remaining old references/events untouched, producing stale/orphaned events on other hosts’ calendars. The PR diff does not include this file, so this verification relies on the reported post-PR line references and the cited offending expression.

**How to replicate.** 1) Create a collective booking with multiple hosts where the booking writes events to more than one calendar (multiple `booking.references` of type including "calendar"). 2) Trigger a reschedule that goes through the merge/newBookingId update path (i.e., replaces the booking and attempts to delete the old booking’s calendar events). 3) Observe: only one host’s old calendar event is removed; the other host(s) still have the original event on their calendars. Expected: all old calendar events for the old booking are deleted/updated across every calendar reference.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·medium, MRV·high, MRV·low; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·high, CE·low, CE·medium, MRV·high, MRV·medium; terra: CE·high, CE·low, MRV·low; astra: CE·high, CE·low, CE·medium, MRV·high, MRV·low

#### A5 — Unscoped credential lookup by ID allows cross-tenant calendar writes using another user’s OAuth credential

**Location:** `packages/core/eventmanager.ts:517–545`  ·  **Severity:** critical  ·  **Judge confidence:** 0.74  ·  63 findings, 25 cells

**Why this is real.** The reported code path around line ~517 performs an unscoped credential fetch like `await prisma.credential.findUnique({ where: { id: bookingReference.credentialId } })` (and similarly around ~344 for `destinationCalendar.credentialId`) and then uses that credential (including its key/token) to update/create external calendar events. There is no accompanying authorization check that the fetched credential belongs to a host of the booking/event type (or the same team) and no validation that the credential is not invalid/disabled. This is a real access-control bug: any flow that can cause `bookingReference.credentialId` / `destinationCalendar.credentialId` to point at a foreign credential will operate on external calendars with another tenant’s OAuth token.

**How to replicate.** 1) Obtain (or guess/leak) a victim user’s `credential.id` (calendar OAuth credential) in the same Cal.com deployment. 2) Create or modify a booking reference / destination calendar record so that `bookingReference.credentialId` (reschedule/update path) or `destinationCalendar.credentialId` (create path) equals the victim credential id. 3) Trigger the corresponding action: reschedule a booking (updateAllCalendarEvents), create a booking (create external event), or cancel a booking (delete external event in handleCancelBooking). Expected: the system should reject/ignore the foreign credential and only use credentials owned by an authorized host/team member. Actual: the system loads the victim credential by raw ID and performs the external calendar operation using the victim’s token.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high, MRV·low, MRV·medium; glm-flash: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sol: CE·medium, MRV·medium; terra: MRV·high

#### A6 — Video booking references persist with undefined credentialId, breaking later cancel/update lookups

**Location:** `eventmanager.ts:169–170`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  51 findings, 28 cells

**Why this is real.** The reported post-PR code sets `credentialid` conditionally: `credentialid: isCalendarType ? result.credentialid : undefined`. This means for non-calendar references (e.g., Zoom/Teams/Meet video meeting references) the `credentialid` is explicitly dropped/serialized as null/undefined in the stored booking reference. Later flows that need to find/delete/update the external video meeting by matching `credentialid` (or selecting the correct credential when multiple exist) will fail because the booking no longer records which credential created the meeting; the PR diff for this file is not shown, so this verification relies on the reviewers' quoted lines.

**How to replicate.** 1) Connect two video provider credentials (e.g., two Zoom accounts) to the same Cal.com user/team. 2) Create an event type using that video integration and make a booking. 3) Inspect the created booking's stored references (DB row / API payload) and observe the video reference has `credentialid` missing/null/undefined (actual) instead of the creating credential id (expected). 4) Cancel the booking (or delete one of the credentials and trigger cleanup): expected behavior is the external meeting is deleted/updated using the recorded credential; actual behavior is the system cannot reliably look up the correct credential/meeting, leading to failed deletion, orphaned meetings, or using the wrong credential.

**Found by:** opus: CE·high, CE·low, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: CE·high, MRV·medium; glm-flash: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·medium; sol: MRV·high; astra: MRV·high

#### A7 — Missing credentialId branch fans out over all credentials per destination, creating duplicate external calendar events

**Location:** `eventmanager.ts:355–381`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  23 findings, 17 cells

**Why this is real.** Multiple reviewers point to the same control-flow defect: in the per-`destinationCalendar` loop (around lines 355–381), the `else` branch for when `destinationCalendar.credentialId` is falsy gathers *all* credentials matching `destinationCalendar.integration` (e.g., via filtering/concatenating by integration type) and then proceeds to create events for each of those credentials. Because this `no-credentialId` branch is executed once per destination entry, two destinations with the same integration type but no credentialId will each iterate the same credential set, producing duplicated event creations (N destinations × M credentials). The PR diff isn’t provided here, so this verification relies on the consistent line-referenced reports describing the exact loop/branch placement and fan-out behavior.

**How to replicate.** 1) Configure a team/collective booking with multiple destination calendars that share the same integration type (e.g., two Google Calendar destinations) and ensure those destination entries do not specify a credentialId (collective/auto-selection case).
2) Ensure there are multiple credentials connected for that same integration type (e.g., two Google accounts connected to the team/hosts).
3) Create a booking that triggers event creation.
Expected: one event per intended destination/credential selection (no duplicates for the same booking).
Actual: the code’s no-credentialId branch runs for each destination and iterates all matching credentials each time, causing duplicated events on the same credential calendars (e.g., identical booking appears multiple times in Google Calendar).

**Found by:** opus: CE·high, CE·low, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high; glm-vis: CE·medium, MRV·high, MRV·medium; sol: MRV·medium

#### A8 — loadUsers wraps validation errors as 500 and leaks Prisma error messages as 400

**Location:** `packages/features/bookings/lib/handlenewbooking.ts:722–762`  ·  **Severity:** medium  ·  **Judge confidence:** 0.68  ·  20 findings, 15 cells

**Why this is real.** Based on the clustered reports (the file was not included in the PR diff, so verification is by reading the post-PR code around the referenced lines), `loadUsers` now throws plain `Error` for client-input validation such as an empty/missing `dynamicUserList` (e.g., `throw new Error(...)` around ~727) and then catches broadly and rethrows a generic 500 (e.g., `throw new HttpError({ statusCode: 500, message: "Unable to load users" })` around ~761-762). This loses the original message and misclassifies a client error (should be 4xx) as a server error (500). Additionally, the catch branch reportedly does `if (error instanceof Prisma.PrismaClientKnownRequestError) throw new HttpError({ statusCode: 400, message: error.message })`, which both misclassifies server-side DB failures as 400 and leaks internal Prisma error details to API clients.

**How to replicate.** 1) Find the booking API/code path that calls `loadUsers` in `handleNewBooking` with a "dynamic booking" configuration.
2) Trigger it with an empty or missing `dynamicUserList` (e.g., dynamic booking request where the selection yields zero users). Expected (pre-change/intended): a 4xx dynamic-booking error (often 404/400) indicating no users found/invalid selection. Actual (post-change): response becomes a 500 with a generic "Unable to load users" and the original validation message is lost.
3) Trigger a Prisma known request error inside `loadUsers` (e.g., malformed query inputs that produce a PrismaClientKnownRequestError). Expected: 5xx with sanitized message (server failure). Actual: 400 with the raw `error.message` from Prisma exposed in the response body.

**Found by:** opus: CE·high, CE·medium; sonnet: MRV·medium; glm-flash: MRV·high, MRV·medium; glm-vis: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; sol: MRV·medium

#### A9 — Reschedule calendar update errors are swallowed: catch returns [] when calendarReference is unset and logs were removed

**Location:** `packages/core/eventmanager.ts:590–607`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  17 findings, 15 cells

**Why this is real.** Per the reported post-PR code around the reschedule/update block, the error handler does `catch (error) { ... return Promise.resolve(calendarReference?.map(...) ?? []) }`. This means if an exception occurs before `calendarReference` is assigned (e.g., a `prisma.booking.findFirst`/lookup throws), the function returns an empty array (`?? []`) and does not log (the prior `console.error(message)`/logger was removed), so callers observe “no results” rather than a failure signal. That is a functional behavior change (silent failure) rather than a style issue, and it can mask real calendar-sync outages.

**How to replicate.** 1) Trigger a reschedule path that calls this eventmanager reschedule/update routine. 2) Force an exception before `calendarReference` is computed/assigned (e.g., make the underlying booking lookup throw by using a non-existent booking ID or temporarily breaking DB connectivity). 3) Observe that the function resolves with `[]` and no error log output, so the caller/UI treats the operation as completed without calendar updates. Expected: a non-empty failure result (e.g., `[{ success: false, ... }]`) and/or logged/propagated error so the user can be warned and retries/alerts can occur.

**Found by:** opus: CE·medium; sonnet: CE·low, MRV·high; glm-vis: CE·high, CE·medium; sol: CE·high, MRV·low, MRV·medium; astra: MRV·low

#### A10 — Collective booking can report success while silently skipping co-host calendar creation when destination credential is missing

**Location:** `packages/core/eventmanager.ts:356–371`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  11 findings, 10 cells

**Why this is real.** In createAllCalendarEvents, the code guards calendar event creation with an `if (credential) { ... }` block around ~369, but there is no corresponding `else` branch to record a failure result or log when the credential cannot be resolved (neither in-memory nor via `prisma.credential.findUnique`). As a result, when a destination has a dangling/invalid `credentialId` (e.g., deleted credential or `app?.slug` is null causing lookup to fail), that host/destination is simply skipped and nothing is pushed into `createdEvents`/results, so downstream checks can treat the overall booking as fully synced even though a co-host event was never created. The PR diff does not include this file, so this verification relies on the reported line references and the described control flow at ~356-371.

**How to replicate.** 1) Set up a collective event type with 2+ hosts/destinations that should each get a calendar event. 2) Ensure one destination references a credential that is no longer resolvable (e.g., delete/disconnect that credential row, or make its associated app have `slug = null` so lookup fails). 3) Create a booking. Expected: booking result should include an explicit failure for the affected host/destination (or fail the booking / at least log/report partial sync failure). Actual: booking completes successfully, but the skipped host has no calendar event and no failure entry/log indicating it was skipped.

**Found by:** opus: CE·high, CE·medium, MRV·high, MRV·low, MRV·medium; sonnet: MRV·high, MRV·medium; glm-vis: CE·high; sol: CE·high, MRV·low

#### A11 — Booking webhook payload breaks backward compatibility by changing destinationCalendar from object/null to array

**Location:** `packages/types/calendar.d.ts:134–136`  ·  **Severity:** high  ·  **Judge confidence:** 0.78  ·  12 findings, 12 cells

**Why this is real.** Multiple reports point to a concrete contract change in the public calendar/webhook event type: `destinationcalendar?: destinationcalendar[] | null;` (previously described/used as a single object or null). This means webhook payloads that historically allowed consumers to read `payload.destinationcalendar.externalid` will now deliver an array (or `[]` from some producers), causing runtime failures/undefined values in existing unversioned webhook subscribers. The PR diff for this file is not provided here, so this verification relies on the referenced post-PR line and the downstream webhook producers cited in the reports.

**How to replicate.** 1) Configure a booking webhook endpoint (or use the repo’s e2e webhook snapshot tests) that expects the old shape, e.g., code that reads `payload.destinationcalendar.externalid`.
2) Create a booking that has a destination calendar selected (or trigger a booking event like confirmed/canceled/rejected).
3) Observe the emitted webhook JSON: `destinationcalendar` is now an array (e.g., `[{ externalid: ... }]`) rather than a single object, so `payload.destinationcalendar.externalid` is undefined/throws.
4) Also verify shape inconsistency across triggers: for some events it becomes `[]` when unset (rather than `null`), which breaks consumers that treat `null` as the only empty-case and/or have strict schema validation.

**Found by:** opus: CE·low, MRV·low, MRV·medium; sonnet: MRV·high; glm-flash: CE·high; sol: CE·high, MRV·low; terra: CE·low; astra: CE·high, CE·low, MRV·high

#### A12 — Recurring cancellation delete sweep runs once per calendar reference, causing redundant deleteEvent calls (O(n) duplicates/404s)

**Location:** `apps/web/pages/api/bookings/[id]/cancel/handleCancelBooking.ts:418–470`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  19 findings, 14 cells

**Why this is real.** Multiple independent reports point to the same structural defect: the recurring-event deletion branch (the block that iterates over all calendar credentials and all updated bookings/references to delete provider events) was moved inside a `for (const reference of bookingCalendarReference)` loop around lines ~418-470. With that nesting, the full recurring deletion sweep is re-executed once per calendar reference, even though the body already loops over all credentials × all updated bookings, producing m×n duplicate `deleteEvent` provider calls and subsequent 404/410 failures or rate limiting. The PR diff is not available here, so this verification relies on the consistent line references and described control-flow from the reports.

**How to replicate.** 1) Create a recurring booking with at least two calendar references (e.g., two hosts or one host + an additional integration reference) and ensure the involved user has multiple calendar credentials connected. 2) Call the cancel endpoint for the series (recurring cancellation) so it triggers the recurring-delete path. 3) Observe server logs/network traces: expected is one delete sweep per affected event/credential; actual is the same events being deleted repeatedly (once per bookingCalendarReference), with duplicate delete calls and follow-up provider errors (404/410) for already-deleted events and/or increased latency/rate-limit errors.

**Found by:** glm-flash: CE·high, MRV·high, MRV·low; glm-vis: CE·high, CE·low, CE·medium, MRV·high, MRV·medium

#### A13 — requestReschedule handler drops user.destinationCalendar fallback, producing empty destinationCalendar array

**Location:** `packages/trpc/server/routers/viewer/bookings/requestreschedule.handler.ts:239–242`  ·  **Severity:** low  ·  **Judge confidence:** 0.80  ·  9 findings, 6 cells

**Why this is real.** In requestreschedule.handler.ts around lines 239-242, the code builds destination calendars from only the booking value (e.g., `destinationCalendar: bookingToReschedule?.destinationCalendar ? [bookingToReschedule?.destinationCalendar] : []`). This preserves the earlier copy/paste bug (`bookingToReschedule?.destinationCalendar || bookingToReschedule?.destinationCalendar`) by still never falling back to `user.destinationCalendar`. As a result, when a legacy booking has `destinationCalendar` null/undefined but the user has a configured destination calendar, this handler emits `[]` while sibling handlers use `booking.destinationCalendar || user.destinationCalendar`.

**How to replicate.** 1) Use (or seed) a user account with a configured `user.destinationCalendar`.
2) Ensure there exists a booking to reschedule whose `booking.destinationCalendar` is null/undefined (common for legacy rows or bookings created before destination calendars were stored per-booking).
3) Call the viewer bookings reschedule request endpoint (the `requestReschedule` TRPC mutation) for that booking.
Expected: the handler should pass the user's destination calendar (consistent with other booking handlers) so downstream event/booking logic has a calendar context.
Actual: `destinationCalendar` becomes an empty array (`[]`), losing the user's fallback and potentially causing the reschedule flow to select no destination calendar or behave inconsistently vs other handlers.

**Found by:** sonnet: MRV·medium; glm-vis: CE·high, CE·low

#### A14 — Public booking endpoint leaks raw Prisma error messages and misclassifies DB failures as HTTP 400 in loadUsers()

**Location:** `packages/features/bookings/lib/handlenewbooking.ts:724–763`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  7 findings, 5 cells

**Why this is real.** The reports consistently point to the new loadUsers() try/catch around lines ~724-762 where Prisma errors are caught and re-thrown as an HttpError 400 using the original Prisma exception message (e.g., `catch (e) { if (e instanceof Prisma.PrismaClientKnownRequestError) throw new HttpError({ statusCode: 400, message: e.message }) ... }`). Returning `e.message` verbatim exposes internal DB/Prisma details (model/field/constraint names) to unauthenticated bookers, and mapping transient infrastructure/DB errors to 400 incorrectly signals a client fault and breaks 5xx-based alerting/retry semantics. Additionally, errors intentionally thrown inside the try (e.g., “dynamicUserList is ... empty”) are swallowed by the same catch and converted into a generic 500, changing behavior and obscuring root cause.

**How to replicate.** 1) Hit the public booking creation endpoint that executes handleNewBooking() with inputs that reach loadUsers(). 2) Trigger a Prisma known request error (e.g., violate a unique/foreign-key constraint via crafted booking payload, or force an invalid relation lookup) so Prisma throws PrismaClientKnownRequestError. 3) Observe the response: Actual = HTTP 400 with the raw Prisma error message in the body; Expected = sanitized client-facing error (no internal schema details) and correct status (typically 5xx for DB failures, or a controlled 4xx with a safe message for true validation errors). Optionally, simulate a transient DB failure (pool timeout/connection drop) and see it misreported as 400 rather than a retryable 5xx.

**Found by:** opus: CE·high, CE·medium, MRV·medium; glm-vis: CE·high, CE·medium

#### A15 — Calendar interface migration to destinationCalendar[] + credentialId is not enforced; unmigrated implementers still type-check

**Location:** `packages/types/calendar.d.ts:171–190`  ·  **Severity:** high  ·  **Judge confidence:** 1.00  ·  12 findings, 11 cells

**Why this is real.** Around line 171 in `packages/types/calendar.d.ts`, the PR’s migration is represented only as a type-level change on `export interface Calendar` (the reports indicate the interface now expects a `destinationCalendar` that is an array and credentialId-aware). TypeScript’s structural typing plus method-parameter bivariance means classes that `implements Calendar` can still compile even if their `createEvent`/similar methods keep the old `destinationCalendar` shape (or otherwise don’t actually consume the new array+credentialId semantics). As a result, `tsc` provides false confidence: the interface update compiles while at least three implementers (office365, lark, and a base service per the report) remain unmigrated and only manual inspection reveals the mismatch.

**How to replicate.** 1) In the post-PR tree, open `packages/types/calendar.d.ts` around line 171 and confirm the `Calendar` interface’s method signature(s) now require the new destinationCalendar representation (array + credentialId-aware). 2) Ripgrep for implementers: `rg "implements Calendar" -n` and inspect the Office365, Lark, and BaseCalendarService classes referenced in the reports. 3) Verify those classes still use the pre-migration destinationCalendar contract (e.g., expecting a single calendar id / not handling an array / not threading credentialId), yet the project still type-checks with `tsc`. 4) Optional runtime confirmation: invoke the code path that creates/syncs an event specifying multiple destination calendars or requiring credentialId disambiguation; expected behavior is correct selection/handling of the new array form, actual behavior in those unmigrated services is incorrect routing/selection or failure because they still assume the old shape.

**Found by:** opus: CE·high, CE·low, MRV·high, MRV·medium; sonnet: MRV·high; glm-flash: MRV·high, MRV·medium; glm-vis: CE·high; astra: CE·high, MRV·high

#### A16 — Missing external calendar id when creating event without credentialId causes booking references to store undefined externalCalendarId

**Location:** `packages/core/eventmanager.ts:370–385`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  4 findings, 4 cells

**Why this is real.** Multiple reviewers point to the same concrete call-site defect in event creation: in the no-credentialId path, the code calls `createevent(c, event)` without the (new/required) third `externalId` argument. Because later code writes booking references from the returned value (e.g., `externalcalendarid: result.externalid`), omitting the argument makes `result.externalid` undefined and the booking reference is persisted with `externalcalendarid: undefined`, so subsequent update/delete operations can no longer route to the correct destination calendar. The PR diff does not include this file, so this verification relies on the reported post-PR line references (~375 and ~378) and their described control-flow/assignments.

**How to replicate.** 1) Configure a destination calendar integration where the selected destination has no `credentialId` (the branch described around eventmanager.ts ~370). 2) Create a booking that triggers this branch; observe the booking reference persisted for that attendee/booking has `externalcalendarid` missing/undefined (instead of the destination calendar external id). 3) Attempt to reschedule/cancel the booking (or any flow that calls update/delete against the provider); expected: it updates/deletes the correct event on the chosen destination calendar; actual: the system cannot target the correct calendar/event reliably (often falling back to provider defaults like Google 'primary' or failing to find the event) because `externalcalendarid` was never recorded.

**Found by:** glm-flash: CE·high; astra: CE·high

#### A17 — eventmanager.update swallows errors and returns [] when calendarReference is undefined

**Location:** `packages/core/eventmanager.ts:595–607`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  6 findings, 3 cells

**Why this is real.** In `eventmanager.update`, the `catch` path returns `calendarReference?.map(...) ?? []` (per the reports around lines ~595-607). If an exception is thrown before `calendarReference` is assigned (e.g., during the booking lookup / prisma query), this expression evaluates to `[]`, which is indistinguishable from “there were no calendar references to update”. This silently converts a real update failure into a no-op result, whereas the prior behavior returned an explicit `{ success: false, ... }` result row.

**How to replicate.** 1) Read `packages/core/eventmanager.ts` and locate `update(...)`’s `try/catch` around ~595-607; confirm the `catch` returns `calendarReference?.map(...) ?? []`. 2) Find where `calendarReference` is assigned inside the `try` block after a booking lookup (e.g., `prisma.booking.findUnique/findFirst`). 3) Consider/force a failure before that assignment (e.g., DB unavailable or booking query throws). 4) Observe that the function resolves to `[]` rather than returning at least one failure result; any caller that checks `results.some(r => !r.success)` will treat `[]` as “no failures” and proceed as if the update succeeded, potentially leaving stale calendar events after a reschedule.

**Found by:** glm-vis: CE·high, CE·medium, MRV·medium

#### A18 — Dynamic group booking loadUsers no longer selects organization.slug (and may return undefined users), breaking org-aware booker URLs

**Location:** `packages/features/bookings/lib/handlenewbooking.ts:735–760`  ·  **Severity:** high  ·  **Judge confidence:** 0.68  ·  4 findings, 4 cells

**Why this is real.** The reports indicate that in the rewritten `loadUsers` around lines ~735–755, the user selection for dynamic/group bookings dropped the previous `organization: { select: { slug: true } }` include, so later code that reads `user.organization.slug` (e.g., when building the booker URL) will now see `organization`/`slug` as missing. The same area also reportedly removed the prior `|| []` fallback, meaning `loadUsers` can return `eventType.users` as `undefined`, leading to downstream logic either generating a non-organization URL or throwing when iterating/accessing user fields. This is a functional regression (missing required data and possible undefined) rather than a style issue; the PR diff is not available here, so this verification relies on the consistent line-referenced reviewer reports.

**How to replicate.** 1) In code, open `packages/features/bookings/lib/handlenewbooking.ts` and inspect `loadUsers` near lines 735–755: confirm the Prisma select for users no longer includes `organization: { select: { slug: true } }` and that the function returns `eventType.users` without an `|| []` safeguard. 2) Run the app with an organization workspace and create a dynamic/group booking event type with organization members. 3) Create a booking for that event: when the booking flow constructs the booker URL (via `getBookerUrl`/equivalent), expected behavior is an org-aware URL containing the organization slug; actual behavior is a URL missing the org slug or a runtime error if user list is undefined.

**Found by:** opus: CE·low; glm-vis: MRV·low; sol: CE·high

#### A19 — Duplicate calendar events when destination calendars contain duplicate (credentialId, externalId) entries

**Location:** `packages/core/eventmanager.ts:339–365`  ·  **Severity:** high  ·  **Judge confidence:** 0.70  ·  3 findings, 3 cells

**Why this is real.** Around `createAllCalendarEvents` (report points to ~line 339), the code iterates over the provided destination calendars and invokes `createEvent` once per entry, but does not deduplicate destinations by `(credentialId, externalId)` (or any equivalent key) before looping. Because upstream booking code can combine organizer/team destinations via array concatenation (reported in `handlenewbooking.ts` ~1003-1010 and ~1085-1087) without removing duplicates, the same calendar can appear twice in the destinations list. That causes this loop to call `createEvent` twice against the same calendar, producing two identical external events rather than one.

**How to replicate.** 1) Configure an event type where the event-type destination calendar is a shared/team calendar (same underlying external calendar). 2) Add a collective host/teammate whose personal destination resolution points to that exact same calendar (same credential and same externalId). 3) Create a booking for that event type. Expected: one event is created on the shared calendar. Actual: two identical events are created on the same external calendar because `createAllCalendarEvents` processes both destination entries without deduplication.

**Found by:** opus: CE·medium; glm-flash: CE·medium; glm-vis: CE·high

#### A20 — Calendar createEvent failure logs full CalendarEvent object including attendee PII and credential IDs

**Location:** `packages/core/calendarmanager.ts:249–249`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  5 findings, 5 cells

**Why this is real.** At/around line 249 the code logs a calendar-creation failure with the full event payload: `log.error("createevent failed", JSON.stringify(error), calEvent)`. The `calEvent` object typically contains attendee/organizer names and emails, notes/custom form responses, timezones, and destination calendar metadata (including credential IDs), so emitting it to application logs leaks sensitive data whenever calendar creation fails. The PR diff reportedly does not change this line, but leaving it in place still constitutes a real information-disclosure bug; this verification relies on the reporters’ referenced line since the file is not part of the PR diff.

**How to replicate.** 1) Configure a booking with an integration/destination calendar that will fail to create events (e.g., revoke OAuth/invalid credential, or set an invalid destination calendar ID). 2) Create a booking with real attendee details (name/email) and optional notes/custom questions. 3) Trigger event creation (normal booking flow) so `createEvent` throws. 4) Check server/application logs: expected is an error message without sensitive payloads; actual is an error log entry containing the serialized error and the full `calEvent` object with attendee PII and destination calendar/credential identifiers (potentially repeated per host in collective bookings).

**Found by:** opus: CE·low, MRV·low; sonnet: MRV·high; glm-vis: MRV·high, MRV·medium

#### A21 — Stale calendar credential reused across references in updateAllCalendarEvents loop

**Location:** `packages/core/eventmanager.ts:493–530`  ·  **Severity:** critical  ·  **Judge confidence:** 0.67  ·  3 findings, 2 cells

**Why this is real.** The bug is that a `credential` variable is declared outside the `for (const reference of calendarReference)` loop and only conditionally reassigned inside it. As reported, the code pattern is effectively `let credential; for (...) { credential = calendarCredentials.find(...) || (await prisma.credential.findFirst(...)); await updateEvent(credential, ...) }` without resetting `credential` when a reference’s credential lookup fails (e.g., deleted credential => DB returns null). This means a later iteration can retain the previous iteration’s credential and call `updateEvent` with the wrong user’s auth, causing incorrect calendar updates or 403/404s; this is a real state-leak bug, not a style issue. (The PR diff does not include this file, so this verification relies on the reported line range and described code structure.)

**How to replicate.** 1) Ensure an event has 2+ `calendarReference` entries (e.g., host A and host B) where each reference normally has its own `credentialId`.
2) Delete/disable host B’s credential record (so `reference.credentialId` exists but is no longer resolvable from `calendarCredentials` and the DB fetch returns null).
3) Trigger an update that calls `updateAllCalendarEvents` (e.g., edit the event title/time and save).
Expected: host A’s calendar updates, and host B’s reference is skipped/marked failed due to missing credential.
Actual: the loop reuses host A’s `credential` when processing host B’s reference, causing an update attempt on the wrong calendar (or a permission error) and potentially marking the wrong references failed or updating the wrong external calendar.

**Found by:** glm-flash: CE·medium; glm-vis: CE·medium

#### A22 — Collective booking destination calendars skip first host and may duplicate organizer due to users.slice(1) assumption

**Location:** `unknown (not in PR diff); search post-PR tree for `teamDestinationCalendars` and `users.slice(1)` in the collective booking calendar-routing code`  ·  **Severity:** high  ·  **Judge confidence:** 0.67  ·  2 findings, 2 cells

**Why this is real.** The reported code constructs `teamDestinationCalendars` from `users.slice(1)`, e.g. `const teamDestinationCalendars = users.slice(1).flatMap(...)`, while separately adding the base destination from `organizerUser` (e.g. `organizerUser.destinationCalendar`). This implicitly assumes `users[0] === organizerUser`, but nothing enforces that ordering; when the organizer is not the first host in `users`, the first host’s destination calendar is never added (skipped by `slice(1)` and absent from the organizer base), and the organizer’s destination can be added twice (once via organizer base, once via inclusion in `slice(1)`). This is a functional correctness bug (missing/duplicated calendar event creation), not a style issue; the file/line cannot be cited exactly because it is explicitly noted as not part of the PR diff, so it must be confirmed by locating the `users.slice(1)` usage in the post-PR code.

**How to replicate.** 1) Configure a collective/team event type with 3 hosts A, B, C, where the booking organizer is B, but the hosts list order returned/loaded is [A, B, C] (A first). 2) Set distinct destination calendars for A, B, and C (ideally Google calendars so duplicates are observable). 3) Create a booking for that event type. Expected: calendar events are created in A, B, and C exactly once each. Actual with the bug: A’s destination calendar is missing entirely, and B’s destination may be included twice (leading to two createEvent calls against the same credential/calendar), while C is included normally.

**Found by:** glm-flash: MRV·high, MRV·low

#### A23 — Booking creation performs sequential awaits and N+1 credential lookups, making latency scale linearly with host/destination count

**Location:** `packages/core/eventmanager.ts:337–520`  ·  **Severity:** high  ·  **Judge confidence:** 0.66  ·  2 findings, 1 cells · ⚠️ **no harness cell found this**

**Why this is real.** Per the clustered reports, post-PR `createAllCalendarEvents` was changed to a sequential `for...of` loop that does `await createEvent(...)` inside the loop, and it also performs `await prisma.credential.findUnique(...)` per destination/reference inside those loops (reported around ~345 and ~510). This is a concrete performance defect: instead of batching independent work (via `Promise.all`) and fetching credentials once (via a single `findMany({ where: { id: { in: [...] } } })`), the code forces serialized network/db calls and repeats identical queries. The PR diff is not provided here, so this verification relies on the reviewers’ consistent line-specific reports; an engineer can confirm by opening the file at the referenced lines and observing the `for...of` + `await` pattern and the `findUnique` calls inside the loops.

**How to replicate.** 1) Configure a booking that triggers `createAllCalendarEvents` for multiple destinations/hosts (e.g., group/collective booking where N attendees/hosts each have a calendar destination). 2) Enable Prisma query logging (e.g., `DEBUG="prisma:query"`) and time the booking endpoint. 3) Increase N (e.g., 1 -> 5 -> 20) and re-run. Expected: roughly constant or sublinear overhead due to parallelization/batched queries. Actual: response time increases ~linearly with N and logs show repeated `prisma.credential.findUnique` queries (N+1 pattern) and serialized calendar event creation.

**Found by:** **no harness cell** — vanilla only: opus

#### A24 — Uncaught prisma/calendar lookup error aborts createAllCalendarEvents loop, failing entire booking and orphaning already-created events

**Location:** `packages/core/eventmanager.ts:336–408`  ·  **Severity:** high  ·  **Judge confidence:** 0.74  ·  2 findings, 2 cells

**Why this is real.** In `createAllCalendarEvents` (reported around lines 336–408), the code performs per-host/per-destination work in a sequential loop and includes an awaited DB lookup like `await prisma.credential.findUnique(...)` (reported at ~line 344) without any surrounding `try/catch` at the per-destination level (or even the method level). Because the loop is sequential, any thrown exception (e.g., prisma timeout/connection error or downstream getCalendar failure) propagates out and aborts processing remaining hosts/destinations. The reports also note that events may already have been created in external calendars before the failure, but references are not saved if the function aborts, leaving those external events orphaned; this is a functional correctness issue, not a style nit. (The file is not in this PR’s diff per the prompt, so this verification relies on the reported line references and described control flow.)

**How to replicate.** 1) Configure a booking with multiple hosts and/or multiple destination calendars so `createAllCalendarEvents` iterates over >1 destination. 2) Induce a failure for exactly one destination during execution (e.g., simulate a transient Prisma failure for `prisma.credential.findUnique` via DB connection drop/timeout, or force one calendar integration’s `getCalendar`/API call to throw). 3) Make a booking request that triggers `EventManager.create()` → `createAllCalendarEvents`. Expected: only the failing destination is skipped/marked failed while other destinations still complete and the booking succeeds (or at least preserves references for already-created external events). Actual: the thrown error is uncaught, the entire booking-creation request fails, remaining destinations are not processed, and any external events created earlier in the loop are left without saved references (orphaned).

**Found by:** opus: CE·low; sonnet: MRV·high

#### A25 — CRM `othercalendar` references updated twice due to overly broad calendar reference filter

**Location:** `packages/core/eventmanager.ts:496–586`  ·  **Severity:** high  ·  **Judge confidence:** 0.95  ·  2 findings, 2 cells

**Why this is real.** The code reportedly changed to filter calendar-related references using `newBooking.references.filter((reference) => reference.type.includes("calendar"))` (and the same for `booking.references`). Because `"othercalendar".includes("calendar")` is true, CRM `othercalendar` references are picked up by this general “calendar” update loop and then updated a second time in the dedicated `othercalendar` loop later (reported around lines 567–586). This creates duplicate external lifecycle updates (two update calls for the same reference) during reschedule/location changes; the PR diff doesn’t include this file, so this verification relies on the reported post-PR code lines.

**How to replicate.** 1) Create a booking that has at least one reference with `type: "othercalendar"` (e.g., via a CRM/other-calendar integration that stores an external event reference). 2) Trigger an operation that updates external calendar events (reschedule the booking or change location). 3) Observe outgoing integration calls/logs: the same `othercalendar` reference will be updated twice—once by the general `includes("calendar")` loop and again by the dedicated `othercalendar` loop—where only one update is expected.

**Found by:** sol: CE·high, MRV·high

#### A26 — Cancel booking fallback loads Credential without app slug/name, breaking getCalendar resolution

**Location:** `packages/features/bookings/lib/handlecancelbooking.ts:638–646`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  2 findings, 2 cells

**Why this is real.** In the DB fallback path, the code reportedly does `foundCalendarCredential = await prisma.credential.findUnique({ where: { id: credentialId } })` and then passes that object to `getCalendar(...)`. Unlike the parallel implementation in `packages/core/eventmanager.ts` (which explicitly selects `app: { select: { slug: true } }` and reconstructs `appname: app.slug`), this fallback does not attach `app.slug`/`appname`, so `getCalendar` can receive a credential missing the `appname` field it relies on to choose the calendar provider. This is a functional mismatch (not stylistic) and can cause cancellation to fail when the fallback path is taken; the PR diff is not available here, so this verification relies on the reported offending lines.

**How to replicate.** 1) Create a collective (multi-host) booking where attendee/cancellation triggers host calendar deletion, and ensure at least one host reference stores only a `credentialId` (so the code must fall back to `prisma.credential.findUnique`). 2) Cancel the booking (via UI or API) to trigger `handleCancelBooking`. 3) Observe that the cancellation workflow attempts to call `getCalendar` with the DB-fetched credential lacking `appname`/`app.slug`; expected: calendar events are deleted for each host; actual: `getCalendar` fails to resolve the calendar app/provider for that host (error or skipped deletion), leaving host events not removed.

**Found by:** sonnet: MRV·medium; glm-vis: CE·high

#### A27 — Collective booking webhook payload leaks all hosts' destinationCalendar identifiers

**Location:** `packages/features/bookings/lib/handlenewbooking.ts:1078–1084`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  2 findings, 1 cells

**Why this is real.** Per the deduplicated reports, around line ~1078 the code for collective events “push[es] every collective host's destinationcalendar row (externalid, credentialid, userid) … into evt”, and `evt` is later spread into webhook/workflow/email payloads. That means a single booking’s event object includes *all* hosts’ `destinationCalendar` entries (including `externalId` which is often an email address), exposing other hosts’ calendar identifiers to any webhook subscriber for the booking/team. This is a concrete confidentiality bug (over-broad data inclusion), not a style issue; note that this file/region is not part of the PR diff, so verification requires reading the current post-PR code at/near the referenced lines.

**How to replicate.** 1) Configure a Collective event type with 2+ hosts, where each host has a Destination Calendar set (so `destinationCalendar` rows exist with `externalId`, `credentialId`, `userId`). 2) Add a webhook subscription for booking-created (or any workflow/webhook that receives the booking event payload) for that team/event type. 3) Create a new booking for that Collective event. Expected: webhook payload contains only the destination calendar relevant to the booking/organizer (or none). Actual (per reports): payload contains an array/list of destinationCalendar rows for *all* hosts, including other users’ `externalId`/`credentialId`/`userId`.

**Found by:** opus: CE·high

#### A28 — Multi-host Google Meet bookings create different Meet links per host calendar event

**Location:** `packages/app-store/googlecalendar/lib/CalendarService.ts:228–259`  ·  **Severity:** high  ·  **Judge confidence:** 0.58  ·  1 findings, 1 cells

**Why this is real.** The per-host calendar event creation calls Google Calendar `events.insert` with `conferenceDataVersion: 1` and a fresh `conferenceData.createRequest` for every host (e.g., `conferenceDataVersion: 1` together with `conferenceData: { createRequest: { requestId: uuidv4() } }`). Because this insert is executed independently for hosts 2..n, Google generates a new Meet for each host’s event, while the booking record/attendee invite keeps only the first returned conference link—so hosts 2..n see a different Meet URL than attendees. (This PR’s diff does not include the relevant file; this verification relies on the reports’ described offending lines/behavior.)

**How to replicate.** 1) Configure a team/collective event type with 2+ hosts, each connected to Google Calendar with Google Meet conferencing enabled. 2) Create a booking as an attendee for a time slot that includes all hosts. 3) Inspect the calendar event created on each host’s Google Calendar and the invite/booking details sent to the attendee. Expected: all parties share the same Google Meet link. Actual: host #1’s event matches the attendee link, while host #2..n’s calendar events contain different Meet URLs (distinct meetings).

**Found by:** glm-flash: MRV·high

#### A29 — handleCancelBooking builds deletion Promise array with undefined entries, risking skipped/duplicated external calendar deletions

**Location:** `packages/features/bookings/lib/handlecancelbooking.ts:482–495`  ·  **Severity:** high  ·  **Judge confidence:** 0.62  ·  1 findings, 1 cells

**Why this is real.** The deduped report indicates that around ~line 486 `handlecancelbooking` pushes “raw promises including undefined” into an `apideletes` array (e.g., an `apideletes.push(<maybePromiseOrUndefined>)` pattern inside a loop over calendar references). This is a real functional defect because `Promise.all(apideletes)` (or similar) will treat `undefined` as an already-resolved value, silently masking the fact that some intended deletions were never scheduled; additionally, pushing per-reference without de-duplication can multiply deletion attempts for the same external event, increasing the chance of missed cleanup/orphaned calendar events. The PR does not include this file in its diff, so verification must be done by directly inspecting the current code near the reported line.

**How to replicate.** 1) Read `handlecancelbooking.ts` around lines ~482–495 and locate where `apideletes` is populated (likely inside a loop over `calendarReferences` / attendees / destinations). 2) Confirm there is a `.push(...)` where the pushed expression can be `undefined` (conditional operator/short-circuit `&&`) or where the same external event deletion is pushed multiple times per calendar reference. 3) Run the app with an event that creates multiple calendar references (e.g., multiple destinations/calendars) and cancel the booking. 4) Observe logs/network: expected is exactly one successful deletion per external calendar event; actual is that some deletions are not attempted (because `undefined` is pushed) and/or duplicate deletion calls occur, leaving an external calendar event orphaned or producing inconsistent deletion results without an explicit failure.

**Found by:** glm-flash: CE·low

#### A30 — Fallback credential construction ignores `invalid` flag and can use revoked/broken OAuth credentials

**Location:** `packages/core/eventmanager.ts:357–366`  ·  **Severity:** high  ·  **Judge confidence:** 0.72  ·  1 findings, 1 cells

**Why this is real.** In the fallback path, the code manually re-creates a credential object from a DB row and explicitly copies the flag verbatim (e.g., `invalid: credentialFromDb.invalid`) but does not gate usage on it before passing the credential into calendar operations. The same file later hands that constructed credential directly to calendar integration calls (create/update/get calendar) without filtering out `invalid` credentials, unlike the normal user-credentials query path which typically excludes invalid ones. The PR diff does not include these files/lines, so this verification relies on the reported line ranges and the described object construction/usage pattern.

**How to replicate.** 1) Ensure a calendar OAuth credential is marked invalid/revoked in the DB (set the credential's `invalid` flag true, e.g., by revoking the token or toggling the DB field). 2) Trigger a code path that uses the fallback credential fetch/construction in `eventmanager.ts` (e.g., an event update/create that falls back to fetching a credential by ID rather than via the normal user credentials list). 3) Observe that the system still attempts calendar API calls with that credential (actual), leading to integration errors or unintended use of a revoked token; expected behavior is to reject/skip invalid credentials and fail early with a clear error or choose an alternative valid credential.

**Found by:** sonnet: MRV·medium

#### A31 — Reschedule can persist in DB even when some host calendar updates fail (no rollback/retry)

**Location:** `packages/core/eventmanager.ts:542–570`  ·  **Severity:** high  ·  **Judge confidence:** 0.66  ·  1 findings, 1 cells

**Why this is real.** The reported code around `eventmanager.ts:542` records per-host calendar update failures only as flags/results ("per-host update failures are only returned as flags") and then continues the reschedule flow without throwing or compensating. Because the DB reschedule write happens regardless, there is no rollback or retry mechanism when one host update fails, leaving some external host calendars at the old time while the booking is updated. This is a real consistency bug (partial failure handling) rather than a style issue; the PR does not touch this file in its diff, so verification requires reading the existing logic at/near the referenced lines.

**How to replicate.** 1) Create an event with multiple hosts (team/round-robin) where each host has a connected calendar. 2) Force one host calendar update to fail during a reschedule (e.g., revoke that host’s OAuth token, make their calendar read-only, or simulate a provider 401/5xx) while another host remains valid. 3) Reschedule the booking. Expected: reschedule should either fail atomically (DB not changed) or retry/compensate so all host calendars match. Actual: booking/reschedule is committed in the database, but the failing host’s calendar still shows the old time (or missing update), producing inconsistent state across hosts.

**Found by:** sol: CE·high

### Golden-duplicates removed (would double-count)

- **duplicate of golden #2** — “Logic error: when externalCalendarId is provided, you're searching for a calendar where externalId === externalCalendarId, but this will always fail since you'r…”
  - cluster: Legacy no-credential destination path creates events without externalCalendarId, breaking later update/delete routing (`packages/core/eventmanager.ts`), 395 findings, 67 cells
- **duplicate of golden #3** — “Logic inversion in organization creation: The slug property is now conditionally set when IS_TEAM_BILLING_ENABLED is true, instead of when it's false as origina…”
  - cluster: Organization slug assignment logic inverted, breaking non-billing org URLs and bypassing requestedSlug gate in billing mode (`packages/trpc/server/routers/viewer/organizations/create.handler.ts`), 50 findings, 23 cells
- **duplicate of golden #5** — “The `credential` may be undefined when passed to `updateEvent` if `reference.credentialId` is set but the credential is not found. This can lead to a runtime er…”
  - cluster: DB-fetched calendar credential missing app relation is silently skipped or passed as undefined, causing missing/failed calendar sync (`packages/core/eventmanager.ts`), 21 findings, 13 cells
- **duplicate of golden #5** — “The `credential` may be undefined when passed to `updateEvent` if `reference.credentialId` is set but the credential is not found. This can lead to a runtime er…”
  - cluster: updateAllCalendarEvents can call updateEvent with missing/stale credential, aborting updates for other references (`packages/lib/CalendarManager/eventmanager.ts`), 8 findings, 6 cells
