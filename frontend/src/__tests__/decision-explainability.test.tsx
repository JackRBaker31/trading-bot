import { fireEvent, screen } from "@testing-library/react";
import { vi } from "vitest";

import DecisionExplainabilityPage from "@/pages/DecisionExplainabilityPage";
import { render } from "@/test/test-utils";

vi.mock("@/hooks/useDecisionIntelligence", () => ({
  useDecisionIntelligence: () => ({
    isPending: false,
    isFetching: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
    data: {
      generated_at: "2026-07-27T12:00:00Z",
      trading_readiness: "NOT_READY",
      graduation_eligible: false,
      decision_count: 1,
      executable_candidate_count: 0,
      platform_blockers: ["Platform trading-readiness checks have not passed."],
      warnings: [],
      decisions: [
        {
          symbol: "AAPL",
          generated_at: "2026-07-27T12:00:00Z",
          recommendation: "BUY_CANDIDATE",
          score: 88.3,
          confidence: 0.91,
          risk_tier: "MEDIUM",
          suggested_position_value: 2500,
          eligible_for_execution: false,
          headline: "Apple raises guidance.",
          event_type: "EARNINGS",
          sentiment: "POSITIVE",
          classification: "CANDIDATE",
          components: [
            {
              code: "NEWS",
              label: "News evidence",
              value: 28,
              maximum: 30,
              detail: "Positive material evidence.",
            },
          ],
          reasons: ["Positive material evidence supports the candidate."],
          blockers: ["Platform trading-readiness checks have not passed."],
          warnings: ["Measured sample remains limited."],
        },
      ],
    },
  }),
}));

vi.mock("@/hooks/useCopilot", () => ({
  useSymbolDecisions: () => ({
    isPending: false,
    isFetching: false,
    refetch: vi.fn(),
    data: {
      items: [
        {
          trace_id: "trace-1",
          captured_at: "2026-07-27T12:00:00Z",
          symbol: "AAPL",
          rank: 1,
          decision: "BLOCKED",
          classification: "CANDIDATE",
          score: 88.3,
          confidence: 0.91,
          headline: "Apple raises guidance.",
          event_type: "EARNINGS",
          sentiment: "POSITIVE",
          eligible_for_trade: false,
          trading_readiness: "NOT_READY",
          graduation_ready: false,
          summary: "AAPL ranks highly but execution remains gated.",
          stages: [
            {
              sequence: 1,
              stage: "EVIDENCE",
              status: "PASS",
              title: "Evidence assessment",
              summary: "Material evidence was recorded.",
              evidence: ["Apple raises guidance."],
            },
          ],
          blockers: ["Platform trading-readiness checks have not passed."],
        },
      ],
    },
  }),
  useSymbolDecisionChangeSummary: () => ({
    isPending: false,
    isFetching: false,
    refetch: vi.fn(),
    data: { available: false, symbol: "AAPL", summary: null },
  }),
}));



vi.mock("@/hooks/useHistoricalSimilarity", () => ({
  useHistoricalSimilarity: () => ({
    isPending: false,
    isFetching: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
    data: {
      generated_at: "2026-07-27T12:00:00Z",
      symbol: "AAPL",
      current_thesis_id: "thesis-1",
      current_recommendation: "BUY_CANDIDATE",
      current_score: 87.5,
      current_confidence: 0.9,
      current_risk_tier: "MEDIUM",
      current_time_horizon: "SWING",
      current_primary_driver: "NEWS",
      methodology_version: "KAIRO-HSIM-1.0",
      methodology_summary: "Weighted feature-vector comparison.",
      minimum_similarity_percent: 65,
      target_horizon_days: 7,
      candidate_count: 12,
      matched_case_count: 3,
      measured_case_count: 2,
      sample_quality: "INSUFFICIENT",
      average_similarity_percent: 82.4,
      win_rate_percent: 50,
      average_return_percent: 1.2,
      median_return_percent: 1.2,
      average_directional_return_percent: 1.2,
      average_alpha_percent: 0.4,
      best_directional_return_percent: 3.4,
      worst_directional_return_percent: -1,
      average_holding_days: 7,
      warnings: ["The measured sample is too small for decision-making."],
      cases: [
        {
          decision_id: "historical-1",
          symbol: "AAPL",
          captured_at: "2026-06-27T12:01:00Z",
          thesis_generated_at: "2026-06-27T12:00:00Z",
          recommendation: "BUY_CANDIDATE",
          score: 85,
          confidence: 0.88,
          risk_tier: "MEDIUM",
          time_horizon: "SWING",
          headline: "Historical Apple earnings setup.",
          primary_driver: "NEWS",
          similarity_percent: 91.2,
          same_symbol: true,
          matching_factors: ["News event type: EARNINGS aligns with EARNINGS."],
          differing_factors: [],
          feature_comparisons: [],
          outcome: {
            horizon_days: 7,
            observed_at: "2026-07-04T12:00:00Z",
            raw_return_percent: 3.4,
            directional_return_percent: 3.4,
            alpha_percent: 2.2,
            maximum_favourable_excursion_percent: 4.1,
            maximum_drawdown_percent: -1.2,
            directional_success: true,
            status: "MEASURED",
          },
        },
      ],
    },
  }),
}));

describe("DecisionExplainabilityPage", () => {
  it("renders evidence-backed decision explanation", () => {
    render(<DecisionExplainabilityPage />);

    expect(screen.getByText("Decision Explainability")).toBeInTheDocument();
    expect(screen.getAllByText("AAPL").length).toBeGreaterThan(0);
    expect(screen.getByText("KAIRO conclusion")).toBeInTheDocument();
    expect(screen.getByText("Score composition")).toBeInTheDocument();
    expect(screen.getByText("Decision timeline")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Historical similarity"));
    expect(screen.getByText("True historical similarity")).toBeInTheDocument();
    expect(screen.getByText("Historical Apple earnings setup.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Ask Copilot/i })).toBeInTheDocument();
  });
});
