import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import OpportunityRankingPage from "@/pages/OpportunityRankingPage";
import { render } from "@/test/test-utils";

vi.mock("@/hooks/useOpportunityRanking", () => ({
  useOpportunityRanking: () => ({
    isLoading: false,
    isFetching: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
    data: {
      generated_at: "2026-07-28T08:30:00Z",
      methodology_version: "KAIRO-ORANK-1.0",
      methodology_summary: "Evidence-backed advisory opportunity ranking.",
      advisory_only: true,
      performance_window_days: 90,
      ranking_count: 2,
      execution_ready_count: 1,
      high_potential_blocked_count: 1,
      market_data_status: "HEALTHY",
      component_weights: {},
      warnings: [],
      items: [
        {
          rank: 1,
          symbol: "AAPL",
          opportunity_score: 82.4,
          category: "HIGH_POTENTIAL_BLOCKED",
          recommendation: "BLOCKED",
          thesis_score: 89,
          raw_confidence: 0.92,
          calibrated_confidence: 0.84,
          confidence_sample_count: 8,
          expected_return_percent: 2.6,
          evidence_coverage_percent: 90,
          data_quality: "MODERATE",
          risk_tier: "LOW",
          eligible_for_execution: false,
          historical_match_count: 9,
          measured_case_count: 7,
          sector: "Technology",
          headline: "Apple raises guidance.",
          generated_at: "2026-07-28T08:30:00Z",
          components: [
            {
              code: "THESIS_QUALITY",
              label: "Thesis quality",
              value: 16,
              maximum: 18,
              status: "AVAILABLE",
              detail: "Current investment thesis score is 89.0/100.",
            },
          ],
          positive_contributors: ["Thesis quality: strong current evidence."],
          penalties: ["Execution blocker: graduation sample is incomplete."],
          improvement_actions: ["Resolve execution gate: graduation sample is incomplete."],
          blockers: ["Graduation sample is incomplete."],
          warnings: [],
        },
        {
          rank: 2,
          symbol: "LLY",
          opportunity_score: 68.1,
          category: "WATCH",
          recommendation: "BUY_CANDIDATE",
          thesis_score: 74,
          raw_confidence: 0.82,
          calibrated_confidence: 0.79,
          confidence_sample_count: 4,
          expected_return_percent: 0.7,
          evidence_coverage_percent: 68,
          data_quality: "LIMITED",
          risk_tier: "MEDIUM",
          eligible_for_execution: true,
          historical_match_count: 2,
          measured_case_count: 1,
          sector: "Healthcare",
          headline: "Lilly expands capacity.",
          generated_at: "2026-07-28T08:30:00Z",
          components: [
            {
              code: "EVIDENCE_COVERAGE",
              label: "Evidence coverage",
              value: 8.2,
              maximum: 12,
              status: "LIMITED",
              detail: "68.0% of configured evidence is available.",
            },
          ],
          positive_contributors: ["Evidence coverage supports monitoring."],
          penalties: [],
          improvement_actions: ["Collect more measured outcomes."],
          blockers: [],
          warnings: [],
        },
      ],
    },
  }),
}));

describe("OpportunityRankingPage", () => {
  it("renders advisory rankings and switches selected opportunity", async () => {
    const user = userEvent.setup();

    render(<OpportunityRankingPage />);

    expect(screen.getByText("Opportunity Ranking")).toBeInTheDocument();
    expect(screen.getByText("Advisory only")).toBeInTheDocument();
    expect(screen.getAllByText("82.4")).toHaveLength(2);
    expect(screen.getByText("Score composition")).toBeInTheDocument();
    expect(screen.getByText("Thesis quality")).toBeInTheDocument();

    await user.click(screen.getByTestId("ranking-symbol-LLY"));

    expect(screen.getAllByText("LLY").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Evidence coverage")).toHaveLength(2);
    expect(screen.getByRole("link", { name: /Ask Copilot/i })).toBeInTheDocument();
  });
});
