# Hidden-gold defect catalogue

**101 distinct verified defects.** Every one has an executed test that failed on the PR head and a
documented fix that made it pass. Two evidence levels:

**Every defect is an independent unit**: it owns `defects/<id>/{test.diff,fix.patch,logs/,meta.json}`.
No defect shares a test with another. `test_origin` records whether the test was written by the verifier
for this defect alone (with a sibling-fix orthogonality check) or copied from the original execution
container where it had been authored for exactly this claim.

Merged duplicates and restored/renamed entries carry a provenance note.

## Known open items (do not treat this catalogue as exhaustive)

- `label_vs_test_mismatch`: where a defect's own test declares a claim that does not match the
  registry label, the TEST is the truth (the label was inherited from an LLM merge audit).
- Under-count: the audits' claim lists imply further distinct defects not in the registry yet
  (4/B33 nil-`downcase` crash, 4/B39 case-sensitive host compare, 4/B26 wrong-rescue, 4/B24
  locale-dependent content_sha1, 4/B07 missing scheme validation, 8/B05 API-contract break,
  several 11059/B19 + 11059/B23 facets). The count is a **floor**, not a ceiling.

## PR 4 — 39 defects

### 4-D01 — Incorrect resolution of relative/protocol-relative URLs in absolutizeurls
- **location**: `app/models/topicembed.rb:64`  ·  **evidence**: `own_executed`  ·  bundle `4-B01` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B01-absolutizeurls-treats-protocol-relative-urls----as-r/defects/4-D01/test.diff`
- **fix**: `analysis/verified_gold/4/B01-absolutizeurls-treats-protocol-relative-urls----as-r/defects/4-D01/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B01-absolutizeurls-treats-protocol-relative-urls----as-r/defects/4-D01/logs`
- **finding**: app/models/topicembed.rb:64 incorrectly rewrites protocol-relative urls as root-relative paths on the article host
- **merged_in_from**: 4-D44

### 4-D03 — Referer header trusted as spoofable embeddability/auth gate
- **location**: `app/controllers/embedcontroller.rb:26`  ·  **evidence**: `own_executed`  ·  bundle `4-B02` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B02-embed-requests-are-wrongly-rejected-due-to-strict-unnorm/defects/4-D03/test.diff`
- **fix**: `analysis/verified_gold/4/B02-embed-requests-are-wrongly-rejected-due-to-strict-unnorm/defects/4-D03/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B02-embed-requests-are-wrongly-rejected-due-to-strict-unnorm/defects/4-D03/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: embedcontroller.rb:26 requiring a referer breaks legitimate embeds when browsers strip it (https→http navigation, referrer-policy: no-referrer), causing 403

### 4-D04 — Retrieval jobs enqueued before throttle/dedupe, allowing Sidekiq queue flooding
- **location**: `app/controllers/embedcontroller.rb:15`  ·  **evidence**: `own_executed`  ·  bundle `4-B02` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B02-embed-requests-are-wrongly-rejected-due-to-strict-unnorm/defects/4-D04/test.diff`
- **fix**: `analysis/verified_gold/4/B02-embed-requests-are-wrongly-rejected-due-to-strict-unnorm/defects/4-D04/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B02-embed-requests-are-wrongly-rejected-due-to-strict-unnorm/defects/4-D04/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: the loading page reloads every 30 seconds unconditionally, looping forever on permanent retrieval failure instead of showing an error

### 4-D05 — Case-sensitive/unnormalized host comparison against free-form embeddablehost setting
- **location**: `app/controllers/embedcontroller.rb:26-27`  ·  **evidence**: `own_executed`  ·  bundle `4-B02` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B02-embed-requests-are-wrongly-rejected-due-to-strict-unnorm/defects/4-D05/test.diff`
- **fix**: `analysis/verified_gold/4/B02-embed-requests-are-wrongly-rejected-due-to-strict-unnorm/defects/4-D05/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B02-embed-requests-are-wrongly-rejected-due-to-strict-unnorm/defects/4-D05/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: referer check in embedcontroller.rb:25 is a weak/forgeable authorization gate for the new public embed/best route, and uri(referer).host may not match embeddablehost with port/scheme

### 4-D06 — Staff-only throttle bypass in RetrieveTopic job
- **location**: `app/controllers/embed_controller.rb`  ·  **evidence**: `own_executed`  ·  bundle `4-B02` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B02-embed-requests-are-wrongly-rejected-due-to-strict-unnorm/defects/4-D06/test.diff`
- **fix**: `analysis/verified_gold/4/B02-embed-requests-are-wrongly-rejected-due-to-strict-unnorm/defects/4-D06/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B02-embed-requests-are-wrongly-rejected-due-to-strict-unnorm/defects/4-D06/logs`
- **orthogonality**: bundle fix leaves it red = `True`

### 4-D07 — topicembed remote article download lacks open/read timeout and size limit
- **location**: `app/models/topicembed.rb:48`  ·  **evidence**: `own_executed`  ·  bundle `4-B03` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B03-unbounded-open-uri-fetch-in-topicembed-can-hang-jobs-or-/defects/4-D07/test.diff`
- **fix**: `analysis/verified_gold/4/B03-unbounded-open-uri-fetch-in-topicembed-can-hang-jobs-or-/defects/4-D07/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B03-unbounded-open-uri-fetch-in-topicembed-can-hang-jobs-or-/defects/4-D07/logs`
- **finding**: open(url).read buffers responses without a size limit, allowing large responses to exhaust sidekiq worker memory

### 4-D10 — topicembeds migration uses destructive force: true and lacks foreign keys/dependent cleanup
- **location**: `db/migrate/20131217174004createtopicembeds.rb:3`  ·  **evidence**: `own_executed`  ·  bundle `4-B04` (confirmed_regression)
- **test**: `analysis/verified_gold/4/B04-destructive-force-true-in-createtable-migration-can-dr/defects/4-D10/test.diff`
- **fix**: `analysis/verified_gold/4/B04-destructive-force-true-in-createtable-migration-can-dr/defects/4-D10/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B04-destructive-force-true-in-createtable-migration-can-dr/defects/4-D10/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: db/migrate/20131217174004createtopicembeds.rb:3 — force: true drops an existing topicembeds table and its data if present when this migration runs.

### 4-D11 — Redis throttle key can become permanent due to non-atomic SETNX + EXPIRE
- **location**: `lib/topicretriever.rb:27`  ·  **evidence**: `own_executed`  ·  bundle `4-B06` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B06-redis-throttle-key-can-become-permanent-due-to-non-atomi/defects/4-D11/test.diff`
- **fix**: `analysis/verified_gold/4/B06-redis-throttle-key-can-become-permanent-due-to-non-atomi/defects/4-D11/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B06-redis-throttle-key-can-become-permanent-due-to-non-atomi/defects/4-D11/logs`
- **finding**: the redis setnx/expire throttle operations are non-atomic: a crash between them throttles that url forever.
- **merged_in_from**: 4-D25

### 4-D12 — SSRF via open-uri redirects not revalidated against allowed host
- **location**: `app/models/topicembed.rb:48`  ·  **evidence**: `own_executed`  ·  bundle `4-B07` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B07-redirect-based-ssrf-only-initial-url-host-is-validated-w/defects/4-D12/test.diff`
- **fix**: `analysis/verified_gold/4/B07-redirect-based-ssrf-only-initial-url-host-is-validated-w/defects/4-D12/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B07-redirect-based-ssrf-only-initial-url-host-is-validated-w/defects/4-D12/logs`
- **finding**: url validation occurs only before redirects, allowing an approved host to redirect server-side requests to internal or metadata endpoints.
- **merged_in_from**: 4-D53

### 4-D14 — TopicEmbed re-import crashes when the embedded post was deleted (embed.post is nil)
- **location**: `app/models/topicembed.rb:32`  ·  **evidence**: `own_executed`  ·  bundle `4-B08` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B08-topicembed-re-import-crashes-when-the-embedded-post-was-/defects/4-D14/test.diff`
- **fix**: `analysis/verified_gold/4/B08-topicembed-re-import-crashes-when-the-embedded-post-was-/defects/4-D14/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B08-topicembed-re-import-crashes-when-the-embedded-post-was-/defects/4-D14/logs`
- **finding**: postrevisor.new(post) with no nil guard crashes if embed.postid points at a deleted post (app/models/topicembed.rb:23-24)
- **merged_in_from**: 4-D21

### 4-D15 — check-then-create race on unique TopicEmbed embedurl
- **location**: `app/models/topicembed.rb:15`  ·  **evidence**: `own_executed`  ·  bundle `4-B09` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B09-race-condition-non-atomic-exists-create-on-topicembed-c/defects/4-D15/test.diff`
- **fix**: `analysis/verified_gold/4/B09-race-condition-non-atomic-exists-create-on-topicembed-c/defects/4-D15/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B09-race-condition-non-atomic-exists-create-on-topicembed-c/defects/4-D15/logs`
- **finding**: topicembed lookup-then-create logic is race-unsafe, so concurrent retrieval jobs can hit a unique-index exception instead of reusing the embed.

### 4-D16 — enqueue/publish before outer transaction commits
- **location**: `app/models/topicembed.rb:21`  ·  **evidence**: `own_executed`  ·  bundle `4-B09` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B09-race-condition-non-atomic-exists-create-on-topicembed-c/defects/4-D16/test.diff`
- **fix**: `analysis/verified_gold/4/B09-race-condition-non-atomic-exists-create-on-topicembed-c/defects/4-D16/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B09-race-condition-non-atomic-exists-create-on-topicembed-c/defects/4-D16/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: app/models/topicembed.rb:21 — postcreator enqueues and publishes before this outer transaction commits, exposing missing or phantom topics to asynchronous consumers

