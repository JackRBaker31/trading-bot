import { ScheduledTask, ScheduleKind } from "@/lib/types";

/** Day names indexed 0 = Monday … 6 = Sunday (matches the backend convention). */
const WEEKDAY_NAMES = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
] as const;

/**
 * Render a human-readable cadence description for a schedule.
 *
 * Examples:
 *   INTERVAL  → "Every 60 minutes" | "Every 2 hours" | "Every 90 minutes"
 *   DAILY     → "Daily at 08:00 America/New_York"
 *   WEEKLY    → "Every Friday at 16:10 America/New_York"
 */
export function formatCadence(schedule: ScheduledTask): string {
  switch (schedule.schedule_kind as ScheduleKind) {
    case "INTERVAL": {
      const secs = schedule.interval_seconds ?? 0;
      if (secs <= 0) return "Interval (unknown)";
      if (secs % 3600 === 0) {
        const hours = secs / 3600;
        return `Every ${hours} ${hours === 1 ? "hour" : "hours"}`;
      }
      const mins = Math.round(secs / 60);
      return `Every ${mins} ${mins === 1 ? "minute" : "minutes"}`;
    }
    case "DAILY": {
      const hh = String(schedule.local_hour ?? 0).padStart(2, "0");
      const mm = String(schedule.local_minute ?? 0).padStart(2, "0");
      return `Daily at ${hh}:${mm} ${schedule.timezone_name}`;
    }
    case "WEEKLY": {
      const dayName = WEEKDAY_NAMES[schedule.weekday ?? 0] ?? "Unknown";
      const hh = String(schedule.local_hour ?? 0).padStart(2, "0");
      const mm = String(schedule.local_minute ?? 0).padStart(2, "0");
      return `Every ${dayName} at ${hh}:${mm} ${schedule.timezone_name}`;
    }
    default:
      return "Unknown cadence";
  }
}

/**
 * Format a remaining-seconds value into a short countdown string.
 *
 * Examples:
 *   3600 → "1h 00m 00s"
 *   1398 → "23m 18s"
 *   45   → "45s"
 *   0    → "Due now"
 *   -5   → "Due now"
 */
export function formatCountdown(secondsRemaining: number): string {
  if (secondsRemaining <= 0) return "Due now";

  const totalSecs = Math.floor(secondsRemaining);
  const hours = Math.floor(totalSecs / 3600);
  const mins = Math.floor((totalSecs % 3600) / 60);
  const secs = totalSecs % 60;

  if (hours > 0) {
    return `${hours}h ${String(mins).padStart(2, "0")}m ${String(secs).padStart(2, "0")}s`;
  }
  if (mins > 0) {
    return `${mins}m ${String(secs).padStart(2, "0")}s`;
  }
  return `${secs}s`;
}
