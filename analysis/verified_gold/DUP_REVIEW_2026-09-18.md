# Total-gold duplicate determination — 2026-09-18

Six independent reviewers (one per PR) proposed 17 candidate duplicate groups over the 120 verified
defects. **Every group was re-adjudicated against hard evidence, not against its label**: the defect's own
test assertions, its own minimal fix diff, and the PR-head source. Labels were frequently wrong (they were
inherited from an LLM merge-audit of multi-concern bundles), so label similarity is not evidence.

## A. Actual duplicates — same site, one fix (14 groups, 15 defects merged away)

| group | verdict | decisive evidence |
|---|---|---|
| 4-D11 = 4-D25 | DUP | both = non-atomic `$redis.setnx` + `$redis.expire`; one site `lib/topic_retriever.rb:27-28` |
| 4-D12 = 4-D53 | DUP | only ONE `open()` exists — `app/models/topic_embed.rb:48` — so "redirects not revalidated" and "open follows redirects past the allowlist" are one weakness, two suggested fixes |
| 4-D33 = 4-D19 | DUP | one inline `Jobs::PollFeed.new.execute({})`, `lib/topic_retriever.rb:40-42` |
| 4-D43 = 4-D02 | DUP | one line, one fix: `uri.port != 80 && != 443` → `uri.port != uri.default_port`, `topic_embed.rb:59` |
| 4-D01 = 4-D44 | DUP | same lines + same fix: protocol-relative `//host` on both `href` (64) and `src` (70) |
| 4-D14 = 4-D21 | DUP | same scenario (orphaned embed → `embed.post` nil on the re-import update path), same 2-line block (32-38); `if post &&` cures both. D21's own test simulates *exactly* D14's case and prints PASS iff no `NoMethodError` |
| 8-D01 = 8-D02 | DUP | `group.visible = params[:visible] == "true"` in `#update` (`groups_controller.rb:38`); D02's own test drives the update-omitted-param case, identical to D01 |
| 10-D02 = 10-D06 | DUP | same lookup site: the stored host keeps its port, lookup compares the bare `uri.host` |
| 10-D07 = 10-D05 | DUP | one line, one fix: over-restrictive `validates_format_of :host` regex (`embeddable_host.rb:2`); D05 is a strict subset of D07 |
| 11059-D03 = 11059-D29 = 11059-D04 | DUP (3→1) | all three own tests assert the same thing — an HTTP **429** after repeated invalid secret attempts; D04's own fix installs a failed-attempt map. Its label ("static shared secret / HMAC") is inherited and does not describe what it demonstrated |
| 11059-D17 = 11059-D07 | DUP | same site: `findFirst` → separate `update`/`create`, lines 61-92 |
| 11059-D10 = 11059-D16 | DUP | same site: decrypted payload persisted unvalidated (lines 57-59); type-check vs schema-check are two strictnesses of one missing validation |
| 11059-D14 = 11059-D15 | DUP | one shared helper return contract (`refreshOAuthTokens.ts`); a helper-level fix cures both callers |
| 11059-D22 = 11059-D27 | DUP | same throw site, `parseRefreshTokenResponse.ts:19-21` |

## B. NOT duplicates — same bug *type* at a different place, or a different root cause

| pair | verdict | why distinct |
|---|---|---|
| 4-D26 vs 4-D29 | **DISTINCT** | D26 = `contents << "\n<hr>…"` mutates the caller-owned string (`topic_embed.rb:13`). D29's own test asserts a degenerate `http://` → `uri.host` nil → `URI::InvalidURIError` (`absolutize_urls`, line 57). D29's test *also* checks the mutation, but fixing one does not fix the other → two defects |
| 11059-D20 vs 11059-D03 family | **DISTINCT** | D20 = the instance-wide static secret is the sole authorization for arbitrary `userId`/`appSlug` (authz model). The D03 family = the same 5 lines are not rate-limited (brute-force protection). Different weakness, different fix |
| 14740-D04 vs 14740-D02 | **DISTINCT** | D04 = handler `isAttendee` over-permissive authorization (`addGuests.handler.ts:52-54`). D02's own test asserts `ZAddGuestsInputSchema.safeParse({guests: [500 emails]})` is rejected and its own fix is `.min(1).max(10)` — the missing guests cap in `addGuests.schema.ts:5`. Different file, different root cause. D02's inherited label was wrong and has been corrected |

## C. Under-count found by the same review (separate from the duplicate question)

The systematic check "does every bundle's own primary claim exist in the registry?" (similarity of each
bundle's `multi_defect.labels[0]` against that bundle's registry defects) found **6 bundles whose own claim
has no close registry match**:

- `4/B21` — *restored* as **4-D55** (premature throttle key suppresses its own retry); the folding had kept
  only the bundle's extra label.
- `11059/B19`, `8/B05` — folded as `duplicate_of` a keeper; their own claims ("case-normalization of env
  header name"; "breaking admin Groups API contract: nested `group[...]` params removed") merit a check that
  the fold was correct.
- `4/B33` (nil/blank `embed_by_username` → `NoMethodError` on `downcase`, line 49) vs the registry's
  "missing configured user silently returns" (line 50) — same 2-line block, two failure modes; needs the
  same same-site treatment.
- `4/B39` (case-sensitive hostname comparison) vs "configured host contains scheme" — both are the single
  exact `!=` comparison at `invalid_host?` (line 15); likely one defect with two manifestations, not two.

## D. Result

| | before | after |
|---|---|---|
| hidden-gold defects | 120 | **106** |
| double-counted | 15 | 0 (merged) |
| restored | — | +1 (4-D55) |
| **total gold (42 + defects)** | 162 (3.86×) | **148 (3.52×)** |
| test-validated hidden gold | 120 (2.86×) | **106 (2.52×)** |
