# Advisory confidence discriminator evaluation — 19 September 2026

**Recommendation: use advisory confidence ≥0.70 as a provisional primary policy, retain ≥0.80 for unsupported/style penalties, and show ≥0.60 and ≥0.80 advisory sensitivity results. Do not adopt ≥0.50.** If one common discriminator is mandatory, retain ≥0.80 until a larger independent audit supports changing both credit and penalties together. No production policy or frozen runner was changed by this evaluation.

This recommendation reflects a tradeoff: recover concrete regression-prevention and schema-hardening advice excluded at 0.80 while avoiding the much weaker marginal evidence below 0.70. It is not an empirically calibrated optimum. The cost of mistakenly crediting advice versus mistakenly penalizing a reviewer has not been measured; keeping the penalty gate at 0.80 is a conservative policy judgment, not a finding that 0.80 is calibrated.

## Population and scoring limits

All 10,057 independent classifier claims across six PRs have saved judgments. The 101 reused audited bug identities are excluded from this population. The table counts raw classifier votes before semantic deduplication, verified-bug overlap exclusion, or aggregation into selected reviews. These are NOT final credited advisory identities, observed developer benefits, or F2′ scores. T and D remain frozen; classifier bug labels do not create new verified bugs.

| Inclusive cutoff | Raw advisory candidates | Added versus next stricter cutoff | Raw penalty candidates if the same cutoff were used |
|---|---:|---:|---:|
| ≥0.5 | 2,325 | 229 | 1,233 |
| ≥0.6 | 2,096 | 595 | 1,216 |
| ≥0.7 | 1,501 | 822 | 955 |
| ≥0.8 | 679 | Baseline | 494 |

Lowering advisory credit to 0.70 admits 822 additional raw candidates (+121% relative to 679 at 0.80). Lowering further to 0.60 adds 595; to 0.50 adds 229, including 165 at exactly 0.55. A common 0.70 cutoff also raises raw penalty candidates from 494 to 955 (+461); that is a separate policy change, not a free side effect of recognizing more advice.

## Audit design and results

Fixed-seed, hash-ordered sampling selected three raw advisory claims per confidence band per representative framework (vanilla-engineered, compound-realistic, metareview-realistic): nine per band, 36 total. Eleven additional penalty-label claims were sampled, one per populated band/framework stratum; vanilla has no penalty claim in [0.50,0.60). Representative framework means the cached claim’s source review, not all frameworks that emitted the same claim. This samples claims, not semantic identities; related test-gap claims recur.

One assistant reviewed original claim wording against the frozen PR diffs before opening the classifier category/confidence key, and saved judgments before unblinding. Original prose was not redacted: several claims contain the original reviewer’s own confidence or severity. Thus this is metadata-hidden, not fully blinded. No classifier reasoning was used to choose the audit judgments. This is an exploratory audit, not an independent human gold standard or measured population precision.

“Supported” means the main actionable advisory is supported by available evidence without a material unsupported premise. “Needs context or narrowing” is not a hallucination finding: a claim may have a useful core but overstate coverage, causality, or consequences. “Unsupported or low value” combines demonstrably unsupported claims and true but minor cleanup/style. B flags category ambiguity where bug handling must precede advisory credit. Test-gap findings establish absence of relevant added tests in the diff, not an exhaustive absence of repository-wide coverage.

| Classifier advisory band | Supported | Needs context/narrowing | Unsupported/low value | Bug-category question |
|---|---:|---:|---:|---:|
| 0.5–<0.6 | 2/9 | 5 | 2 | 0 |
| 0.6–<0.7 | 2/9 | 5 | 2 | 0 |
| 0.7–<0.8 | 5/9 | 3 | 0 | 1 |
| 0.8–1.0 | 6/9 | 3 | 0 | 0 |

The small equally allocated strata cannot support population precision estimates, confidence calibration, framework rankings, or a statistically established superiority of 0.70 over 0.80. In particular, 5/9 versus 6/9 is not persuasive evidence of a measurable quality difference. It does show concrete useful findings in the 0.70 band, while both lower bands contain substantial unsupported assumptions and minor cleanup. Decisions depend on the strictness of the full-claim rubric: many N claims could become useful if narrowed, but silently rewriting them would evaluate a different review.

