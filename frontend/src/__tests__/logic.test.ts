/**
 * Tests for pure helper logic used throughout the dashboard:
 *
 * - infraDotClass: online → emerald, offline → destructive
 * - infraStatusTextClass: colour for IDLE / BUSY / STALE / FAILED
 * - renderTopOpportunity: handles string or object shapes without throwing
 * - renderReason: handles string, plain object, null — never returns a raw object
 * - graduation percentage: correct ratio calculation
 * - RESEARCH ONLY stage detection
 */
import { describe, it, expect } from "vitest";

// ── Helpers mirroring DashboardPage logic ─────────────────────────────────────
// (Functions are defined inline in DashboardPage; we replicate them here to
//  test the identical logic in isolation without rendering the full page.)

function infraDotClass(online: boolean): string {
  return online ? "bg-emerald-500" : "bg-destructive";
}

function infraStatusTextClass(status: string, online: boolean): string {
  if (!online) return "text-destructive";
  const s = status.toUpperCase();
  if (["IDLE", "ONLINE", "HEALTHY", "CURRENT", "CONFIGURED"].includes(s))
    return "text-emerald-400";
  if (s === "BUSY") return "text-blue-400";
  if (["STALE", "DEGRADED", "WARNING"].includes(s)) return "text-amber-400";
  if (["STOPPED", "NOT_SEEN", "OFFLINE", "FAILED"].includes(s))
    return "text-destructive";
  return "text-emerald-400";
}

interface TopOpportunityObject {
  symbol?: string;
  ticker?: string;
  headline?: string;
}

type TopOpportunity = string | TopOpportunityObject | null | undefined;

function renderTopOpportunity(val: TopOpportunity): string {
  if (!val) return "";
  if (typeof val === "string") return val;
  const obj = val as TopOpportunityObject;
  return obj.symbol ?? obj.ticker ?? obj.headline ?? "—";
}

function renderReason(item: unknown): string {
  if (!item) return "";
  if (typeof item === "string") return item;
  if (typeof item === "object") {
    const o = item as Record<string, unknown>;
    return (
      (typeof o.reason === "string" ? o.reason : null) ??
      (typeof o.message === "string" ? o.message : null) ??
      (typeof o.text === "string" ? o.text : null) ??
      (typeof o.headline === "string" ? o.headline : null) ??
      JSON.stringify(item)
    );
  }
  return String(item);
}

function calcGradPct(passed: number, remaining: number): number {
  const total = passed + remaining;
  return total > 0 ? Math.round((passed / total) * 100) : 0;
}

// ── infraDotClass ─────────────────────────────────────────────────────────────

describe("infraDotClass", () => {
  it("returns emerald class for online services", () => {
    expect(infraDotClass(true)).toBe("bg-emerald-500");
  });

  it("returns destructive class for offline services", () => {
    expect(infraDotClass(false)).toBe("bg-destructive");
  });
});

// ── infraStatusTextClass ──────────────────────────────────────────────────────

describe("infraStatusTextClass", () => {
  it("returns emerald text for IDLE (online)", () => {
    expect(infraStatusTextClass("IDLE", true)).toBe("text-emerald-400");
  });

  it("returns blue text for BUSY (online)", () => {
    expect(infraStatusTextClass("BUSY", true)).toBe("text-blue-400");
  });

  it("returns amber text for STALE (online)", () => {
    expect(infraStatusTextClass("STALE", true)).toBe("text-amber-400");
  });

  it("returns destructive text for FAILED (online)", () => {
    expect(infraStatusTextClass("FAILED", true)).toBe("text-destructive");
  });

  it("returns destructive text when offline regardless of status", () => {
    expect(infraStatusTextClass("IDLE", false)).toBe("text-destructive");
  });

  it("returns emerald text for ONLINE (online)", () => {
    expect(infraStatusTextClass("ONLINE", true)).toBe("text-emerald-400");
  });
});

// ── renderTopOpportunity ──────────────────────────────────────────────────────

