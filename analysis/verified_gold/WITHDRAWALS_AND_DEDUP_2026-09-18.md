# Withdrawals and deduplication — 2026-09-18

Post-publication evidence audit triggered by an external review of REPORT.md (then `REPORT_FINAL.md`), which found
(a) two "verified" defects whose tests do not demonstrate them, and (b) duplicates inside the
supposedly distinct verified universe. Every decision below was independently validated against
the stored artifacts (tests, fixes, logs, registry, golden comments) before being applied, and the
kept-after-audit cases were adjudicated with the repo's own cross-fix standard (a pair is one
defect only if one minimal fix cures both tests).

## Audit method

1. **Scripted failure-reason audit of all 110 defect head logs** — first-line `RESULT:` records
   were extracted for every defect and scanned for incidental-error signatures (undefined method,
   undefined local variable, NameError, NoMethodError, missing response, TypeError on undefined).
   Six hits; each was adjudicated individually (see below). No head run that should have failed
   recorded PASS, and every recorded fixed run recorded PASS.
2. **Mock-target survey of all test diffs** — every `vi.mock(...)` target was extracted from all
   110 `test.diff` files. 38 tests (all in the TypeScript projects) use `vi.mock`, but every one
   mocks *infrastructure or external services* (prisma, emails, EventManager, crypto, jsforce,
   app-store utils) for test isolation. **Only 11059-D28 mocks the very dependency its claim is
   about** — the single manufactured-failure case in the universe.
3. **Cross-fix adjudication of flagged duplicate pairs** — pairs flagged by the pairwise vote
   record, DUP_REVIEW Section C open items, and the external review were adjudicated by checking
   whether either defect's minimal fix cures the other's own test.

## Removals (5)

### Withdrawn — evidence does not demonstrate the claimed defect (3)

| defect | bundle | one-line evidence |
|---|---|---|
| 11059-D28 | 11059-B31 | `test.diff` mocks zod with `default: undefined` ("Simulate the real-world failure mode"), but the installed zod 3.22.2 exports a default (`lib/index.js:29 exports.default = z`; `index.mjs:4006 export { z as default }`) — the recorded head crash cannot occur against the real dependency. |
| 4-D04 | 4-B02 | `logs/head.log:1` = `RESULT: FAIL: undefined method 'blank?' for "example.com":String` — a harness stub error that fires *before* the claimed queue-flooding behavior; sibling run fails on missing `response`; `fix.patch` also changes production code solely to survive incomplete stubs (`blank?` → `to_s.strip.empty?`, `respond_to?(:response)` guard). |
| 4-D29 | 4-B26 | `logs/head.log:1` = `RESULT: FAIL: expected URI::InvalidURIError for 'http://', got #<NameError: uninitialized constant TopicEmbed::Nokogiri>` — the claimed `URI()` raise never fired on the recorded toolchain (ruby 2.6.10 accepts `URI('http://')` with empty host); the fix's own guard then manufactures the expected exception. The underlying line-anchored-regex class may be real but is not demonstrated by this evidence. |

### Merged as duplicates (2)

| defect | kept / covered by | one-line evidence |
|---|---|---|
| 11059-D32 | 11059-D19 | Same missing-secret/missing-header auth bypass at `apps/web/pages/api/webhook/app-credential.ts:25`; both fixes add a missing-secret guard to the same hunk; only the expected status (500 vs 403) differs — one fail-closed decision, per the repo's own D22/D23 merge precedent. |
| 11059-D14 | original golden (`cal_dot_com.json:158`) | The golden comment explicitly names HubSpot/HubspotToken and the fetch-Response mismatch, and prescribes adjusting the return value — D14's exact mechanism and fix site; not distinct hidden gold. |

## Kept after audit (4)

| case | verdict | reason |
|---|---|---|
| 4-D14 (bundle 4-B08) | **keep** | Head failure (`NoMethodError: undefined method 'raw' for nil:NilClass`) fires *at* the claimed site: nil `embed.post` reaches `PostRevisor.new` from the real, unstubbed `topic_embed.rb`. The fix adds the nil guard in the file under test. |
| 4-D45 (bundle 4-B46) | **keep** | The Ruby-2.0 `String#scrub` NoMethodError **is** the claim; the runtime emulation is applied identically to head and fixed runs, so the PASS is causally the fix removing the `scrub` call. (Residual note: the Ruby-2.0 pin is asserted by the finder reports and era toolchain, not stored repo metadata.) |
| 11059-D33 vs 11059-D22 | **distinct — keep both** | D22 = throw-vs-return at `parseRefreshTokenResponse.ts:19-21`; D33 = Salesforce schema strictness at `CalendarService.ts:45`. Neither minimal fix cures the other's own test (D33's test asserts `credential.update` was called; D22's fix alone leaves it red). |
| 4-D56 vs 4-D36 | **distinct — keep both** | D56 = crash guard at `topic_retriever.rb:49` (nil `embed_by_username` → NoMethodError); D36 = silent no-op at line 50 (`return if user.blank?` leaves embed loading). Orthogonal fixes at adjacent lines — resolves DUP_REVIEW Section C's open item under its own "fixing one does not fix the other → two defects" rule. |

Also confirmed clean: the unanimous 11059|B24|B33 pairwise dup vote is already correctly folded —
no registry defect derives from 11059-B33; 11059-D26 (from B24) is the sole keeper of that claim.

## Resulting universe

- **105 verified distinct hidden-gold defects** (was 110): 3 withdrawn, 2 merged as duplicates.
- Per-PR verified counts: PR 4 = 42, PR 8 = 6, PR 10 = 20, PR 10967 = 5, PR 11059 = 15, PR 14740 = 17.
- Verified-variant denominator: 42 original goldens + 105 = **147** (was 152).
- All downstream metrics (DEFECT_ASSIGN, DEFECT_METRICS, catalog, figures, dashboard, report
  tables) were recomputed the same day; the withdrawn/duplicate tiers are excluded from the
  verified variant automatically by `tools/verified_gold_defect_metrics.py`'s tier filter.
- The evidence directories of the withdrawn and merged defects are retained untouched, so each
  can be re-verified with a valid reproducer (e.g. 4-D29 with a URL that genuinely raises, plus
  a Nokogiri stub; 4-D04 with complete request stubs).

## Provenance

- External review findings validated 2026-09-18 by independent read-only review lanes
  (per-defect artifact adjudication; mock-target survey; cross-fix pair adjudication).
- Registry/meta changes applied 2026-09-18: `DEFECT_REGISTRY.json` (tiers, header counts, per_pr),
  per-defect `meta.json` for the five ids (fields added; historical verdicts preserved).