### 4-D17 — Embed URL lookup uses exact, unnormalized string match, allowing duplicate topics for equivalent URLs
- **location**: `app/models/topicembed.rb:15`  ·  **evidence**: `own_executed`  ·  bundle `4-B12` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B12-embed-url-lookup-uses-exact-unnormalized-string-match-al/defects/4-D17/test.diff`
- **fix**: `analysis/verified_gold/4/B12-embed-url-lookup-uses-exact-unnormalized-string-match-al/defects/4-D17/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B12-embed-url-lookup-uses-exact-unnormalized-string-match-al/defects/4-D17/logs`
- **finding**: topicembed.rb:79 lookup is an exact string match on embedurl, so query params, trailing slashes, and fragments create separate topics for the same article

### 4-D18 — Inline feed poll exceptions abort performretrieve before HTTP fallback and may propagate into retry logic
- **location**: `lib/topicretriever.rb:41`  ·  **evidence**: `own_executed`  ·  bundle `4-B14` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B14-unrescued-inline-feed-poll-aborts-http-fallback-on-embed/defects/4-D18/test.diff`
- **fix**: `analysis/verified_gold/4/B14-unrescued-inline-feed-poll-aborts-http-fallback-on-embed/defects/4-D18/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B14-unrescued-inline-feed-poll-aborts-http-fallback-on-embed/defects/4-D18/logs`
- **finding**: lib/topicretriever.rb:41 — an exception from the inline pollfeed propagates and skips the fetchhttp fallback, so the article is never retrieved.

### 4-D20 — ignored revise! failure with unconditional contentsha1 advance
- **location**: `app/models/topicembed.rb:37`  ·  **evidence**: `own_executed`  ·  bundle `4-B15` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B15-topicembed-advances-contentsha1-even-when-post-revision-/defects/4-D20/test.diff`
- **fix**: `analysis/verified_gold/4/B15-topicembed-advances-contentsha1-even-when-post-revision-/defects/4-D20/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B15-topicembed-advances-contentsha1-even-when-post-revision-/defects/4-D20/logs`
- **finding**: app/models/topicembed.rb:37 — advancing contentsha1 without checking revise! success permanently marks callback-rejected post updates as imported

### 4-D22 — concurrent import body/digest race
- **location**: `app/models/topicembed.rb:37`  ·  **evidence**: `own_executed`  ·  bundle `4-B15` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B15-topicembed-advances-contentsha1-even-when-post-revision-/defects/4-D22/test.diff`
- **fix**: `analysis/verified_gold/4/B15-topicembed-advances-contentsha1-even-when-post-revision-/defects/4-D22/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B15-topicembed-advances-contentsha1-even-when-post-revision-/defects/4-D22/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: app/models/topicembed.rb:36 — concurrent imports can interleave post and checksum writes, leaving mismatched content that later polls skip because its checksum already matches.

### 4-D23 — TopicEmbed embedurl column defaults to varchar(255), causing failures for valid long URLs during imports/polling
- **location**: `db/migrate/20131217174004createtopicembeds.rb:6`  ·  **evidence**: `own_executed`  ·  bundle `4-B16` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B16-topicembed-embedurl-column-defaults-to-varchar255-causi/defects/4-D23/test.diff`
- **fix**: `analysis/verified_gold/4/B16-topicembed-embedurl-column-defaults-to-varchar255-causi/defects/4-D23/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B16-topicembed-embedurl-column-defaults-to-varchar255-causi/defects/4-D23/logs`
- **finding**: embedurl uses varchar(255) despite accepting unbounded urls, causing longer article urls to fail asynchronously during insertion

### 4-D26 — mutating caller-owned contents string with <<
- **location**: `app/models/topicembed.rb:13`  ·  **evidence**: `own_executed`  ·  bundle `4-B24` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B24-topicembed-import-mutates-caller-owned-contents-via--/defects/4-D26/test.diff`
- **fix**: `analysis/verified_gold/4/B24-topicembed-import-mutates-caller-owned-contents-via--/defects/4-D26/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B24-topicembed-import-mutates-caller-owned-contents-via--/defects/4-D26/logs`
- **finding**: contents << "\n<hr>..." mutates the caller's string in place and raises on frozen strings (app/models/topicembed.rb:12)

### 4-D28 — Existing TopicEmbed updates ignore title-only changes, leaving topic titles stale
- **location**: `app/models/topicembed.rb:34`  ·  **evidence**: `own_executed`  ·  bundle `4-B25` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B25-existing-topicembed-updates-ignore-title-only-changes-le/defects/4-D28/test.diff`
- **fix**: `analysis/verified_gold/4/B25-existing-topicembed-updates-ignore-title-only-changes-le/defects/4-D28/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B25-existing-topicembed-updates-ignore-title-only-changes-le/defects/4-D28/logs`
- **finding**: app/models/topicembed.rb:34 ignores title changes for existing embeds, preventing title-only feed updates and title corrections

### 4-D29 — TopicEmbedImport mutates caller's contents string in place
- **location**: `app/models/topic_embed.rb`  ·  **evidence**: `own_executed`  ·  bundle `4-B26` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B26-topicembed-url-guard-uses-line-anchored-regex-and-later-/defects/4-D29/test.diff`
- **fix**: `analysis/verified_gold/4/B26-topicembed-url-guard-uses-line-anchored-regex-and-later-/defects/4-D29/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B26-topicembed-url-guard-uses-line-anchored-regex-and-later-/defects/4-D29/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: topicembedimport mutates the caller's contents string in place, and url =~ /^https?\:\/\// accepts degenerate urls like 'http://' causing uri::invalidurierror in absolutizeurls, crashing the importing job instead of reje

### 4-D33 — Embed/topic retrieval synchronously runs full feed poll (Jobs::PollFeed) on cache miss, coupling embeds to feed health and enabling resource
- **location**: `lib/topicretriever.rb:47`  ·  **evidence**: `own_executed`  ·  bundle `4-B28` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B28-embed-topic-retrieval-synchronously-runs-full-feed-poll-/defects/4-D33/test.diff`
- **fix**: `analysis/verified_gold/4/B28-embed-topic-retrieval-synchronously-runs-full-feed-poll-/defects/4-D33/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B28-embed-topic-retrieval-synchronously-runs-full-feed-poll-/defects/4-D33/logs`
- **finding**: performretrieve calls jobs::pollfeed.new.execute({}) inline, running a full feed fetch, parse, and import synchronously on every cache-miss embed request with no timeout (lib/topicretriever.rb:44-46)
- **merged_in_from**: 4-D19

### 4-D34 — TopicEmbed uses open(url) without requiring open-uri, causing URL opens to be treated as local files
- **location**: `app/models/topicembed.rb:48`  ·  **evidence**: `own_executed`  ·  bundle `4-B29` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B29-topicembed-uses-openurl-without-requiring-open-uri-caus/defects/4-D34/test.diff`
- **fix**: `analysis/verified_gold/4/B29-topicembed-uses-openurl-without-requiring-open-uri-caus/defects/4-D34/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B29-topicembed-uses-openurl-without-requiring-open-uri-caus/defects/4-D34/logs`
- **finding**: app/models/topicembed.rb:48 — open(url).read relies on open-uri but topicembed.rb never requires it, so kernelopen can treat the url as a filename and raise errno::enoent; add require 'open-uri'

### 4-D36 — Missing/mismatched configured user silently returns and leaves embed loading
- **location**: `lib/topicretriever.rb:50`  ·  **evidence**: `own_executed`  ·  bundle `4-B33` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B33-embed-topic-retrieval-can-crash-or-silently-no-op-when-e/defects/4-D36/test.diff`
- **fix**: `analysis/verified_gold/4/B33-embed-topic-retrieval-can-crash-or-silently-no-op-when-e/defects/4-D36/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B33-embed-topic-retrieval-can-crash-or-silently-no-op-when-e/defects/4-D36/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: lib/topicretriever.rb:50 — return if user.blank? silently gives up when embedbyusername is '' (the shipped default) or names a missing user, so the job reports success and the embed stays on "loading" forever with nothin

### 4-D37 — Gemfile updated with new gems but default Gemfile.lock not regenerated, breaking frozen/deployment bundler installs
- **location**: `Gemfile`  ·  **evidence**: `own_executed`  ·  bundle `4-B34` (confirmed_regression)
- **test**: `analysis/verified_gold/4/B34-gemfile-updated-with-new-gems-but-default-gemfilelock-no/defects/4-D37/test.diff`
- **fix**: `analysis/verified_gold/4/B34-gemfile-updated-with-new-gems-but-default-gemfilelock-no/defects/4-D37/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B34-gemfile-updated-with-new-gems-but-default-gemfilelock-no/defects/4-D37/logs`
- **finding**: ruby-readability and simple-rss added to gemfile:209 but only gemfilerails4.lock regenerated; the default gemfile.lock is untouched, breaking bundle install --deployment/frozen builds

