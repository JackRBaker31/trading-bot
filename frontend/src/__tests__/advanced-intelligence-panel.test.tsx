import React from "react";

import {
  AdvancedIntelligencePanel,
} from "@/components/copilot/AdvancedIntelligencePanel";
import {
  render,
  screen,
} from "@/test/test-utils";


describe(
  "AdvancedIntelligencePanel",
  () => {
    it(
      "renders regime and explainable decision",
      () => {
        render(
          <AdvancedIntelligencePanel
            report={{
              generated_at:
                "2026-07-24T19:30:00+00:00",
              execution_mode:
                "ADVISORY_ONLY",
              regime: {
                as_of_date:
                  "2026-07-24",
                regime: "BULL",
                trend_state:
                  "TRENDING_UP",
                volatility_state:
                  "NORMAL",
                risk_state:
                  "RISK_ON",
                score: 85,
                confidence: 0.98,
                buy_threshold: 75,
                position_multiplier: 1,
                evidence: [],
                warnings: [],
              },
              multi_timeframe: [],
              decisions: [
                {
                  symbol: "AAPL",
                  recommendation: "BUY",
                  raw_score: 82,
                  adjusted_score: 88,
                  raw_confidence: 0.9,
                  calibrated_confidence:
                    0.86,
                  regime: "BULL",
                  timeframe_alignment:
                    "ALIGNED_BULLISH",
                  blockers: [],
                  summary:
                    "AAPL is BUY.",
                  contributions: [],
                },
              ],
              calibration: {
                posterior_mean: 0.75,
                credible_lower: 0.6,
                credible_upper: 0.88,
                sample_count: 25,
                confidence_weight: 0.25,
              },
              warnings: [],
            }}
            refreshing={false}
            onRefresh={() => {}}
          />,
        );

        expect(
          screen.getByText(
            "Advanced Intelligence",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "BULL",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "AAPL",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);