Penalty spot-check: 8 of 11 claims were unsupported or low value; 3 required more context. None was clearly supported useful advice under this rubric, but one claim per stratum is far too little to estimate false-penalty rates. A lack of supporting context does not establish that a claim is false. Do not relabel all N cases as hallucinations.

## Concrete evidence

- S47 (0.70): schema-level absence of a category foreign key is a concrete hardening advisory; the claim limits itself to schema-level protection. This is useful below 0.80.
- S25 (0.70): Office365 error handling changes from logging a failed parse to a throwing parser without a corresponding added test. This identifies a specific regression-prevention benefit.
- S21 (0.60): nonstandard-port and already-absolute URL invariants lack added tests. This is a useful finding below 0.70; the proposed cutoff knowingly loses some real advice.
- S14 (0.60): claim says an invalid-URL test would pass without its rescue. URI parsing occurs before host comparison; a local Ruby 2.6.10 check raises URI::InvalidURIError for “not a url.” The claimed mechanism is contradicted, although the historical project runtime was not reproduced.
- S10 (0.70): controller test gaps are real, but the same claim also says normalization/host-lookup tests are absent when the diff explicitly adds them. A score of 0.70 does not guarantee a wholly correct claim.
- S41 (penalty label, 0.60): alleged empty encryption-key execution is contradicted by APP_CREDENTIAL_SHARING_ENABLED requiring both keys and the early 403 gate. The workflow can identify false premises, but this one-pass classifier is not an independent second hallucination audit.

## What changes in the statistics

For α=1, F2′=(5T+A)/(4D+T+A+H). With T, D and H fixed, admitting an additional deduplicated advisory increases F2′ (except an already perfect score). Therefore merely getting a higher F2′ at a lower advisory threshold is not evidence that the lower threshold is more valid. Lowering H’s cutoff at the same time can offset or reverse that change. Which framework benefits depends on per-review advisory/penalty counts after deduplication, not the global raw totals above.

Recompute each advisory policy with the same frozen T/D and H cutoff, exact selected-review coverage, verified-bug exclusion, and policy-specific semantic deduplication. Reuse validated equivalence evidence where valid, but inspect boundaries previously separated by category/threshold; do not just append raw new claims to old A counts. Compare paired scores, rankings and recommendations at advisory cutoffs 0.60/0.70/0.80. Final PR deduplication/export was still in progress during this evaluation (5/6 PRs, 337/403 exported reviews), so no complete F2′ sensitivity or ranking claims are made here.

Processed findings below a scoring threshold remain classified findings with their original category/confidence. They are not “unresolved.” Keep incomplete jobs and scoring-policy exclusions separate.

## Reproduction and audit trail

Run `python3 select_sample.py`, `python3 audit_before_unblinding.py`, and `python3 summarize_audit.py` from this directory (or use their absolute paths). Selection and tables are deterministic; audit judgments are recorded expert-assistant assessments and are not mechanically derived truth. Re-running the judgment-recording script reproduces the saved assessments, not a new blinded audit. Source SHA-256 hashes are verified for every population record by this summarizer. Frozen diff hashes are recorded in audit_summary.json. No production sources are written.

Seed: `threshold-audit-20260919-v1`. Pass digest: `9c5f733ce7a3f996c90c67f262cc4a77e2b234bc415c197afa7c73477ad320be`.

## Full 47-claim audit

### S01 — Supported useful advisory

Classifier: important_non_bug, confidence 0.85; representative framework: metareview-realistic.

> The new RetrieveTopic job has no spec anywhere in this diff (spec/jobs contains only poll_feed_spec.rb), leaving its user_id lookup and no_throttle/staff branching untested. A regression in the user_id→User lookup or the no_throttle: user.try(:staff?) logic (e.g. throttling bypass silently applying to all users or none) ships undetected, and every future change to this job is made with no safety net.

New RetrieveTopic job has user lookup and staff/no_throttle branches; no job spec is added. Test-gap support is limited to the submitted diff, not proof that the entire repository lacks coverage.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/4.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/4-fc3517910f88/156.json).

### S02 — Supported useful advisory

Classifier: important_non_bug, confidence 0.7; representative framework: vanilla-engineered.

> Missing unit test coverage for addGuestsHandler, the tRPC schema, and AddGuestsDialog/MultiEmail components