### 4-D38 — Rails migration adds NOT NULL column with DEFAULT, causing full table rewrite and ACCESS EXCLUSIVE lock on PostgreSQL < 11
- **location**: `db/migrate/20131219203905addcookmethodtoposts.rb:3`  ·  **evidence**: `own_executed`  ·  bundle `4-B37` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B37-rails-migration-adds-not-null-column-with-default-causin/defects/4-D38/test.diff`
- **fix**: `analysis/verified_gold/4/B37-rails-migration-adds-not-null-column-with-default-causin/defects/4-D38/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B37-rails-migration-adds-not-null-column-with-default-causin/defects/4-D38/logs`
- **finding**: db/migrate/20131219203905addcookmethodtoposts.rb:3 adds a column with a non-null default to posts, rewriting the whole table under an access exclusive lock on postgres < 11

### 4-D40 — configured host contains scheme causing exact host mismatch
- **location**: `lib/topic_retriever.rb`  ·  **evidence**: `own_executed`  ·  bundle `4-B39` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B39-embeddable-host-validation-uses-strict-string-equality-r/defects/4-D40/test.diff`
- **fix**: `analysis/verified_gold/4/B39-embeddable-host-validation-uses-strict-string-equality-r/defects/4-D40/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B39-embeddable-host-validation-uses-strict-string-equality-r/defects/4-D40/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: p2: embed url/host mismatch when admin enters a scheme in embeddablehost (exact equality against uri(...).host rejects all embeds if scheme included, killing the feature)

### 4-D41 — Migration backfills posts.cookmethod to rawhtml, causing all existing posts to bypass cooking/sanitization
- **location**: `db/migrate/20131219203905addcookmethodtoposts.rb:3`  ·  **evidence**: `own_executed`  ·  bundle `4-B40` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B40-migration-backfills-postscookmethod-to-rawhtml-causing-a/defects/4-D41/test.diff`
- **fix**: `analysis/verified_gold/4/B40-migration-backfills-postscookmethod-to-rawhtml-causing-a/defects/4-D41/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B40-migration-backfills-postscookmethod-to-rawhtml-causing-a/defects/4-D41/logs`
- **finding**: migration defaults posts to the rawhtml enum value, causing ordinary posts to bypass cooking and render raw markdown/html.

### 4-D42 — Dead feed-modified cache key means PollFeed always re-downloads and reprocesses the full feed
- **location**: `pollfeed.rb:20`  ·  **evidence**: `own_executed`  ·  bundle `4-B41` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B41-dead-feed-modified-cache-key-means-pollfeed-always-re-do/defects/4-D42/test.diff`
- **fix**: `analysis/verified_gold/4/B41-dead-feed-modified-cache-key-means-pollfeed-always-re-do/defects/4-D42/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B41-dead-feed-modified-cache-key-means-pollfeed-always-re-do/defects/4-D42/logs`
- **finding**: pollfeed.rb:20 feedkey is defined but never used

### 4-D43 — incorrect default-port comparison in absolutize_urls
- **location**: `topicembed.rb:59`  ·  **evidence**: `own_executed`  ·  bundle `4-B42` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B42-topicembedrb59-port-logic-should-compare-against-uridef/defects/4-D43/test.diff`
- **fix**: `analysis/verified_gold/4/B42-topicembedrb59-port-logic-should-compare-against-uridef/defects/4-D43/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B42-topicembedrb59-port-logic-should-compare-against-uridef/defects/4-D43/logs`
- **finding**: topicembed.rb:59 port logic should compare against uri.defaultport; https://host:80 and http://host:443 produce wrong prefixes
- **merged_in_from**: 4-D02

### 4-D45 — Poll feed processing calls `String#scrub` via `stringscrub`, crashing on Ruby 2.0 (requires Ruby >= 2.1)
- **location**: `pollfeed.rb:35`  ·  **evidence**: `own_executed`  ·  bundle `4-B46` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B46-poll-feed-processing-calls-stringscrub-via-stringscrub/defects/4-D45/test.diff`
- **fix**: `analysis/verified_gold/4/B46-poll-feed-processing-calls-stringscrub-via-stringscrub/defects/4-D45/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B46-poll-feed-processing-calls-stringscrub-via-stringscrub/defects/4-D45/logs`
- **finding**: stringscrub requires ruby >= 2.1; on ruby 2.0, which discourse targeted at this time, it raises nomethoderror even for valid strings

### 4-D46 — Embed source hash includes localized footer, causing false-positive content changes on locale/footer updates
- **location**: `app/models/topicembed.rb:16`  ·  **evidence**: `own_executed`  ·  bundle `4-B48` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B48-embed-source-hash-includes-localized-footer-causing-fals/defects/4-D46/test.diff`
- **fix**: `analysis/verified_gold/4/B48-embed-source-hash-includes-localized-footer-causing-fals/defects/4-D46/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B48-embed-source-hash-includes-localized-footer-causing-fals/defects/4-D46/logs`
- **finding**: app/models/topicembed.rb:16 — hashing after appending the localized footer couples source-change detection to presentation text, so footer or locale changes trigger needless post revisions

### 4-D47 — `skip_validations` allows saving posts/topics with invalid or unsafe data (validations fully bypassed)
- **location**: `lib/postrevisor.rb:85`  ·  **evidence**: `own_executed`  ·  bundle `4-B51` (confirmed_regression)
- **test**: `analysis/verified_gold/4/B51-skipvalidations-allows-saving-posts-topics-with-invalid/defects/4-D47/test.diff`
- **fix**: `analysis/verified_gold/4/B51-skipvalidations-allows-saving-posts-topics-with-invalid/defects/4-D47/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B51-skipvalidations-allows-saving-posts-topics-with-invalid/defects/4-D47/logs`
- **finding**: p2: importremote with skipvalidations: true can create topics with nil/blank titles when both opts[:title] and doc.title are nil

### 4-D48 — poll_feed job processes unbounded RSS items, creating/enqueuing work for every entry in a single run
- **location**: `app/jobs/scheduled/poll_feed.rb`  ·  **evidence**: `own_executed`  ·  bundle `4-B56` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B56-pollfeed-job-processes-unbounded-rss-items-creating-enqu/defects/4-D48/test.diff`
- **fix**: `analysis/verified_gold/4/B56-pollfeed-job-processes-unbounded-rss-items-creating-enqu/defects/4-D48/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B56-pollfeed-job-processes-unbounded-rss-items-creating-enqu/defects/4-D48/logs`
- **finding**: [advisory] pollfeed fetches the feed with open() and then iterates rss.items with no count cap, running postcreator (which enqueues per-post processing jobs) for every item in a single job. a feed with thousands of entri

### 4-D49 — EmbedController enqueues RetrieveTopic job but spec expects synchronous TopicRetriever call
- **location**: `app/controllers/embedcontroller.rb:16`  ·  **evidence**: `own_executed`  ·  bundle `4-B60` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B60-embedcontroller-enqueues-retrievetopic-job-but-spec-expe/defects/4-D49/test.diff`
- **fix**: `analysis/verified_gold/4/B60-embedcontroller-enqueues-retrievetopic-job-but-spec-expe/defects/4-D49/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B60-embedcontroller-enqueues-retrievetopic-job-but-spec-expe/defects/4-D49/logs`
- **finding**: app/controllers/embedcontroller.rb:16 — the controller enqueues jobs::retrievetopic, but spec/controllers/embedcontrollerspec.rb:43 asserts topicretriever.new is called synchronously, so the tests encode a different cont

### 4-D50 — RetrieveTopic job unnecessarily eager-loads mail stack via stray require_dependency
- **location**: `app/jobs/regular/retrievetopic.rb:1`  ·  **evidence**: `own_executed`  ·  bundle `4-B61` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B61-retrievetopic-job-unnecessarily-eager-loads-mail-stack-v/defects/4-D50/test.diff`
- **fix**: `analysis/verified_gold/4/B61-retrievetopic-job-unnecessarily-eager-loads-mail-stack-v/defects/4-D50/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B61-retrievetopic-job-unnecessarily-eager-loads-mail-stack-v/defects/4-D50/logs`
- **finding**: retrievetopic.rb requiredependency 'email/sender' is unused

### 4-D51 — embedurl param not type-checked allows non-String, causing unrescued TypeError in URI parsing and Sidekiq retry churn
- **location**: `embedcontroller.rb:9-16`  ·  **evidence**: `own_executed`  ·  bundle `4-B69` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B69-embedurl-param-not-type-checked-allows-non-string-causin/defects/4-D51/test.diff`
- **fix**: `analysis/verified_gold/4/B69-embedurl-param-not-type-checked-allows-non-string-causin/defects/4-D51/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B69-embedurl-param-not-type-checked-allows-non-string-causin/defects/4-D51/logs`
- **finding**: embedcontroller.rb:9-16 / topicretriever.rb:15-18: embedurl is never validated as a string — params.require(:embedurl) happily returns an array/hash (?embedurl[]=x), and uri(@embedurl) in invalidhost? raises typeerror (n

### 4-D52 — Invalid or wrong-host embed URLs are treated as successful retrieval, causing infinite loading loop
- **location**: `lib/topicretriever.rb:9`  ·  **evidence**: `own_executed`  ·  bundle `4-B71` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B71-invalid-or-wrong-host-embed-urls-are-treated-as-successf/defects/4-D52/test.diff`
- **fix**: `analysis/verified_gold/4/B71-invalid-or-wrong-host-embed-urls-are-treated-as-successf/defects/4-D52/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B71-invalid-or-wrong-host-embed-urls-are-treated-as-successf/defects/4-D52/logs`
- **finding**: lib/topicretriever.rb:9 — [p1, confidence 100] performretrieve unless (invalidhost? || retrievedrecently?) acknowledges a malformed or wrong-host embed url as successful background work, so the controller’s loading page 

### 4-D54 — Feed item URL fallback uses entry.id (often not a URL), causing items to be silently skipped
- **location**: `app/jobs/scheduled/poll_feed.rb`  ·  **evidence**: `own_executed`  ·  bundle `4-B73` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/4/B73-feed-item-url-fallback-uses-entryid-often-not-a-url-ca/defects/4-D54/test.diff`
- **fix**: `analysis/verified_gold/4/B73-feed-item-url-fallback-uses-entryid-often-not-a-url-ca/defects/4-D54/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B73-feed-item-url-fallback-uses-entryid-often-not-a-url-ca/defects/4-D54/logs`
- **finding**: pollfeed.rb falls back to i.id which may not be a url, causing silent skipping of feed items with no logging (p3)

### 4-D55 — Premature throttle key: the dedupe key is written BEFORE the retrieval succeeds, so a failed fetch suppresses its own retry for 60s
- **location**: `lib/topic_retriever.rb`  ·  **evidence**: `own_executed`  ·  bundle `4-B21` (None)
- **test**: `analysis/verified_gold/4/B21-throttle-key-is-acquired-before-successful-fetch-and-use/defects/4-D55/test.diff`
- **fix**: `analysis/verified_gold/4/B21-throttle-key-is-acquired-before-successful-fetch-and-use/defects/4-D55/fix.patch`  ·  **logs**: `analysis/verified_gold/4/B21-throttle-key-is-acquired-before-successful-fetch-and-use/defects/4-D55/logs`
- **restored**: recovered in the 2026-09-18 total-gold duplicate review: the earlier duplicate-folding kept only this bundle's extra label (4-D11's non-atomic facet) and dropped the bundle's own claim; 4-B21's own executed test demonstrates it

