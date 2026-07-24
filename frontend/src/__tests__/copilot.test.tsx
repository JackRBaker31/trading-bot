import React from "react";

import {
  http,
  HttpResponse,
} from "msw";

import userEvent from "@testing-library/user-event";

import CopilotPage from "@/pages/CopilotPage";
import {
  render,
  screen,
  waitFor,
} from "@/test/test-utils";
import { server } from "@/test/handlers";


const BASE =
  "http://127.0.0.1:8000";


const healthyOverview = {
  generated_at:
    "2026-07-24T08:00:00+00:00",
  overall_status: "HEALTHY",
  platform: {
    overall_status: "HEALTHY",
    online_services: 5,
    required_services: 5,
  },
  activity: {
    running_jobs: 1,
    queued_jobs: 2,
    active_jobs: 3,
  },
  schedule: {
    task_type:
      "INTELLIGENCE_CYCLE",
    next_run_at:
      "2026-07-24T09:30:00+00:00",
    schedule_id: "schedule-001",
  },
  failures: {
    recent_count: 0,
    latest: null,
  },
  trading_intelligence: {
    trading_readiness:
      "NOT_READY",
    market_outlook:
      "CAUTIOUS",
    confidence: 63.5,
    signal_count: 12,
    actionable_signal_count: 2,
    evidence_quality: "LOW",
  },
  graduation: {
    ready: false,
    passed_checks: 1,
    total_checks: 2,
    failed_checks: 1,
    checks: [
      {
        name:
          "Decision sample",
        passed: false,
        reason:
          "More shadow decisions are required.",
      },
      {
        name:
          "Loss containment",
        passed: true,
        reason: null,
      },
    ],
  },
  attention_items: [],
};


function useHealthyOverview() {
  server.use(
    http.get(
      `${BASE}/api/copilot/overview`,
      () =>
        HttpResponse.json(
          healthyOverview,
        ),
    ),
    http.get(
      `${BASE}/api/copilot/change-summary`,
      () =>
        HttpResponse.json(
          changeSummary,
        ),
    ),
  );
}


const changeSummary = {
  generated_at: "2026-07-24T10:00:00+00:00",
  comparison_available: true,
  current: {
    snapshot_id: "2",
    captured_at: "2026-07-24T10:00:00+00:00",
    overall_status: "HEALTHY",
    platform_status: "HEALTHY",
    trading_readiness: "NOT_READY",
    market_outlook: "CAUTIOUS",
    confidence: 72.5,
    signal_count: 14,
    actionable_signal_count: 3,
    evidence_quality: "LOW",
    graduation_ready: false,
    graduation_passed_checks: 1,
    graduation_total_checks: 2,
    graduation_failed_checks: 1,
    decision: "NO_TRADE",
    blockers: [],
  },
  previous: null,
  confidence_change: {
    metric: "confidence", previous: 63.5, current: 72.5,
    change: 9, direction: "UP",
  },
  signal_count_change: {
    metric: "signal_count", previous: 12, current: 14,
    change: 2, direction: "UP",
  },
  actionable_signal_change: {
    metric: "actionable_signal_count", previous: 2, current: 3,
    change: 1, direction: "UP",
  },
  graduation_passed_change: {
    metric: "graduation_passed_checks", previous: 0, current: 1,
    change: 1, direction: "UP",
  },
  new_blockers: [],
  cleared_blockers: ["More shadow decisions are required."],
  summary:
    "Confidence increased by 9.0. Actionable signals increased by 1. 1 blocker(s) cleared.",
};