New handler, schema and dialog/components add authorization and guest-input behavior without corresponding test additions in the diff.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/14740.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/14740-374f52b2ca4d/737.json).

### S03 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.85; representative framework: metareview-realistic.

> apps/web/playwright/webhook.e2e.ts:249 — the only test change in the diff is updating an expected snapshot value from `destinationCalendar: null` to `destinationCalendar: []`; it verifies the output shape of a webhook payload but does not exercise or assert on the new multi-calendar iteration, per-destination credential lookup, or DB credential-fallback logic added in packages/core/EventManager.ts (createAllCalendarEvents, ~lines 337-386) and packages/core/CalendarManager.ts (createEvent signature change adding externalId/credentialId), so the behavioral migration from single destinationCalendar object to array is effectively untested.

Behavioral test gap is supported, but CalendarManager createEvent adds externalId as an argument and returns credentialId; the claim conflates that with a signature adding credentialId. Narrow this compound claim.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/10967.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/10967-79f0acefe9cd/674.json).

### S04 — Unsupported or low value

Classifier: important_non_bug, confidence 0.55; representative framework: vanilla-engineered.

> office365calendar CalendarService.ts:258-260 and salesforce CalendarService.ts:90-92 — parseRefreshTokenResponse throws on failure, so the `tokenResponse.success &&` and `if (!accessTokenParsed.success)` checks are dead code

Parser throws on unsuccessful safeParse; the success checks are redundant. No material user/developer consequence is identified beyond small cleanup; insufficient for senior/staff bonus.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/11059.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/11059-511610aff73a/922.json).

### S05 — Unsupported or low value

Classifier: hallucination, confidence 0.75; representative framework: vanilla-engineered.

> `teamId ?? 0` fallback makes the permission check meaningless for non-team bookings

Organizer and attendee checks still apply to non-team bookings. The teamId fallback does not make the entire permission check meaningless.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/14740.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/14740-374f52b2ca4d/1371.json).

### S06 — Supported useful advisory

Classifier: important_non_bug, confidence 0.8; representative framework: compound-realistic.

> spec/controllers/admin/embeddable_hosts_controller_spec.rb:5 — The new controller specs only assert the subclass relationship, so create/update/destroy, the nil-record crashes, and the category fallback are completely untested (silent pass).

Both new controller specs assert only ancestry; no added action-level coverage protects CRUD or category fallback. Does not independently establish the mentioned crashes.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/10.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/10-429ee35af503/1501.json).

### S07 — Supported useful advisory

Classifier: important_non_bug, confidence 0.85; representative framework: vanilla-engineered.

> Admin embeddable_hosts_controller_spec and embedding_controller_spec only assert the superclass; no coverage for create/update/destroy, uncategorized fallback, missing-id handling, invalid host rejection, or the `show` payload shape (`embeddable_host_ids` sideloading)

Ancestry-only controller specs do not exercise actions, validation, fallback or show serialization. Concrete regression-prevention benefit.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/10.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/10-429ee35af503/362.json).

### S08 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.5; representative framework: vanilla-engineered.

> $redis.setnx lock in topic_retriever.rb is not released or handled if perform_retrieve raises, causing legitimate retries within 60s to be silently dropped after a failed fetch

Redis throttle persists until TTL after a failure, but the code deliberately throttles for 60 seconds. Treating this as an unreleased lock requiring immediate retry needs an explicit retry requirement.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/4.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/4-fc3517910f88/0.json).

### S09 — Supported useful advisory

Classifier: important_non_bug, confidence 0.55; representative framework: vanilla-engineered.

> Missing test coverage for removing a non-member, adding an already-present member, adding non-existent usernames, update changing name/alias_level on a non-automatic group, and the paginated GroupsController#members response meta (total/limit/offset)

Added/removed group tests leave named membership edge cases and pagination metadata without replacement coverage in the diff.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/8.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/8-aa1332bcfff4/949.json).

### S10 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.7; representative framework: compound-realistic.

> spec/controllers/admin/embeddable_hosts_controller_spec.rb:5 — Only assertion for both new admin controllers is `< Admin::AdminController`; no specs cover create/update/destroy, the uncategorized fallback, or the `EmbeddableHost` normalization/`record_for_host` logic.

Controller gap is real, but the diff explicitly adds model tests for normalization and host lookup. Cannot accept the whole no-coverage claim.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/10.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/10-429ee35af503/1489.json).

