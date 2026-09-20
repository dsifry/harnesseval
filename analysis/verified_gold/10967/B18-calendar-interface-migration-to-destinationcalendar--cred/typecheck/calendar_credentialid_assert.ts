/**
 * Compile-time evidence for candidate 10967-B18:
 *   "Calendar interface migration to destinationCalendar[] + credentialId is not enforced;
 *    unmigrated implementers still type-check"
 *
 * Instrument: tsc (runtime vitest cannot evaluate type assertions).
 * Signal A: this file compiles only if Calendar.createEvent requires a credentialId argument.
 * Signal B: the @ts-expect-error below is satisfied only if a legacy ONE-argument implementation
 *           is rejected by the compiler. If it is NOT rejected, tsc reports TS2578
 *           ("Unused '@ts-expect-error' directive") => the claim is supported.
 */
import type { Calendar, CalendarEvent } from "../packages/types/Calendar";

type Params = Parameters<Calendar["createEvent"]>;
const SIGNAL_A_requires_credential_id: Params extends [CalendarEvent, number] ? true : false = true;

class LegacyCalendarService {
  async createEvent(event: CalendarEvent) {
    return { calendarEvent: event } as any;
  }
}

// SIGNAL B: if the interface requires credentialId, this assignment must be a type error,
// which consumes the directive below.
// @ts-expect-error - a legacy one-argument createEvent must not satisfy Calendar
const legacyIsAssignable: Calendar = new LegacyCalendarService();

export { SIGNAL_A_requires_credential_id, legacyIsAssignable };
