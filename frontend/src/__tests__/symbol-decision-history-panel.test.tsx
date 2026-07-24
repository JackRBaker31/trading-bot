import React from "react";

import {
  SymbolDecisionHistoryPanel,
} from "@/components/copilot/SymbolDecisionHistoryPanel";
import {
  render,
  screen,
} from "@/test/test-utils";


describe(
  "SymbolDecisionHistoryPanel",
  () => {
    it(
      "renders symbol decision changes",
      () => {
        render(
          <SymbolDecisionHistoryPanel
            summary={{
              generated_at:
                "2026-07-24T13:00:00+00:00",
              symbol: "NVDA",
              comparison_available:
                true,
              current: {} as never,
              previous: {} as never,
              score_change: {
                metric: "score",
                previous: 70,
                current: 84.5,
                change: 14.5,
                direction:
                  "IMPROVED",
              },
              confidence_change: {
                metric:
                  "confidence",
                previous: 0.8,
                current: 0.91,
                change: 0.11,
                direction:
                  "IMPROVED",
              },
              rank_change: {
                metric: "rank",
                previous: 3,
                current: 1,
                change: -2,
                direction:
                  "IMPROVED",
              },
              decision_changed:
                true,
              sentiment_changed:
                false,
              classification_changed:
                true,
              new_blockers: [],
              cleared_blockers: [
                "Portfolio blocked.",
              ],
              summary:
                "The decision changed from BLOCKED to TRADE_CANDIDATE.",
            }}
            refreshing={false}
            onRefresh={() => {}}
          />,
        );

        expect(
          screen.getByText(
            "Symbol Decision History",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "The decision changed from BLOCKED to TRADE_CANDIDATE.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Portfolio blocked.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "+14.50",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);
