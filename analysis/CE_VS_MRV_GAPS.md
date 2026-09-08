# What Compound Engineering finds that metareview doesn't

**Question:** Across matched (model × effort × PR) pairs, what does CE catch that MRV misses,
and what clusters does it fall into?

**Method.** 81 matched pairs (mrv + ce, latest pass run each, same PR) across 8 models ×
low/high × 6 PRs (opus-5, sonnet-5, sol, terra, fable-5.1, astra, glm-5.3, glm-5.3-flash;
GLM "high" = manifest `xhigh` per report2 §2.2). Every CE confirmed hidden-gold bug
(`readjudication3` `new_verdict == "bug"`, n=1,581) was semantically matched against the full
MRV finding list for the same pair (parallel subagent matching, `analysis/match_results/`).
Data: `analysis/pairs.json`, `analysis/ce_only.json`, `analysis/all_matches.json`.

## Headline numbers

| quantity | value |
|---|---:|
| CE confirmed hidden-gold bugs (total) | 1,581 |
| … also reported by MRV in the same pair | 1,340 (85%) |
| **CE-only (MRV never reported it)** | **241 (15%)** |
| Goldens CE caught & MRV missed | 27 distinct (49 pair-instances) |
| Goldens MRV caught & CE missed | 36 distinct (83 pair-instances) |

Of the 1,340 matched: MRV's own pipeline called 906 "bug", 216 golden-matches, **98
"important_non_bug" and 18 "true hallucination"** — i.e. ~9% of identical issues flip verdict
depending on which run phrased them (adjudicator wording sensitivity, not just discovery gap).

CE-only findings by model: GLM runs contribute 110/241 (46%) from 26% of pairs — CE's edge
concentrates on GLM; on Claude models MRV actually wins golden recall (e.g. opus-low 0.86 vs
0.67, sonnet-low 0.60 vs 0.19).

CE-only by persona: adversarial 54, reliability 50, correctness 44, maintainability 22,
api-contract 18, performance 16, testing 12, security 10, data-migration 10.
MRV lens coverage of *matched* findings: architecture 374, completeness 269, security 196,
feasibility 185, data-migration 95, scope 85, intent 83, **testing-quality 40** — no lens
owns runtime error paths, frontend promise hygiene, or API-contract-for-existing-consumers.

## The ten clusters (241 CE-only findings)