describe("renderTopOpportunity", () => {
  it("passes a plain string ticker through unchanged", () => {
    expect(renderTopOpportunity("AAPL")).toBe("AAPL");
  });

  it("extracts symbol from an object shape", () => {
    expect(renderTopOpportunity({ symbol: "MSFT", headline: "Some news" })).toBe(
      "MSFT",
    );
  });

  it("falls back to ticker when symbol is absent", () => {
    expect(renderTopOpportunity({ ticker: "TSLA" })).toBe("TSLA");
  });

  it("falls back to headline when symbol and ticker are absent", () => {
    expect(renderTopOpportunity({ headline: "Bullish signal" })).toBe(
      "Bullish signal",
    );
  });

  it("returns '—' for an empty object", () => {
    expect(renderTopOpportunity({})).toBe("—");
  });

  it("returns empty string for null", () => {
    expect(renderTopOpportunity(null)).toBe("");
  });

  it("does NOT return a raw object (would cause React child error)", () => {
    const result = renderTopOpportunity({ symbol: "NVDA" });
    expect(typeof result).toBe("string");
  });
});

// ── renderReason ──────────────────────────────────────────────────────────────

describe("renderReason", () => {
  it("returns a plain string reason as-is", () => {
    expect(renderReason("Insufficient volume")).toBe("Insufficient volume");
  });

  it("extracts .reason field from an object", () => {
    expect(renderReason({ reason: "Below threshold", score: 0.3 })).toBe(
      "Below threshold",
    );
  });

  it("falls back to .message when .reason is absent", () => {
    expect(renderReason({ message: "No signal found" })).toBe("No signal found");
  });

  it("falls back to .text when .reason and .message are absent", () => {
    expect(renderReason({ text: "Watchlist excluded" })).toBe("Watchlist excluded");
  });

  it("falls back to .headline when other fields are absent", () => {
    expect(renderReason({ headline: "Breaking news" })).toBe("Breaking news");
  });

  it("JSON-stringifies an unrecognised object shape instead of returning the object", () => {
    const result = renderReason({ unknown_field: 42 });
    expect(typeof result).toBe("string");
    // Must NOT return a plain object (which would cause a React child error)
    expect(result).not.toStrictEqual({ unknown_field: 42 });
  });

  it("returns empty string for null", () => {
    expect(renderReason(null)).toBe("");
  });

  it("returns empty string for undefined", () => {
    expect(renderReason(undefined)).toBe("");
  });
});

// ── Graduation progress bar ───────────────────────────────────────────────────

describe("graduation progress bar ratio", () => {
  it("reflects the correct checked/total ratio (3 of 4 = 75 %)", () => {
    expect(calcGradPct(3, 1)).toBe(75);
  });

  it("returns 0 when no checks are passed", () => {
    expect(calcGradPct(0, 4)).toBe(0);
  });

  it("returns 100 when all checks pass", () => {
    expect(calcGradPct(4, 0)).toBe(100);
  });

  it("returns 0 when both values are zero (avoids divide-by-zero)", () => {
    expect(calcGradPct(0, 0)).toBe(0);
  });
});

// ── RESEARCH ONLY stage detection ─────────────────────────────────────────────

describe("RESEARCH ONLY label visibility", () => {
  it("is visible when graduation stage includes 'RESEARCH'", () => {
    const stage = "RESEARCH_ONLY";
    expect(stage.toUpperCase().includes("RESEARCH")).toBe(true);
  });

  it("is NOT visible when stage is ELIGIBLE_FOR_PAPER_FILTER_REVIEW", () => {
    const stage = "ELIGIBLE_FOR_PAPER_FILTER_REVIEW";
    expect(stage.toUpperCase().includes("RESEARCH")).toBe(false);
  });

  it("is NOT visible when stage is null / undefined", () => {
    const stage: string | undefined = undefined;
    expect((stage ?? "").toUpperCase().includes("RESEARCH")).toBe(false);
  });
});
