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


describe(
  "KAIRO Copilot page",
  () => {
    it(
      "loads suggested questions",
      async () => {
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
  },
);