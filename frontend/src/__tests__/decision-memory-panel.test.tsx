import React from "react";

import {
  DecisionMemoryPanel,
} from "@/components/copilot/DecisionMemoryPanel";
import {
  render,
  screen,
} from "@/test/test-utils";


describe(
  "DecisionMemoryPanel",
  () => {
    it(
      "renders recent decisions",
      () => {
        render(
          <DecisionMemoryPanel
            overview={{
              generated_at:
                "2026-07-24T16:00:00+00:00",
              total_count: 1,
              executable_count: 0,
              executed_count: 0,
              symbol_count: 1,
              latest: [
                {
                  decision_id:
                    "KAIRO-2026-ABC123",
                  fingerprint:
                    "fingerprint",
                  captured_at:
                    "2026-07-24T16:00:00+00:00",
                  thesis_generated_at:
                    "2026-07-24T16:00:00+00:00",
                  symbol: "AAPL",
                  recommendation:
                    "INCOMPLETE",
                  score: 84.5,
                  confidence: 0.91,
                  confidence_coverage:
                    0.83,
                  risk_tier: "HIGH",
                  time_horizon:
                    "POSITION",
                  suggested_position_value:
                    0,
                  eligible_for_execution:
                    false,
                  headline:
                    "Apple raises guidance.",
                  primary_driver:
                    "NEWS",
                  capabilities: [],
                  reasons: [],
                  blockers: [
                    "Valuation unavailable.",
                  ],
                  warnings: [],
                  executed: false,
                  paper_trade_id: null,
                },
              ],
            }}
            refreshing={false}
            onRefresh={() => {}}
          />,
        );

        expect(
          screen.getByText(
            "Decision Memory",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "AAPL",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "KAIRO-2026-ABC123",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);
