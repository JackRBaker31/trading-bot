import { describe, it, expect } from "vitest";
import { formatCadence, formatCountdown } from "@/lib/schedule-utils";
import type { ScheduledTask } from "@/lib/types";

// ─── Test fixtures ────────────────────────────────────────────────────────────

function makeSchedule(overrides: Partial<ScheduledTask>): ScheduledTask {
  return {
    schedule_id: "test-schedule",
    task_type: "INTELLIGENCE_CYCLE",
    enabled: true,
    schedule_kind: "INTERVAL",
    timezone_name: "UTC",
    interval_seconds: 3600,
    local_hour: null,
    local_minute: null,
    weekday: null,
    next_run_at: null,
    last_run_at: null,
    last_job_id: null,
    last_status: null,
    payload: {},
    catch_up_policy: "SKIP",
    catch_up_window_seconds: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

// ─── formatCadence ────────────────────────────────────────────────────────────

describe("formatCadence", () => {
  describe("INTERVAL", () => {
    it("formats exact minutes", () => {
      expect(formatCadence(makeSchedule({ schedule_kind: "INTERVAL", interval_seconds: 3600 }))).toBe(
        "Every 1 hour",
      );
    });

    it("formats plural hours", () => {
      expect(formatCadence(makeSchedule({ schedule_kind: "INTERVAL", interval_seconds: 7200 }))).toBe(
        "Every 2 hours",
      );
    });

    it("formats 60 minutes", () => {
      expect(formatCadence(makeSchedule({ schedule_kind: "INTERVAL", interval_seconds: 3600 }))).toBe(
        "Every 1 hour",
      );
    });

    it("formats 90 minutes (not a whole hour)", () => {
      expect(formatCadence(makeSchedule({ schedule_kind: "INTERVAL", interval_seconds: 5400 }))).toBe(
        "Every 90 minutes",
      );
    });

    it("formats 1 minute", () => {
      expect(formatCadence(makeSchedule({ schedule_kind: "INTERVAL", interval_seconds: 60 }))).toBe(
        "Every 1 minute",
      );
    });

    it("formats plural minutes", () => {
      expect(formatCadence(makeSchedule({ schedule_kind: "INTERVAL", interval_seconds: 300 }))).toBe(
        "Every 5 minutes",
      );
    });

    it("handles null interval_seconds gracefully", () => {
      expect(formatCadence(makeSchedule({ schedule_kind: "INTERVAL", interval_seconds: null }))).toBe(
        "Interval (unknown)",
      );
    });
  });

  describe("DAILY", () => {
    it("formats daily at midnight UTC", () => {
      expect(
        formatCadence(
          makeSchedule({
            schedule_kind: "DAILY",
            local_hour: 0,
            local_minute: 0,
            timezone_name: "UTC",
          }),
        ),
      ).toBe("Daily at 00:00 UTC");
    });

    it("formats daily with leading zero padding", () => {
      expect(
        formatCadence(
          makeSchedule({
            schedule_kind: "DAILY",
            local_hour: 8,
            local_minute: 5,
            timezone_name: "America/New_York",
          }),
        ),
      ).toBe("Daily at 08:05 America/New_York");
    });

    it("formats daily at 16:10 London", () => {
      expect(
        formatCadence(
          makeSchedule({
            schedule_kind: "DAILY",
            local_hour: 16,
            local_minute: 10,
            timezone_name: "Europe/London",
          }),
        ),
      ).toBe("Daily at 16:10 Europe/London");
    });
  });

  describe("WEEKLY", () => {
    it("formats weekly on Monday", () => {
      expect(
        formatCadence(
          makeSchedule({
            schedule_kind: "WEEKLY",
            weekday: 0,
            local_hour: 9,
            local_minute: 0,
            timezone_name: "UTC",
          }),
        ),
      ).toBe("Every Monday at 09:00 UTC");
    });

    it("formats weekly on Friday afternoon New York", () => {
      expect(
        formatCadence(
          makeSchedule({
            schedule_kind: "WEEKLY",
            weekday: 4,
            local_hour: 16,
            local_minute: 10,
            timezone_name: "America/New_York",
          }),
        ),
      ).toBe("Every Friday at 16:10 America/New_York");
    });

    it("formats weekly on Sunday", () => {
      expect(
        formatCadence(
          makeSchedule({
            schedule_kind: "WEEKLY",
            weekday: 6,
            local_hour: 23,
            local_minute: 59,
            timezone_name: "Europe/London",
          }),
        ),
      ).toBe("Every Sunday at 23:59 Europe/London");
    });
  });
});

// ─── formatCountdown ──────────────────────────────────────────────────────────

describe("formatCountdown", () => {
  it('returns "Due now" for zero', () => {
    expect(formatCountdown(0)).toBe("Due now");
  });

  it('returns "Due now" for negative values', () => {
    expect(formatCountdown(-1)).toBe("Due now");
    expect(formatCountdown(-999)).toBe("Due now");
  });

  it("formats seconds only", () => {
    expect(formatCountdown(45)).toBe("45s");
    expect(formatCountdown(1)).toBe("1s");
    expect(formatCountdown(59)).toBe("59s");
  });

  it("formats minutes and seconds", () => {
    expect(formatCountdown(1398)).toBe("23m 18s");
    expect(formatCountdown(60)).toBe("1m 00s");
    expect(formatCountdown(3599)).toBe("59m 59s");
  });

  it("formats hours, minutes and seconds", () => {
    expect(formatCountdown(3600)).toBe("1h 00m 00s");
    expect(formatCountdown(3661)).toBe("1h 01m 01s");
    expect(formatCountdown(7200)).toBe("2h 00m 00s");
    expect(formatCountdown(86399)).toBe("23h 59m 59s");
  });

  it("floors fractional seconds", () => {
    expect(formatCountdown(1.9)).toBe("1s");
    expect(formatCountdown(61.7)).toBe("1m 01s");
  });
});
