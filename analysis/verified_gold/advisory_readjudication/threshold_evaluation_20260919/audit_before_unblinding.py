"""Record diff-based audit judgments before revealing classifier confidence/category.
No production artifacts are modified. Original review prose sometimes contains its
own severity/confidence; only the re-adjudicator metadata is hidden.
"""
import json
from pathlib import Path
P = Path(__file__).resolve().parent
# S=supported useful advisory; N=needs context/narrowing; L=unsupported/low value;
# B=credible bug or missing-feature claim requiring bug-truth handling, not bonus.
notes = [
('S', 'New RetrieveTopic job has user lookup and staff/no_throttle branches; no job spec is added. Test-gap support is limited to the submitted diff, not proof that the entire repository lacks coverage.'),
('S', 'New handler, schema and dialog/components add authorization and guest-input behavior without corresponding test additions in the diff.'),
('N', 'Behavioral test gap is supported, but CalendarManager createEvent adds externalId as an argument and returns credentialId; the claim conflates that with a signature adding credentialId. Narrow this compound claim.'),
('L', 'Parser throws on unsuccessful safeParse; the success checks are redundant. No material user/developer consequence is identified beyond small cleanup; insufficient for senior/staff bonus.'),
('L', 'Organizer and attendee checks still apply to non-team bookings. The teamId fallback does not make the entire permission check meaningless.'),
('S', 'Both new controller specs assert only ancestry; no added action-level coverage protects CRUD or category fallback. Does not independently establish the mentioned crashes.'),
('S', 'Ancestry-only controller specs do not exercise actions, validation, fallback or show serialization. Concrete regression-prevention benefit.'),
('N', 'Redis throttle persists until TTL after a failure, but the code deliberately throttles for 60 seconds. Treating this as an unreleased lock requiring immediate retry needs an explicit retry requirement.'),
('S', 'Added/removed group tests leave named membership edge cases and pagination metadata without replacement coverage in the diff.'),
('N', 'Controller gap is real, but the diff explicitly adds model tests for normalization and host lookup. Cannot accept the whole no-coverage claim.'),
('S', 'Only webhook snapshot shape changes; added multi-destination create/update/cancel behavior receives no dedicated test additions in the diff.'),
('L', 'Environment-variable alphabetical ordering is style, with no material runtime/developer benefit established.'),
('N', 'Association deletion followed by save is visible. Calling save a no-op and asserting missing error handling requires Group callbacks and global handling not available in these hunks.'),
('L', 'URI parsing raises before host comparison. Local Ruby 2.6.10 URI("not a url") raises URI::InvalidURIError, contradicting the stated reason the rescue test would pass without rescue. Historical runtime not reproduced.'),
('N', 'The alleged unchanged Acceptable options documentation is outside the displayed post_creator hunk. Neither omission nor senior-level materiality is established by this diff.'),
('N', 'Deleted tests explicitly cover nonexistent users and removing nonmembers; the claim that previously specified duplicate-add coverage was dropped is not established.'),
('L', 'Code deliberately sends new invitees scheduled invitations and existing attendees guest-change notifications. No evidence that the scheduled template is stale or wrong for new guests.'),
('L', 'HTML readability and RSS parsing serve different formats. Shared fetching could be discussed, but guaranteeing drift and implying equivalent sanitation requirements is unsupported architecture preference.'),
('B', 'Salesforce directly fetches its provider while the new wrapper routes through the sync endpoint. This is a credible missing capability/bug candidate if Salesforce sync is required, not automatically a non-bug bonus. Requirement and fixed bug identities must decide.'),
('S', 'New controller tests only check ancestry and therefore cannot detect action failures. Useful missing behavioral-test coverage; repository-wide lack of inherited authorization tests is not proven.'),
('S', 'New URL transformation has no added tests for nondefault ports or preserving already-absolute URLs. Specific invariants and regression-prevention benefit.'),
('N', 'Missing replacement nonmember-deletion test is supported; the additional assertion that group.save is a no-op hiding failures is not established without model/callback context.'),
('S', 'Visible update test checks cooked content but does not pin digest update, row identity or unchanged-content idempotency. Concrete regression invariants.'),
('N', 'Nonempty interpolated string defeats fallback, but err.message is translated and the cited error key is added to translations. The example of exposing that raw key is contradicted by the diff.'),
('S', 'Office365 replaces a failed-parse logging path with the throwing helper and no corresponding invalid-response test is added. Specific changed error-propagation contract.'),
('N', 'Cancellation lookup is inside a missing-credential conditional, not unconditional for every reference. Batch advice may apply to multiple cache misses, but its trigger must be narrowed.'),
('N', 'No local catch is visible, but shared AJAX error behavior is outside the diff. Bare absence does not establish an important user-facing failure.'),
('N', 'No schema index or FK is added, but inevitable orphaning/PostCreator failure requires deletion and model context. Also no workload evidence establishes that a small host table scan is important.'),
('N', 'Task document and commit chronology are not part of the frozen PR diff. Cannot independently verify the claimed absence of prior intent/acceptance from this evidence.'),
('N', 'The menu addition is visible, but upstream booking visibility and menu filtering are not established. Claim about unrelated users receiving this action needs broader context.'),
('N', 'Handler test gap is supported; an unspecified single test is not guaranteed to catch all cited authorization and case-sensitivity defects. Narrow the claim to concrete required cases.'),
('N', 'Spec expects the retriever and controller enqueues a job, but synchronous test-job configuration may make this intentional. Missing direct enqueue assertion alone does not establish material weakness.'),
('S', 'Pagination and metadata serialization change with no added GroupsController tests. Concrete contract-test need; scope of this conclusion is the diff.'),
('N', 'force:true is destructive if the table exists, but this migration creates a new table. Already-provisioned/reapplied migration scenario is not established; cannot assume important data-loss exposure.'),
('N', 'Silent blank-user return and loading retry are visible and support better diagnostics. Claims of no admin-time validation and nothing anywhere in logs require context outside the diff.'),
('N', 'Local catch drops the error details, supporting better logging. Completely undiagnosable across production is stronger than evidence: upstream/provider logging is not inspected.'),
('S', 'Added PollFeed spec exercises execute guard conditions, not the new RSS parsing/import loop. Concrete behavior needs regression tests.'),
('L', 'Migration explicitly deletes the removed settings. Hypothetical skipped/failed migration is not evidence for a separate deleted-setting registry requirement or actionable defect.'),
('N', 'Removed methods/settings establish a compatibility concern for dependent Ruby consumers, but the compound claim also asserts exact external admin-client behavior without inspecting that API. Narrow to verified contract removals and identify supported consumers.'),
('S', 'Ancestry-only controller tests and absent migration authorization edge-case tests leave concrete new contracts unpinned; model normalization tests do not substitute for migration behavior.'),
('L', 'APP_CREDENTIAL_SHARING_ENABLED requires both secret and encryption key, and the handler returns 403 when disabled before decrypting. The missing-key execution scenario is contradicted by the gate; startup-validation preference does not rescue that claim.'),
('L', 'Failure branch is unreachable because the helper throws. This is true redundant code, but no material impact beyond cleanup is established, so no senior/staff bonus.'),
('L', 'Literal callback slug is visible; no evidence it differs from appConfig.slug or breaks behavior. Labeling this a regression and intent violation is unsupported.'),
('L', 'Naming total versus user_count is a consistency preference; no important compatibility or correctness consequence is shown.'),
('L', 'Organiser/organizer copy spelling is not a material advisory; no evidence that a required signoff was omitted.'),
('S', 'Bulk endpoint performs sequential per-username lookups with no visible bound. Large import is an explicit trigger for avoidable database work. Similar old code limits novelty but does not falsify the optimization advisory.'),
('S', 'Schema adds non-null category_id without FK/index. Narrow claim correctly identifies absence of schema-level referential protection; does not prove ordinary application deletion actually orphans rows.')
]
assert len(notes) == 47
claims = json.loads((P/'sample_claims.json').read_text())
rows = [{**r, 'audit_outcome': notes[i][0], 'audit_reason': notes[i][1], 'evidence_diff': r['url'].rsplit('/',1)[-1]+'.diff'} for i,r in enumerate(claims)]
(P/'audit_before_unblinding.json').write_text(json.dumps({'method':'Single-assistant exploratory diff audit; re-adjudicator category/confidence hidden until judgments written. Original review prose not redacted. S/N/L/B definitions in source. No production scoring change.', 'judgments':rows}, indent=2))