## PR 8 — 5 defects

### 8-D01 — Updating a group without `visible` param unintentionally flips visibility to false
- **location**: `app/controllers/groupscontroller.rb:22`  ·  **evidence**: `own_executed`  ·  bundle `8-B00` (confirmed_regression)
- **test**: `analysis/verified_gold/8/B00-updating-a-group-without-visible-param-unintentionally-f/defects/8-D01/test.diff`
- **fix**: `analysis/verified_gold/8/B00-updating-a-group-without-visible-param-unintentionally-f/defects/8-D01/fix.patch`  ·  **logs**: `analysis/verified_gold/8/B00-updating-a-group-without-visible-param-unintentionally-f/defects/8-D01/logs`
- **finding**: public group members page fetches only 50 users and has no pagination controls, making later members inaccessible
- **merged_in_from**: 8-D02

### 8-D03 — Admin::GroupsController#add_members splits usernames without trimming, causing spaced names to be skipped while still returning success
- **location**: `app/controllers/admin/groupscontroller.rb:71`  ·  **evidence**: `own_executed`  ·  bundle `8-B03` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/8/B03-admingroupscontrolleraddmembers-splits-usernames-witho/defects/8-D03/test.diff`
- **fix**: `analysis/verified_gold/8/B03-admingroupscontrolleraddmembers-splits-usernames-witho/defects/8-D03/fix.patch`  ·  **logs**: `analysis/verified_gold/8/B03-admingroupscontrolleraddmembers-splits-usernames-witho/defects/8-D03/logs`
- **finding**: addmembers doesn't .strip split username items, so 'bob, alice' silently drops ' alice'

### 8-D04 — Admin group creation drops submitted aliaslevel and saves default instead
- **location**: `app/controllers/admin/groupscontroller.rb:22`  ·  **evidence**: `own_executed`  ·  bundle `8-B04` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/8/B04-admin-group-creation-drops-submitted-aliaslevel-and-save/defects/8-D04/test.diff`
- **fix**: `analysis/verified_gold/8/B04-admin-group-creation-drops-submitted-aliaslevel-and-save/defects/8-D04/fix.patch`  ·  **logs**: `analysis/verified_gold/8/B04-admin-group-creation-drops-submitted-aliaslevel-and-save/defects/8-D04/logs`
- **finding**: admin group creation ignores the submitted aliaslevel, causing new groups to retain the default alias level

### 8-D05 — Admin::GroupsController specs hardcode group id=1, implicitly depending on seeded automatic group
- **location**: `spec/controllers/admin/groupscontrollerspec.rb:94`  ·  **evidence**: `own_executed`  ·  bundle `8-B15` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/8/B15-admingroupscontroller-specs-hardcode-group-id1-implici/defects/8-D05/test.diff`
- **fix**: `analysis/verified_gold/8/B15-admingroupscontroller-specs-hardcode-group-id1-implici/defects/8-D05/fix.patch`  ·  **logs**: `analysis/verified_gold/8/B15-admingroupscontroller-specs-hardcode-group-id1-implici/defects/8-D05/logs`
- **finding**: spec/controllers/admin/groupscontrollerspec.rb automatic-group tests hardcode groupid: 1 and group.find(1), relying on seed-data ids

### 8-D06 — Group name is stripped on create but not on update, allowing whitespace-padded names
- **location**: `app/controllers/admin/groups_controller.rb`  ·  **evidence**: `own_executed`  ·  bundle `8-B18` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/8/B18-group-name-is-stripped-on-create-but-not-on-update-allow/defects/8-D06/test.diff`
- **fix**: `analysis/verified_gold/8/B18-group-name-is-stripped-on-create-but-not-on-update-allow/defects/8-D06/fix.patch`  ·  **logs**: `analysis/verified_gold/8/B18-group-name-is-stripped-on-create-but-not-on-update-allow/defects/8-D06/logs`
- **finding**: groupscontrollerupdate does not strip group.name (unlike create), so a name like " bob " can be saved via update, inconsistent with create and the username-style name rule

## PR 10 — 20 defects

### 10-D01 — Plural *_ids hydration blindly calls .map on null/undefined and can drop unresolved relationship ids
- **location**: `app/assets/javascripts/discourse/models/store.js.es6`  ·  **evidence**: `own_executed`  ·  bundle `10-B02` (confirmed_regression)
- **test**: `analysis/verified_gold/10/B02-plural-ids-hydration-blindly-calls-map-on-null-undefine/defects/10-D01/test.diff`
- **fix**: `analysis/verified_gold/10/B02-plural-ids-hydration-blindly-calls-map-on-null-undefine/defects/10-D01/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B02-plural-ids-hydration-blindly-calls-map-on-null-undefine/defects/10-D01/logs`
- **finding**: store.js.es6 plural branch leaves null entries in the hydrated array for unresolved ids

### 10-D02 — port handling mismatch between validation and lookup
- **location**: `app/models/embeddablehost.rb:17`  ·  **evidence**: `own_executed`  ·  bundle `10-B03` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B03-embeddable-hosts-saved-with-a-port-never-match-because-l/defects/10-D02/test.diff`
- **fix**: `analysis/verified_gold/10/B03-embeddable-hosts-saved-with-a-port-never-match-because-l/defects/10-D02/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B03-embeddable-hosts-saved-with-a-port-never-match-because-l/defects/10-D02/logs`
- **finding**: hosts containing ports can be saved but never match because uri parsing drops the port before lookup
- **merged_in_from**: 10-D06

### 10-D03 — Blank/nil `host` crashes `before_validation` on a mutating (create/update) embeddable-host request
- **location**: `app/models/embeddable_host.rb`  ·  **evidence**: `own_executed`  ·  bundle `10-B03` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B03-embeddable-hosts-saved-with-a-port-never-match-because-l/defects/10-D03/test.diff`
- **fix**: `analysis/verified_gold/10/B03-embeddable-hosts-saved-with-a-port-never-match-because-l/defects/10-D03/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B03-embeddable-hosts-saved-with-a-port-never-match-because-l/defects/10-D03/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **label_corrected**: the test asserts normalization + lookup + that a nil host does not raise on the mutating path; the inherited label described test coverage, which is not a behaviour

### 10-D04 — case-insensitive host comparison only lowercases stored column
- **location**: `app/models/embeddablehost.rb:17`  ·  **evidence**: `own_executed`  ·  bundle `10-B03` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B03-embeddable-hosts-saved-with-a-port-never-match-because-l/defects/10-D04/test.diff`
- **fix**: `analysis/verified_gold/10/B03-embeddable-hosts-saved-with-a-port-never-match-because-l/defects/10-D04/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B03-embeddable-hosts-saved-with-a-port-never-match-because-l/defects/10-D04/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: app/models/embeddablehost.rb:17 — the lookup lowercases only the stored column, not the incoming referer host, so mixed-case referers are wrongly rejected.

### 10-D07 — Migrated legacy rows bypass validation and normalization
- **location**: `app/models/embeddablehost.rb:2`  ·  **evidence**: `own_executed`  ·  bundle `10-B05` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B05-embeddablehost-hostname-validation-regex-rejects-valid-h/defects/10-D07/test.diff`
- **fix**: `analysis/verified_gold/10/B05-embeddablehost-hostname-validation-regex-rejects-valid-h/defects/10-D07/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B05-embeddablehost-hostname-validation-regex-rejects-valid-h/defects/10-D07/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: app/models/embeddablehost.rb:2 — validation regex rejects tlds longer than 5 chars, localhost, ips with ports and idns; hosts migrated raw from the old setting will load but can never be re-saved from the ui.
- **merged_in_from**: 10-D05

### 10-D08 — EmbeddableHost allows duplicate host mappings, making lookup via `.first` nondeterministic
- **location**: `app/models/embeddablehost.rb:17`  ·  **evidence**: `own_executed`  ·  bundle `10-B06` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B06-embeddablehost-allows-duplicate-host-mappings-making-loo/defects/10-D08/test.diff`
- **fix**: `analysis/verified_gold/10/B06-embeddablehost-allows-duplicate-host-mappings-making-loo/defects/10-D08/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B06-embeddablehost-allows-duplicate-host-mappings-making-loo/defects/10-D08/logs`
- **finding**: migration lacks a unique index on host, allowing duplicate host rows with conflicting categories

### 10-D09 — EmbeddableHost persists arbitrary categoryid without verifying category exists or is accessible
- **location**: `app/controllers/admin/embeddablehostscontroller.rb:24`  ·  **evidence**: `own_executed`  ·  bundle `10-B09` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B09-embeddablehost-persists-arbitrary-categoryid-without-ver/defects/10-D09/test.diff`
- **fix**: `analysis/verified_gold/10/B09-embeddablehost-persists-arbitrary-categoryid-without-ver/defects/10-D09/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B09-embeddablehost-persists-arbitrary-categoryid-without-ver/defects/10-D09/logs`
- **finding**: [medium/data] categoryid is persisted without verifying that the category exists, allowing dangling relationships that can pass an invalid category into topic creation

### 10-D10 — Irreversible destructive data migration in `change` permanently deletes site settings on rollback
- **location**: `db/migrate/20150818190757createembeddablehosts.rb:31`  ·  **evidence**: `own_executed`  ·  bundle `10-B11` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B11-irreversible-destructive-data-migration-in-change-perman/defects/10-D10/test.diff`
- **fix**: `analysis/verified_gold/10/B11-irreversible-destructive-data-migration-in-change-perman/defects/10-D10/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B11-irreversible-destructive-data-migration-in-change-perman/defects/10-D10/logs`
- **finding**: the migration's delete from sitesettings inside change is irreversible on rollback - permanent data loss

