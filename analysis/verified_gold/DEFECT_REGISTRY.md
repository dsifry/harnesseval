# Defect registry — individual bugs (bundle -> defect renumbering)

**135 individual defects** from 101 verified bundles (includes duplicate bundles' unique labels): **91 D-verified** (own executed test+fix) and **44 D-labelled** (split out by the merge audit, findings only, no dedicated test yet).

| PR | D-verified | D-labelled | total |
|---|---|---|---|
| 4 | 35 | 19 | 54 |
| 8 | 5 | 1 | 6 |
| 10 | 18 | 4 | 22 |
| 10967 | 4 | 1 | 5 |
| 11059 | 13 | 16 | 29 |
| 14740 | 16 | 3 | 19 |
| **total** | **91** | **44** | **135** |

## First 25 defects

| id | tier | anchor | label |
|---|---|---|---|
| 4-D01 | D-verified | `app/models/topic_embed.rb:` | Incorrect resolution of relative/protocol-relative URLs in absolutizeurls |
| 4-D02 | D-labelled | `app/models/topic_embed.rb:` | Incorrect scheme-unaware port handling drops explicit cross-scheme ports |
| 4-D03 | D-labelled | `app/controllers/embed_controller.rb:` | Referer header trusted as spoofable embeddability/auth gate |
| 4-D04 | D-labelled | `app/controllers/embed_controller.rb:` | Retrieval jobs enqueued before throttle/dedupe, allowing Sidekiq queue flooding |
| 4-D05 | D-verified | `app/controllers/embed_controller.rb:` | Case-sensitive/unnormalized host comparison against free-form embeddablehost setting |
| 4-D06 | D-labelled | `app/controllers/embed_controller.rb:` | Staff-only throttle bypass in RetrieveTopic job |
| 4-D07 | D-verified | `app/models/topic_embed.rb:` | topicembed remote article download lacks open/read timeout and size limit |
| 4-D08 | D-labelled | `app/models/topic_embed.rb:` | pollfeed scheduled feed fetch lacks timeout and error handling |
| 4-D09 | D-labelled | `db/migrate/20131223171005_create_top_topics.rb:` | unsafe historical edit to createtoptopics adding force: true |
| 4-D10 | D-verified | `db/migrate/20131223171005_create_top_topics.rb:` | topicembeds migration uses destructive force: true and lacks foreign keys/dependent cleanu |
| 4-D11 | D-verified | `lib/topic_retriever.rb:` | Redis throttle key can become permanent due to non-atomic SETNX + EXPIRE |
| 4-D12 | D-verified | `lib/topic_retriever.rb:` | SSRF via open-uri redirects not revalidated against allowed host |
| 4-D13 | D-labelled | `lib/topic_retriever.rb:` | Missing scheme validation in TopicEmbed#import_remote allowing SSRF/pipe-to-shell |
| 4-D14 | D-verified | `app/models/topic_embed.rb:` | TopicEmbed re-import crashes when the embedded post was deleted (embed.post is nil) |
| 4-D15 | D-verified | `lib/topic_retriever.rb:` | check-then-create race on unique TopicEmbed embedurl |
| 4-D16 | D-labelled | `lib/topic_retriever.rb:` | enqueue/publish before outer transaction commits |
| 4-D17 | D-verified | `app/models/topic_embed.rb:` | Embed URL lookup uses exact, unnormalized string match, allowing duplicate topics for equi |
| 4-D18 | D-verified | `lib/topic_retriever.rb:` | Inline feed poll exceptions abort performretrieve before HTTP fallback and may propagate i |
| 4-D19 | D-labelled | `lib/topic_retriever.rb:` | Every embed cache miss runs a full synchronous feed poll, repeatedly downloading/importing |
| 4-D20 | D-verified | `app/models/topic_embed.rb:` | ignored revise! failure with unconditional contentsha1 advance |
| 4-D21 | D-labelled | `app/models/topic_embed.rb:` | missing update-path spec coverage/nil-post edge |
| 4-D22 | D-labelled | `app/models/topic_embed.rb:` | concurrent import body/digest race |
| 4-D23 | D-verified | `db/migrate/20131217174004_create_topic_embeds.rb:` | TopicEmbed embedurl column defaults to varchar(255), causing failures for valid long URLs  |
| 4-D24 | D-labelled | `lib/topic_retriever.rb:` | Premature throttle key set before fetch success suppresses retries |
| 4-D25 | D-verified | `lib/topic_retriever.rb:` | Non-atomic setnx plus expire can leave permanent throttle key |