### S11 — Supported useful advisory

Classifier: important_non_bug, confidence 0.7; representative framework: vanilla-engineered.

> [Medium/test_gap] apps/web/playwright/webhook.e2e.ts — the only test change is updating the expected destinationCalendar shape to []; there is no test coverage for the new collective multi-destination behavior (multiple hosts' calendars created, per-credential matching, update/delete of all references) across create/update/cancel/reschedule paths

Only webhook snapshot shape changes; added multi-destination create/update/cancel behavior receives no dedicated test additions in the diff.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/10967.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/10967-79f0acefe9cd/625.json).

### S12 — Unsupported or low value

Classifier: hallucination, confidence 0.85; representative framework: vanilla-engineered.

> CALCOM_WEBHOOK_SECRET is added out of alphabetical order in turbo.json's env var list, breaking the existing sorting convention

Environment-variable alphabetical ordering is style, with no material runtime/developer benefit established.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/11059.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/11059-511610aff73a/793.json).

### S13 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.6; representative framework: vanilla-engineered.

> remove_member calls group.users.delete(user_id) which executes immediately, making the subsequent group.save a no-op, with no error handling if delete raises

Association deletion followed by save is visible. Calling save a no-op and asserting missing error handling requires Group callbacks and global handling not available in these hunks.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/8.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/8-aa1332bcfff4/1065.json).

### S14 — Unsupported or low value

Classifier: important_non_bug, confidence 0.6; representative framework: metareview-realistic.

> spec/components/topic_retriever_spec.rb:22 — The "not a url" test passes regardless of the InvalidURIError rescue because embeddable_host defaults to '' which already differs from any host, so the rescue branch is not actually proven (P3, conf 50)

URI parsing raises before host comparison. Local Ruby 2.6.10 URI("not a url") raises URI::InvalidURIError, contradicting the stated reason the rescue test would pass without rescue. Historical runtime not reproduced.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/4.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/4-fc3517910f88/1485.json).

### S15 — Needs context or narrowing

Classifier: hallucination, confidence 0.7; representative framework: compound-realistic.

> lib/post_creator.rb:11 — the "Acceptable options" doc block that callers rely on was not updated for the new `cook_method` opt (nor the `skip_validations` opt now used by TopicEmbed)

The alleged unchanged Acceptable options documentation is outside the displayed post_creator hunk. Neither omission nor senior-level materiality is established by this diff.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/4.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/4-fc3517910f88/1141.json).

### S16 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.75; representative framework: compound-realistic.

> spec/controllers/admin/groups_controller_spec.rb:98 — Dropped coverage for the previously-specified edge cases: adding a non-existent user, removing a non-member, and duplicate adds.

Deleted tests explicitly cover nonexistent users and removing nonmembers; the claim that previously specified duplicate-add coverage was dropped is not established.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/8.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/8-aa1332bcfff4/1177.json).

### S17 — Unsupported or low value

Classifier: hallucination, confidence 0.6; representative framework: compound-realistic.

> sendAddGuestsEmails sends AttendeeScheduledEmail to new guests with stale 'scheduled'/'confirmed' content instead of using the new_guests_added / guests_added_event_type_subject keys or the existing AttendeeAddGuestsEmail/OrganizerAddGuestsEmail templates

Code deliberately sends new invitees scheduled invitations and existing attendees guest-change notifications. No evidence that the scheduled template is stale or wrong for new guests.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/14740.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/14740-374f52b2ca4d/1338.json).

### S18 — Unsupported or low value

Classifier: hallucination, confidence 0.7; representative framework: metareview-realistic.

> app/models/topic_embed.rb:44,app/jobs/scheduled/poll_feed.rb:19 — URL fetching/parsing for remote content is implemented twice (raw `open-uri` + `ruby-readability` in `TopicEmbed.import_remote`, and raw `open-uri` + `SimpleRSS` in `PollFeed#poll_feed`) with no shared fetcher abstraction, so the two paths already diverge in encoding/sanitization handling (`CGI.unescapeHTML(i.content.scrub)` only in PollFeed) and any future timeout/retry/error-handling fix has to be applied twice, guaranteeing drift between the RSS path and the on-demand embed path

