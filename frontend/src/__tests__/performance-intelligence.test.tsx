import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import PerformanceIntelligencePage from "@/pages/PerformanceIntelligencePage";

vi.mock("@/hooks/usePerformanceReview", () => ({
  usePerformanceReview: () => ({
    isLoading: false, isFetching: false, error: null, refetch: vi.fn(),
    data: {
      generated_at: "2026-07-27T09:00:00Z", period: { start: "2026-07-26T00:00:00Z", end: "2026-07-27T09:00:00Z", hours: 33 },
      executive_summary: "KAIRO completed its review.",
      system_health: { total_jobs: 10, intelligence_cycles: 8, succeeded: 7, succeeded_with_warnings: 1, failed: 0, queued: 0, abandoned_running: 0, completion_rate_percent: 100, healthy_completion_percent: 100, average_cycle_duration_seconds: 14.5, longest_cycle_duration_seconds: 18, warning_stages: {} },
      research_activity: { research_runs: 8, created_count: 12, skipped_count: 300, failure_count: 0, skip_rate_percent: 96.2, articles_fetched: 12, signals_stored: 9, provider_cycles: { TWELVE_DATA: 8 } },
      decision_intelligence: { shadow_decisions: 4, eligible_decisions: 0, eligibility_rate_percent: 0, average_confidence_percent: 87, actions: { BLOCKED: 4 }, top_symbols: [{ symbol: "AAPL", count: 2 }], memory_decisions: 4, recommendations: {}, opportunities_seen: 4, decisions_skipped: 0 },
      shadow_performance: { total_decisions: 4, measured_1d_decisions: 2, directional_success_percent: 50, profitable_after_cost_percent: 50, recorded_outcomes: 2, outcomes_recorded_by_cycles: 2, snapshots_captured: 0, price_operation_failures: 0, average_recorded_return_percent: 0.5, opportunities_seen: 4, decisions_skipped: 0 },
      confidence_calibration: { snapshot_count: 8, average_snapshot_confidence_percent: 88, latest_snapshot_confidence_percent: 89, stale_snapshot_percent: 0, decision_confidence_bands: { "80–89%": 4 }, calibration_sample_size: 2, mean_absolute_calibration_gap_points: 37, calibration_buckets: [{ label: "80–89%", decision_count: 4, measured_count: 2, expected_accuracy_percent: 87, actual_accuracy_percent: 50, calibration_gap_points: -37, average_return_percent: 0.5 }] },
      sector_analytics: [{ sector: "Technology", decision_count: 2, measured_count: 1, average_confidence_percent: 88, directional_accuracy_percent: 100, average_return_percent: 2, eligible_count: 0 }],
      symbol_analytics: [{ symbol: "AAPL", sector: "Technology", decision_count: 2, measured_count: 1, average_confidence_percent: 88, average_score: 90, directional_accuracy_percent: 100, average_return_percent: 2, eligible_count: 0, latest_headline: "Apple headline" }],
      blocker_analytics: { total_blocker_events: 4, unique_blockers: 1, top_blockers: [{ reason: "Platform trading-readiness checks have not passed.", count: 4, symbol_count: 2, symbols: ["AAPL", "MSFT"] }] },
      trends: [{ date: "2026-07-27", cycles: 8, healthy_cycles: 8, failed_cycles: 0, created: 12, skipped: 300, decisions: 4, measured_outcomes: 2, cycle_duration_seconds: 14.5 }],
      maturity: { score_percent: 38, label: "Learning", graduation_passed_checks: 2, graduation_total_checks: 8, trading_readiness: "NOT_READY", evidence_quality: "STRONG", components: { reliability: 25, measured_sample: 0.4, decision_history: 0.3, graduation: 6.3 } },
      insights: ["Operational completion was strong."], markdown: "# Review"
    }
  })
}));

describe("PerformanceIntelligencePage", () => {
  it("renders analytics 2.0 sections", () => {
    render(<PerformanceIntelligencePage />);
    expect(screen.getByText("KAIRO Analytics 2.0")).toBeInTheDocument();
    expect(screen.getByText("Platform maturity")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Confidence" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Sectors" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Blockers" })).toBeInTheDocument();
  });
});
