# Defect registry — final state (after the orthogonality experiment)

**Total gold = 42 goldens + 103 defects = 145 (3.45x goldens)**  ·  **test-validated hidden gold = 103 (2.45x goldens)**

- 16 labels were MERGED away: the sibling fix also cured them, so they were the bundle's own defect restated.
- 0 defects are undemonstrated in this harness, each with a specific reason.

| defect | bundle | class | why not demonstrated |
|---|---|---|---|

## Merged away (same defect as their bundle's label)

| defect | bundle | label |
|---|---|---|
| 11059-D02 | 11059-B05 | Unhandled req.headers string[]/undefined type causing comparison mismatch |
| 11059-D05 | 11059-B19 | array-valued duplicate headers |
| 11059-D06 | 11059-B19 | missing-config undefined auth bypass |
| 11059-D11 | 11059-B09 | non-constant-time webhook secret comparison |
| 11059-D24 | 11059-B23 | Salesforce refresh-token schema incorrectly requires scope |
| 11059-D25 | 11059-B23 | hardcoded Salesforce login host breaks sandbox orgs |
| 4-D08 | 4-B03 | pollfeed scheduled feed fetch lacks timeout and error handling |
| 4-D09 | 4-B04 | unsafe historical edit to createtoptopics adding force: true |
| 4-D13 | 4-B07 | Missing scheme validation in TopicEmbed#import_remote allowing SSRF/pipe-to-shell |
| 4-D24 | 4-B21 | Premature throttle key set before fetch success suppresses retries |
| 4-D27 | 4-B24 | contentsha1 hashes locale-dependent imported-from footer |
| 4-D30 | 4-B26 | line-anchored URL scheme regex allows multiline bypass/injection |
| 4-D31 | 4-B26 | unhandled URI parse errors abort import on malformed or degenerate URLs |
| 4-D32 | 4-B26 | EmbedController rescues wrong URI exception for invalid referer bytes |
| 4-D35 | 4-B33 | Nil/blank embedbyusername raises NoMethodError on downcase |
| 4-D39 | 4-B39 | case-sensitive hostname comparison |