HTML readability and RSS parsing serve different formats. Shared fetching could be discussed, but guaranteeing drift and implying equivalent sanitation requirements is unsupported architecture preference.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/4.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/4-fc3517910f88/819.json).

### S19 — Bug/missing-feature candidate; not automatic advisory credit

Classifier: important_non_bug, confidence 0.7; representative framework: vanilla-engineered.

> [Low/bug] packages/app-store/salesforce/lib/CalendarService.ts:~75 — the Salesforce token refresh bypasses refreshOAuthTokens entirely, so credential-sync deployments cannot refresh Salesforce tokens through the sync endpoint, inconsistent with every other integration wired in this PR.

Salesforce directly fetches its provider while the new wrapper routes through the sync endpoint. This is a credible missing capability/bug candidate if Salesforce sync is required, not automatically a non-bug bonus. Requirement and fixed bug identities must decide.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/11059.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/11059-511610aff73a/570.json).

### S20 — Supported useful advisory

Classifier: important_non_bug, confidence 0.85; representative framework: compound-realistic.

> spec/controllers/admin/embeddable_hosts_controller_spec.rb:6 — Both new controller specs assert only `X < Admin::AdminController`, so they stay green if every action 500s — create/update/destroy, category assignment, and admin-only enforcement have zero coverage.

New controller tests only check ancestry and therefore cannot detect action failures. Useful missing behavioral-test coverage; repository-wide lack of inherited authorization tests is not proven.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/10.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/10-429ee35af503/1518.json).

### S21 — Supported useful advisory

Classifier: important_non_bug, confidence 0.6; representative framework: compound-realistic.

> app/models/topic_embed.rb:56-77 — absolutize_urls edge cases are untested: non-standard ports and the 'already-absolute URLs stay untouched' invariant are unpinned.

New URL transformation has no added tests for nondefault ports or preserving already-absolute URLs. Specific invariants and regression-prevention benefit.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/4.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/4-fc3517910f88/842.json).

### S22 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.55; representative framework: metareview-realistic.

> remove_member calls group.users.delete(user_id) followed by group.save, but the diff removes the patch-based incremental delete path (update_patch) that the old specs verified ('can make incremental deletes', 'succeeds silently when removing non-members') without any replacement coverage for non-existent user_ids. The new DELETE endpoint has no spec for removing a user who is not a member (or a non-existent user_id), so a regression in GroupUser join-row deletion would ship unnoticed; group.save on an association mutation is also a no-op placeholder that hides whether deletion actually failed.

Missing replacement nonmember-deletion test is supported; the additional assertion that group.save is a no-op hiding failures is not established without model/callback context.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/8.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/8-aa1332bcfff4/189.json).

### S23 — Supported useful advisory

Classifier: important_non_bug, confidence 0.55; representative framework: compound-realistic.

> spec/models/topic_embed_spec.rb:39 — The update test asserts only that cooked changed; it does not assert content_sha1 was updated, that no duplicate topic/TopicEmbed row was created, or that identical content skips the revision

Visible update test checks cooked content but does not pin digest update, row identity or unchanged-content idempotency. Concrete regression invariants.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/4.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/4-fc3517910f88/1654.json).

### S24 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.65; representative framework: vanilla-engineered.

> The `|| t("unable_to_add_guests")` fallback in AddGuestsDialog.tsx:43-44 is dead code because the template string is always non-empty, exposing raw output like `BAD_REQUEST: emails_must_be_unique_valid` to users

Nonempty interpolated string defeats fallback, but err.message is translated and the cited error key is added to translations. The example of exposing that raw key is contradicted by the diff.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/14740.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/14740-374f52b2ca4d/1395.json).

### S25 — Supported useful advisory

Classifier: important_non_bug, confidence 0.7; representative framework: compound-realistic.

> packages/app-store/office365calendar/lib/CalendarService.ts:263 — Behavior changed from logging a failed parse and continuing to throwing, with no test for the invalid-token-response path.

Office365 replaces a failed-parse logging path with the throwing helper and no corresponding invalid-response test is added. Specific changed error-propagation contract.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/11059.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/11059-511610aff73a/1138.json).

### S26 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.5; representative framework: metareview-realistic.

