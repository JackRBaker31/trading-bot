import { http, HttpResponse } from "msw";
import { screen } from "@testing-library/react";

import ShadowIntelligencePage from "@/pages/ShadowIntelligencePage";
import { server } from "@/test/handlers";
import { render } from "@/test/test-utils";

const BASE = "http://127.0.0.1:8000";

describe("Shadow Intelligence contract", () => {
  it("renders the live backend summary, performance and graduation fields", async () => {
    server.use(
      http.get(`${BASE}/api/shadow-decisions/summary`, () =>
        HttpResponse.json({
          decision_count: 88,
          total_decisions: 88,
          measured_decisions: 83,
          eligible_decisions: 0,
          blocked_decisions: 88,
          latest_decision_at: "2026-08-04T07:30:00+00:00",
          model_version: "KAIRO_SHADOW_V1",
          action_counts: {
            MONITOR: 0,
            WATCH: 0,
            CONSIDER_LONG: 0,
            BLOCKED: 88,
          },
          performance_by_horizon: [],
          trading_impact: "NONE",
        }),
      ),
      http.get(`${BASE}/api/shadow-performance`, () =>
        HttpResponse.json({
          model_version: "KAIRO_SHADOW_V1",
          total_decision_count: 88,
          execution_cost_percent: 0.2,
          horizons: [],
          trading_impact: "NONE",
          available: true,
          generated_at: null,
          periods: {
            "1d": {
              directional_success: 0.3614,
              profitable_after_costs: 0.3373,
              average_return: 0.000672,
              average_net_return: -0.001328,
              maximum_drawdown: 0.181622,
              rolling_stability: 0.375,
              coverage: 0.9432,
              sample_count: 83,
            },
          },
        }),
      ),
      http.get(`${BASE}/api/intelligence/graduation-status`, () =>
        HttpResponse.json({
          eligible: false,
          checks_passed: 0,
          total_checks: 8,
          checks_remaining: 8,
          checks: [
            {
              name: "TOTAL_SHADOW_DECISIONS",
              passed: false,
              actual: 88,
              required: 250,
              reason: "Only 88 shadow decisions are available; 250 are required.",
              description: "Only 88 shadow decisions are available; 250 are required.",
            },
          ],
          failed_checks: [],
          status: "RESEARCH_ONLY",
          stage: "RESEARCH_ONLY",
          trading_impact: "NONE",
        }),
      ),
      http.get(`${BASE}/api/shadow-decisions`, () =>
        HttpResponse.json({
          total_count: 1,
          offset: 0,
          limit: 50,
          count: 1,
          items: [
            {
              decision_id: "decision-1",
              symbol: "AAPL",
              action: "BLOCKED",
              score: 82.4,
              confidence: 0.88,
              event_type: "STOCK_SHORTTERM_POSITIVE",
              is_material: true,
              headline: "Example signal",
              eligible_for_trade: false,
              reasons: ["High score."],
              blocking_reasons: ["Research only."],
              reference_price: 210.5,
              reference_captured_at: "2026-08-04T07:00:00+00:00",
              model_version: "KAIRO_SHADOW_V1",
              created_at: "2026-08-04T07:30:00+00:00",
            },
          ],
        }),
      ),
    );

    render(<ShadowIntelligencePage />);

    expect(await screen.findByText("Total Decisions")).toBeInTheDocument();

    expect(
      screen.getAllByText("88").length
    ).toBeGreaterThanOrEqual(2);
    expect(await screen.findByText("Measured")).toBeInTheDocument();

    expect(
      screen.getAllByText("83").length
    ).toBeGreaterThanOrEqual(2);
    expect(await screen.findByText("36.1%")).toBeInTheDocument();
    expect(await screen.findByText("33.7%")).toBeInTheDocument();
    expect(await screen.findByText("18.2%")).toBeInTheDocument();
    expect(await screen.findByText("0/8 checks")).toBeInTheDocument();
    expect(await screen.findByText("RESEARCH ONLY")).toBeInTheDocument();
    expect(await screen.findByText("BLOCKED")).toBeInTheDocument();
    expect(screen.queryByText("Performance data unavailable.")).not.toBeInTheDocument();
  });
});