describe(
  "KAIRO Copilot page",
  () => {
    it(
      "loads suggested questions",
      async () => {
        useHealthyOverview();

        server.use(
          http.get(
            `${BASE}/api/copilot/suggestions`,
            () =>
              HttpResponse.json({
                items: [
                  "Is KAIRO healthy?",
                  "What failed recently?",
                ],
              }),
          ),
        );

        render(
          <CopilotPage />,
        );

        expect(
          await screen.findByText(
            "Is KAIRO healthy?",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "What failed recently?",
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "submits a question and renders the response",
      async () => {
        useHealthyOverview();

        let submittedQuestion:
          | string
          | null = null;

        server.use(
          http.get(
            `${BASE}/api/copilot/suggestions`,
            () =>
              HttpResponse.json({
                items: [],
              }),
          ),

          http.post(
            `${BASE}/api/copilot/query`,
            async ({
              request,
            }) => {
              const payload =
                await request.json() as {
                  question: string;
                };

              submittedQuestion =
                payload.question;

              return HttpResponse.json({
                summary:
                  "KAIRO is operating normally.",
                suggestions: [
                  {
                    title:
                      "Platform health",
                    message:
                      "All required services are online.",
                    kind:
                      "success",
                  },
                ],
              });
            },
          ),
        );

        const user =
          userEvent.setup();

        render(
          <CopilotPage />,
        );

        await user.type(
          screen.getByTestId(
            "copilot-question",
          ),
          "Is KAIRO healthy?",
        );

        await user.click(
          screen.getByTestId(
            "copilot-submit",
          ),
        );

        await waitFor(
          () => {
            expect(
              submittedQuestion,
            ).toBe(
              "Is KAIRO healthy?",
            );
          },
        );

        expect(
          await screen.findByText(
            "KAIRO is operating normally.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Platform health",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "All required services are online.",
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "submits a suggested question",
      async () => {
        useHealthyOverview();

        let submittedQuestion:
          | string
          | null = null;

        server.use(
          http.get(
            `${BASE}/api/copilot/suggestions`,
            () =>
              HttpResponse.json({
                items: [
                  "What happens next?",
                ],
              }),
          ),

          http.post(
            `${BASE}/api/copilot/query`,
            async ({
              request,
            }) => {
              const payload =
                await request.json() as {
                  question: string;
                };

              submittedQuestion =
                payload.question;

              return HttpResponse.json({
                summary:
                  "The next Intelligence Cycle is scheduled.",
                suggestions: [],
              });
            },
          ),
        );

        const user =
          userEvent.setup();

        render(
          <CopilotPage />,
        );

        await user.click(
          await screen.findByText(
            "What happens next?",
          ),
        );

        await waitFor(
          () => {
            expect(
              submittedQuestion,
            ).toBe(
              "What happens next?",
            );
          },
        );

        expect(
          await screen.findByText(
            "The next Intelligence Cycle is scheduled.",
          ),
        ).toBeInTheDocument();
      },
    );


    it(
      "renders the executive intelligence dashboard",
      async () => {
        useHealthyOverview();

        server.use(
          http.get(
            `${BASE}/api/copilot/suggestions`,
            () =>
              HttpResponse.json({
                items: [],
              }),
          ),
        );

        render(
          <CopilotPage />,
        );

        expect(
          await screen.findByText(
            "Executive Intelligence Dashboard",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "5 of 5 required services online.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "63.5%",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "2 / 12",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "1 requirement(s) remain blocked.",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "NO TRADE",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Why KAIRO is not trading",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Recommended Actions",
          ),
        ).toBeInTheDocument();

        expect(
        screen.getAllByText(
            "More shadow decisions are required.",
        ),
        ).toHaveLength(2);
      },
    );

    it(
      "renders change intelligence",
      async () => {
        useHealthyOverview();

        server.use(
          http.get(
            `${BASE}/api/copilot/suggestions`,
            () => HttpResponse.json({ items: [] }),
          ),
        );

        render(<CopilotPage />);

        expect(
          await screen.findByText("What Changed"),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Confidence increased by 9.0. Actionable signals increased by 1. 1 blocker(s) cleared.",
          ),
        ).toBeInTheDocument();
      },
    );

  },
);
