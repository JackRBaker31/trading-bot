import React from "react";

import {
  TechnicalAnalysisPanel,
} from "@/components/copilot/TechnicalAnalysisPanel";
import {
  render,
  screen,
} from "@/test/test-utils";


describe(
  "TechnicalAnalysisPanel",
  () => {
    it(
      "renders technical metrics",
      () => {
        render(
          <TechnicalAnalysisPanel
            analysis={{
              symbol: "AAPL",
              as_of_date:
                "2026-07-24",
              bar_count: 260,
              score: 17.5,
              maximum: 20,
              confidence: 0.98,
              stance: "BULLISH",
              trend:
                "STRONG_UPTREND",
              momentum: "STRONG",
              volatility: "HEALTHY",
              volume_confirmation:
                "CONFIRMED",
              price_structure:
                "CONSTRUCTIVE",
              latest_close: 215.2,
              warnings: [],
              evidence: [],
              metrics: [
                {
                  code: "TREND",
                  label:
                    "Trend alignment",
                  value: 1.2,
                  display_value:
                    "EMA alignment",
                  score: 5,
                  maximum: 5,
                  stance:
                    "STRONG_UPTREND",
                  detail:
                    "All checks passed.",
                },
              ],
            }}
            refreshing={false}
            onRefresh={() => {}}
          />,
        );

        expect(
          screen.getByText(
            "Technical Capability",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "17.5/20",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Trend alignment",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);