### 10-D11 — Migration uses create_table force: true causing silent drop/recreate and data loss
- **location**: `db/migrate/20150818190757createembeddablehosts.rb:3`  ·  **evidence**: `own_executed`  ·  bundle `10-B12` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B12-migration-uses-createtable-force-true-causing-silent-dro/defects/10-D11/test.diff`
- **fix**: `analysis/verified_gold/10/B12-migration-uses-createtable-force-true-causing-silent-dro/defects/10-D11/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B12-migration-uses-createtable-force-true-causing-silent-dro/defects/10-D11/logs`
- **finding**: the migration uses createtable with force: true, which silently drops a pre-existing embeddablehosts table along with its data

### 10-D12 — PUT /admin/customize/embedding update is a no-op that returns 200 without persisting changes
- **location**: `app/controllers/admin/embeddingcontroller.rb:10`  ·  **evidence**: `own_executed`  ·  bundle `10-B13` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B13-put--admin-customize-embedding-update-is-a-no-op-that-re/defects/10-D12/test.diff`
- **fix**: `analysis/verified_gold/10/B13-put--admin-customize-embedding-update-is-a-no-op-that-re/defects/10-D12/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B13-put--admin-customize-embedding-update-is-a-no-op-that-re/defects/10-D12/logs`
- **finding**: put /admin/customize/embedding is a no-op that renders the serializer without persisting anything, returning 200 success while no update occurs

### 10-D13 — Migration skips importing legacy embeddable hosts by using cmdtuples on a SELECT, then deletes the only copy of the config
- **location**: `db/migrate/20150818190757createembeddablehosts.rb:19`  ·  **evidence**: `own_executed`  ·  bundle `10-B16` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B16-migration-skips-importing-legacy-embeddable-hosts-by-usi/defects/10-D13/test.diff`
- **fix**: `analysis/verified_gold/10/B16-migration-skips-importing-legacy-embeddable-hosts-by-usi/defects/10-D13/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B16-migration-skips-importing-legacy-embeddable-hosts-by-usi/defects/10-D13/logs`
- **finding**: migration never imports existing embeddablehosts because cmdtuples is 0 for select statements, then deletes the legacy setting

### 10-D14 — Routes expose REST actions for embeddable_hosts that the controller doesn't implement (ActionNotFound on GET)
- **location**: `config/routes.rb:153`  ·  **evidence**: `own_executed`  ·  bundle `10-B18` (confirmed_regression)
- **test**: `analysis/verified_gold/10/B18-routes-expose-rest-actions-for-embeddablehosts-that-the-/defects/10-D14/test.diff`
- **fix**: `analysis/verified_gold/10/B18-routes-expose-rest-actions-for-embeddablehosts-that-the-/defects/10-D14/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B18-routes-expose-rest-actions-for-embeddablehosts-that-the-/defects/10-D14/logs`
- **finding**: config/routes.rb:153 — resources :embeddablehosts declares index/show/new/edit routes that the controller does not implement

### 10-D15 — EmbeddingSerializer emits only embeddable_host_ids (no sideloaded embeddable_hosts), breaking client hydration
- **location**: `app/serializers/embeddingserializer.rb:3`  ·  **evidence**: `own_executed`  ·  bundle `10-B21` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B21-embeddingserializer-emits-only-embeddablehostids-no-sid/defects/10-D15/test.diff`
- **fix**: `analysis/verified_gold/10/B21-embeddingserializer-emits-only-embeddablehostids-no-sid/defects/10-D15/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B21-embeddingserializer-emits-only-embeddablehostids-no-sid/defects/10-D15/logs`
- **finding**: app/serializers/embeddingserializer.rb:3 — hasmany ... embed: :ids without include: true emits only embeddablehostids and no root embeddablehosts collection, so lookupsubtype finds nothing and the admin list hydrates emp

### 10-D16 — EmbeddableHost host format validation allows trailing newline due to end-anchor, creating broken allowlist entries
- **location**: `app/models/embeddablehost.rb:2`  ·  **evidence**: `own_executed`  ·  bundle `10-B23` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B23-embeddablehost-host-format-validation-allows-trailing-ne/defects/10-D16/test.diff`
- **fix**: `analysis/verified_gold/10/B23-embeddablehost-host-format-validation-allows-trailing-ne/defects/10-D16/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B23-embeddablehost-host-format-validation-allows-trailing-ne/defects/10-D16/logs`
- **finding**: host format regex anchored with \a/\z instead of \z, allowing a host value ending in newline followed by malicious content to bypass validation

### 10-D17 — EmbeddableHost destroy action always reports success even when destroy fails
- **location**: `app/controllers/admin/embeddablehostscontroller.rb:16`  ·  **evidence**: `own_executed`  ·  bundle `10-B25` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B25-embeddablehost-destroy-action-always-reports-success-eve/defects/10-D17/test.diff`
- **fix**: `analysis/verified_gold/10/B25-embeddablehost-destroy-action-always-reports-success-eve/defects/10-D17/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B25-embeddablehost-destroy-action-always-reports-success-eve/defects/10-D17/logs`
- **finding**: app/controllers/admin/embeddablehostscontroller.rb:16 — return value of host.destroy is ignored and successjson is always rendered, so a destroy blocked by callbacks/fk reports success

### 10-D18 — EmbedController authorization can be bypassed by forging the Referer header
- **location**: `app/controllers/embedcontroller.rb:61`  ·  **evidence**: `own_executed`  ·  bundle `10-B26` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B26-embedcontroller-authorization-can-be-bypassed-by-forging/defects/10-D18/test.diff`
- **fix**: `analysis/verified_gold/10/B26-embedcontroller-authorization-can-be-bypassed-by-forging/defects/10-D18/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B26-embedcontroller-authorization-can-be-bypassed-by-forging/defects/10-D18/logs`
- **finding**: app/controllers/embedcontroller.rb:61 — ensureembeddable authorizes the entire embedcontroller (comments/count, csrf-exempt via skipbeforefilter :verifyauthenticitytoken) solely by checking embeddablehost.hostallowed?(re

### 10-D19 — Embed allowlist check does not scope requested topic/embed_url to the referer host's permitted category
- **location**: `app/controllers/embedcontroller.rb:61`  ·  **evidence**: `own_executed`  ·  bundle `10-B33` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B33-embed-allowlist-check-does-not-scope-requested-topic-emb/defects/10-D19/test.diff`
- **fix**: `analysis/verified_gold/10/B33-embed-allowlist-check-does-not-scope-requested-topic-emb/defects/10-D19/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B33-embed-allowlist-check-does-not-scope-requested-topic-emb/defects/10-D19/logs`
- **finding**: app/controllers/embedcontroller.rb:61 — hostallowed? only verifies the referer matches some embeddable host; the requested embedurl/topicid is not scoped to that host's category, so any allowed host can embed another hos

