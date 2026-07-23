import { describe, it, expect } from "vitest";
import { computeSession, toET, etDateString, isHoliday } from "./useMarketSession";

/**
 * Build a UTC Date that corresponds to a given Eastern Time clock reading.
 * Uses the Intl API indirectly: we construct via the known NYC UTC offset.
 * To keep tests deterministic we pass a fixed ISO string and rely on
 * `toET` (already tested separately) to convert back when needed.
 *
 * Simpler approach: just build a UTC timestamp string that represents the
 * desired ET time, assuming the correct DST offset.
 *
 * For 2026 dates:
 *   EDT (summer, UTC-4): Mar 8 – Nov 1
 *   EST (winter, UTC-5): Nov 1 – Mar 8
 */
function etToUtc(
  year: number,
  month: number, // 1-based
  day: number,
  hour: number,
  minute: number,
): Date {
  // Determine offset: EDT (-4) vs EST (-5)
  // DST in 2026: starts 2nd Sunday March = Mar 8; ends 1st Sunday Nov = Nov 1
  const isDST =
    (month > 3 && month < 11) ||
    (month === 3 && day >= 8) ||
    (month === 11 && day < 1);
  const offsetHours = isDST ? 4 : 5;
  const utcHour = hour + offsetHours;
  const isoStr = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}T${String(utcHour).padStart(2, "0")}:${String(minute).padStart(2, "0")}:00.000Z`;
  return new Date(isoStr);
}

describe("computeSession — NYSE market hours", () => {
  // ── OPEN ─────────────────────────────────────────────────────────────────

  it("is OPEN during regular session hours (Mon–Fri 09:30–16:00 ET)", () => {
    // Tuesday 2026-07-07 at 11:00 ET (EDT, weekday, non-holiday)
    const now = etToUtc(2026, 7, 7, 11, 0);
    const session = computeSession(now);
    expect(session.isOpen).toBe(true);
    expect(session.exchange).toBe("NYSE");
    expect(session.label).toContain("until close");
  });

  it("shows correct countdown when less than 1 hour remains", () => {
    // 15:45 ET → 15 minutes until close
    const now = etToUtc(2026, 7, 7, 15, 45);
    const session = computeSession(now);
    expect(session.isOpen).toBe(true);
    expect(session.label).toBe("15m until close");
  });

  it("shows hours + minutes in countdown", () => {
    // 09:30 ET → 6h 30m until close
    const now = etToUtc(2026, 7, 7, 9, 30);
    const session = computeSession(now);
    expect(session.isOpen).toBe(true);
    expect(session.label).toBe("6h 30m until close");
  });

  // ── CLOSED: pre-open ──────────────────────────────────────────────────────

  it("is CLOSED before 09:30 on a valid trading day and says 'Opens today'", () => {
    // Tuesday 2026-07-07 at 08:00 ET
    const now = etToUtc(2026, 7, 7, 8, 0);
    const session = computeSession(now);
    expect(session.isOpen).toBe(false);
    expect(session.label).toBe("Opens today 09:30 ET");
  });

  it("is CLOSED at exactly 09:29 and says 'Opens today'", () => {
    const now = etToUtc(2026, 7, 7, 9, 29);
    const session = computeSession(now);
    expect(session.isOpen).toBe(false);
    expect(session.label).toBe("Opens today 09:30 ET");
  });

  // ── CLOSED: post-close ────────────────────────────────────────────────────

  it("is CLOSED after 16:00 on a weekday and shows 'Opens tomorrow'", () => {
    // Tuesday 2026-07-07 at 17:00 ET → tomorrow = Wed
    const now = etToUtc(2026, 7, 7, 17, 0);
    const session = computeSession(now);
    expect(session.isOpen).toBe(false);
    expect(session.label).toBe("Opens tomorrow 09:30 ET");
  });

  it("is CLOSED at exactly 16:00 (boundary — exclusive)", () => {
    const now = etToUtc(2026, 7, 7, 16, 0);
    const session = computeSession(now);
    expect(session.isOpen).toBe(false);
  });

  // ── CLOSED: weekend ───────────────────────────────────────────────────────

  it("is CLOSED on Saturday and shows next Monday", () => {
    // 2026-07-11 (Saturday) at 12:00 ET
    const now = etToUtc(2026, 7, 11, 12, 0);
    const session = computeSession(now);
    expect(session.isOpen).toBe(false);
    expect(session.label).toBe("Opens Mon 09:30 ET");
  });

  it("is CLOSED on Sunday and shows 'Opens tomorrow' (Mon is next day)", () => {
    // 2026-07-12 (Sunday) at 12:00 ET — Monday July 13 is tomorrow
    const now = etToUtc(2026, 7, 12, 12, 0);
    const session = computeSession(now);
    expect(session.isOpen).toBe(false);
    expect(session.label).toBe("Opens tomorrow 09:30 ET");
  });

  it("is CLOSED on Saturday and shows 'Opens Mon' (Mon is two days away)", () => {
    // 2026-07-11 (Saturday) at 12:00 ET — Monday July 13 is two days away, not tomorrow
    const now = etToUtc(2026, 7, 11, 12, 0);
    const session = computeSession(now);
    expect(session.isOpen).toBe(false);
    expect(session.label).toBe("Opens Mon 09:30 ET");
  });

  it("is CLOSED on Friday after close and shows next Monday", () => {
    // 2026-07-10 (Friday) at 17:00 ET → next trading day = Mon 2026-07-13
    const now = etToUtc(2026, 7, 10, 17, 0);
    const session = computeSession(now);
    expect(session.isOpen).toBe(false);
    expect(session.label).toMatch(/Mon/);
  });

  // ── CLOSED: holiday ───────────────────────────────────────────────────────

  it("is CLOSED on Independence Day 2026 (July 3, observed) even during session hours", () => {
    // 2026-07-03 at 11:00 ET — holiday (Independence Day observed)
    const now = etToUtc(2026, 7, 3, 11, 0);
    const session = computeSession(now);
    expect(session.isOpen).toBe(false);
  });

  it("is CLOSED on Christmas 2026 and shows next trading day", () => {
    // 2026-12-25 (Friday) at 10:00 ET — next trading day = Mon 2026-12-28
    const now = etToUtc(2026, 12, 25, 10, 0);
    const session = computeSession(now);
    expect(session.isOpen).toBe(false);
    expect(session.label).toMatch(/Mon/);
  });
});

describe("helpers", () => {
  it("toET converts UTC to ET correctly (EDT, UTC-4)", () => {
    // 2026-07-07 14:00 UTC → 10:00 EDT
    const utc = new Date("2026-07-07T14:00:00.000Z");
    const et = toET(utc);
    expect(et.getHours()).toBe(10);
    expect(et.getMinutes()).toBe(0);
  });

  it("etDateString formats a date as YYYY-MM-DD", () => {
    const d = new Date(2026, 6, 7); // July 7 (local)
    expect(etDateString(d)).toBe("2026-07-07");
  });

  it("isHoliday returns true for NYSE holidays", () => {
    const holiday = new Date(2026, 11, 25); // Dec 25, 2026 (local)
    expect(isHoliday(holiday)).toBe(true);
  });

  it("isHoliday returns false for non-holidays", () => {
    const notHoliday = new Date(2026, 6, 7); // Jul 7, 2026
    expect(isHoliday(notHoliday)).toBe(false);
  });
});
