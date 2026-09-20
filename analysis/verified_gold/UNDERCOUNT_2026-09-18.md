# Under-count triage — 2026-09-18

The merge audit (`MERGE_AUDIT.json`) split multi-concern bundles into 2–4 claims each, but only the claims
that got assigned findings became registry defects. Claims that were dropped are *candidate* defects. This
pass registers them and runs the same standard: author a test for the claim → must FAIL on the PR head →
author its own minimal fix → must PASS → the container's fix must leave it RED (orthogonality).

## The 13 candidates

| id | container | claim (from the audit) | location |
|---|---|---|---|
| `4-D56` | 4/B33 | blank/nil `embed_by_username` → `NoMethodError` on `downcase` | `lib/topic_retriever.rb:49` |
| `4-D57` | 4/B39 | case-sensitive hostname comparison in `invalid_host?` | `lib/topic_retriever.rb:15` |
| `4-D58` | 4/B07 | no URL-scheme validation before `open(url)` (SSRF / pipe-to-shell) | `app/models/topic_embed.rb:48` |
| `4-D59` | 4/B24 | `content_sha1` hashes the locale-dependent imported-from footer | `app/models/topic_embed.rb:13` |
| `4-D60` | 4/B03 | scheduled feed poll fetch has no timeout / error handling | `app/jobs/scheduled/poll_feed.rb` |
| `4-D61` | 4/B26 | EmbedController rescues the wrong URI exception for bad referer bytes | `app/controllers/embed_controller.rb:29` |
| `4-D62` | 4/B04 | historic `create_top_topics` migration carries destructive `force: true` | `db/migrate/20131223171005_create_top_topics.rb:3` |
| `8-D07` | 8/B05 | admin Groups API contract broken (nested `group[...]` params) | `app/controllers/admin/groups_controller.rb:22` |
| `11059-D30` | 11059/B19 | header lookup is not case-normalized | `app-credential.ts:25` |
| `11059-D31` | 11059/B19 | array-valued duplicate headers break the `!==` comparison | `app-credential.ts:25` |
| `11059-D32` | 11059/B19 | unset secret + absent header both `undefined` → auth bypass | `app-credential.ts:25` |
| `11059-D33` | 11059/B23 | Salesforce token schema requires `scope`, which its refresh response omits | `salesforce/lib/CalendarService.ts:45` |
| `11059-D34` | 11059/B23 | hardcoded Salesforce login host breaks sandbox orgs | `salesforce/lib/CalendarService.ts:75` |

`claim_index` records which audit claim each candidate came from (`0` = the container's own claim).

## The false-merge rule (fixed)

The verifier's orthogonality step asks "does the container's fix cure this candidate?" For a `claim_index == 0`
candidate, the container's fix **is its own minimal fix**, so the answer is yes *by construction* and must not
be read as a duplicate. `tools/verified_gold_registry_sync.py` and `tools/undercount_postprocess.py` now keep
and verify such candidates (`claim_index == 0` → D-verified, no sibling check) instead of merging/dropping
them. `4-D56` and `4-D57` were both affected; `4-D57` had been dropped and is restored.

## Outcomes so far

| id | outcome |
|---|---|
| `4-D56` | **D-verified** (container's own claim; container fix is its own fix) |
| `4-D57` | **D-verified** (same) |
| `4-D58` | **D-verified (orthogonal=True)** — a genuinely new, independent defect |
| `14740-D04` | **MERGED into `14740-D03`** — the B06 status-guard fix cures its test, so the "attendee-authz" claim is not separately demonstrated (the authz claim stays on the under-count list for a test that actually requires the authz restriction) |

Remaining candidates are still running; the monitor wakes the session on completion.
