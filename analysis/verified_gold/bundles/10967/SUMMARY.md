# Verified hidden gold — PR 10967

Candidates: 31 · verdicts: {'inconclusive_env': 14, 'static_text_test': 1, 'confirmed_regression': 5, 'defect_present_before_pr': 9, 'not_a_bug': 1, 'unresolved_file': 1}

| bug id | bug | verdict | head | base | fix | file | tarball sha256 |
|---|---|---|---|---|---|---|---|
| 10967-B03 | B03-google-meet-event-creation-can-crash-when-destinationcalen | `confirmed_regression` | FAIL | PASS | PASS | `packages/core/eventmanager.ts` | `069d23fe064c…` |
| 10967-B11 | B11-reschedule-calendar-update-errors-are-swallowed-catch-retu | `confirmed_regression` | FAIL | PASS | PASS | `packages/core/eventmanager.ts` | `33c6a129785a…` |
| 10967-B13 | B13-booking-webhook-payload-breaks-backward-compatibility-by-c | `confirmed_regression` | FAIL | PASS | PASS | `packages/types/calendar.d.ts` | `5f4e9f9fcdfd…` |
| 10967-B14 | B14-recurring-cancellation-delete-sweep-runs-once-per-calendar | `confirmed_regression` | FAIL | PASS | PASS | `apps/web/pages/api/bookings/[id]/cancel/handleCancelBooking.ts` | `a48c57bced38…` |
| 10967-B20 | B20-eventmanagerupdate-swallows-errors-and-returns--when-cale | `confirmed_regression` | FAIL | PASS | PASS | `packages/core/eventmanager.ts` | `f731fae44fc9…` |
| 10967-B05 | B05-unscoped-credential-lookup-by-id-allows-cross-tenant-calen | `defect_present_before_pr` | FAIL | FAIL | PASS | `packages/core/eventmanager.ts` | `c02e09631a3c…` |
| 10967-B09 | B09-missing-credentialid-branch-fans-out-over-all-credentials- | `defect_present_before_pr` | FAIL | FAIL | PASS | `eventmanager.ts` | `64b4de907165…` |
| 10967-B12 | B12-collective-booking-can-report-success-while-silently-skipp | `defect_present_before_pr` | FAIL | FAIL | PASS | `packages/core/eventmanager.ts` | `c48ba54b9ead…` |
| 10967-B19 | B19-missing-external-calendar-id-when-creating-event-without-c | `defect_present_before_pr` | FAIL | FAIL | PASS | `packages/core/eventmanager.ts` | `45d032741b5f…` |
| 10967-B22 | B22-duplicate-calendar-events-when-destination-calendars-conta | `defect_present_before_pr` | FAIL | FAIL | PASS | `packages/core/eventmanager.ts` | `5d5f326fe22f…` |
| 10967-B23 | B23-calendar-createevent-failure-logs-full-calendarevent-objec | `defect_present_before_pr` | FAIL | FAIL | PASS | `packages/core/calendarmanager.ts` | `545c7a6b1ccf…` |
| 10967-B26 | B26-booking-creation-performs-sequential-awaits-and-n1-credent | `defect_present_before_pr` | FAIL | FAIL | PASS | `packages/core/eventmanager.ts` | `c716a68f0914…` |
| 10967-B27 | B27-uncaught-prisma-calendar-lookup-error-aborts-createallcale | `defect_present_before_pr` | FAIL | FAIL | PASS | `packages/core/eventmanager.ts` | `9f281bc427d0…` |
| 10967-B31 | B31-multi-host-google-meet-bookings-create-different-meet-link | `defect_present_before_pr` | FAIL | FAIL | PASS | `packages/app-store/googlecalendar/lib/CalendarService.ts` | `f4516e285ead…` |
| 10967-B01 | B01-collective-bookings-persist-only-destinationcalendar0-dro | `inconclusive_env` | FAIL | — | FAIL | `packages/features/bookings/lib/handlenewbooking.ts` | `8c49abcf0b87…` |
| 10967-B04 | B04-reschedule-merge-deletes-only-the-first-calendar-reference | `inconclusive_env` | FAIL | — | FAIL | `packages/trpc/server/routers/viewer/booking/eventmanager.ts` | `a23aacdab1b5…` |
| 10967-B06 | B06-video-booking-references-persist-with-undefined-credential | `inconclusive_env` | FAIL | — | FAIL | `eventmanager.ts` | `d43d3cfdfac6…` |
| 10967-B10 | B10-loadusers-wraps-validation-errors-as-500-and-leaks-prisma- | `inconclusive_env` | FAIL | — | FAIL | `packages/features/bookings/lib/handlenewbooking.ts` | `375bfd4de776…` |
| 10967-B15 | B15-requestreschedule-handler-drops-userdestinationcalendar-fa | `inconclusive_env` | FAIL | — | FAIL | `packages/trpc/server/routers/viewer/bookings/requestreschedule.handler.ts` | `7081720a9570…` |
| 10967-B17 | B17-public-booking-endpoint-leaks-raw-prisma-error-messages-an | `inconclusive_env` | FAIL | — | FAIL | `packages/features/bookings/lib/handlenewbooking.ts` | `e21bd5dfb0bb…` |
| 10967-B21 | B21-dynamic-group-booking-loadusers-no-longer-selects-organiza | `inconclusive_env` | FAIL | — | FAIL | `packages/features/bookings/lib/handlenewbooking.ts` | `10da79334205…` |
| 10967-B24 | B24-stale-calendar-credential-reused-across-references-in-upda | `inconclusive_env` | FAIL | — | FAIL | `packages/core/eventmanager.ts` | `fdb6da2c6429…` |
| 10967-B28 | B28-crm-othercalendar-references-updated-twice-due-to-overly-b | `inconclusive_env` | FAIL | — | FAIL | `packages/core/eventmanager.ts` | `d3db07b1ec2c…` |
| 10967-B29 | B29-cancel-booking-fallback-loads-credential-without-app-slug- | `inconclusive_env` | FAIL | — | ? | `packages/features/bookings/lib/handlecancelbooking.ts` | `eccde8faaf26…` |
| 10967-B30 | B30-collective-booking-webhook-payload-leaks-all-hosts-destina | `inconclusive_env` | FAIL | — | FAIL | `packages/features/bookings/lib/handlenewbooking.ts` | `bcf8e7726c0c…` |
| 10967-B32 | B32-handlecancelbooking-builds-deletion-promise-array-with-und | `inconclusive_env` | FAIL | — | FAIL | `packages/features/bookings/lib/handlecancelbooking.ts` | `660c527d98cf…` |
| 10967-B33 | B33-fallback-credential-construction-ignores-invalid-flag-and- | `inconclusive_env` | FAIL | — | ? | `packages/core/eventmanager.ts` | `89aea6b9bd04…` |
| 10967-B34 | B34-reschedule-can-persist-in-db-even-when-some-host-calendar- | `inconclusive_env` | FAIL | — | FAIL | `packages/core/eventmanager.ts` | `c641c570ee69…` |
| 10967-B18 | B18-calendar-interface-migration-to-destinationcalendar--cred | `not_a_bug` | PASS | — | — | `packages/types/calendar.d.ts` | `f964316e6e00…` |
| 10967-B02 | B02-collective-hosts-destination-calendars-are-dropped-when-or | `static_text_test` | FAIL | PASS | PASS | `packages/features/bookings/lib/handlenewbooking.ts` | `0e3731fb220d…` |
| 10967-B25 | B25-collective-booking-destination-calendars-skip-first-host-a | `unresolved_file` | — | — | — | `unknown (not in PR diff); search post-PR tree for `teamDestinationCalendars` and `users.slice(1)` in the collective booking calendar-routing code` | `61f86dc00c00…` |
