# Verified hidden gold — PR 4

Candidates: 70 · verdicts: {'behavior_change_not_regression': 38, 'confirmed_regression': 3, 'inconclusive_env': 8, 'defect_present_before_pr': 10, 'unresolved_file': 10, 'test_quality_verified': 1}

| bug id | bug | verdict | head | base | fix | file | tarball sha256 |
|---|---|---|---|---|---|---|---|
| 4-B01 | B01-absolutizeurls-treats-protocol-relative-urls----as-r | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/models/topicembed.rb` | `a8d07fdbc931…` |
| 4-B02 | B02-embed-requests-are-wrongly-rejected-due-to-strict-unnorm | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/controllers/embedcontroller.rb` | `86015f62b99d…` |
| 4-B03 | B03-unbounded-open-uri-fetch-in-topicembed-can-hang-jobs-or- | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/models/topicembed.rb` | `1d0c920d5f1b…` |
| 4-B06 | B06-redis-throttle-key-can-become-permanent-due-to-non-atomi | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `lib/topicretriever.rb` | `843de583d387…` |
| 4-B07 | B07-redirect-based-ssrf-only-initial-url-host-is-validated-w | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `lib/topicretriever.rb` | `e67872ad0a22…` |
| 4-B08 | B08-topicembed-re-import-crashes-when-the-embedded-post-was- | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/models/topic_embed.rb` | `e0bf8e546140…` |
| 4-B09 | B09-race-condition-non-atomic-exists-create-on-topicembed-c | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `lib/topicretriever.rb` | `140a372204d6…` |
| 4-B12 | B12-embed-url-lookup-uses-exact-unnormalized-string-match-al | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/models/topicembed.rb` | `0dd1e10eae8a…` |
| 4-B14 | B14-unrescued-inline-feed-poll-aborts-http-fallback-on-embed | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `lib/topicretriever.rb` | `1ca52957cb9a…` |
| 4-B15 | B15-topicembed-advances-contentsha1-even-when-post-revision- | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/models/topicembed.rb` | `98c006632b14…` |
| 4-B16 | B16-topicembed-embedurl-column-defaults-to-varchar255-causi | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `db/migrate/20131217174004createtopicembeds.rb` | `7eab0faa750c…` |
| 4-B21 | B21-throttle-key-is-acquired-before-successful-fetch-and-use | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `lib/topicretriever.rb` | `8f197c6ec675…` |
| 4-B24 | B24-topicembed-import-mutates-caller-owned-contents-via-- | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/models/topicembed.rb` | `f2d14f6aeb80…` |
| 4-B25 | B25-existing-topicembed-updates-ignore-title-only-changes-le | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/models/topicembed.rb` | `e456891c2932…` |
| 4-B26 | B26-topicembed-url-guard-uses-line-anchored-regex-and-later- | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/models/topicembed.rb` | `d1ae94d4edf4…` |
| 4-B28 | B28-embed-topic-retrieval-synchronously-runs-full-feed-poll- | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `lib/topicretriever.rb` | `b20a06fca97b…` |
| 4-B29 | B29-topicembed-uses-openurl-without-requiring-open-uri-caus | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/models/topicembed.rb` | `b54a1ce1655c…` |
| 4-B33 | B33-embed-topic-retrieval-can-crash-or-silently-no-op-when-e | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `lib/topicretriever.rb` | `43327524c037…` |
| 4-B35 | B35-redis-throttle-key-is-set-before-retrieval-succeeds-supp | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `lib/topicretriever.rb` | `5f49a6865ffe…` |
| 4-B37 | B37-rails-migration-adds-not-null-column-with-default-causin | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `db/migrate/20131219203905addcookmethodtoposts.rb` | `df2110eff72f…` |
| 4-B39 | B39-embeddable-host-validation-uses-strict-string-equality-r | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `lib/topicretriever.rb` | `83c73b6aa875…` |
| 4-B40 | B40-migration-backfills-postscookmethod-to-rawhtml-causing-a | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `db/migrate/20131219203905_add_cookmethod_to_posts.rb` | `022f82662f8c…` |
| 4-B41 | B41-dead-feed-modified-cache-key-means-pollfeed-always-re-do | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/jobs/scheduled/pollfeed.rb` | `6764b15854ed…` |
| 4-B42 | B42-topicembedrb59-port-logic-should-compare-against-uridef | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `None` | `a41ef09ff00e…` |
| 4-B46 | B46-poll-feed-processing-calls-stringscrub-via-stringscrub | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `lib/pollfeed.rb` | `43dcf99ce48f…` |
| 4-B48 | B48-embed-source-hash-includes-localized-footer-causing-fals | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/models/topicembed.rb` | `b659db07b180…` |
| 4-B55 | B55-topicembed-import-uses-non-atomic-exists-create-allowing | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/models/topic_embed.rb` | `af81677fdd8b…` |
| 4-B56 | B56-pollfeed-job-processes-unbounded-rss-items-creating-enqu | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/jobs/regular/poll_feed.rb` | `150eb8721ecc…` |
| 4-B60 | B60-embedcontroller-enqueues-retrievetopic-job-but-spec-expe | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/controllers/embedcontroller.rb` | `5e19ff99819a…` |
| 4-B61 | B61-retrievetopic-job-unnecessarily-eager-loads-mail-stack-v | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/jobs/regular/retrievetopic.rb` | `d9c5dca57da1…` |
| 4-B67 | B67-missing-presence-check-before-calling-downcase-on-sites | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `lib/discourse_graphite/topic_retriever.rb` | `5d8cb782eb0c…` |
| 4-B69 | B69-embedurl-param-not-type-checked-allows-non-string-causin | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/controllers/embed_controller.rb` | `a26469c49b14…` |
| 4-B71 | B71-invalid-or-wrong-host-embed-urls-are-treated-as-successf | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `lib/topicretriever.rb` | `473dabeff7ce…` |
| 4-B72 | B72-openuri-follows-redirects-bypassing-host-allowlist-when- | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `lib/topicembed.rb` | `37aae558b8df…` |
| 4-B73 | B73-feed-item-url-fallback-uses-entryid-often-not-a-url-ca | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `pollfeed.rb` | `a021944fd2f8…` |
| 4-B74 | B74-embed-endpoint-trusts-spoofable-referer-embedurl-and-use | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `app/controllers/embedcontroller.rb` | `ad98813f266c…` |
| 4-B78 | B78-using--to-append-to-contents-mutates-the-callers-st | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `lib/topicembed.rb` | `879ad002f024…` |
| 4-B79 | B79-cache-miss-on-arbitrary-url-triggers-synchronous-full-rs | `behavior_change_not_regression` | FAIL | ERROR:LoadError | PASS | `topicretriever.rb` | `2ca6a4c2fd25…` |
| 4-B04 | B04-destructive-force-true-in-createtable-migration-can-dr | `confirmed_regression` | FAIL | PASS | PASS | `db/migrate/20131223171005createtoptopics.rb` | `2d2984ff3a47…` |
| 4-B34 | B34-gemfile-updated-with-new-gems-but-default-gemfilelock-no | `confirmed_regression` | FAIL | PASS | PASS | `Gemfile` | `813e4840d676…` |
| 4-B51 | B51-skipvalidations-allows-saving-posts-topics-with-invalid | `confirmed_regression` | FAIL | PASS | PASS | `lib/post_revisor.rb` | `96e84151017c…` |
| 4-B10 | B10-embed-loading-page-reloads-forever-with-no-terminal-fail | `defect_present_before_pr` | FAIL | ? | PASS | `app/views/embed/loading.html.erb` | `8ada24c4786e…` |
| 4-B17 | B17-embedcontroller-spec-expects-synchronous-topicretriever- | `defect_present_before_pr` | FAIL | FAIL | PASS | `spec/controllers/embed_controller_spec.rb` | `ea7d0af528a7…` |
| 4-B18 | B18-embedjs-throws-when-discourse-comments-container-is-miss | `defect_present_before_pr` | FAIL | ? | PASS | `app/assets/javascripts/embed.js` | `fc63bc5a0c03…` |
| 4-B32 | B32-embed-layout-references-standalone-embed-assets-that-are | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/views/layouts/embed.html.erb` | `34fd6a5bd1b3…` |
| 4-B38 | B38-embed-best-view-renders-imported-post-html-as-raw-enabli | `defect_present_before_pr` | FAIL | ? | PASS | `app/views/embed/best.html.erb` | `2924e844c9ee…` |
| 4-B44 | B44-disqus-importer-now-live-fetches-thread-urls-via-topicem | `defect_present_before_pr` | FAIL | FAIL | PASS | `lib/tasks/disqus.thor` | `a9cef886b8f9…` |
| 4-B57 | B57-erb-syntax-error-invalid-end-if-terminator-breaks-embed | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/views/embed/best.html.erb` | `e91d7ff146ee…` |
| 4-B62 | B62-requiredependency-nokogiri-can-raise-loaderror-in-r | `defect_present_before_pr` | FAIL | FAIL | PASS | `app/models/topicembed.rb` | `22c938f7918d…` |
| 4-B70 | B70-unescaped-requestreferer-interpolated-into-js-string-bre | `defect_present_before_pr` | FAIL | ? | PASS | `app/views/layouts/embed.html.erb` | `85810e7ab946…` |
| 4-B80 | B80-embed-loading-page-auto-reloads-every-30s-amplifying-una | `defect_present_before_pr` | FAIL | ? | PASS | `app/views/embed/loading.html.erb` | `7f4b2e9c1eb1…` |
| 4-B05 | B05-disqus-importer-silently-drops---category--c-support-and | `inconclusive_env` | FAIL | — | FAIL | `lib/tasks/disqus.thor` | `35bc405cbcbd…` |
| 4-B31 | B31-pollfeed-specs-for-missing-url-username-are-vacuous-beca | `inconclusive_env` | FAIL | — | FAIL | `spec/jobs/pollfeedspec.rb` | `7ee9b1f07a51…` |
| 4-B45 | B45-disqus-importer-is-no-longer-idempotent-reruns-duplicate | `inconclusive_env` | ERROR:NameError | — | — | `lib/tasks/disqus.thor` | `dcfe890396e8…` |
| 4-B49 | B49-disqus-import-passes-untrusted-thread-link-to-importremo | `inconclusive_env` | FAIL | — | FAIL | `lib/tasks/disqus.thor` | `0a5986e8488f…` |
| 4-B53 | B53-stored-xss-postcook-returns-raw-html-unchanged-when-cook | `inconclusive_env` | ERROR:NoMethodError | — | — | `app/models/post.rb` | `daa6052090fd…` |
| 4-B63 | B63-topicembed-stores-redundant-topicid-that-can-go-stale-wh | `inconclusive_env` | FAIL | — | ERROR:NameError | `app/models/topicembed.rb` | `3cc07201cce3…` |
| 4-B64 | B64-embedded-iframe-height-is-posted-only-on-load-causing-cl | `inconclusive_env` | FAIL | — | FAIL | `app/views/layouts/embed.html.erb` | `4f49c4224f48…` |
| 4-B65 | B65-new--embed-best-route-is-unnamed-and-unconstrained-so-it | `inconclusive_env` | ERROR:uninitialized constant | — | — | `config/routes.rb` | `07c694c81ba5…` |
| 4-B75 | B75-embed-controller-spec-for-missing-embedurl-is-a-false-po | `test_quality_verified` | PASS | ERROR:LoadError | — | `spec/controllers/embed_controller_spec.rb` | `06ab48a01245…` |
| 4-B19 | B19-disqusimport-regresses-to-live-http-fetch-per-thread-wit | `unresolved_file` | — | — | — | `lib/tasks/disqus.rake` | `c46f1212154e…` |
| 4-B30 | B30-readability-import-sanitizer-preserves-javascript-urls-i | `unresolved_file` | — | — | — | `lib/import_remote/readability.rb` | `47c6d305376d…` |
| 4-B43 | B43-falling-back-to-iid-when-link-is-blank-may-store-a-non-u | `unresolved_file` | — | — | — | `None` | `46efd7edcc35…` |
| 4-B47 | B47-disqus-importer-drops-original-topic-op-createdat-by-swi | `unresolved_file` | — | — | — | `script/import_scripts/disqus.rb` | `de6ae249d4be…` |
| 4-B50 | B50-migration-uses-force-true-risking-silent-table-drop-an | `unresolved_file` | — | — | — | `migrations/createtoptopics.rb` | `03c10c4c2096…` |
| 4-B54 | B54-referer-based-gating-breaks-for-referer-suppressing-clie | `unresolved_file` | — | — | — | `None` | `8d657b6d70cf…` |
| 4-B59 | B59-migrations-add-postscookmethod-and-topicembeds-table-but | `unresolved_file` | — | — | — | `db/schema.rb` | `d60de81c7615…` |
| 4-B66 | B66-embed-url-is-constructed-by-naive-string-concatenation-b | `unresolved_file` | — | — | — | `N/A (not referenced in the deduplicated reports; not modified in PR #4 diff)` | `c83ef1824962…` |
| 4-B76 | B76-the-embeddablehost-setting-is-silently-config-sensitive- | `unresolved_file` | — | — | — | `None` | `219e48f528e8…` |
| 4-B77 | B77-scheduled-and-inline-poll-can-run-concurrently-and-dupli | `unresolved_file` | — | — | — | `N/A (not referenced in reports; affected file not included in this PR diff)` | `a1d20b13bef5…` |
