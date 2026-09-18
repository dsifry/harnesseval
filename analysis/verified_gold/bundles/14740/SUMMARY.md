# Verified hidden gold — PR 14740

Candidates: 33 · verdicts: {'inconclusive_env': 6, 'unresolved_file': 7, 'behavior_change_not_regression': 14, 'base_not_comparable': 4, 'defect_present_before_pr': 2}

| bug id | bug | verdict | head | base | fix | file | tarball sha256 |
|---|---|---|---|---|---|---|---|
| 14740-B05 | B05-addguestsdialog-leaves-stale-isinvalidemail-and-email-inp | `base_not_comparable` | FAIL | FAIL | PASS | `apps/web/components/dialogs/AddGuestsDialog.tsx` | `2716714a86a1…` |
| 14740-B09 | B09-addguestsdialog-error-toast-fallback-is-unreachable-users- | `base_not_comparable` | FAIL | FAIL | PASS | `apps/web/components/dialog/addguestsdialog.tsx` | `7fd7827041de…` |
| 14740-B18 | B18-multiemail-list-items-keyed-by-array-index-cause-stale-shi | `base_not_comparable` | FAIL | FAIL | PASS | `packages/ui/form/multiemail.tsx` | `4ad8ec046b66…` |
| 14740-B30 | B30-multiemail-label-htmlfor-references-missing-input-id-break | `base_not_comparable` | FAIL | FAIL | PASS | `packages/ui/form/multiemail.tsx` | `cbd77eb8e87f…` |
| 14740-B03 | B03-addguests-input-schema-allows-unbounded-guests-array-email | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `apps/web/server/routers/viewer/bookings/addGuests.schema.ts` | `9880fd9f9a0d…` |
| 14740-B06 | B06-authorization-bypass-any-attendee-can-add-arbitrary-guests | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts` | `624dd2c6e669…` |
| 14740-B07 | B07-add-guests-handler-emails-raw-guests-list-instead-of-filte | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `addguests.handler.ts` | `2521a4e94421…` |
| 14740-B08 | B08-addguests-crashes-with-unhandled-prisma-p2025-when-booking | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/trpc/server/routers/viewer/bookings/addGuests.handler.ts` | `90c94928fde5…` |
| 14740-B10 | B10-add-guests-endpoint-can-overbook-seat-limited-events-by-ap | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts` | `eba6d7100fd7…` |
| 14740-B12 | B12-add-guests-email-send-failure-is-swallowed-no-error-contex | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts` | `919c1313abf9…` |
| 14740-B14 | B14-race-condition-in-addguests-allows-duplicate-attendee-rows | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts` | `de63b5b42c65…` |
| 14740-B16 | B16-add-guests-flow-persists-new-guest-attendees-with-empty-na | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts` | `587f62478bea…` |
| 14740-B17 | B17-organizer-add-guests-email-sets-reply-to-to-all-attendee-e | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/emails/templates/organizer-add-guests-email.ts` | `e6ff5e788d16…` |
| 14740-B23 | B23-addguests-mutation-allows-adding-guests-even-when-the-even | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts` | `30363835529b…` |
| 14740-B25 | B25-addguests-loads-booking-by-raw-id-with-heavy-includes-befo | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts` | `51749838e85f…` |
| 14740-B31 | B31-add-guests-on-a-recurring-booking-updates-only-one-occurre | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts` | `409853c3971d…` |
| 14740-B32 | B32-concurrent-add-guests-requests-can-overwrite-calendar-atte | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts` | `4e4a4b447dd7…` |
| 14740-B33 | B33-addguests-throws-badrequest-when-all-submitted-emails-alre | `behavior_change_not_regression` | FAIL | N/A_module_absent | PASS | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts` | `eb6a653480b3…` |
| 14740-B22 | B22-remove-email-tooltip-is-hardcoded-in-english-instead-of-us | `defect_present_before_pr` | FAIL | FAIL | PASS | `packages/ui/form/multiemail.tsx` | `c246ed1ae5ca…` |
| 14740-B26 | B26-add-guests-email-path-bypasses-hidecalendarnotes-redaction | `defect_present_before_pr` | FAIL | FAIL | PASS | `packages/emails/email-manager.ts` | `eaf09e978792…` |
| 14740-B01 | B01-calendar-sync-uses-requesting-users-credentials-instead-of | `inconclusive_env` | FAIL | — | FAIL | `packages/trpc/server/routers/viewer/bookings.ts` | `a9704e826086…` |
| 14740-B11 | B11-team-member-add-guest-notification-branch-is-unreachable-b | `inconclusive_env` | FAIL | — | FAIL | `packages/emails/email-manager.ts` | `cc02447391f1…` |
| 14740-B20 | B20-organizer-add-guests-email-subject-crashes-on-empty-attend | `inconclusive_env` | FAIL | — | FAIL | `packages/emails/templates/organizer-add-guests-email.ts` | `6df1ce4e6282…` |
| 14740-B28 | B28-multiemail-leaf-module-imports-calcom-ui-barrel-creating-a | `inconclusive_env` | FAIL | — | FAIL | `packages/ui/form/multiemail.tsx` | `4449bbd45c44…` |
| 14740-B37 | B37-trpc-input-allows-non-integer-bookingid-causing-prisma-int | `inconclusive_env` | FAIL | — | ? | `packages/trpc/server/routers/viewer/bookings.ts` | `e83b789e9911…` |
| 14740-B40 | B40-missing-i18n-key-causes-add-guests-permission-error-to-dis | `inconclusive_env` | FAIL | — | FAIL | `packages/trpc/server/routers/viewer/bookings/addguests.handler.ts` | `a9b308ba3e9b…` |
| 14740-B02 | B02-non-atomic-guest-attendee-persistence-causes-db-calendar-d | `unresolved_file` | — | — | — | `unknown (reports did not include a file path; PR diff not provided in evidence pack)` | `7d7cf043eeb6…` |
| 14740-B21 | B21-add-guests-mutation-silently-drops-blacklisted-already-att | `unresolved_file` | — | — | — | `unknown (not referenced in the clustered reports and not present in PR #14740 diff; likely the server-side add-guests mutation/handler for bookings/attendees)` | `7e04de7b33c2…` |
| 14740-B34 | B34-guest-email-blacklist-is-undocumented-missing-from-envexam | `unresolved_file` | — | — | — | `apps/web/pages/api/book/[...slug].ts` | `63cadf7958c9…` |
| 14740-B35 | B35-organizer-gets-duplicate-guests-added-email-for-team-booki | `unresolved_file` | — | — | — | `packages/features/emails/sendAddGuestsEmails.ts` | `0b1bfc8cee88…` |
| 14740-B36 | B36-ui-shows-additional-guests---add-members-action-to-users-w | `unresolved_file` | — | — | — | `unknown (not included in PR diff; reports did not provide a path)` | `da1cce56d043…` |
| 14740-B38 | B38-newly-added-booking-attendees-are-not-synced-to-the-existi | `unresolved_file` | — | — | — | `packages/core/EventManager.ts` | `5c99649a0aca…` |
| 14740-B41 | B41-null-eventtypeteamid-is-coerced-to-0-causing-incorrect-tea | `unresolved_file` | — | — | — | `packages/trpc/server/routers/viewer/eventTypes/get.handler.ts` | `48dc2cd2d8b3…` |
