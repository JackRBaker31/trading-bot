import { useState, useEffect } from "react";

// ── NYSE Holiday Computation ──────────────────────────────────────────────────
//
// NYSE observes 10 holidays each year. The rules below cover every case
// indefinitely — no manual updates needed when the static list runs out.
//
// "Observed" rule (NYSE): if a fixed-date holiday falls on Saturday it is
// observed the preceding Friday; if it falls on Sunday it is observed the
// following Monday.

/** Meeus/Jones/Butcher algorithm — returns [month (1-based), day] of Easter. */
function easterDate(year: number): [number, number] {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31); // 1-based
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return [month, day];
}

/** Return day-of-week (0=Sun…6=Sat) for a given year/month/day. */
function dow(year: number, month: number, day: number): number {
  return new Date(year, month - 1, day).getDay();
}

/**
 * Apply the NYSE "nearest weekday" observed rule to a fixed-date holiday.
 * Sat → Fri, Sun → Mon, weekday → unchanged.
 * Returns a YYYY-MM-DD string.
 */
function observed(year: number, month: number, day: number): string {
  const d = dow(year, month, day);
  let oDay = day;
  if (d === 6) oDay -= 1; // Saturday → Friday
  if (d === 0) oDay += 1; // Sunday   → Monday
  const dt = new Date(year, month - 1, oDay);
  return fmt(dt.getFullYear(), dt.getMonth() + 1, dt.getDate());
}

