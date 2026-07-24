import React from "react";

import {
  DecisionOutcomePanel,
} from "@/components/copilot/DecisionOutcomePanel";
import {
  render,
  screen,
} from "@/test/test-utils";


describe(
  "DecisionOutcomePanel",
  () => {
    it(
      "renders recorded outcomes",
      () => {
        render(
          <DecisionOutcomePanel
            overview={{
              generated_at:
                "2026-07-24T17:00:00+00:00",
              tracked_decision_count: 1,
              observation_count: 1,
              positive_outcome_count: 1,
              negative_outcome_count: 0,
              average_return: 0.05,
              average_alpha: 0.03,
              latest: [
                {
                  outcome_id:
                    "OUTCOME-1",
                  decision_id:
                    "KAIRO-2026-ABC",
                  symbol: "AAPL",
                  horizon_days: 7,
                  target_date:
                    "2026-07-20",
                  observed_at:
                    "2026-07-24T17:00:00+00:00",
                  entry_price: 100,
                  observed_price: 105,
                  absolute_return: 0.05,
                  benchmark_symbol:
                    "SPY",
                  benchmark_entry_price:
                    500,
                  benchmark_observed_price:
                    510,
                  benchmark_return: 0.02,
                  alpha: 0.03,
                  maximum_favourable_excursion:
                    0.07,
                  maximum_drawdown:
                    -0.02,
                  status: "POSITIVE",
                },
              ],
            }}
            refreshing={false}
            capturing={false}
            onRefresh={() => {}}
            onCapture={() => {}}
          />,
        );

        expect(
          screen.getByText(
            "Outcome Tracking",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getAllByText(
            "+5.00%",
          ),
        ).toHaveLength(2);

        expect(
          screen.getByText(
            "AAPL",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);
