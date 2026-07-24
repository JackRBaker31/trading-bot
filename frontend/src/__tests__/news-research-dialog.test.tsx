import React from "react";
import { describe, it, expect } from "vitest";
import { server } from "@/test/handlers";
import { render, screen, waitFor } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { RunNewsResearchDialog } from "@/components/RunNewsResearchDialog";

const BASE = "http://127.0.0.1:8000";

function renderOpenDialog(onStarted = () => {}) {
  render(
    <RunNewsResearchDialog
      open={true}
      onOpenChange={() => {}}
      onStarted={onStarted}
    />,
  );
}

describe("News Research dialog", () => {
  it("shows fixed news provider and controlled defaults", () => {
    renderOpenDialog();

    expect(screen.getByTestId("fixed-news-provider")).toHaveTextContent(
      "Alpha Vantage",
    );
    expect(
      screen.getByTestId("select-market-data-provider"),
    ).toHaveTextContent("Twelve Data");
    expect(screen.getByTestId("select-watchlist")).toHaveTextContent(
      "US Large Cap",
    );
  });

  it("sends the approved watchlist and explicit market-data provider", async () => {
    let capturedBody: Record<string, unknown> | null = null;

    server.use(
      http.post(`${BASE}/api/jobs/news-research`, async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ job_id: "job-watchlist-001" });
      }),
    );

    const user = userEvent.setup();
    renderOpenDialog();

    await user.click(screen.getByTestId("submit-news-research"));

    await waitFor(() => expect(capturedBody).not.toBeNull());

    expect(capturedBody).toEqual({
      watchlist: "data/watchlists/us_large_cap.txt",
      market_data_provider: "TWELVE_DATA",
      max_price_requests: 5,
    });
  });

  it("sends custom symbols without a watchlist", async () => {
    let capturedBody: Record<string, unknown> | null = null;

    server.use(
      http.post(`${BASE}/api/jobs/news-research`, async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ job_id: "job-symbols-001" });
      }),
    );

    const user = userEvent.setup();
    renderOpenDialog();

    await user.click(screen.getByTestId("select-research-target"));
    await user.click(
      screen.getByRole("option", {
        name: /custom symbols/i,
      }),
    );

    const input = screen.getByTestId("input-symbols");
    await user.type(input, "aapl, msft");

    await user.click(screen.getByTestId("submit-news-research"));

    await waitFor(() => expect(capturedBody).not.toBeNull());

    expect(capturedBody).toEqual({
      symbols: ["AAPL", "MSFT"],
      market_data_provider: "TWELVE_DATA",
      max_price_requests: 5,
    });
  });

  it("does not submit empty custom symbols", async () => {
    let called = false;

    server.use(
      http.post(`${BASE}/api/jobs/news-research`, async () => {
        called = true;
        return HttpResponse.json({ job_id: "unexpected" });
      }),
    );

    const user = userEvent.setup();
    renderOpenDialog();

    await user.click(screen.getByTestId("select-research-target"));
    await user.click(
      screen.getByRole("option", {
        name: /custom symbols/i,
      }),
    );

    const submit = screen.getByTestId("submit-news-research");
    expect(submit).toBeDisabled();
    await user.click(submit);

    expect(called).toBe(false);
  });
});
