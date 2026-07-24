import React from "react";

import {
  DecisionIntelligencePanel,
} from "@/components/copilot/DecisionIntelligencePanel";
import {
  render,
  screen,
} from "@/test/test-utils";


describe(
  "DecisionIntelligencePanel",
  () => {
    it(
      "renders scored decisions",
      () => {
        render(
          <DecisionIntelligencePanel
            report={{
              generated_at:
                "2026-07-24T14:00:00+00:00",
              trading_readiness:
                "NOT_READY",
              graduation_eligible:
                false,
              decision_count: 1,
              executable_candidate_count:
                0,
              platform_blockers: [
                "More shadow decisions are required.",
              ],
              warnings: [],
              decisions: [
                {
                  symbol: "AAPL",
                  generated_at:
                    "2026-07-24T14:00:00+00:00",
                  recommendation:
                    "BLOCKED",
                  score: 87.5,
                  confidence: 0.94,
                  risk_tier: "MEDIUM",
                  suggested_position_value:
                    0,
                  eligible_for_execution:
                    false,
                  headline:
                    "Apple raises guidance.",
                  event_type:
                    "STOCK_LONGTERM_POSITIVE",
                  sentiment: "POSITIVE",
                  classification:
                    "CANDIDATE",
                  components: [
                    {
                      code:
                        "OPPORTUNITY",
                      label:
                        "Opportunity score",
                      value: 59.8,
                      maximum: 65,
                      detail:
                        "Weighted evidence.",
                    },
                  ],
                  reasons: [],
                  blockers: [
                    "More shadow decisions are required.",
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
            "Decision Intelligence v2",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "AAPL",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "87.5",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getAllByText(
            "More shadow decisions are required.",
          ),
        ).toHaveLength(2);
      },
    );
  },
);