/** Zero-padded YYYY-MM-DD formatter. */
function fmt(y: number, m: number, d: number): string {
  return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

/**
 * Return the date of the Nth occurrence of a given weekday in a month.
 * weekday: 0=Sun…6=Sat, n: 1-based (1=first, -1=last).
 */
function nthWeekday(year: number, month: number, weekday: number, n: number): string {
  if (n > 0) {
    // Count forward from the 1st of the month.
    const first = new Date(year, month - 1, 1);
    const diff = (weekday - first.getDay() + 7) % 7;
    const day = 1 + diff + (n - 1) * 7;
    return fmt(year, month, day);
  } else {
    // Count backward from the last day of the month.
    const last = new Date(year, month, 0); // last day of month
    const diff = (last.getDay() - weekday + 7) % 7;
    const day = last.getDate() - diff;
    return fmt(year, month, day);
  }
}

/**
 * Compute all NYSE market holidays for a given year as YYYY-MM-DD strings.
 *
 * NYSE closes for exactly these 10 holidays:
 *   1.  New Year's Day         (Jan 1, observed)
 *   2.  Martin Luther King Day (3rd Monday, January)
 *   3.  Presidents' Day        (3rd Monday, February)
 *   4.  Good Friday            (Friday before Easter)
 *   5.  Memorial Day           (last Monday, May)
 *   6.  Juneteenth             (Jun 19, observed) — added 2022
 *   7.  Independence Day       (Jul 4, observed)
 *   8.  Labor Day              (1st Monday, September)
 *   9.  Thanksgiving           (4th Thursday, November)
 *  10.  Christmas Day          (Dec 25, observed)
 *
 * Source: https://www.nyse.com/markets/hours-calendars
 */
export function computeNyseHolidays(year: number): Set<string> {
  const holidays: string[] = [];

  // 1. New Year's Day (observed)
  holidays.push(observed(year, 1, 1));

  // 2. Martin Luther King Jr. Day — 3rd Monday in January
  holidays.push(nthWeekday(year, 1, 1, 3));

  // 3. Presidents' Day — 3rd Monday in February
  holidays.push(nthWeekday(year, 2, 1, 3));

  // 4. Good Friday — Friday before Easter
  const [eMonth, eDay] = easterDate(year);
  const easter = new Date(year, eMonth - 1, eDay);
  easter.setDate(easter.getDate() - 2); // two days before Easter = Friday
  holidays.push(fmt(easter.getFullYear(), easter.getMonth() + 1, easter.getDate()));

  // 5. Memorial Day — last Monday in May
  holidays.push(nthWeekday(year, 5, 1, -1));

  // 6. Juneteenth (Jun 19, observed) — NYSE started observing in 2022
  if (year >= 2022) {
    holidays.push(observed(year, 6, 19));
  }

  // 7. Independence Day (Jul 4, observed)
  holidays.push(observed(year, 7, 4));

  // 8. Labor Day — 1st Monday in September
  holidays.push(nthWeekday(year, 9, 1, 1));

  // 9. Thanksgiving — 4th Thursday in November
  holidays.push(nthWeekday(year, 11, 4, 4));

  // 10. Christmas Day (observed)
  holidays.push(observed(year, 12, 25));

  return new Set(holidays);
}

// Cache computed holiday sets by year so we never recompute within a session.
const _holidayCache = new Map<number, Set<string>>();

function getHolidaysForYear(year: number): Set<string> {
  if (!_holidayCache.has(year)) {
    _holidayCache.set(year, computeNyseHolidays(year));
  }
  return _holidayCache.get(year)!;
}

/**
 * Static fallback covering 2025–2027 verified against the official NYSE
 * calendar. Used only if algorithmic computation produces an unexpected gap.
 */
const NYSE_HOLIDAYS_STATIC: Set<string> = new Set([
  // 2025
  "2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18",
  "2025-05-26", "2025-06-19", "2025-07-04", "2025-09-01",
  "2025-11-27", "2025-12-25",
  // 2026
  "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03",
  "2026-05-25", "2026-06-19", "2026-07-03", "2026-09-07",
  "2026-11-26", "2026-12-25",
  // 2027
  "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26",
  "2027-05-31", "2027-06-18", "2027-07-05", "2027-09-06",
  "2027-11-25", "2027-12-24",
  // 2027-12-31: observed New Year's Day 2028 (Jan 1 2028 is Saturday)
  "2027-12-31",
]);

// ── Public API ────────────────────────────────────────────────────────────────

export interface MarketSession {
  isOpen: boolean;
  /** e.g. "NYSE" */
  exchange: string;
  /** When open: "2h 14m until close". When closed: "Opens today 09:30 ET" / "Opens Mon 09:30 ET" */
  label: string;
}

/**
 * Convert a UTC Date to its local "clock face" in America/New_York.
 * Returns a plain Date whose year/month/day/hour/minute/second fields
 * match what a clock on the wall in New York would show.
 */
export function toET(date: Date): Date {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(date);

  const get = (type: string) =>
    parseInt(parts.find((p) => p.type === type)?.value ?? "0", 10);

  return new Date(
    get("year"),
    get("month") - 1,
    get("day"),
    get("hour"),
    get("minute"),
    get("second"),
  );
}

export function etDateString(etDate: Date): string {
  const y = etDate.getFullYear();
  const m = String(etDate.getMonth() + 1).padStart(2, "0");
  const d = String(etDate.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/**
 * Returns true if `etDate` is an NYSE holiday.
 *
 * Checks the algorithmically computed sets for the current year AND the
 * following year. The following year is required because when Jan 1 of
 * year+1 falls on Saturday, NYSE observes it on Dec 31 of the current
 * year — that date is emitted by `computeNyseHolidays(year+1)`, not
 * `computeNyseHolidays(year)`.
 *
 * Falls back to the verified static list for 2025–2027 as a safety net.
 */
export function isHoliday(etDate: Date): boolean {
  const dateStr = etDateString(etDate);
  const year = etDate.getFullYear();

  // Primary: algorithmic (works for any year, zero maintenance).
  // Check current year and the next year to catch cross-year observed dates
  // (e.g. Dec 31 observed New Year's when Jan 1 of year+1 is a Saturday).
  if (getHolidaysForYear(year).has(dateStr)) return true;
  if (getHolidaysForYear(year + 1).has(dateStr)) return true;

  // Fallback: verified static list (2025–2027 + known cross-year dates)
  if (NYSE_HOLIDAYS_STATIC.has(dateStr)) return true;

  return false;
}

const DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

/** Return the next calendar trading day strictly after `etDate` (does not include today). */
function nextTradingDay(etDate: Date): Date {
  const next = new Date(etDate);
  do {
    next.setDate(next.getDate() + 1);
  } while (next.getDay() === 0 || next.getDay() === 6 || isHoliday(next));
  return next;
}

export function computeSession(now: Date): MarketSession {
  const et = toET(now);
  const dayOfWeek = et.getDay(); // 0=Sun … 6=Sat
  const h = et.getHours();
  const m = et.getMinutes();
  const totalMinutes = h * 60 + m;

  const OPEN_MINUTES = 9 * 60 + 30; // 09:30
  const CLOSE_MINUTES = 16 * 60;    // 16:00

  const isWeekday = dayOfWeek >= 1 && dayOfWeek <= 5;
  const isTradingDay = isWeekday && !isHoliday(et);

  // ── OPEN ────────────────────────────────────────────────────────────────────
  if (isTradingDay && totalMinutes >= OPEN_MINUTES && totalMinutes < CLOSE_MINUTES) {
    const minutesLeft = CLOSE_MINUTES - totalMinutes;
    const hLeft = Math.floor(minutesLeft / 60);
    const mLeft = minutesLeft % 60;
    const label =
      hLeft > 0 ? `${hLeft}h ${mLeft}m until close` : `${mLeft}m until close`;
    return { isOpen: true, exchange: "NYSE", label };
  }

  // ── CLOSED ──────────────────────────────────────────────────────────────────
  // Case 1: pre-open on a valid trading day → opens today
  if (isTradingDay && totalMinutes < OPEN_MINUTES) {
    return { isOpen: false, exchange: "NYSE", label: "Opens today 09:30 ET" };
  }

  // Case 2: post-close, weekend, or holiday → find next trading day
  const next = nextTradingDay(et);

  // Is `next` literally tomorrow in ET?
  const tomorrowET = new Date(et);
  tomorrowET.setDate(tomorrowET.getDate() + 1);
  const isNextTomorrow = etDateString(next) === etDateString(tomorrowET);

  const label = isNextTomorrow
    ? "Opens tomorrow 09:30 ET"
    : `Opens ${DAY_NAMES[next.getDay()]} 09:30 ET`;

  return { isOpen: false, exchange: "NYSE", label };
}

export function useMarketSession(): MarketSession {
  const [session, setSession] = useState<MarketSession>(() =>
    computeSession(new Date()),
  );

  useEffect(() => {
    // Refresh every 30 seconds so the countdown stays accurate.
    const id = setInterval(() => {
      setSession(computeSession(new Date()));
    }, 30_000);
    return () => clearInterval(id);
  }, []);

  return session;
}
