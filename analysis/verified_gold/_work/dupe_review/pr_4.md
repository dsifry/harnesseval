# PR 4 — 37 verified hidden gold bugs (id, summary, file:startline-endline, first supporting report)

## 4-B01
- summary: absolutize_urls treats protocol-relative URLs (//...) as root-relative and rewrites them to the article host
- location: app/models/topicembed.rb:48, 52-67, 53, 54, 55, 56, 56-58, 56-77
- reports: 116
- example report: absolutizeurls incorrectly rewrites protocol-relative urls under the article host

## 4-B02
- summary: Embed requests are wrongly rejected due to strict/unnormalized Referer host check (and requiring Referer)
- location: app/controllers/embedcontroller.rb:13, 13-16, 14, 15, 16, 17, 21, 25
- reports: 123
- example report: referer header check gating topicretriever fetching is not an authentication mechanism and can be manipulated by attackers

## 4-B03
- summary: Unbounded open-uri fetch in TopicEmbed can hang jobs or exhaust Sidekiq memory
- location: app/models/topicembed.rb:38, 44, 45, 46, 46-47, 47, 47-53, 48
- reports: 101
- example report: no fetch timeout or size cap is set on the open() fetches, so retrieval/poll jobs can be hung or oom'd

## 4-B04
- summary: Destructive `force: true` in create_table migration can drop existing data
- location: db/migrate/20131223171005createtoptopics.rb:3, 4
- reports: 82
- example report: db/migrate/20131223171005createtoptopics.rb:3 — force: true drops any existing toptopics table and its data before recreating it

## 4-B06
- summary: Redis throttle key can become permanent due to non-atomic SETNX + EXPIRE
- location: lib/topicretriever.rb:20-27, 22, 23-30, 24-31, 25-26, 26, 26-29, 26-30
- reports: 74
- example report: the redis setnx/expire throttle operations are non-atomic: a crash between them throttles that url forever.

## 4-B07
- summary: Redirect-based SSRF: only initial URL host is validated while open-uri follows redirects
- location: app/models/topicembed.rb:15, 36, 42, 43, 44, 44-46, 44-53, 45
- reports: 69
- example report: url validation occurs only before redirects, allowing an approved host to redirect server-side requests to internal or metadata endpoints.

## 4-B08
- summary: TopicEmbed re-import crashes when the embedded post was deleted (embed.post is nil)
- location: app/models/topicembed.rb:23-24, 24, 25-28, 27-31, 32, 32-37, 33, 34
- reports: 68
- example report: postrevisor.new(post) with no nil guard crashes if embed.postid points at a deleted post (app/models/topicembed.rb:23-24)

## 4-B09
- summary: Race condition: non-atomic exists?/create! on TopicEmbed causes RecordNotUnique under concurrent imports
- location: app/models/topicembed.rb:13-26, 14, 14-27, 15, 15-29, 15-30, 16, 16-30
- reports: 72
- example report: p2: race condition on unique embedurl — import does check-then-create instead of upsert, so concurrent retrieves raise recordnotunique

## 4-B12
- summary: Embed URL lookup uses exact, unnormalized string match, allowing duplicate topics for equivalent URLs
- location: app/models/topicembed.rb:11, 14, 15, 17, 78, 78-80, 79, 81
- reports: 42
- example report: topicembed.rb:79 lookup is an exact string match on embedurl, so query params, trailing slashes, and fragments create separate topics for the same article

## 4-B14
- summary: Unrescued inline feed poll aborts HTTP fallback on embed cache miss
- location: lib/topicretriever.rb:35-46, 37, 38, 38-41, 40, 41, 41-43, 42
- reports: 35
- example report: lib/topicretriever.rb:41 — an exception from the inline pollfeed propagates and skips the fetchhttp fallback, so the article is never retrieved.

## 4-B15
- summary: TopicEmbed advances contentsha1 even when post revision fails, permanently skipping future re-syncs
- location: app/models/topicembed.rb:9-38, 31-38, 34, 34-38, 36, 36-40, 37
- reports: 37
- example report: app/models/topicembed.rb:37 — advancing contentsha1 without checking revise! success permanently marks callback-rejected post updates as imported

## 4-B16
- summary: TopicEmbed embedurl column defaults to varchar(255), causing failures for valid long URLs during imports/polling
- location: app/models/topicembed.rb:20, 22, 47, 51
- reports: 33
- example report: db/migrate/20131217174004createtopicembeds.rb:6: embedurl has the default 255-character string limit, causing imports of valid longer urls to fail

## 4-B21
- summary: Throttle key is acquired before successful fetch and uses non-atomic setnx+expire, causing skipped retries or permanent lockout
- location: topicretriever.rb:27-28, 27-29, 28-35
- reports: 18
- example report: lib/topicretriever.rb:27 — recording the throttle before retrieval makes a failed fetch's sidekiq retry silently return success instead of retrying

## 4-B24
- summary: TopicEmbed import mutates caller-owned contents via `<<`, causing duplicate footers and FrozenError on frozen strings
- location: app/models/topicembed.rb:12, 13, 14
- reports: 16
- example report: contents << "\n<hr>..." mutates the caller's string in place and raises on frozen strings (app/models/topicembed.rb:12)

## 4-B25
- summary: Existing TopicEmbed updates ignore title-only changes, leaving topic titles stale
- location: app/models/topicembed.rb:34, 35, 36, 37
- reports: 18
- example report: app/models/topicembed.rb:34 ignores title changes for existing embeds, preventing title-only feed updates and title corrections

## 4-B26
- summary: TopicEmbed URL guard uses line-anchored regex and later calls URI() without rescue, allowing malformed/multiline URLs to crash imports
- location: app/models/topicembed.rb:11, 12, 56, 57, 58
- reports: 12
- example report: absolutizeurls: unhandled invalidurierror from uri(url) inside import causes job crash (p3)

## 4-B28
- summary: Embed/topic retrieval synchronously runs full feed poll (Jobs::PollFeed) on cache miss, coupling embeds to feed health and enabling resource exhaustion
- location: lib/topicretriever.rb:44-46, 47
- reports: 11
- example report: performretrieve calls jobs::pollfeed.new.execute({}) inline, running a full feed fetch, parse, and import synchronously on every cache-miss embed request with no timeout (lib/topicretriever.rb:44-46)

## 4-B29
- summary: TopicEmbed uses open(url) without requiring open-uri, causing URL opens to be treated as local files
- location: app/models/topicembed.rb:46, 47, 48
- reports: 12
- example report: app/models/topicembed.rb:48 — open(url).read relies on open-uri but topicembed.rb never requires it, so kernelopen can treat the url as a filename and raise errno::enoent; add require 'open-uri'

## 4-B33
- summary: Embed topic retrieval can crash or silently no-op when embedbyusername is blank/missing, leaving embeds stuck on infinite “loading”
- location: lib/topicretriever.rb:49, 50
- reports: 7
- example report: lib/topicretriever.rb:49 — a blank embedbyusername raises on downcase after every valid-host cache miss, and the loading page keeps re-enqueuing the permanently failing retrieval.

## 4-B34
- summary: Gemfile updated with new gems but default Gemfile.lock not regenerated, breaking frozen/deployment bundler installs
- location: Gemfile:(no line refs)
- reports: 6
- example report: ruby-readability and simple-rss added to gemfile:209 but only gemfilerails4.lock regenerated; the default gemfile.lock is untouched, breaking bundle install --deployment/frozen builds

## 4-B37
- summary: Rails migration adds NOT NULL column with DEFAULT, causing full table rewrite and ACCESS EXCLUSIVE lock on PostgreSQL < 11
- location: db/migrate/20131219203905addcookmethodtoposts.rb:3
- reports: 5
- example report: db/migrate/20131219203905addcookmethodtoposts.rb:3 adds a column with a non-null default to posts, rewriting the whole table under an access exclusive lock on postgres < 11

## 4-B39
- summary: Embeddable host validation uses strict string equality, rejecting valid hosts with different casing or with a scheme included
- location: lib/topicretriever.rb:14, 15
- reports: 4
- example report: lib/topicretriever.rb:15 — hostnames are compared case-sensitively even though dns host matching is case-insensitive, rejecting otherwise valid embed urls

## 4-B40
- summary: Migration backfills posts.cookmethod to rawhtml, causing all existing posts to bypass cooking/sanitization
- location: db/migrate/20131219203905addcookmethodtoposts.rb:3
- reports: 4
- example report: migration defaults posts to the rawhtml enum value, causing ordinary posts to bypass cooking and render raw markdown/html.

## 4-B41
- summary: Dead feed-modified cache key means PollFeed always re-downloads and reprocesses the full feed
- location: app/jobs/scheduled/pollfeed.rb:20, 20-22, 21
- reports: 4
- example report: pollfeed.rb:20 feedkey is defined but never used

## 4-B42
- summary: None
- location: topicembed.rb:59
- reports: 4
- example report: topicembed.rb:59 port logic should compare against uri.defaultport; https://host:80 and http://host:443 produce wrong prefixes

## 4-B46
- summary: Poll feed processing calls `String#scrub` via `stringscrub`, crashing on Ruby 2.0 (requires Ruby >= 2.1)
- location: pollfeed.rb:35
- reports: 3
- example report: stringscrub requires ruby >= 2.1; on ruby 2.0, which discourse targeted at this time, it raises nomethoderror even for valid strings

## 4-B48
- summary: Embed source hash includes localized footer, causing false-positive content changes on locale/footer updates
- location: app/models/topicembed.rb:12, 16
- reports: 2
- example report: app/models/topicembed.rb:16 — hashing after appending the localized footer couples source-change detection to presentation text, so footer or locale changes trigger needless post revisions

## 4-B51
- summary: `skip_validations` allows saving posts/topics with invalid or unsafe data (validations fully bypassed)
- location: lib/postrevisor.rb:85
- reports: 2
- example report: p2: importremote with skipvalidations: true can create topics with nil/blank titles when both opts[:title] and doc.title are nil

## 4-B56
- summary: poll_feed job processes unbounded RSS items, creating/enqueuing work for every entry in a single run
- location: app/jobs/scheduled/poll_feed.rb:(no line refs)
- reports: 1
- example report: [advisory] pollfeed fetches the feed with open() and then iterates rss.items with no count cap, running postcreator (which enqueues per-post processing jobs) for every item in a single job. a feed wit

## 4-B60
- summary: EmbedController enqueues RetrieveTopic job but spec expects synchronous TopicRetriever call
- location: app/controllers/embedcontroller.rb:16
- reports: 1
- example report: app/controllers/embedcontroller.rb:16 — the controller enqueues jobs::retrievetopic, but spec/controllers/embedcontrollerspec.rb:43 asserts topicretriever.new is called synchronously, so the tests enc

## 4-B61
- summary: RetrieveTopic job unnecessarily eager-loads mail stack via stray require_dependency
- location: app/jobs/regular/retrievetopic.rb:1
- reports: 2
- example report: app/jobs/regular/retrievetopic.rb:1 has an unrelated requiredependency 'email/sender' (copy-paste) that needlessly eager-loads the mail stack in the worker

## 4-B67
- summary: Missing presence check before calling `downcase` on `SiteSetting.embed_by_username` can raise NoMethodError
- location: pollfeed.rb:25
- reports: 1
- example report: duplication with drift risk: user.where(usernamelower: sitesetting.embedbyusername.downcase).first is duplicated at pollfeed.rb:25 and topicretriever.rb with inconsistent guards (pollfeed checks .pres

## 4-B69
- summary: embedurl param not type-checked allows non-String, causing unrescued TypeError in URI parsing and Sidekiq retry churn
- location: embedcontroller.rb:9-16
- reports: 1
- example report: embedcontroller.rb:9-16 / topicretriever.rb:15-18: embedurl is never validated as a string — params.require(:embedurl) happily returns an array/hash (?embedurl[]=x), and uri(@embedurl) in invalidhost?

## 4-B71
- summary: Invalid or wrong-host embed URLs are treated as successful retrieval, causing infinite loading loop
- location: lib/topicretriever.rb:9
- reports: 1
- example report: lib/topicretriever.rb:9 — [p1, confidence 100] performretrieve unless (invalidhost? || retrievedrecently?) acknowledges a malformed or wrong-host embed url as successful background work, so the contro

## 4-B72
- summary: OpenURI follows redirects, bypassing host allowlist when fetching embedded topic HTML
- location: topicembed.rb:48
- reports: 1
- example report: open(url) at topicembed.rb:48 follows redirects, so the host check in topicretriever does not actually constrain what gets fetched — one open redirect on the embeddable host hands the attacker control

## 4-B73
- summary: Feed item URL fallback uses entry.id (often not a URL), causing items to be silently skipped
- location: app/jobs/scheduled/poll_feed.rb:(no line refs)
- reports: 1
- example report: pollfeed.rb falls back to i.id which may not be a url, causing silent skipping of feed items with no logging (p3)

## 4-B74
- summary: Embed endpoint trusts spoofable Referer/embedurl and uses Referer as postMessage targetOrigin
- location: app/controllers/embedcontroller.rb:28
- reports: 1
- example report: referer check is weak/case-sensitive host equality and the embed endpoint trusts the client for both referer and embedurl; also post.message targetorigin uses request.referer, allowing spoofed referer