> packages/features/bookings/lib/handleCancelBooking.ts:422-441 — same N+1 pattern on cancellation: `for (const reference of bookingCalendarReference) { ... await prisma.credential.findUnique(...) ...}` performs a sequential DB lookup per calendar reference instead of one batched query (P2, confidence 90).

Cancellation lookup is inside a missing-credential conditional, not unconditional for every reference. Batch advice may apply to multiple cache misses, but its trigger must be narrowed.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/10967.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/10967-79f0acefe9cd/1515.json).

### S27 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.6; representative framework: vanilla-engineered.

> admin-group.js.es6 addMembers action has no .catch/error handling if the addMembers promise rejects

No local catch is visible, but shared AJAX error behavior is outside the diff. Bare absence does not establish an important user-facing failure.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/8.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/8-aa1332bcfff4/317.json).

### S28 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.6; representative framework: metareview-realistic.

> embeddable_hosts.host has no index and no foreign key on category_id, while host is now the lookup key for the per-request ensure_embeddable? path and category_id is dereferenced at topic-import time. Every embed comments/retrieve request issues an unindexed full-table scan on embeddable_hosts, and a deleted category leaves orphan rows whose dead category_id blows up PostCreator on the next import from that host.

No schema index or FK is added, but inevitable orphaning/PostCreator failure requires deletion and model context. Also no workload evidence establishes that a small host table scan is important.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/10.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/10-429ee35af503/28.json).

### S29 — Needs context or narrowing

Classifier: hallucination, confidence 0.9; representative framework: metareview-realistic.

> docs/tasks/task-001.md:1 — Task commit (1081288) was authored 2026-09-13, three weeks after the "pr" commit (aeaf77e, 2026-08-24) that implements the change, so the task description describing "guest management" was written to retroactively document already-completed code rather than specify intent beforehand, meaning there is no original pre-implementation intent record to check the PR against, only a post-hoc label with no recorded human acceptance that the shipped scope satisfies it.

Task document and commit chronology are not part of the frozen PR diff. Cannot independently verify the claimed absence of prior intent/acceptance from this evidence.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/14740.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/14740-374f52b2ca4d/597.json).

### S30 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.65; representative framework: metareview-realistic.

> The 'additional_guests' menu option is added unconditionally to every booking item with no gating on booking state (past/cancelled bookings) or the user's role, even though the handler will reject FORBIDDEN for unrelated users. Users browsing bookings where they are neither organizer, attendee, nor team owner see the Add Guests action, open the dialog, enter emails, and only then receive a FORBIDDEN toast — work the diff ships that is not traceable to the intended audience of the feature.

The menu addition is visible, but upstream booking visibility and menu filtering are not established. Claim about unrelated users receiving this action needs broader context.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/14740.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/14740-374f52b2ca4d/62.json).

### S31 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.85; representative framework: metareview-realistic.

> The new handler contains non-trivial authorization, dedup, persistence, calendar-sync, and email logic, and the diff includes no test for it. The && authorization bug and the case-sensitivity bugs above would all have been caught by a single handler test; any future regression in this permission path ships silently.

Handler test gap is supported; an unspecified single test is not guaranteed to catch all cited authorization and case-sensitivity defects. Narrow the claim to concrete required cases.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/14740.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/14740-374f52b2ca4d/117.json).

### S32 — Needs context or narrowing

Classifier: hallucination, confidence 0.55; representative framework: compound-realistic.

> spec/controllers/embed_controller_spec.rb:41 — Test expects TopicRetriever.new/retrieve directly but controller only calls Jobs.enqueue(:retrieve_topic), so the spec depends on synchronous job execution and never asserts the enqueue itself.

Spec expects the retriever and controller enqueues a job, but synchronous test-job configuration may make this intentional. Missing direct enqueue assertion alone does not establish material weakness.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/4.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/4-fc3517910f88/1546.json).

### S33 — Supported useful advisory

Classifier: important_non_bug, confidence 0.75; representative framework: metareview-realistic.

> The members action gained non-trivial new behavior (limit/offset pagination, total counting, and a brand-new meta envelope serialized via serialize_data instead of render_serialized) with no spec added anywhere in this diff. A regression in the pagination math, the meta payload shape, or the envelope serialization ships unnoticed; the removed 'TODO: more than 200 groups truncates' workaround is also deleted with no test pinning the new behavior that replaces it.