### 1. Frontend async error propagation (~45 findings; biggest cluster)
Unhandled promise rejections, missing `.catch`, unreturned inner promises, fire-and-forget
refreshes, no error state rendered. Canonical: `destroyRecord()` with no `.catch` (PR #10) —
CE confirmed it in 10 pair-runs, MRV reported it in only 4 of those; CE-only in 6 runs across
6 different models (fable, terra, astra, glm×2, sol). Same shape: `findMembers()` unchained
in `removeMember`/`addMembers` (PR #8), `setupController` discarding the promise,
`utils.viewer.bookings.invalidate()` not caught (PR #14740), `PostCreator.create` returning
nil with errors discarded (PR #4).

### 2. Optimistic-UI races & state desync (~25)
Pagination races: offset mutated before the request resolves, no in-flight guard, out-of-order
responses overwrite (`last response wins`), stale-offset cascade showing page "2/1" after
add/remove, fetching members by the *mutable, unsaved* group `name` instead of id, concurrent
webhook `findFirst`-then-create duplicate credentials, check-then-insert `RecordNotUnique` on
embed_url.

### 3. Silent partial success — APIs that lie (~20)
Server-side counterpart of cluster 1: unknown usernames skipped while `success_json` returns;
unresolvable destination credentials silently skipped with no EventResult and no log (booking
" succeeds" while a host's calendar never gets the event); throttle key committed *before* the
fetch succeeds so retries no-op "successfully"; `content_sha1` advanced even when the revision
failed to persist; blacklisted guest emails silently dropped while the mutation reports
success; `alias_level` silently replaced by model default.

### 4. Cross-layer format/normalization drift (~15)
Two components disagree about the canonical form of the same value: host saved with port
(`example.com:8080`) but lookup compares `URI#host` without the port (3 models); migrated
hosts stored verbatim with `http://` prefix vs bare-host `lower(host) = uri.host` lookup;
mixed-case referer vs lowercased column (also a golden CE catches 3×); protocol-relative
`//cdn...` URLs mangled by `start_with?('/')`; `discourseUrl` trailing-slash concat; JSON
`true` vs string `"true"` for `params[:visible]`; usernames as JSON array → `NoMethodError`.

### 5. Migration operational semantics (~15)
`force: true` added to already-shipped migrations (drops pre-existing tables — 3 models);
`cmd_tuples > 0` is always false for SELECTs → migration deletes all `embeddable_hosts`
settings and creates no rows (**silent data loss**, caught once, glm-flash-high); backfill
bypasses model validation (junk/whitespace rows, unescaped SQL interpolation); `embed_category`
deleted unconditionally though inserts were conditional; `cook_method` default `1` backfills
every existing post as `raw_html`; nil-crash when the setting row was never saved (6 findings,
2 models — the golden twin of this was caught by MRV).

### 6. Outbound-call hardening (~15)
No timeout on `open(url)` / `fetch` (feed polling, import_remote, credential sync); unbounded
download into memory re-parsed twice; unbounded username CSV → N+1 amplification; no rate
limit on `/embed/best` enqueue (per-URL throttle bypassed by varying path); webhook `keys`
field with no `max()` bound written into `Credential.key`.

### 7. Credential/token lifecycle across boundaries (~15)
Sync-mode response shape can *never* satisfy provider schemas (webex `scope` literal, lark
`data.*` envelope) → every refresh fails; connection rebuilt with the pre-refresh token after
persisting the new one (2 models); `response.ok` never checked before parsing; no timeout on
credential sync; `findFirst` on `{userId, appId}` picks an arbitrary credential and never
resets `invalid: false`; replayed/delayed webhook overwrites newer tokens; user-existence
oracle (NOT_FOUND returned before the authorization check → FORBIDDEN after).

### 8. API-contract drift for existing consumers (~12)
`resources :embeddable_hosts` advertises index/show/new/edit with no actions (ActionNotFound
500s; 2 models); create/update no longer accepts the established nested `group` payload;
`destinationCalendar` object/null → array breaking webhook consumers; missing params envelope
→ 500 instead of 400; update ignores fields in partial updates.

### 9. UI state-machine / context bugs (~12)
`isInvalidEmail` never reset on edit or success; dialog state not reset when closed via
X/Esc/backdrop; blank category badge after save (client overwrites server-hydrated category
with `undefined`); `group_member.hbs` resolves `automatic` against the member context instead
of the group (remove button renders for automatic groups → server 422s); error-toast fallback
dead because the template literal is always truthy; topic title never updated on re-import;
transient loading page cached 1 minute.

### 10. Test defects as findings (~10)
Fixture identity not tied to id (`find('fruit', 2)` actually receives `fruits[0]` — verifies
the mock, not the record); copy-paste `require_dependency 'jobs/regular/process_post'` in
`poll_feed_spec`; spec joins usernames with bare `,` so the whitespace path is never exercised;
no migration-crash test; no auth test for unset `CALCOM_WEBHOOK_SECRET`.

### One-off but severe
`Kernel#open` on attacker-controlled URL (disqus import path, `|command` injection);
`CGI.unescapeHTML` double-decode turning escaped HTML into live tags; Readability tag
whitelist not stripping `javascript:` URIs / event handlers; `X-Frame-Options: ALLOWALL`
serving embeds from the forum origin.

## Why MRV misses these (mechanisms)

1. **Lens taxonomy is artifact-review shaped, not runtime shaped.** The 8 lenses ask "is this
   design feasible/complete/in-scope/secure"; nothing asks "what happens at runtime when this
   call fails, arrives twice, or returns in a different shape than expected." Clusters 1–3, 6,
   7 have no owning lens; `testing-quality` (40 matched of 1,340) is the weakest lens.
2. **Conditional, surface-triggered personas.** CE's roster adapts to the diff (reliability,
   api-contract, adversarial spawned when the trigger surface is present), so frontend JS and
   controller error paths get dedicated context. MRV lenses run fixed briefs regardless of
   diff composition.
3. **Consistency, not blindness.** Per root cause, MRV catches the *majority* of instances
   (pagination races 24/30 CE-confirmed instances also in MRV; unbounded payload 54/63) — but
   drops a residue (6/30, 9/63) that compounds across a 6-PR run into the ~10/PR hidden-gold
   gap. The 241 CE-only set includes ~40 root causes MRV caught in *zero* runs (cmd_tuples,
   sync-schema mismatch, destroyRecord at low-effort GLM, etc.) and ~100 it caught sometimes.
4. **Verdict instability.** 98 matched CE-confirmed bugs were adjudicated
   `important_non_bug` in the MRV run and 18 `hallucination` — phrasing sensitivity in the
   v2 adjudicator costs MRV ~7% of its overlap even when it does find the issue.
5. **Model interaction.** The gap is largest exactly where the model is weakest (GLM): CE's
   structure substitutes for model strength; MRV's consolidation seems to *amplify* model
   weakness (fewer, safer findings).

## What metareview should steal

1. **Add a runtime-reliability lens** (error propagation, promise hygiene, partial failure,
   compensation/rollback, timeouts) — targets clusters 1, 3, 6; the single highest-yield add.
2. **Add an api-contract lens** (existing consumers, param envelope/coercion, advertised
   routes, payload shape changes) — cluster 8.
3. **Extend the architecture brief with format-drift invariants** ("saved form ≠ lookup form":
   case, scheme, port, trailing slash, type coercion) — cluster 4; the brief already hunts
   "sentinel-meaning-change" patterns, this is the same family.
4. **Extend the data-migration brief with re-run semantics**: `force: true` on shipped
   migrations, conditional-delete/unconditional-delete pairs, backfills that bypass model
   validation, `cmd_tuples`-class dead checks — cluster 5.
5. **Give a lens explicit frontend parity** (the diff's JS/TS is in context but briefs
   emphasize backend/architecture) — clusters 1, 2, 9.
6. **Adjudication hardening**: same-issue verdict flips (bug ↔ important_non_bug) on ~9% of
   overlap; a tie-break or dual-phrasing pass would recover most of it.

## Caveats

- Matching was one-pass subagent semantic matching (no second judge); spot checks were
  consistent with lexical evidence, but ±5% boundary error is plausible.
- The reverse direction (MRV-confirmed bugs CE missed) was not matched; given MRV's 1,367
  confirmed bugs vs CE's 1,581 and 85% overlap, MRV likely has a several-hundred-finding set
  CE misses too — especially on Claude models, where MRV wins golden recall.
- Golden recall is a wash overall (CE-only 27 vs MRV-only 36 distinct); CE's advantage is in
  hidden gold, and mostly on GLM.
