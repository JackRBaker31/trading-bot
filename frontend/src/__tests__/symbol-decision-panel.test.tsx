import React from "react";

import {
  SymbolDecisionPanel,
} from "@/components/copilot/SymbolDecisionPanel";
import {
  render,
  screen,
} from "@/test/test-utils";


const traces = [
  {
    trace_id: "trace-1",
    captured_at:
      "2026-07-24T12:00:00+00:00",
    symbol: "NVDA",
    rank: 1,
    decision: "BLOCKED",
    classification: "BLOCKED",
    score: 84.5,
    confidence: 0.91,
    headline:
      "NVIDIA raises revenue guidance.",
    event_type: "EARNINGS",
    sentiment: "BULLISH",
    eligible_for_trade: false,
    trading_readiness: "NOT_READY",
    graduation_ready: false,
    summary:
      "NVDA remains blocked by 2 recorded conditions.",
    blockers: [
      "Trading readiness has not passed.",
    ],
    stages: [
      {
        sequence: 1,
        stage: "RESEARCH",
        status: "PASS",
        title: "Research Evidence",
        summary:
          "NVIDIA raises revenue guidance.",
        evidence: [
          "Event type: EARNINGS.",
        ],
      },
      {
        sequence: 2,
        stage: "DECISION",
        status: "BLOCKED",
        title:
          "Final Symbol Decision",
        summary:
          "KAIRO withheld NVDA from trade-candidate status.",
        evidence: [
          "Trading readiness has not passed.",
        ],
      },
    ],
  },
];


describe(
  "SymbolDecisionPanel",
  () => {
    it(
      "renders a grounded symbol decision trace",
      () => {
        render(
          <SymbolDecisionPanel
            traces={traces}
            refreshing={false}
            onRefresh={() => undefined}
          />,
        );

        expect(
          screen.getByText(
            "Symbol Decision Intelligence",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getAllByText(
            "NVIDIA raises revenue guidance.",
          ),
        ).toHaveLength(2);

        expect(
          screen.getByText(
            "Final Symbol Decision",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText("91.0%"),
        ).toBeInTheDocument();
      },
    );
  },
);
