import React from "react";

import {
  InvestmentThesisPanel,
} from "@/components/copilot/InvestmentThesisPanel";
import {
  render,
  screen,
} from "@/test/test-utils";


describe(
  "InvestmentThesisPanel",
  () => {
    it(
      "shows incomplete capabilities",
      () => {
        render(
          <InvestmentThesisPanel
            report={{
              generated_at:
                "2026-07-24T15:00:00+00:00",
              thesis_count: 1,
              executable_count: 0,
              complete_capability_count:
                3,
              required_capability_count:
                6,
              platform_blockers: [],
              warnings: [],
              theses: [
                {
                  thesis_id: "thesis-1",
                  generated_at:
                    "2026-07-24T15:00:00+00:00",
                  symbol: "AAPL",
                  recommendation:
                    "INCOMPLETE",
                  score: 88.2,
                  available_score:
                    44.1,
                  available_maximum:
                    50,
                  confidence: 0.92,
                  confidence_coverage:
                    0.625,
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
                  capabilities: [
                    {
                      capability:
                        "TECHNICAL",
                      status:
                        "UNAVAILABLE",
                      score: null,
                      maximum: 20,
                      confidence: null,
                      stance: "UNKNOWN",
                      summary:
                        "Technical provider not connected.",
                      evidence: [],
                      blockers: [],
                    },
                  ],
                  reasons: [],
                  blockers: [
                    "Required capabilities are not yet available: TECHNICAL.",
                  ],
                  warnings: [],
                },
              ],
            }}
            refreshing={false}
            onRefresh={() => {}}
          />,
        );

        expect(
          screen.getByText(
            "Decision Intelligence v3",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "AAPL",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "3/6",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);