Pagination and metadata serialization change with no added GroupsController tests. Concrete contract-test need; scope of this conclusion is the diff.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/8.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/8-aa1332bcfff4/108.json).

### S34 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.55; representative framework: compound-realistic.

> db/migrate/20150818190757_create_embeddable_hosts.rb:3 — force: true` drops an existing `embeddable_hosts` table during migration, risking irreversible loss of already-provisioned relationship data.

force:true is destructive if the table exists, but this migration creates a new table. Already-provisioned/reapplied migration scenario is not established; cannot assume important data-loss exposure.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/10.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/10-429ee35af503/1162.json).

### S35 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.7; representative framework: metareview-realistic.

> fetch_http returns silently when embed_by_username does not resolve to a user (`return if user.blank?`), and poll_feed:28 does the same, with no log entry, no error, and no admin-time validation that pairs the settings. An admin who sets embeddable_host but not embed_by_username gets a widget that renders 'Loading Discussion...' and reloads every 30 seconds forever while the job chain completes 'successfully' — nothing anywhere indicates which setting is missing, so the misconfiguration is undiagnosable from either the blog or the Discourse logs.

Silent blank-user return and loading retry are visible and support better diagnostics. Claims of no admin-time validation and nothing anywhere in logs require context outside the diff.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/4.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/4-fc3517910f88/65.json).

### S36 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.85; representative framework: vanilla-engineered.

> catch (err) { console.log("Error sending AddGuestsEmails") } in addGuests.handler.ts:163-167 discards the error object (no details, no logger), making email delivery failures completely undiagnosable in production

Local catch drops the error details, supporting better logging. Completely undiagnosable across production is stronger than evidence: upstream/provider logging is not inspected.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/14740.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/14740-374f52b2ca4d/575.json).

### S37 — Supported useful advisory

Classifier: important_non_bug, confidence 0.9; representative framework: compound-realistic.

> app/jobs/scheduled/poll_feed.rb:23 — Jobs::PollFeed#poll_feed`, the actual RSS parsing/import loop, has zero test coverage — the spec only covers the guard-clause conditions in `#execute

Added PollFeed spec exercises execute guard conditions, not the new RSS parsing/import loop. Concrete behavior needs regression tests.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/4.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/4-fc3517910f88/587.json).

### S38 — Unsupported or low value

Classifier: important_non_bug, confidence 0.55; representative framework: compound-realistic.

> P3: Removed site settings not registered as deleted, leaving orphaned settings referencing removed code paths if the migration's delete fails or is skipped

Migration explicitly deletes the removed settings. Hypothetical skipped/failed migration is not evidence for a separate deleted-setting registry requirement or actionable defect.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/10.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/10-429ee35af503/1437.json).

### S39 — Needs context or narrowing

Classifier: important_non_bug, confidence 0.5; representative framework: metareview-realistic.

> app/models/site_setting.rb:71 — API-CONTRACT-BREAKING: `SiteSetting.allows_embeddable_host?`, `SiteSetting.embeddable_hosts`, and `SiteSetting.embed_category` are removed outright with no deprecation shim delegating to `EmbeddableHost`, so any plugin, import script, or admin API client reading/writing these settings raises NoMethodError / 'unknown setting' after upgrade, and a `PUT /admin/site_settings/embeddable_hosts` from an older admin client errors instead of being redirected to the new resource (severity P2, confidence 50, advisory)

Removed methods/settings establish a compatibility concern for dependent Ruby consumers, but the compound claim also asserts exact external admin-client behavior without inspecting that API. Narrow to verified contract removals and identify supported consumers.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/10.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/10-429ee35af503/802.json).

### S40 — Supported useful advisory

Classifier: important_non_bug, confidence 0.8; representative framework: vanilla-engineered.

> [Medium/test_gap] spec/controllers/admin/embeddable_hosts_controller_spec.rb and spec/controllers/admin/embedding_controller_spec.rb — the only specs assert class ancestry; there is no coverage of create/update/destroy behavior (unknown id, invalid host → error JSON, category defaulting to uncategorized), no test that migration-imported protocol/path-bearing hosts still authorize, and no mixed-case host test.

Ancestry-only controller tests and absent migration authorization edge-case tests leave concrete new contracts unpinned; model normalization tests do not substitute for migration behavior.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/10.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/10-429ee35af503/350.json).

### S41 — Unsupported or low value

Classifier: hallucination, confidence 0.6; representative framework: vanilla-engineered.

> app-credential.ts:64-67: symmetricDecrypt falls back to an empty key if CALCOM_APP_CREDENTIAL_ENCRYPTION_KEY is unset, which will throw or behave unpredictably instead of failing fast; CALCOM_WEBHOOK_SECRET and header-name fallbacks also lack startup validation

APP_CREDENTIAL_SHARING_ENABLED requires both secret and encryption key, and the handler returns 403 when disabled before decrypting. The missing-key execution scenario is contradicted by the gate; startup-validation preference does not rescue that claim.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/11059.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/11059-511610aff73a/608.json).

### S42 — Unsupported or low value

Classifier: important_non_bug, confidence 0.6; representative framework: compound-realistic.

> packages/app-store/salesforce/lib/CalendarService.ts:92 — The `!accessTokenParsed.success` branch is unreachable because parseRefreshTokenResponse throws on failure, so the advertised SafeParse return contract is handled inconsistently across call sites.

Failure branch is unreachable because the helper throws. This is true redundant code, but no material impact beyond cleanup is established, so no senior/staff bonus.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/11059.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/11059-511610aff73a/1311.json).

### S43 — Unsupported or low value

Classifier: hallucination, confidence 0.6; representative framework: metareview-realistic.

> packages/app-store/zoho-bigin/api/add.ts:17 — `const redirectUri = WEBAPP_URL + \`/api/integrations/zoho-bigin/callback\`;` replaces the dynamic `appConfig.slug` interpolation with a hardcoded literal, an unrelated regression bundled into an "OAuth credential sync" task with no stated requirement to change zoho-bigin's redirect-URI construction.

