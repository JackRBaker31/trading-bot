import React from "react";

import {
  IntelligenceHealthPanel,
} from "@/components/copilot/IntelligenceHealthPanel";
import {
  fireEvent,
  render,
  screen,
} from "@/test/test-utils";


describe(
  "IntelligenceHealthPanel",
  () => {
    it(
      "shows named expandable stages",
      () => {
        render(
          <IntelligenceHealthPanel
            overview={{
              generated_at:
                "2026-07-24T20:00:00+00:00",
              health_status:
                "DEGRADED",
              recent_job_count: 1,
              succeeded_count: 0,
              warning_count: 1,
              failed_count: 0,
              active_count: 0,
              operation_failure_count:
                0,
              recovered_operation_count:
                0,
              average_job_duration_ms:
                53000,
              average_operation_latency_ms:
                null,
              cache_hit_rate: null,
              retry_count: 0,
              latest_warning: null,
              attention_items: [
                (
                  "1 job contains legacy "
                  + "warnings."
                ),
              ],
              recent_jobs: [
                {
                  job_id: "JOB-1",
                  job_type:
                    "INTELLIGENCE_CYCLE",
                  status:
                    "SUCCEEDED_WITH_WARNINGS",
                  created_at:
                    "2026-07-24T19:58:00+00:00",
                  started_at:
                    "2026-07-24T19:58:00+00:00",
                  finished_at:
                    "2026-07-24T19:59:00+00:00",
                  duration_ms: 53000,
                  trading_impact:
                    "NONE",
                  warning_count: 2,
                  failure_count: 2,
                  retry_count: 0,
                  recovered_count: 0,
                  cache_hit_count: 0,
                  average_latency_ms:
                    null,
                  diagnostics_complete:
                    false,
                  stages: [
                    {
                      stage:
                        "CAPTURE_PRICE_OUTCOMES",
                      display_name:
                        "Capture Price Outcomes",
                      status:
                        "SUCCEEDED_WITH_WARNINGS",
                      duration_ms: null,
                      detail: {
                        failure_count: 2,
                      },
                      warnings: [
                        (
                          "Detailed diagnostics "
                          + "were not captured."
                        ),
                      ],
                      events: [],
                      event_count: 0,
                      failure_count: 2,
                      retry_count: 0,
                      recovered_count: 0,
                      cache_hit_count: 0,
                      average_latency_ms:
                        null,
                      diagnostics_complete:
                        false,
                    },
                  ],
                },
              ],
            }}
            refreshing={false}
            onRefresh={() => {}}
          />,
        );

        expect(
          screen.getByText(
            "Intelligence Health",
          ),
        ).toBeInTheDocument();

        const stage = screen.getByText(
          "Capture Price Outcomes",
        );

        fireEvent.click(stage);

        expect(
          screen.getByText(
            /Detailed diagnostics/,
          ),
        ).toBeInTheDocument();
      },
    );
  },
);
