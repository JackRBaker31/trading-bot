import React from "react";

import {
  AdaptiveIntelligencePanel,
} from "@/components/copilot/AdaptiveIntelligencePanel";
import {
  render,
  screen,
} from "@/test/test-utils";


describe(
  "AdaptiveIntelligencePanel",
  () => {
    it(
      "renders advisory intelligence",
      () => {
        render(
          <AdaptiveIntelligencePanel
            report={{
              generated_at:
                "2026-07-24T18:00:00+00:00",
              execution_mode:
                "ADVISORY_ONLY",
              performance: {
                observation_count: 20,
                tracked_decision_count: 10,
                positive_rate: 0.65,
                average_return: 0.04,
                average_alpha: 0.01,
                best_horizon_days: 7,
                learning_confidence: 0.08,
                findings: [],
                confidence_bands: [],
              },
              portfolio: {
                available_cash: 10000,
                investable_cash: 8000,
                maximum_symbol_weight: 0.25,
                unallocated_cash: 6000,
                warnings: [],
                allocations: [
                  {
                    symbol: "AAPL",
                    constrained_weight: 0.25,
                    suggested_value: 2000,
                    score: 90,
                    confidence: 0.9,
                    risk_tier: "LOW",
                  },
                ],
              },
              risk: {
                overall_risk_score: 15,
                overall_tier: "LOW",
                dominant_risk: null,
                warnings: [],
                contributions: [],
              },
              position_sizes: [],
              committee: [
                {
                  symbol: "AAPL",
                  final_stance: "BUY",
                  consensus_score: 82,
                  disagreement_score: 10,
                  confidence: 0.9,
                  summary: "Consensus.",
                },
              ],
              proposals: [],
              warnings: [],
            }}
            refreshing={false}
            proposing={false}
            onRefresh={() => {}}
            onPropose={() => {}}
          />,
        );

        expect(
          screen.getByText(
            "Adaptive Intelligence",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "ADVISORY_ONLY",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getAllByText(
            "AAPL",
          ),
        ).toHaveLength(2);
      },
    );
  },
);