### 10-D20 — None
- **location**: `app/models/embeddablehost.rb:6`  ·  **evidence**: `own_executed`  ·  bundle `10-B34` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B34-app-models-embeddablehostrb6--beforevalidation-only-str/defects/10-D20/test.diff`
- **fix**: `analysis/verified_gold/10/B34-app-models-embeddablehostrb6--beforevalidation-only-str/defects/10-D20/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B34-app-models-embeddablehostrb6--beforevalidation-only-str/defects/10-D20/logs`
- **finding**: app/models/embeddablehost.rb:6 — beforevalidation only strips lowercase http(s)://; http://example.com or //example.com become http:/empty and fail with a confusing format error rather than being normalized.

### 10-D21 — Migration splits embeddable host list on newlines instead of pipe delimiter, losing hosts
- **location**: `db/migrate/20150818190757createembeddablehosts.rb:22`  ·  **evidence**: `own_executed`  ·  bundle `10-B35` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B35-migration-splits-embeddable-host-list-on-newlines-instea/defects/10-D21/test.diff`
- **fix**: `analysis/verified_gold/10/B35-migration-splits-embeddable-host-list-on-newlines-instea/defects/10-D21/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B35-migration-splits-embeddable-host-list-on-newlines-instea/defects/10-D21/logs`
- **finding**: db/migrate/20150818190757createembeddablehosts.rb:22 — embeddablehosts was declared type: hostlist in head~2 config/sitesettings.yml and discourse list-type settings persist as pipe-delimited (|, cf. app/models/sitesetti

### 10-D22 — EmbeddableHost missing presence validation for non-null category_id causes DB NotNullViolation
- **location**: `app/models/embeddable_host.rb`  ·  **evidence**: `own_executed`  ·  bundle `10-B36` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/10/B36-embeddablehost-missing-presence-validation-for-non-null-/defects/10-D22/test.diff`
- **fix**: `analysis/verified_gold/10/B36-embeddablehost-missing-presence-validation-for-non-null-/defects/10-D22/fix.patch`  ·  **logs**: `analysis/verified_gold/10/B36-embeddablehost-missing-presence-validation-for-non-null-/defects/10-D22/logs`
- **finding**: the categoryid column is null: false but embeddablehost has no presence validation on categoryid, so creation paths outside the controller raise notnullviolation instead of a validation error

## PR 10967 — 5 defects

### 10967-D01 — Google Meet event creation can crash when destinationCalendar is missing/empty
- **location**: `packages/core/eventmanager.ts:119`  ·  **evidence**: `own_executed`  ·  bundle `10967-B03` (confirmed_regression)
- **test**: `analysis/verified_gold/10967/B03-google-meet-event-creation-can-crash-when-destinationcalen/defects/10967-D01/test.diff`
- **fix**: `analysis/verified_gold/10967/B03-google-meet-event-creation-can-crash-when-destinationcalen/defects/10967-D01/fix.patch`  ·  **logs**: `analysis/verified_gold/10967/B03-google-meet-event-creation-can-crash-when-destinationcalen/defects/10967-D01/logs`
- **finding**: eventmanager.ts:118 missing optional chaining on destinationcalendar.integration throws typeerror when destinationcalendar is undefined

### 10967-D02 — Reschedule calendar update errors are swallowed: catch returns [] when calendarReference is unset and logs were removed
- **location**: `eventmanager.ts:596`  ·  **evidence**: `own_executed`  ·  bundle `10967-B11` (confirmed_regression)
- **test**: `analysis/verified_gold/10967/B11-reschedule-calendar-update-errors-are-swallowed-catch-retu/defects/10967-D02/test.diff`
- **fix**: `analysis/verified_gold/10967/B11-reschedule-calendar-update-errors-are-swallowed-catch-retu/defects/10967-D02/fix.patch`  ·  **logs**: `analysis/verified_gold/10967/B11-reschedule-calendar-update-errors-are-swallowed-catch-retu/defects/10967-D02/logs`
- **finding**: eventmanager.ts:596 — console.error(message) removed from the catch block, so failures in updateallcalendarevents are swallowed with no log

### 10967-D03 — Booking webhook payload breaks backward compatibility by changing destinationCalendar from object/null to array
- **location**: `packages/types/calendar.d.ts:171`  ·  **evidence**: `own_executed`  ·  bundle `10967-B13` (confirmed_regression)
- **test**: `analysis/verified_gold/10967/B13-booking-webhook-payload-breaks-backward-compatibility-by-c/defects/10967-D03/test.diff`
- **fix**: `analysis/verified_gold/10967/B13-booking-webhook-payload-breaks-backward-compatibility-by-c/defects/10967-D03/fix.patch`  ·  **logs**: `analysis/verified_gold/10967/B13-booking-webhook-payload-breaks-backward-compatibility-by-c/defects/10967-D03/logs`
- **finding**: packages/types/calendar.d.ts:171 — changing destinationcalendar from an object or null to an array breaks existing webhook payload consumers without versioning or compatibility handling

### 10967-D04 — Recurring deletion sweep nested inside bookingCalendarReference loop causing duplicate provider deletes/404s
- **location**: `handlecancelbooking.ts:445`  ·  **evidence**: `own_executed`  ·  bundle `10967-B14` (confirmed_regression)
- **test**: `analysis/verified_gold/10967/B14-recurring-cancellation-delete-sweep-runs-once-per-calendar/defects/10967-D04/test.diff`
- **fix**: `analysis/verified_gold/10967/B14-recurring-cancellation-delete-sweep-runs-once-per-calendar/defects/10967-D04/fix.patch`  ·  **logs**: `analysis/verified_gold/10967/B14-recurring-cancellation-delete-sweep-runs-once-per-calendar/defects/10967-D04/logs`
- **finding**: [p2] handlecancelbooking recurring-deletion loop nested inside bookingcalendarreference loop, multiplying duplicate delete calls per reference per credential

### 10967-D05 — Inner references.find only deletes the first calendar reference per updated booking, leaving orphaned secondary-host events
- **location**: `handlecancelbooking.ts:441-463`  ·  **evidence**: `own_executed`  ·  bundle `10967-B14` (confirmed_regression)
- **test**: `analysis/verified_gold/10967/B14-recurring-cancellation-delete-sweep-runs-once-per-calendar/defects/10967-D05/test.diff`
- **fix**: `analysis/verified_gold/10967/B14-recurring-cancellation-delete-sweep-runs-once-per-calendar/defects/10967-D05/fix.patch`  ·  **logs**: `analysis/verified_gold/10967/B14-recurring-cancellation-delete-sweep-runs-once-per-calendar/defects/10967-D05/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: handlecancelbooking.ts:441-463 — recurring-event deletion branch is nested inside the loop over bookingcalendarreference, so it runs n times issuing duplicate delete calls that fail; it also still only deletes the first 

## PR 11059 — 14 defects

### 11059-D01 — Timing-unsafe webhook secret comparison (non-constant-time !==)
- **location**: `apps/web/pages/api/webhook/app-credential.ts:25`  ·  **evidence**: `own_executed`  ·  bundle `11059-B05` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/11059/B05-webhook-secret-validation-uses-non-constant-time-string-co/defects/11059-D01/test.diff`
- **fix**: `analysis/verified_gold/11059/B05-webhook-secret-validation-uses-non-constant-time-string-co/defects/11059-D01/fix.patch`  ·  **logs**: `analysis/verified_gold/11059/B05-webhook-secret-validation-uses-non-constant-time-string-co/defects/11059-D01/logs`
- **finding**: non-constant-time string comparison of webhook secret allows timing attacks; use crypto.timingsafeequal or hmac comparison

### 11059-D03 — Missing rate limiting on webhook secret verification
- **location**: `apps/web/pages/api/webhook/app-credential.ts`  ·  **evidence**: `own_executed`  ·  bundle `11059-B05` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/11059/B05-webhook-secret-validation-uses-non-constant-time-string-co/defects/11059-D03/test.diff`
- **fix**: `analysis/verified_gold/11059/B05-webhook-secret-validation-uses-non-constant-time-string-co/defects/11059-D03/fix.patch`  ·  **logs**: `analysis/verified_gold/11059/B05-webhook-secret-validation-uses-non-constant-time-string-co/defects/11059-D03/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: webhook secret in apps/web/pages/api/webhook/app-credential.ts is compared with !== (not constant-time) with no rate limiting, on an endpoint that can create/replace oauth credentials for any user; use crypto.timingsafee
- **merged_in_from**: 11059-D29, 11059-D04

### 11059-D09 — Handler lacks request hardening: no HTTP-method guard and an unescaped ZodError from malformed input
- **location**: `apps/web/pages/api/webhook/app-credential.ts`  ·  **evidence**: `own_executed`  ·  bundle `11059-B09` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/11059/B09-webhook-api-handler-performs-credential-create-update-with/defects/11059-D09/test.diff`
- **fix**: `analysis/verified_gold/11059/B09-webhook-api-handler-performs-credential-create-update-with/defects/11059-D09/fix.patch`  ·  **logs**: `analysis/verified_gold/11059/B09-webhook-api-handler-performs-credential-create-update-with/defects/11059-D09/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: unhandled zod.parse and json.parse of decrypted keys in app-credential webhook throw 500s instead of 400s on malformed input
- **merged_in_from**: 11059-D08
- **label_corrected**: the test asserts GET -> 405 and a malformed body -> 400 rather than an escaped schema error; the inherited label only mentioned 'unhandled schema/decryption/JSON parse errors'

### 11059-D10 — missing validation of decrypted credential object before persistence
- **location**: `apps/web/pages/api/webhook/app-credential.ts`  ·  **evidence**: `own_executed`  ·  bundle `11059-B09` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/11059/B09-webhook-api-handler-performs-credential-create-update-with/defects/11059-D10/test.diff`
- **fix**: `analysis/verified_gold/11059/B09-webhook-api-handler-performs-credential-create-update-with/defects/11059-D10/fix.patch`  ·  **logs**: `analysis/verified_gold/11059/B09-webhook-api-handler-performs-credential-create-update-with/defects/11059-D10/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: webhook handler does not validate that decrypted keys is a valid credential object before persisting to prisma.credential.key
- **merged_in_from**: 11059-D16

### 11059-D12 — credential-sync endpoint requests are unauthenticated
- **location**: `packages/app-store/utils/oauth/refreshoauthtokens.ts:8`  ·  **evidence**: `own_executed`  ·  bundle `11059-B10` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/11059/B10-credential-sync-token-refresh-request-omits-shared-secret-/defects/11059-D12/test.diff`
- **fix**: `analysis/verified_gold/11059/B10-credential-sync-token-refresh-request-omits-shared-secret-/defects/11059-D12/fix.patch`  ·  **logs**: `analysis/verified_gold/11059/B10-credential-sync-token-refresh-request-omits-shared-secret-/defects/11059-D12/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: credential-sync requests include no authentication secret or authorization header, allowing attackers to potentially obtain oauth tokens by enumerating user ids

### 11059-D14 — HubSpot refresh treats raw credential-sync response as HubSpotToken object
- **location**: `packages/app-store/_utils/oauth/refreshOAuthTokens.ts`  ·  **evidence**: `own_executed`  ·  bundle `11059-B10` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/11059/B10-credential-sync-token-refresh-request-omits-shared-secret-/defects/11059-D14/test.diff`
- **fix**: `analysis/verified_gold/11059/B10-credential-sync-token-refresh-request-omits-shared-secret-/defects/11059-D14/fix.patch`  ·  **logs**: `analysis/verified_gold/11059/B10-credential-sync-token-refresh-request-omits-shared-secret-/defects/11059-D14/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: hubspot calendarservice result is typed hubspottoken but is a fetch response in the sync branch, so expiresin/accesstoken are undefined and get persisted
- **merged_in_from**: 11059-D15, 11059-D13

### 11059-D17 — non-atomic find-then-create/upsert race causing duplicate credentials under concurrency
- **location**: `apps/web/pages/api/webhook/app-credential.ts:62-73`  ·  **evidence**: `own_executed`  ·  bundle `11059-B14` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/11059/B14-webhook-updates-an-arbitrary-credential-when-user-has-mult/defects/11059-D17/test.diff`
- **fix**: `analysis/verified_gold/11059/B14-webhook-updates-an-arbitrary-credential-when-user-has-mult/defects/11059-D17/fix.patch`  ·  **logs**: `analysis/verified_gold/11059/B14-webhook-updates-an-arbitrary-credential-when-user-has-mult/defects/11059-D17/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: webhook find-then-update/create race can create duplicate credentials for the same userid+appid under concurrent deliveries
- **merged_in_from**: 11059-D07

### 11059-D18 — ambiguous credential lookup by userId+appId without a disambiguator causing arbitrary credential overwrite
- **location**: `apps/web/pages/api/webhook/app-credential.ts:62`  ·  **evidence**: `own_executed`  ·  bundle `11059-B14` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/11059/B14-webhook-updates-an-arbitrary-credential-when-user-has-mult/defects/11059-D18/test.diff`
- **fix**: `analysis/verified_gold/11059/B14-webhook-updates-an-arbitrary-credential-when-user-has-mult/defects/11059-D18/fix.patch`  ·  **logs**: `analysis/verified_gold/11059/B14-webhook-updates-an-arbitrary-credential-when-user-has-mult/defects/11059-D18/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: webhook's findfirst has no orderby, so it nondeterministically picks an arbitrary credential when duplicates exist

### 11059-D19 — Webhook auth fails open when CALCOM_WEBHOOK_SECRET is unset (undefined equals missing header)
- **location**: `apps/web/pages/api/webhook/app-credential.ts:25`  ·  **evidence**: `own_executed`  ·  bundle `11059-B21` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/11059/B21-webhook-auth-fails-open-when-calcomwebhooksecret-is-unset-/defects/11059-D19/test.diff`
- **fix**: `analysis/verified_gold/11059/B21-webhook-auth-fails-open-when-calcomwebhooksecret-is-unset-/defects/11059-D19/fix.patch`  ·  **logs**: `analysis/verified_gold/11059/B21-webhook-auth-fails-open-when-calcomwebhooksecret-is-unset-/defects/11059-D19/logs`
- **finding**: apps/web/pages/api/webhook/app-credential.ts:25 — an unset calcomwebhooksecret makes an absent header compare equal to undefined and bypasses webhook authentication

### 11059-D20 — Instance-wide static webhook secret authorizes credential writes for arbitrary userid/appslug
- **location**: `apps/web/pages/api/webhook/app-credential.ts:9-13`  ·  **evidence**: `own_executed`  ·  bundle `11059-B22` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/11059/B22-instance-wide-shared-webhook-secret-allows-overwriting-any/defects/11059-D20/test.diff`
- **fix**: `analysis/verified_gold/11059/B22-instance-wide-shared-webhook-secret-allows-overwriting-any/defects/11059-D20/fix.patch`  ·  **logs**: `analysis/verified_gold/11059/B22-instance-wide-shared-webhook-secret-allows-overwriting-any/defects/11059-D20/logs`
- **finding**: apps/web/pages/api/webhook/app-credential.ts:62 — a single global webhook secret authorizes credential create/overwrite for any userid, so one leaked secret compromises every user's app credentials

### 11059-D21 — No replay/event-identity/version guard permits stale or concurrent credential overwrites
- **location**: `apps/web/pages/api/webhook/app-credential.ts:72`  ·  **evidence**: `own_executed`  ·  bundle `11059-B22` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/11059/B22-instance-wide-shared-webhook-secret-allows-overwriting-any/defects/11059-D21/test.diff`
- **fix**: `analysis/verified_gold/11059/B22-instance-wide-shared-webhook-secret-allows-overwriting-any/defects/11059-D21/fix.patch`  ·  **logs**: `analysis/verified_gold/11059/B22-instance-wide-shared-webhook-secret-allows-overwriting-any/defects/11059-D21/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: apps/web/pages/api/webhook/app-credential.ts:20 — no timestamp, nonce, or constant-time comparison, so a captured webhook request can be replayed indefinitely to roll a user's credentials back to stale keys.

### 11059-D22 — parseRefreshTokenResponse throws instead of returning structured failure, breaking caller branches
- **location**: `packages/app-store/utils/oauth/parserefreshtokenresponse.ts:19-21`  ·  **evidence**: `own_executed`  ·  bundle `11059-B23` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/11059/B23-parserefreshtokenresponse-throws-on-schema-mismatch-and-ca/defects/11059-D22/test.diff`
- **fix**: `analysis/verified_gold/11059/B23-parserefreshtokenresponse-throws-on-schema-mismatch-and-ca/defects/11059-D22/fix.patch`  ·  **logs**: `analysis/verified_gold/11059/B23-parserefreshtokenresponse-throws-on-schema-mismatch-and-ca/defects/11059-D22/logs`
- **finding**: parserefreshtokenresponse now unconditionally throws on parse failure, but callers in office365calendar, salesforce, and zoom still branch on success, making the office365 fallback path unreachable and silently changing 
- **merged_in_from**: 11059-D27, 11059-D23

### 11059-D26 — Webhook credential sync updates key but does not clear previously set invalid flag
- **location**: `apps/web/pages/api/webhook/app-credential.ts:73`  ·  **evidence**: `own_executed`  ·  bundle `11059-B24` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/11059/B24-webhook-credential-sync-updates-key-but-does-not-clear-pre/defects/11059-D26/test.diff`
- **fix**: `analysis/verified_gold/11059/B24-webhook-credential-sync-updates-key-but-does-not-clear-pre/defects/11059-D26/fix.patch`  ·  **logs**: `analysis/verified_gold/11059/B24-webhook-credential-sync-updates-key-but-does-not-clear-pre/defects/11059-D26/logs`
- **finding**: apps/web/pages/api/webhook/app-credential.ts:77: updating a previously invalid credential replaces only its key without clearing the invalid flag, so newly synchronized valid credentials can remain disabled.

### 11059-D28 — API route default-imports zod, making `z` undefined and crashing on module load
- **location**: `apps/web/pages/api/webhook/app-credential.ts`  ·  **evidence**: `own_executed`  ·  bundle `11059-B31` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/11059/B31-api-route-default-imports-zod-making-z-undefined-and-cras/defects/11059-D28/test.diff`
- **fix**: `analysis/verified_gold/11059/B31-api-route-default-imports-zod-making-z-undefined-and-cras/defects/11059-D28/fix.patch`  ·  **logs**: `analysis/verified_gold/11059/B31-api-route-default-imports-zod-making-z-undefined-and-cras/defects/11059-D28/logs`
- **finding**: [bug] the route default-imports zod (import z from "zod"), but zod's commonjs entry sets esmodule and exports no default, so z binds to undefined at runtime. z.object(...) on line 9 throws typeerror: cannot read properti

## PR 14740 — 18 defects

### 14740-D01 — Missing max/rate limits on guests array enables unbounded guest inserts and email fan-out
- **location**: `packages/trpc/server/routers/viewer/bookings/addguests.schema.ts:5`  ·  **evidence**: `own_executed`  ·  bundle `14740-B03` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B03-addguests-input-schema-allows-unbounded-guests-array-email/defects/14740-D01/test.diff`
- **fix**: `analysis/verified_gold/14740/B03-addguests-input-schema-allows-unbounded-guests-array-email/defects/14740-D01/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B03-addguests-input-schema-allows-unbounded-guests-array-email/defects/14740-D01/logs`
- **finding**: guests array has no max() in the zod schema, allowing authorized callers to add thousands of attendees in one mutation
- **merged_in_from**: 14740-D02

### 14740-D03 — Missing booking status/end-time validation allows adding guests to cancelled, rejected, or past bookings
- **location**: `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:26`  ·  **evidence**: `own_executed`  ·  bundle `14740-B06` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B06-authorization-bypass-any-attendee-can-add-arbitrary-guests/defects/14740-D03/test.diff`
- **fix**: `analysis/verified_gold/14740/B06-authorization-bypass-any-attendee-can-add-arbitrary-guests/defects/14740-D03/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B06-authorization-bypass-any-attendee-can-add-arbitrary-guests/defects/14740-D03/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: cancelled or past bookings are accepted, allowing attendees and confirmed calendar invitations to be added to inactive events.

### 14740-D04 — Over-permissive attendee-based authorization lets any attendee add arbitrary guests without organizer consent
- **location**: `packages/trpc/server/routers/viewer/bookings/addGuests.handler.ts`  ·  **evidence**: `own_executed`  ·  bundle `14740-B06` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B06-authorization-bypass-any-attendee-can-add-arbitrary-guests/defects/14740-D04/test.diff`
- **fix**: `analysis/verified_gold/14740/B06-authorization-bypass-any-attendee-can-add-arbitrary-guests/defects/14740-D04/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B06-authorization-bypass-any-attendee-can-add-arbitrary-guests/defects/14740-D04/logs`
- **finding**: any booking attendee can add arbitrary guests, with no check that the booking is not cancelled/rejected or in the past

### 14740-D05 — add-guests handler emails raw guests list instead of filtered uniqueGuests, causing duplicate/wrong notifications
- **location**: `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:168`  ·  **evidence**: `own_executed`  ·  bundle `14740-B07` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B07-add-guests-handler-emails-raw-guests-list-instead-of-filte/defects/14740-D05/test.diff`
- **fix**: `analysis/verified_gold/14740/B07-add-guests-handler-emails-raw-guests-list-instead-of-filte/defects/14740-D05/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B07-add-guests-handler-emails-raw-guests-list-instead-of-filte/defects/14740-D05/logs`
- **finding**: passing guests instead of uniqueguests misclassifies existing attendees as new and sends them scheduled-event emails

### 14740-D06 — addGuests crashes with unhandled Prisma P2025 when booking.userId is null (id coerced to 0)
- **location**: `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:58`  ·  **evidence**: `own_executed`  ·  bundle `14740-B08` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B08-addguests-crashes-with-unhandled-prisma-p2025-when-booking/defects/14740-D06/test.diff`
- **fix**: `analysis/verified_gold/14740/B08-addguests-crashes-with-unhandled-prisma-p2025-when-booking/defects/14740-D06/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B08-addguests-crashes-with-unhandled-prisma-p2025-when-booking/defects/14740-D06/logs`
- **finding**: organizer lookup crashes for bookings with userid null, throwing raw prisma error as unhandled 500

### 14740-D07 — Add-guests endpoint can overbook seat-limited events by appending attendees without enforcing seatsPerTimeSlot
- **location**: `apps/web/components/booking/bookinglistitem.tsx:194`  ·  **evidence**: `own_executed`  ·  bundle `14740-B10` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B10-add-guests-endpoint-can-overbook-seat-limited-events-by-ap/defects/14740-D07/test.diff`
- **fix**: `analysis/verified_gold/14740/B10-add-guests-endpoint-can-overbook-seat-limited-events-by-ap/defects/14740-D07/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B10-add-guests-endpoint-can-overbook-seat-limited-events-by-ap/defects/14740-D07/logs`
- **finding**: no check against seatspertimeslot for seated events, so guest additions can exceed available seats

### 14740-D08 — Add-guests email send failure is swallowed (no error context) and request still succeeds
- **location**: `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:170`  ·  **evidence**: `own_executed`  ·  bundle `14740-B12` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B12-add-guests-email-send-failure-is-swallowed-no-error-contex/defects/14740-D08/test.diff`
- **fix**: `analysis/verified_gold/14740/B12-add-guests-email-send-failure-is-swallowed-no-error-contex/defects/14740-D08/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B12-add-guests-email-send-failure-is-swallowed-no-error-contex/defects/14740-D08/logs`
- **finding**: catch block logs 'error sending addguestsemails' without the error object, making email failures undiagnosable

### 14740-D09 — Race condition in addGuests allows duplicate attendee rows (check-then-insert without transaction/unique constraint)
- **location**: `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:92`  ·  **evidence**: `own_executed`  ·  bundle `14740-B14` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B14-race-condition-in-addguests-allows-duplicate-attendee-rows/defects/14740-D09/test.diff`
- **fix**: `analysis/verified_gold/14740/B14-race-condition-in-addguests-allows-duplicate-attendee-rows/defects/14740-D09/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B14-race-condition-in-addguests-allows-duplicate-attendee-rows/defects/14740-D09/logs`
- **finding**: addguests.handler.ts:92 — read-then-write is not transactional; two concurrent requests adding the same email both pass the uniqueness filter and both insert

### 14740-D10 — Add-guests flow persists new guest attendees with empty name (blank greetings/ICS CN)
- **location**: `addguests.handler.ts:83-90`  ·  **evidence**: `own_executed`  ·  bundle `14740-B16` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B16-add-guests-flow-persists-new-guest-attendees-with-empty-na/defects/14740-D10/test.diff`
- **fix**: `analysis/verified_gold/14740/B16-add-guests-flow-persists-new-guest-attendees-with-empty-na/defects/14740-D10/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B16-add-guests-flow-persists-new-guest-attendees-with-empty-na/defects/14740-D10/logs`
- **finding**: addguests.handler.ts:~70 persists guest attendees with empty name, causing blank names in organizer email and ics attendees

### 14740-D11 — unbounded reply-to header including all attendee emails
- **location**: `packages/emails/templates/organizer-add-guests-email.ts:25`  ·  **evidence**: `own_executed`  ·  bundle `14740-B17` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B17-organizer-add-guests-email-sets-reply-to-to-all-attendee-e/defects/14740-D11/test.diff`
- **fix**: `analysis/verified_gold/14740/B17-organizer-add-guests-email-sets-reply-to-to-all-attendee-e/defects/14740-D11/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B17-organizer-add-guests-email-sets-reply-to-to-all-attendee-e/defects/14740-D11/logs`
- **finding**: packages/emails/templates/organizer-add-guests-email.ts:25 — replyto includes every attendee email, leaking the full attendee list to each team member recipient.

### 14740-D12 — team-member variant sends organizer-personalized content without teammember prop (email leakage/content mismatch)
- **location**: `packages/emails/templates/organizer-add-guests-email.ts`  ·  **evidence**: `own_executed`  ·  bundle `14740-B17` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B17-organizer-add-guests-email-sets-reply-to-to-all-attendee-e/defects/14740-D12/test.diff`
- **fix**: `analysis/verified_gold/14740/B17-organizer-add-guests-email-sets-reply-to-to-all-attendee-e/defects/14740-D12/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B17-organizer-add-guests-email-sets-reply-to-to-all-attendee-e/defects/14740-D12/logs`
- **orthogonality**: bundle fix leaves it red = `True`
- **finding**: team-member variant of organizer email sends mismatched organizer-personalized content without teammember prop, and replyto includes all attendees leaking emails

### 14740-D13 — Organizer add-guests email subject crashes on empty attendees due to unguarded attendees[0].name access
- **location**: `packages/emails/templates/organizer-add-guests-email.ts:29`  ·  **evidence**: `own_executed`  ·  bundle `14740-B20` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B20-organizer-add-guests-email-subject-crashes-on-empty-attend/defects/14740-D13/test.diff`
- **fix**: `analysis/verified_gold/14740/B20-organizer-add-guests-email-subject-crashes-on-empty-attend/defects/14740-D13/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B20-organizer-add-guests-email-subject-crashes-on-empty-attend/defects/14740-D13/logs`
- **finding**: subject template accesses attendees[0].name which throws if the attendees array is empty

### 14740-D14 — addGuests mutation allows adding guests even when the EventType disables/blocks guests
- **location**: `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:74`  ·  **evidence**: `own_executed`  ·  bundle `14740-B23` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B23-addguests-mutation-allows-adding-guests-even-when-the-even/defects/14740-D14/test.diff`
- **fix**: `analysis/verified_gold/14740/B23-addguests-mutation-allows-adding-guests-even-when-the-even/defects/14740-D14/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B23-addguests-mutation-allows-adding-guests-even-when-the-even/defects/14740-D14/logs`
- **finding**: the mutation does not enforce the event type's disabled-guests restriction

### 14740-D15 — addGuests loads booking by raw id (with heavy includes) before authorization, enabling cross-tenant probing/enumeration
- **location**: `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:26-56`  ·  **evidence**: `own_executed`  ·  bundle `14740-B25` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B25-addguests-loads-booking-by-raw-id-with-heavy-includes-befo/defects/14740-D15/test.diff`
- **fix**: `analysis/verified_gold/14740/B25-addguests-loads-booking-by-raw-id-with-heavy-includes-befo/defects/14740-D15/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B25-addguests-loads-booking-by-raw-id-with-heavy-includes-befo/defects/14740-D15/logs`
- **finding**: booking lookup findfirst({ where: { id } }) is not scoped to the requester's team/user before loading organizer details and credentials (addguests.handler.ts:43-49)

### 14740-D16 — Add-guests on a recurring booking updates only one occurrence but sends a series-wide calendar invite
- **location**: `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:138`  ·  **evidence**: `own_executed`  ·  bundle `14740-B31` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B31-add-guests-on-a-recurring-booking-updates-only-one-occurre/defects/14740-D16/test.diff`
- **fix**: `analysis/verified_gold/14740/B31-add-guests-on-a-recurring-booking-updates-only-one-occurre/defects/14740-D16/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B31-add-guests-on-a-recurring-booking-updates-only-one-occurre/defects/14740-D16/logs`
- **finding**: packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:138 — for recurring bookings only this one occurrence gets the new attendees, but the event carries the eventtype recurringevent, so the new guest's ics i

### 14740-D17 — Concurrent add-guests requests can overwrite calendar attendees with stale snapshot (lost updates)
- **location**: `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:164`  ·  **evidence**: `own_executed`  ·  bundle `14740-B32` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B32-concurrent-add-guests-requests-can-overwrite-calendar-atte/defects/14740-D17/test.diff`
- **fix**: `analysis/verified_gold/14740/B32-concurrent-add-guests-requests-can-overwrite-calendar-atte/defects/14740-D17/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B32-concurrent-add-guests-requests-can-overwrite-calendar-atte/defects/14740-D17/logs`
- **finding**: packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:165 — concurrent add-guest calls perform unversioned full attendee-list provider updates, allowing the last external write to omit guests committed by a r

### 14740-D18 — addGuests throws BAD_REQUEST when all submitted emails already attendees, enabling email probing and breaking retry/idempotency
- **location**: `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:80`  ·  **evidence**: `own_executed`  ·  bundle `14740-B33` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B33-addguests-throws-badrequest-when-all-submitted-emails-alre/defects/14740-D18/test.diff`
- **fix**: `analysis/verified_gold/14740/B33-addguests-throws-badrequest-when-all-submitted-emails-alre/defects/14740-D18/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B33-addguests-throws-badrequest-when-all-submitted-emails-alre/defects/14740-D18/logs`
- **finding**: packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:80 — distinct badrequest when every submitted address is already an attendee lets a caller probe whether a specific email is on the booking.

### 14740-D19 — Missing i18n key causes add-guests permission error to display raw `forbidden: youdonothavepermission`
- **location**: `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:55`  ·  **evidence**: `own_executed`  ·  bundle `14740-B40` (behavior_change_not_regression)
- **test**: `analysis/verified_gold/14740/B40-missing-i18n-key-causes-add-guests-permission-error-to-dis/defects/14740-D19/test.diff`
- **fix**: `analysis/verified_gold/14740/B40-missing-i18n-key-causes-add-guests-permission-error-to-dis/defects/14740-D19/fix.patch`  ·  **logs**: `analysis/verified_gold/14740/B40-missing-i18n-key-causes-add-guests-permission-error-to-dis/defects/14740-D19/logs`
- **finding**: packages/trpc/server/routers/viewer/bookings/addguests.handler.ts:55 — [p3 confidence=100] throw new trpcerror({ code: "forbidden", message: "youdonothavepermission" }); when this permission path executes, the absent com
