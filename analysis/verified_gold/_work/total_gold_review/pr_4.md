# PR 4 — 45 VERIFIED defects (total gold, excluding the 42 original goldens)

Every entry below already passed: its own test FAILS on the PR head, its own minimal fix makes it PASS, and the
bundle's own (sibling) fix leaves it RED — i.e. an executed orthogonality check. The question is whether any two
entries nevertheless describe the SAME underlying defect (same root cause, same code path, one fix would cover both).

## 4-D01  [D-verified]  bundle=4-B01
- label: Incorrect resolution of relative/protocol-relative URLs in absolutizeurls
- location: app/models/topic_embed.rb:(no line refs)
- example finding: app/models/topicembed.rb:65 — importing a scheme-relative link or image such as //cdn.example.com/image.png rewrites its authority into a path on the article host, while ordinary relative references remain relative to discourse and explicit http port 443 is discarded, breaking imported navigation an

## 4-D02  [D-verified, orthogonal]  bundle=4-B01
- label: Incorrect scheme-unaware port handling drops explicit cross-scheme ports
- location: app/models/topic_embed.rb:(no line refs)
- example finding: app/models/topicembed.rb:59 — an article served at http://example.com:443/post or https://example.com:80/post loses its explicit nondefault port when root-relative links are converted, sending readers and image requests to the wrong service (p2; confidence 100; code: prefix << ":{uri.port}" if uri.p

## 4-D03  [D-verified, orthogonal]  bundle=4-B02
- label: Referer header trusted as spoofable embeddability/auth gate
- location: app/controllers/embed_controller.rb:(no line refs)
- example finding: [advisory] the referer host check is the only gate on the unauthenticated /embed/best endpoint, but referer is a client-supplied header, and the jobs.enqueue at line 15 runs on every request with no request-level rate limit. anyone can curl the endpoint with a forged referer and unlimited distinct e

## 4-D04  [D-verified, orthogonal]  bundle=4-B02
- label: Retrieval jobs enqueued before throttle/dedupe, allowing Sidekiq queue flooding
- location: app/controllers/embed_controller.rb:(no line refs)
- example finding: app/controllers/embedcontroller.rb:15 — jobs.enqueue(:retrievetopic, ...) is called on every request for an embedurl with no existing topicid, with no request-level dedup/rate-limit in the controller itself; the only downstream guard is topicretrieverretrievedrecently?'s redis setnx, but that guard 

## 4-D05  [D-verified]  bundle=4-B02
- label: Case-sensitive/unnormalized host comparison against free-form embeddablehost setting
- location: app/controllers/embed_controller.rb:(no line refs)
- example finding: app/controllers/embedcontroller.rb:26 — uri(request.referer || '').host != sitesetting.embeddablehost is a bare string equality on host only, ignoring scheme and port, so http://embeddablehost:9999 or a subdomain-based spoof with a permissive proxy setup passes this check identically to the legitima

## 4-D06  [D-verified, orthogonal]  bundle=4-B02
- label: Staff-only throttle bypass in RetrieveTopic job
- location: app/controllers/embed_controller.rb:(no line refs)
- example finding: 

## 4-D07  [D-verified]  bundle=4-B03
- label: topicembed remote article download lacks open/read timeout and size limit
- location: app/models/topic_embed.rb:(no line refs)
- example finding: app/models/topicembed.rb:48 — an article endpoint that keeps streaming a large body is consumed without a total deadline or byte limit and then copied fully into memory for readability, exhausting a worker's capacity instead of terminating the retrieval (p2; confidence 100; code: doc = readability::

