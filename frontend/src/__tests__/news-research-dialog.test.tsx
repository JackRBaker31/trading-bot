/**
 * Tests for RunNewsResearchDialog payload shapes:
 * - Symbol mode sends { symbols, provider, max_price_requests } — no watchlist key
 * - Watchlist mode sends { watchlist, provider, max_price_requests } — no symbols key
 * - Empty symbols in symbol mode prevents submission
 * - Form cannot be submitted with an empty body {}
 */
import React from "react";
import { describe, it, expect } from "vitest";
import { server } from "@/test/handlers";
import { render, screen, waitFor } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { RunNewsResearchDialog } from "@/components/RunNewsResearchDialog";

const BASE = "http://127.0.0.1:8000";

// Helper — render the dialog already open (controlled mode)
function renderOpenDialog(onStarted = () => {}) {
  const handleOpenChange = () => {};
  render(
    <RunNewsResearchDialog
      open={true}
      onOpenChange={handleOpenChange}
      onStarted={onStarted}
    />,
  );
}

// ── Symbol mode ───────────────────────────────────────────────────────────────

describe("News Research dialog — symbol mode", () => {
  it("sends { symbols, provider, max_price_requests } and no watchlist key", async () => {
    let capturedBody: Record<string, unknown> | null = null;

    server.use(
      http.post(`${BASE}/api/jobs/news-research`, async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ job_id: "job-sym-001" });
      }),
    );

    const user = userEvent.setup();
    renderOpenDialog();

    // Default mode is "symbols" — type a symbol
    const input = screen.getByTestId("input-target");
    await user.clear(input);
    await user.type(input, "AAPL");

    await user.click(screen.getByTestId("submit-news-research"));

    await waitFor(() => expect(capturedBody).not.toBeNull());

    expect(capturedBody).toMatchObject({
      symbols: ["AAPL"],
      provider: expect.any(String),
      max_price_requests: expect.any(Number),
    });

    // watchlist key must be absent
    expect(capturedBody).not.toHaveProperty("watchlist");
  });

  it("sends multiple symbols as an array", async () => {
    let capturedBody: Record<string, unknown> | null = null;

    server.use(
      http.post(`${BASE}/api/jobs/news-research`, async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ job_id: "job-multi" });
      }),
    );

    const user = userEvent.setup();
    renderOpenDialog();

    const input = screen.getByTestId("input-target");
    await user.clear(input);
    await user.type(input, "AAPL, MSFT, TSLA");

    await user.click(screen.getByTestId("submit-news-research"));

    await waitFor(() => expect(capturedBody).not.toBeNull());

    expect(capturedBody!.symbols).toEqual(["AAPL", "MSFT", "TSLA"]);
  });

  it("does not submit when no symbols are entered (submit button is disabled)", async () => {
    let called = false;

    server.use(
      http.post(`${BASE}/api/jobs/news-research`, async () => {
        called = true;
        return HttpResponse.json({ job_id: "should-not-be-called" });
      }),
    );

    const user = userEvent.setup();
    renderOpenDialog();

    // Input is already empty — ensure it stays empty
    const input = screen.getByTestId("input-target");
    await user.clear(input);

    const submitButton = screen.getByTestId("submit-news-research");
    expect(submitButton).toBeDisabled();

    await user.click(submitButton);

    // Wait a tick to ensure nothing fired
    await new Promise((r) => setTimeout(r, 50));
    expect(called).toBe(false);
  });
});

// ── Watchlist mode ────────────────────────────────────────────────────────────

describe("News Research dialog — watchlist mode", () => {
  it("sends { watchlist, provider, max_price_requests } and no symbols key", async () => {
    let capturedBody: Record<string, unknown> | null = null;

    server.use(
      http.post(`${BASE}/api/jobs/news-research`, async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ job_id: "job-wl-001" });
      }),
    );

    const user = userEvent.setup();
    renderOpenDialog();

    // Switch to watchlist mode via the toggle button
    await user.click(screen.getByTestId("source-type-watchlist"));

    // Enter a watchlist path
    const input = screen.getByTestId("input-target");
    await user.clear(input);
    await user.type(input, "data/watchlists/custom.txt");

    await user.click(screen.getByTestId("submit-news-research"));

    await waitFor(() => expect(capturedBody).not.toBeNull());

    expect(capturedBody).toMatchObject({
      watchlist: "data/watchlists/custom.txt",
      provider: expect.any(String),
      max_price_requests: expect.any(Number),
    });

    // symbols key must be absent
    expect(capturedBody).not.toHaveProperty("symbols");
  });

  it("defaults to the standard watchlist path when the path input is empty", async () => {
    let capturedBody: Record<string, unknown> | null = null;

    server.use(
      http.post(`${BASE}/api/jobs/news-research`, async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ job_id: "job-default-wl" });
      }),
    );

    const user = userEvent.setup();
    renderOpenDialog();

    // Switch to watchlist mode
    await user.click(screen.getByTestId("source-type-watchlist"));

    // Leave the path input empty — should default to us_large_cap.txt
    await user.click(screen.getByTestId("submit-news-research"));

    await waitFor(() => expect(capturedBody).not.toBeNull());

    expect(capturedBody!.watchlist).toBe("data/watchlists/us_large_cap.txt");
  });
});
