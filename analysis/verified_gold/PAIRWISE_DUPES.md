# Within-PR duplicate check of the verified hidden gold set

Adjudicated 352 candidate pairs (pre-filtered by shared file or >= 0.3 token overlap).
**Duplicate pairs found: 3**

| PR | bundle A | bundle B | confidence | reason |
|---|---|---|---|---|
| 11059 | 11059-B24 | 11059-B33 | 0.74 | Both findings point to the same update logic for an existing app-credential row that only overwrites the key/p |
| 4 | 4-B24 | 4-B78 | 0.98 | Both findings describe the same root cause in topic_embed.rb: using `contents << ...` mutates the caller-owned |
| 4 | 4-B28 | 4-B79 | 0.93 | Both findings describe the same root cause in lib/topic_retriever.rb: on embed/cache miss, perform_retrieve sy |