Literal callback slug is visible; no evidence it differs from appConfig.slug or breaks behavior. Labeling this a regression and intent violation is unsupported.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/11059.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/11059-511610aff73a/1770.json).

### S44 — Unsupported or low value

Classifier: hallucination, confidence 0.8; representative framework: compound-realistic.

> app/controllers/groups_controller.rb:31 — New `meta.total` names the member count differently from `user_count` used by the group serializer and JS model, forcing clients to remap the same concept.

Naming total versus user_count is a consistency preference; no important compatibility or correctness consequence is shown.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/8.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/8-aa1332bcfff4/830.json).

### S45 — Unsupported or low value

Classifier: hallucination, confidence 0.55; representative framework: metareview-realistic.

> An unrelated copy change (organiser → organizer in the hideCalendarNotes string) was slipped into the same commit as the destinationCalendar array refactor. User-visible email text changes are bundled invisibly with a schema-shape refactor; reviewers accepting 'collective destination calendar support' also silently accepted a copy change nobody signed off on — textbook intent drift inside an iteration.

Organiser/organizer copy spelling is not a material advisory; no evidence that a required signoff was omitted.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/10967.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/10967-79f0acefe9cd/2.json).

### S46 — Supported useful advisory

Classifier: important_non_bug, confidence 0.6; representative framework: compound-realistic.

> app/controllers/admin/groups_controller.rb:71 — Bulk additions perform one user lookup per supplied username with no batch-size bound, producing an avoidable N+1 query storm for large imports.

Bulk endpoint performs sequential per-username lookups with no visible bound. Large import is an explicit trigger for avoidable database work. Similar old code limits novelty but does not falsify the optimization advisory.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/8.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/8-aa1332bcfff4/650.json).

### S47 — Supported useful advisory

Classifier: important_non_bug, confidence 0.7; representative framework: metareview-realistic.

> db/migrate/20150818190757_create_embeddable_hosts.rb:5 — `category_id` is `null: false` with a `belongs_to :category` association but no DB foreign key constraint and no index, so category deletion can silently orphan embeddable_hosts rows (dangling category_id) with no referential-integrity guard at the schema level .

Schema adds non-null category_id without FK/index. Narrow claim correctly identifies absence of schema-level referential protection; does not prove ordinary application deletion actually orphans rows.

Evidence: [frozen PR diff](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/threshold_evaluation_20260919/10.diff); [saved verdict](/Users/dsifry/Developer/harnesseval/analysis/verified_gold/advisory_readjudication/passes/glm_base_claim_v3/verdicts/10-429ee35af503/1199.json).
