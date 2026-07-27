import { screen } from "@testing-library/react";
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

vi.mock("@/hooks/usePerformanceReview", () => ({
  usePerformanceReview: () => ({
    isPending: false,
    isFetching: false,
    refetch: vi.fn(),
    data: {
      symbol_analytics: [
        {
          symbol: "AAPL",
          sector: "Technology",
          decision_count: 8,
          measured_count: 4,
          average_confidence_percent: 87,
          average_score: 84,
          directional_accuracy_percent: 75,
          average_return_percent: 1.8,
          eligible_count: 0,
          latest_headline: "Apple raises guidance.",
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
    expect(screen.getByRole("link", { name: /Ask Copilot/i })).toBeInTheDocument();
  });
});
