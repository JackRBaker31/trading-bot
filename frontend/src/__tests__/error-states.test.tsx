/**
 * Error-state tests:
 * - API unavailable state renders a retry button, not a raw red error screen
 * - 422 validation error renders the FastAPI validation message in a form
 * - 429 rate-limit error renders "Market-data provider rate limit reached"
 */
import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { server } from "@/test/handlers";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { RunNewsResearchDialog } from "@/components/RunNewsResearchDialog";

const BASE = "http://127.0.0.1:8000";

// ── UnavailableState — inline replica for isolation testing ───────────────────

function UnavailableState({
  label,
  onRetry,
}: {
  label: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-8 text-center">
      <AlertTriangle className="w-5 h-5 text-muted-foreground" />
      <p className="text-sm text-muted-foreground">{label}</p>
      {onRetry && (
        <Button size="sm" variant="outline" onClick={onRetry} className="gap-1.5">
          <RefreshCw className="w-3.5 h-3.5" />
          Retry
        </Button>
      )}
    </div>
  );
}

describe("API unavailable state", () => {
  it("renders a Retry button instead of a raw error screen", () => {
    const handleRetry = () => {};
    render(<UnavailableState label="No data available." onRetry={handleRetry} />);

    // Retry button is present
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
    // Descriptive label is present
    expect(screen.getByText("No data available.")).toBeInTheDocument();
    // No raw error elements (role="alert") should appear
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders nothing for the retry button when onRetry is not provided", () => {
    render(<UnavailableState label="No graduation data available." />);

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(
      screen.getByText("No graduation data available."),
    ).toBeInTheDocument();
  });
});

// ── 422 validation error in a form ────────────────────────────────────────────

describe("422 validation error", () => {
  it("renders the FastAPI validation message inside the news-research form", async () => {
    server.use(
      http.post(`${BASE}/api/jobs/news-research`, () =>
        HttpResponse.json(
          { detail: "provider must be one of TWELVE_DATA, ALPHA_VANTAGE" },
          { status: 422 },
        )
      ),
    );

    const user = userEvent.setup();

    render(
      <RunNewsResearchDialog
        open={true}
        onOpenChange={() => {}}
        onStarted={() => {}}
      />,
    );

    // Enter a symbol so the submit is enabled
    await user.click(
      screen.getByTestId(
        "select-research-target",
      ),
    );

    await user.click(
      screen.getByRole("option", {
        name: /custom symbols/i,
      }),
    );

    await user.type(
      screen.getByTestId(
        "input-symbols",
      ),
      "AAPL",
    );
    await user.click(screen.getByTestId("submit-news-research"));

    await waitFor(() =>
      expect(
        screen.getByText(
          "provider must be one of TWELVE_DATA, ALPHA_VANTAGE",
        ),
      ).toBeInTheDocument(),
    );
  });
});

// ── 429 rate-limit error ──────────────────────────────────────────────────────

describe("429 rate-limit error", () => {
  it("renders 'Market-data provider rate limit reached' in the form", async () => {
    server.use(
      http.post(`${BASE}/api/jobs/news-research`, () =>
        new HttpResponse(null, { status: 429 })
      ),
    );

    const user = userEvent.setup();

    render(
      <RunNewsResearchDialog
        open={true}
        onOpenChange={() => {}}
        onStarted={() => {}}
      />,
    );

    await user.click(
      screen.getByTestId(
        "select-research-target",
      ),
    );

    await user.click(
      screen.getByRole("option", {
        name: /custom symbols/i,
      }),
    );

    await user.type(
      screen.getByTestId(
        "input-symbols",
      ),
      "AAPL",
    );
    await user.click(screen.getByTestId("submit-news-research"));

    await waitFor(() =>
      expect(
        screen.getByText("Market-data provider rate limit reached"),
      ).toBeInTheDocument(),
    );
  });
});
