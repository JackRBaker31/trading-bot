/**
 * Research page form payload tests:
 * - Strategy-report job creation sends { force: false }
 * - Shadow-analysis job creation sends { force: false }
 * - Job polling stops when a job reaches a terminal state
 */
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { server } from "@/test/handlers";
import { render, screen, waitFor, renderHook } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import ResearchPage from "@/pages/ResearchPage";
import { useResearchJobPoll } from "@/pages/ResearchPage";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createTestQueryClient } from "@/test/test-utils";

const BASE = "http://127.0.0.1:8000";

// ── Strategy report ───────────────────────────────────────────────────────────

describe("Strategy Report form", () => {
  it("sends { force: false } to /jobs/strategy-report", async () => {
    let capturedBody: unknown = null;

    server.use(
      http.post(`${BASE}/api/jobs/strategy-report`, async ({ request }) => {
        capturedBody = await request.json();
        return HttpResponse.json({ job_id: "job-strat-001" });
      }),
    );

    const user = userEvent.setup();
    render(<ResearchPage />);

    // Wait for the page to settle (queries resolve)
    await waitFor(() =>
      expect(screen.getByTestId("submit-generate-report")).toBeInTheDocument(),
    );

    await user.click(screen.getByTestId("submit-generate-report"));

    await waitFor(() => expect(capturedBody).not.toBeNull());

    expect(capturedBody).toEqual({ force: false });
  });
});

// ── Shadow analysis ───────────────────────────────────────────────────────────

describe("Shadow Analysis form", () => {
  it("sends { force: false } even when no symbols are entered", async () => {
    let capturedBody: unknown = null;

    server.use(
      http.post(`${BASE}/api/jobs/shadow-analysis`, async ({ request }) => {
        capturedBody = await request.json();
        return HttpResponse.json({ job_id: "job-shadow-001" });
      }),
    );

    const user = userEvent.setup();
    render(<ResearchPage />);

    await waitFor(() =>
      expect(screen.getByTestId("submit-shadow-analysis")).toBeInTheDocument(),
    );

    await user.click(screen.getByTestId("submit-shadow-analysis"));

    await waitFor(() => expect(capturedBody).not.toBeNull());

    expect(capturedBody).toMatchObject({ force: false });
    // No symbols key when the input is empty
    expect(capturedBody as Record<string, unknown>).not.toHaveProperty("symbols");
  });
});

// ── Job polling ───────────────────────────────────────────────────────────────

describe("useResearchJobPoll", () => {
  it("stops polling when the job reaches a terminal state", async () => {
    let pollCount = 0;

    server.use(
      http.get(`${BASE}/api/jobs/test-terminal-job`, () => {
        pollCount++;
        return HttpResponse.json({
          job_id: "test-terminal-job",
          job_type: "NEWS_RESEARCH_CYCLE",
          status: "SUCCEEDED",
          created_at: new Date().toISOString(),
          started_at: new Date().toISOString(),
          completed_at: new Date().toISOString(),
          duration_seconds: 5,
          error_summary: null,
          result_summary: null,
        });
      }),
    );

    const onComplete = vi.fn();

    // Provide a fresh QueryClient via the wrapper option so useQuery works
    const { result } = renderHook(
      () => useResearchJobPoll("test-terminal-job", onComplete),
      {
        wrapper: ({ children }: { children: React.ReactNode }) => (
          <QueryClientProvider client={createTestQueryClient()}>
            {children}
          </QueryClientProvider>
        ),
      },
    );

    // Wait for the first fetch and completion callback
    await waitFor(() => expect(onComplete).toHaveBeenCalledTimes(1));

    const countAfterComplete = pollCount;

    // Wait a bit longer — polling must have stopped (refetchInterval returns false)
    await new Promise((r) => setTimeout(r, 100));
    expect(pollCount).toBe(countAfterComplete);
    expect(result.current.data?.status).toBe("SUCCEEDED");
  });
});
