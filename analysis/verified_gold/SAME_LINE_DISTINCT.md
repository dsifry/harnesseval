# Same-line pairs that are NOT duplicates (reviewer adjudication)

Mechanical screens (identical anchors, <=10-line proximity) flagged many pairs that merely live in the same
function. Judged on mechanism and on the fix each would require, these pairs are DISTINCT defects:

| PR | bundle A | bundle B | shared lines | A's defect | B's defect |
|---|---|---|---|---|---|
| 4 | 4-B06 | 4-B21 | `topicretriever.rb:27-29` | non-atomic setnx+expire leaves a PERMANENT throttle key on a crash between the calls | throttle key written BEFORE the fetch succeeds, so a failed fetch is not retried for 60s |
| 10 | 10-B11 | 10-B12 | `20150818190757_create_embeddable_hosts.rb:3` | execute + destructive DELETE FROM site_settings inside change (irreversible rollback) | create_table force: true silently drops an existing table and its data |
| 10 | 10-B23 | 10-B05 | `embeddablehost.rb:2` | \z lets a trailing-newline host PASS validation (false accept) | {2,5} TLD cap REJECTS valid long gTLDs (false reject) |
| 11059 | 11059-B05 | 11059-B19 | `app-credential.ts:24-27` | !== non-constant-time compare (timing side channel) | env header name used raw, so a mixed-case value always 403s (case normalization) |

Also noted: 11059-B05's cluster absorbed a case-sensitivity report, so its title understates its
content; and 8-B00's cluster mixes pagination + API-contract + visible-flip (its pagination sub-claim
is tracked separately in its meta.multi_defect).
