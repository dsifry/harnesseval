# Within-PR duplicate check of the verified hidden gold set

Adjudicated 305 candidate pairs (pre-filtered by shared file or >= 0.3 token overlap).
**Duplicate pairs found: 3**

| PR | bundle A | bundle B | confidence | reason |
|---|---|---|---|---|
| 11059 | 11059-B23 | 11059-B26 | 0.72 | Both findings center on the same root cause in parseRefreshTokenResponse: changing Zod safeParse failures/sche |
| 4 | 4-B02 | 4-B74 | 0.66 | Both findings center on the same root cause in embed_controller.rb: relying on the spoofable/unnormalized Refe |
| 8 | 8-B04 | 8-B05 | 0.62 | Both findings stem from the controller extracting only a limited set of top-level params (e.g., name/visible)  |
