import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import OpportunityRankingPage from "@/pages/OpportunityRankingPage";
import { render } from "@/test/test-utils";

const rankingData = {
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
};

function history(symbol: string) {
  return {
    generated_at: "2026-07-28T08:30:00Z",
    symbol,
    window_days: 7,
    first_seen_at: "2026-07-27T08:30:00Z",
    last_observed_at: "2026-07-28T08:30:00Z",
    snapshot_count: 2,
    current_rank: symbol === "AAPL" ? 1 : 2,
    current_score: symbol === "AAPL" ? 82.4 : 68.1,
    score_change: symbol === "AAPL" ? 3.2 : -1.1,
    rank_change: symbol === "AAPL" ? 1 : -1,
    streak_direction: symbol === "AAPL" ? "IMPROVING_1" : "WEAKENING_1",
    snapshots: [
      {
        snapshot_id: 1,
        captured_at: "2026-07-27T08:30:00Z",
        last_observed_at: "2026-07-27T08:30:00Z",
        source: "INTELLIGENCE_CYCLE",
        methodology_version: "KAIRO-ORANK-1.0",
        symbol,
        rank: symbol === "AAPL" ? 2 : 1,
        opportunity_score: symbol === "AAPL" ? 79.2 : 69.2,
        category: "WATCH",
        recommendation: "BUY_CANDIDATE",
        calibrated_confidence: 0.8,
        expected_return_percent: 1.5,
        evidence_coverage_percent: 75,
        data_quality: "MODERATE",
        risk_tier: "LOW",
        eligible_for_execution: false,
        historical_match_count: 4,
        measured_case_count: 2,
        sector: "Technology",
        headline: "Earlier setup",
        component_values: { THESIS_QUALITY: 14 },
        component_labels: { THESIS_QUALITY: "Thesis quality" },
        blockers: ["Graduation sample is incomplete."],
      },
      {
        snapshot_id: 2,
        captured_at: "2026-07-28T08:30:00Z",
        last_observed_at: "2026-07-28T08:30:00Z",
        source: "INTELLIGENCE_CYCLE",
        methodology_version: "KAIRO-ORANK-1.0",
        symbol,
        rank: symbol === "AAPL" ? 1 : 2,
        opportunity_score: symbol === "AAPL" ? 82.4 : 68.1,
        category: "HIGH_POTENTIAL_BLOCKED",
        recommendation: "BUY_CANDIDATE",
        calibrated_confidence: 0.84,
        expected_return_percent: 2.6,
        evidence_coverage_percent: 90,
        data_quality: "MODERATE",
        risk_tier: "LOW",
        eligible_for_execution: false,
        historical_match_count: 9,
        measured_case_count: 7,
        sector: "Technology",
        headline: "Current setup",
        component_values: { THESIS_QUALITY: 16 },
        component_labels: { THESIS_QUALITY: "Thesis quality" },
        blockers: ["Graduation sample is incomplete."],
      },
    ],
    changes: [
      {
        captured_at: "2026-07-28T08:30:00Z",
        previous_captured_at: "2026-07-27T08:30:00Z",
        score_change: symbol === "AAPL" ? 3.2 : -1.1,
        rank_change: symbol === "AAPL" ? 1 : -1,
        direction: symbol === "AAPL" ? "IMPROVING" : "WEAKENING",
        summary: symbol === "AAPL" ? "score +3.20; rank up 1" : "score -1.10; rank down 1",
        component_changes: [
          { code: "THESIS_QUALITY", label: "Thesis quality", change: 2 },
        ],
        blockers_added: [],
        blockers_resolved: [],
        readiness_changed: false,
        previous_eligible_for_execution: false,
        eligible_for_execution: false,
      },
    ],
  };
}

vi.mock("@/hooks/useOpportunityRanking", () => ({
  useOpportunityRanking: () => ({
    isLoading: false,
    isFetching: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
    data: rankingData,
  }),
  useOpportunityRankingHistory: (symbol: string) => ({
    isLoading: false,
    data: history(symbol || "AAPL"),
  }),
  useOpportunityRankingHistoryOverview: () => ({
    isLoading: false,
    data: {
      generated_at: "2026-07-28T08:30:00Z",
      window_days: 1,
      tracked_symbol_count: 2,
      snapshot_count: 4,
      latest_observed_at: "2026-07-28T08:30:00Z",
      largest_risers: [
        {
          symbol: "AAPL",
          current_rank: 1,
          current_score: 82.4,
          score_change: 3.2,
          rank_change: 1,
          eligible_for_execution: false,
          category: "HIGH_POTENTIAL_BLOCKED",
          last_observed_at: "2026-07-28T08:30:00Z",
        },
      ],
      largest_fallers: [
        {
          symbol: "LLY",
          current_rank: 2,
          current_score: 68.1,
          score_change: -1.1,
          rank_change: -1,
          eligible_for_execution: true,
          category: "WATCH",
          last_observed_at: "2026-07-28T08:30:00Z",
        },
      ],
      items: [],
    },
  }),
}));

describe("OpportunityRankingPage", () => {
  it("renders advisory rankings, rank drift and switches selected opportunity", async () => {
    const user = userEvent.setup();

    render(<OpportunityRankingPage />);

    expect(screen.getByText("Opportunity Ranking")).toBeInTheDocument();
    expect(screen.getByText("Advisory only")).toBeInTheDocument();
    expect(screen.getAllByText("82.4").length).toBeGreaterThan(0);
    expect(screen.getByText("Opportunity History & Rank Drift")).toBeInTheDocument();
    expect(screen.getByText("24-hour rank drift")).toBeInTheDocument();
    expect(screen.getByText("score +3.20; rank up 1")).toBeInTheDocument();
    expect(screen.getByText("Score composition")).toBeInTheDocument();
    expect(screen.getAllByText("Thesis quality").length).toBeGreaterThan(0);

    await user.click(screen.getByTestId("ranking-symbol-LLY"));

    expect(screen.getAllByText("LLY").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Evidence coverage").length).toBeGreaterThan(0);
    expect(screen.getByText("score -1.10; rank down 1")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Ask Copilot/i })).toBeInTheDocument();
  });
});
