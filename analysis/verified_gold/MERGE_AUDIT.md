# Merge audit — does each promoted bundle describe one defect?

Audited 100 promoted bundles with judge deepseek-4.1-flash. **Flagged as multi-defect: 28**

| bundle | findings | distinct | labels |
|---|---|---|---|
| 11059-B05 | 91 | 4 | Timing-unsafe webhook secret comparison (non-constant-time !==); Unhandled req.headers string[]/undefined type causing comparison mismatch;  |
| 11059-B09 | 41 | 4 | missing HTTP method guard on webhook endpoint; unhandled schema/decryption/JSON parse errors; missing validation of decrypted credential obj |
| 11059-B10 | 75 | 4 | credential-sync endpoint requests are unauthenticated; Lark refresh passes credential-sync flat response to handleLarkError expecting Lark e |
| 11059-B19 | 21 | 4 | case-normalization of env header name; array-valued duplicate headers; missing-config undefined auth bypass |
| 11059-B23 | 8 | 4 | parseRefreshTokenResponse throws instead of returning structured failure, breaking caller branches; credential refresh read-modify-write rac |
| 4-B02 | 123 | 4 | Referer header trusted as spoofable embeddability/auth gate; Retrieval jobs enqueued before throttle/dedupe, allowing Sidekiq queue flooding |
| 4-B26 | 12 | 4 | TopicEmbedImport mutates caller's contents string in place; line-anchored URL scheme regex allows multiline bypass/injection; unhandled URI  |
| 10-B03 | 143 | 3 | port handling mismatch between validation and lookup; missing controller test coverage for mutating endpoints and fallbacks; case-insensitiv |
| 10-B05 | 89 | 3 | Overly restrictive hostname/TLD validation regex; Port/path allowed in stored host but matching uses uri.host without port; Migrated legacy  |
| 4-B15 | 37 | 3 | ignored revise! failure with unconditional contentsha1 advance; missing update-path spec coverage/nil-post edge; concurrent import body/dige |
| 10967-B14 | 19 | 2 | Recurring deletion sweep nested inside bookingCalendarReference loop causing duplicate provider deletes/404s; Inner references.find only del |
| 11059-B14 | 49 | 2 | non-atomic find-then-create/upsert race causing duplicate credentials under concurrency; ambiguous credential lookup by userId+appId without |
| 11059-B22 | 11 | 2 | Instance-wide static webhook secret authorizes credential writes for arbitrary userid/appslug; No replay/event-identity/version guard permit |
| 14740-B03 | 104 | 2 | Missing max/rate limits on guests array enables unbounded guest inserts and email fan-out; addGuests authorization allows any booking attend |
| 14740-B06 | 124 | 2 | Missing booking status/end-time validation allows adding guests to cancelled, rejected, or past bookings; Over-permissive attendee-based aut |
| 14740-B17 | 14 | 2 | unbounded reply-to header including all attendee emails; team-member variant sends organizer-personalized content without teammember prop (e |
| 4-B01 | 116 | 2 | Incorrect resolution of relative/protocol-relative URLs in absolutizeurls; Incorrect scheme-unaware port handling drops explicit cross-schem |
| 4-B03 | 101 | 2 | topicembed remote article download lacks open/read timeout and size limit; pollfeed scheduled feed fetch lacks timeout and error handling |
| 4-B04 | 82 | 2 | unsafe historical edit to createtoptopics adding force: true; topicembeds migration uses destructive force: true and lacks foreign keys/depe |
| 4-B07 | 69 | 2 | SSRF via open-uri redirects not revalidated against allowed host; Missing scheme validation in TopicEmbed#import_remote allowing SSRF/pipe-t |
| 4-B09 | 72 | 2 | check-then-create race on unique TopicEmbed embedurl; enqueue/publish before outer transaction commits |
| 4-B14 | 35 | 2 | Inline feed poll exceptions abort performretrieve before HTTP fallback and may propagate into retry logic; Every embed cache miss runs a ful |
| 4-B21 | 18 | 2 | Premature throttle key set before fetch success suppresses retries; Non-atomic setnx plus expire can leave permanent throttle key |
| 4-B24 | 16 | 2 | mutating caller-owned contents string with <<; contentsha1 hashes locale-dependent imported-from footer |
| 4-B33 | 7 | 2 | Nil/blank embedbyusername raises NoMethodError on downcase; Missing/mismatched configured user silently returns and leaves embed loading |
| 4-B39 | 4 | 2 | case-sensitive hostname comparison; configured host contains scheme causing exact host mismatch |
| 4-B42 | 4 | 2 | incorrect default-port comparison in absolutize_urls; protocol-relative URLs treated as root-relative |
| 8-B05 | 96 | 2 | Breaking admin Groups API contract: nested group[...] params removed and updatepatch deleted without deprecation; Incorrect visible assignme |
