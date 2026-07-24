import React from "react";

import { MacroAnalysisPanel } from "@/components/copilot/MacroAnalysisPanel";
import { render, screen } from "@/test/test-utils";


describe("MacroAnalysisPanel", () => {
  it("renders macro regime metrics", () => {
    render(
      <MacroAnalysisPanel
        analysis={{
          as_of_date: "2026-07-24",
          score: 8.5,
          maximum: 10,
          confidence: 0.98,
          stance: "SUPPORTIVE",
          regime: "RISK_ON",
          broad_market_trend: "STRONG_UPTREND",
          growth_leadership: "LEADING",
          rate_pressure: "EASING",
          volatility_regime: "NORMAL",
          evidence: [],
          warnings: [],
          metrics: [
            {
              code: "BROAD_MARKET",
              label: "Broad-market trend",
              value: 1.2,
              display_value: "SPY above EMA200",
              score: 3,
              maximum: 3,
              stance: "STRONG_UPTREND",
              detail: "All checks passed.",
            },
          ],
        }}
        refreshing={false}
        onRefresh={() => {}}
      />,
    );

    expect(
      screen.getByText("Macro Capability"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("8.5/10"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("RISK_ON"),
    ).toBeInTheDocument();
  });
});