## 4-D10  [D-verified]  bundle=4-B04
- label: topicembeds migration uses destructive force: true and lacks foreign keys/dependent cleanup
- location: db/migrate/20131223171005_create_top_topics.rb:(no line refs)
- example finding: [advisory] createtable :topicembeds uses force: true, making the migration destructive on re-run, and the table defines topicid/postid as plain integers with no foreign keys or dependent cleanup. re-running the migration drops any populated topicembeds rows (losing the embedurl→topic mapping, which 

## 4-D11  [D-verified]  bundle=4-B06
- label: Redis throttle key can become permanent due to non-atomic SETNX + EXPIRE
- location: lib/topic_retriever.rb:(no line refs)
- example finding: lib/topicretriever.rb:27 — advisory p2, confidence 100: $redis.setnx(retrievedkey, "1") followed by the separate $redis.expire(retrievedkey, 60) permanently suppresses that article's retrieval for nonstaff readers when the process exits or the redis connection fails between the commands; the stronge

## 4-D12  [D-verified]  bundle=4-B07
- label: SSRF via open-uri redirects not revalidated against allowed host
- location: lib/topic_retriever.rb:(no line refs)
- example finding: [bug] the ssrf guard compares only the initial url's host string against sitesetting.embeddablehost, but the actual fetch in topicembed.importremote (app/models/topicembed.rb:48) uses open(), which follows cross-host http->http redirects, and a string host comparison is defeated by dns rebinding, so

## 4-D14  [D-verified]  bundle=4-B08
- label: TopicEmbed re-import crashes when the embedded post was deleted (embed.post is nil)
- location: app/models/topic_embed.rb:(no line refs)
- example finding: [bug] topicembed rows are never cleaned up when their topic or post is destroyed (the diff adds no destroy hook and no admin path to remove an embed), so topicidforembed keeps returning a dead topicid and the update path dereferences a nil post. after an admin permanently deletes an imported topic, 

## 4-D15  [D-verified]  bundle=4-B09
- label: check-then-create race on unique TopicEmbed embedurl
- location: lib/topic_retriever.rb:(no line refs)
- example finding: [advisory] import is check-then-create on embedurl (where first, then create!) with no rescue of the unique-index violation, so two concurrent imports of the same url collide on the unique index. embedcontroller enqueues a retrievetopic job per viewer for a not-yet-imported article; two viewers with

## 4-D16  [D-verified, orthogonal]  bundle=4-B09
- label: enqueue/publish before outer transaction commits
- location: lib/topic_retriever.rb:(no line refs)
- example finding: app/models/topicembed.rb:23 — wrapping postcreator.create in an outer transaction causes its enqueuejobs and topic publication to execute before the new topic and post commit, so a worker or subscriber running immediately cannot see the announced records (p1; confidence 75; code: post = creator.crea

## 4-D17  [D-verified]  bundle=4-B12
- label: Embed URL lookup uses exact, unnormalized string match, allowing duplicate topics for equivalent URLs
- location: app/models/topic_embed.rb:(no line refs)
- example finding: [bug] the embedurl join key is written by two independent producers — pollfeed stores the feed item's link while topicretriever stores the page's discourseembedurl query param — and every lookup (topicembed.where(embedurl: url) here and topicidforembed at line 78) is exact string equality with no ca

## 4-D18  [D-verified]  bundle=4-B14
- label: Inline feed poll exceptions abort performretrieve before HTTP fallback and may propagate into retry logic
- location: lib/topic_retriever.rb:(no line refs)
- example finding: lib/topicretriever.rb:41 — jobs::pollfeed.new.execute({}) runs inline with no rescue; any feed failure (openuri::httperror, timeout, simplersserror, bad item) propagates and prevents the fetchhttp fallback from ever being tried, so the embed stays stuck on "loading" even though the page itself is fe

## 4-D19  [D-verified, orthogonal]  bundle=4-B14
- label: Every embed cache miss runs a full synchronous feed poll, repeatedly downloading/importing the entire feed per URL
- location: lib/topic_retriever.rb:(no line refs)
- example finding: lib/topicretriever.rb:41 — concurrent first visits to n distinct article urls each download and process all m entries of the same feed, multiplying network traffic and import queries to n full downloads and n×m import attempts (p2; confidence 100; code: jobs::pollfeed.new.execute({}); advisory: the 

## 4-D20  [D-verified]  bundle=4-B15
- label: ignored revise! failure with unconditional contentsha1 advance
- location: app/models/topic_embed.rb:(no line refs)
- example finding: [bug] on the update path, embed.updatecolumn(:contentsha1, contentsha1) runs unconditionally after postrevisorrevise!, without checking whether the revision actually succeeded. postrevisorrevise! returns false without saving when shouldrevise? is false, and the new @post.save(validate: !@opts[:skipv

## 4-D21  [D-verified, orthogonal]  bundle=4-B15
- label: missing update-path spec coverage/nil-post edge
- location: app/models/topic_embed.rb:(no line refs)
- example finding: topicembed.rb:31-34 update path assumes embed.post is non-nil when passing it to postrevisor.new; nothing removes topicembeds rows when a topic/post is destroyed, so an orphaned embed makes postrevisorinitialize nomethoderror mid-loop inside pollfeed's rss.items.each with retry: false — every feed i

## 4-D22  [D-verified, orthogonal]  bundle=4-B15
- label: concurrent import body/digest race
- location: app/models/topic_embed.rb:(no line refs)
- example finding: app/models/topicembed.rb:37 — concurrent scheduled and on-demand feed imports can commit body a, then body b and digest b, then digest a, leaving a body/digest mismatch that causes the next import of a to skip the required update (p2; confidence 75; code: embed.updatecolumn(:contentsha1, contentsha1

## 4-D23  [D-verified]  bundle=4-B16
- label: TopicEmbed embedurl column defaults to varchar(255), causing failures for valid long URLs during imports/polling
- location: db/migrate/20131217174004_create_topic_embeds.rb:(no line refs)
- example finding: [bug] topicembed.import writes unvalidated, unlength-capped external data into storage: embedurl is only presence-validated (line 6) against a varchar(255) column, and feed titles flow into topic's title with skipvalidations: true, so an embed url over 255 characters (long query strings) or an overs

## 4-D25  [D-verified]  bundle=4-B21
- label: Non-atomic setnx plus expire can leave permanent throttle key
- location: lib/topic_retriever.rb:(no line refs)
- example finding: setnx/expire are not atomic in topicretriever.rb:27-28 — if the process dies between the two calls, the retrieved:<url> key persists with no ttl, permanently throttling that url so every subsequent embed view skips retrieval and shows 'loading discussion...' indefinitely with no recovery short of ma

## 4-D26  [D-verified]  bundle=4-B24
- label: mutating caller-owned contents string with <<
- location: app/models/topic_embed.rb:(no line refs)
- example finding: app/models/topicembed.rb:13 — advisory p2, confidence 100: contents << "\n<hr>\n<small>{i18n.t('embed.importedfrom', link: "<a href='{url}'>{url}</a>")}</small>\n" mutates the caller's article string, so an integration developer retrying import with the same content object appends a second attributi

## 4-D28  [D-verified]  bundle=4-B25
- label: Existing TopicEmbed updates ignore title-only changes, leaving topic titles stale
- location: app/models/topic_embed.rb:(no line refs)
- example finding: app/models/topicembed.rb:34 — advisory p2 confidence 100: if contentsha1 != embed.contentsha1 keys updates solely on body content and revisor.revise!(user, absolutizeurls(url, contents), skipvalidations: true, bypassratelimiter: true) never writes the supplied title, so publishers correcting an arti

## 4-D29  [D-verified, orthogonal]  bundle=4-B26
- label: TopicEmbedImport mutates caller's contents string in place
- location: app/models/topic_embed.rb:(no line refs)
- example finding: topicembedimport mutates the caller's contents string in place, and url =~ /^https?\:\/\// accepts degenerate urls like 'http://' causing uri::invalidurierror in absolutizeurls, crashing the importing job instead of rejecting the url

## 4-D30  [D-verified]  bundle=4-B26
- label: line-anchored URL scheme regex allows multiline bypass/injection
- location: app/models/topic_embed.rb:(no line refs)
- example finding: app/models/topicembed.rb:11 — the url check return unless url =~ /^https?\:\/\// uses ruby's line anchor ^, so a multi-line value such as "javascript:alert(1)\nhttp://x" passes. that url is then placed unescaped into <a href='{url}'> on line 13 inside a rawhtml post, so the check is weaker than the 

## 4-D33  [D-verified]  bundle=4-B28
- label: Embed/topic retrieval synchronously runs full feed poll (Jobs::PollFeed) on cache miss, coupling embeds to feed health and enabling resource
- location: lib/topic_retriever.rb:(no line refs)
- example finding: [bug] topicretrieverperformretrieve executes the entire scheduled pollfeed job synchronously (jobs::pollfeed.new.execute({}) fetches the whole feed and imports every item) on the per-embed-request path, and any exception it raises propagates out before fetchhttp can run. each distinct embed url's fi

## 4-D34  [D-verified]  bundle=4-B29
- label: TopicEmbed uses open(url) without requiring open-uri, causing URL opens to be treated as local files
- location: app/models/topic_embed.rb:(no line refs)
- example finding: [advisory] topicembedimportremote calls open(url) but never requires open-uri; the diff's only require 'open-uri' sits in jobs::pollfeed, which is never loaded on the retrievetopic path when feed polling is disabled (the default). when open-uri is not loaded in the sidekiq process, kernelopen treats

## 4-D36  [D-verified]  bundle=4-B33
- label: Missing/mismatched configured user silently returns and leaves embed loading
- location: lib/topic_retriever.rb:(no line refs)
- example finding: lib/topicretriever.rb:49 — user = user.where(usernamelower: sitesetting.embedbyusername.downcase).first followed by return if user.blank? completes the retrieval job without importing whenever the configured username has no matching user, so embedcontrollerbest returns an auto-reloading loading fram

## 4-D37  [D-verified]  bundle=4-B34
- label: Gemfile updated with new gems but default Gemfile.lock not regenerated, breaking frozen/deployment bundler installs
- location: Gemfile:(no line refs)
- example finding: [advisory] the two new gems are added to the gemfile but only gemfilerails4.lock is regenerated; the repository's primary gemfile.lock is left without ruby-readability and simple-rss, breaking the lockfiles-in-lockstep invariant this repo maintains during the rails 3.2/4 transition. the default (rai

## 4-D38  [D-verified]  bundle=4-B37
- label: Rails migration adds NOT NULL column with DEFAULT, causing full table rewrite and ACCESS EXCLUSIVE lock on PostgreSQL < 11
- location: db/migrate/20131219203905_add_cook_method_to_posts.rb:(no line refs)
- example finding: db/migrate/20131219203905addcookmethodtoposts.rb:3 — addcolumn :posts, :cookmethod, :integer, default: 1, null: false rewrites the whole posts table under an access exclusive lock on postgres < 11, causing multi-minute downtime; add the column nullable, backfill in batches, then set default/not null

## 4-D40  [D-verified]  bundle=4-B39
- label: configured host contains scheme causing exact host mismatch
- location: lib/topic_retriever.rb:(no line refs)
- example finding: p2: embed url/host mismatch when admin enters a scheme in embeddablehost (exact equality against uri(...).host rejects all embeds if scheme included, killing the feature)

## 4-D41  [D-verified]  bundle=4-B40
- label: Migration backfills posts.cookmethod to rawhtml, causing all existing posts to bypass cooking/sanitization
- location: db/migrate/20131219203905_add_cook_method_to_posts.rb:(no line refs)
- example finding: db/migrate/20131219203905addcookmethodtoposts.rb:3 — [p1, confidence 100] addcolumn :posts, :cookmethod, :integer, default: 1, null: false assigns every pre-existing post the rawhtml enum value, so the new return raw branch bypasses cooking for all historical posts instead of retaining the declared 

## 4-D42  [D-verified]  bundle=4-B41
- label: Dead feed-modified cache key means PollFeed always re-downloads and reprocesses the full feed
- location: app/jobs/scheduled/poll_feed.rb:(no line refs)
- example finding: app/jobs/scheduled/pollfeed.rb:20-22 defines feedkey computing a feed-modified: cache key that is never read or written, so the hourly job re-downloads and re-imports the whole feed every time while the dead method advertises caching that does not exist

## 4-D43  [D-verified]  bundle=4-B42
- label: incorrect default-port comparison in absolutize_urls
- location: app/models/topic_embed.rb:(no line refs)
- example finding: spec/models/topicembedspec.rb:34 — .startwith?(...).should betrue covers only root-relative / hrefs on port 80; the non-default port branch (prefix << ":{uri.port}" at app/models/topicembed.rb:59) and //-prefixed protocol-relative urls (which startwith?('/') rewrites into http://host/host2/...) are 

## 4-D44  [D-verified, orthogonal]  bundle=4-B42
- label: protocol-relative URLs treated as root-relative
- location: app/models/topic_embed.rb:(no line refs)
- example finding: spec/models/topicembedspec.rb:34 — absolutizeurls edge cases are untested: protocol-relative "//host" urls, which get rewritten incorrectly, non-default ports, and https urls.

## 4-D45  [D-verified]  bundle=4-B46
- label: Poll feed processing calls `String#scrub` via `stringscrub`, crashing on Ruby 2.0 (requires Ruby >= 2.1)
- location: app/jobs/scheduled/poll_feed.rb:(no line refs)
- example finding: stringscrub is ruby >= 2.1 only — on the ruby 2.0 runtime current at this date, every pollfeed poll raises; rely on a backported scrub or an alternative

## 4-D46  [D-verified]  bundle=4-B48
- label: Embed source hash includes localized footer, causing false-positive content changes on locale/footer updates
- location: app/models/topic_embed.rb:(no line refs)
- example finding: sha1 is computed over the locale-translated footer, so changing site locale marks every previously imported topic as changed and triggers a spurious revision of every post (app/models/topicembed.rb:12)

## 4-D47  [D-verified]  bundle=4-B51
- label: `skip_validations` allows saving posts/topics with invalid or unsafe data (validations fully bypassed)
- location: lib/post_revisor.rb:(no line refs)
- example finding: lib/postrevisor.rb:85 — the new skipvalidations option lets callers persist posts bypassing all activerecord validations (spam/host/content checks) on content that originates from attacker-triggered imports.

## 4-D48  [D-verified]  bundle=4-B56
- label: poll_feed job processes unbounded RSS items, creating/enqueuing work for every entry in a single run
- location: app/jobs/scheduled/poll_feed.rb:(no line refs)
- example finding: [advisory] pollfeed fetches the feed with open() and then iterates rss.items with no count cap, running postcreator (which enqueues per-post processing jobs) for every item in a single job. a feed with thousands of entries becomes one multi-hour job that floods the sidekiq queue with per-post jobs a

## 4-D49  [D-verified]  bundle=4-B60
- label: EmbedController enqueues RetrieveTopic job but spec expects synchronous TopicRetriever call
- location: app/controllers/embed_controller.rb:(no line refs)
- example finding: app/controllers/embedcontroller.rb:16 — the controller enqueues jobs::retrievetopic, but spec/controllers/embedcontrollerspec.rb:43 asserts topicretriever.new is called synchronously, so the tests encode a different contract than the shipped code and cannot confirm the intended behavior (p1, conf 75

## 4-D50  [D-verified]  bundle=4-B61
- label: RetrieveTopic job unnecessarily eager-loads mail stack via stray require_dependency
- location: app/jobs/regular/retrieve_topic.rb:(no line refs)
- example finding: app/jobs/regular/retrievetopic.rb:1 has an unrelated requiredependency 'email/sender' (copy-paste) that needlessly eager-loads the mail stack in the worker

## 4-D51  [D-verified]  bundle=4-B69
- label: embedurl param not type-checked allows non-String, causing unrescued TypeError in URI parsing and Sidekiq retry churn
- location: app/controllers/embed_controller.rb:(no line refs)
- example finding: embedcontroller.rb:9-16 / topicretriever.rb:15-18: embedurl is never validated as a string — params.require(:embedurl) happily returns an array/hash (?embedurl[]=x), and uri(@embedurl) in invalidhost? raises typeerror (not uri::invalidurierror) which escapes the rescue, so each such request enqueues

## 4-D52  [D-verified]  bundle=4-B71
- label: Invalid or wrong-host embed URLs are treated as successful retrieval, causing infinite loading loop
- location: lib/topic_retriever.rb:(no line refs)
- example finding: lib/topicretriever.rb:9 — [p1, confidence 100] performretrieve unless (invalidhost? || retrievedrecently?) acknowledges a malformed or wrong-host embed url as successful background work, so the controller’s loading page reloads forever instead of returning the 4xx the invalid input requires.

## 4-D53  [D-verified]  bundle=4-B72
- label: OpenURI follows redirects, bypassing host allowlist when fetching embedded topic HTML
- location: app/models/topic_embed.rb:(no line refs)
- example finding: open(url) at topicembed.rb:48 follows redirects, so the host check in topicretriever does not actually constrain what gets fetched — one open redirect on the embeddable host hands the attacker control of the imported html, feeding the xss/url-injection issues

## 4-D54  [D-verified]  bundle=4-B73
- label: Feed item URL fallback uses entry.id (often not a URL), causing items to be silently skipped
- location: app/jobs/scheduled/poll_feed.rb:(no line refs)
- example finding: pollfeed.rb falls back to i.id which may not be a url, causing silent skipping of feed items with no logging (p3)
