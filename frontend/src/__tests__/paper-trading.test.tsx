/**
 * PaperTradingPage confirmation modal tests:
 *
 * - "Start DEMO Paper Trading" button opens a modal before any POST fires
 * - The modal copy matches the brief
 * - Clicking "Confirm Start" in the modal fires POST /paper-trading/start
 * - Clicking Cancel does NOT fire the POST
 * - "Request Graceful Stop" button opens a modal before any POST fires
 * - Clicking "Confirm Stop" fires POST /paper-trading/stop
 */
import React from "react";
import { describe, it, expect, beforeEach } from "vitest";
import { server } from "@/test/handlers";
import { render, screen, waitFor, within } from "@/test/test-utils";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import PaperTradingPage from "@/pages/PaperTradingPage";

const BASE = "http://127.0.0.1:8000";

// ── Start flow ────────────────────────────────────────────────────────────────

describe("Paper Trading — Start flow", () => {
  beforeEach(() => {
    // Default handler: worker is STOPPED
    server.use(
      http.get(`${BASE}/api/paper-trading/status`, () =>
        HttpResponse.json({
          state: "STOPPED",
          active: false,
          process_id: null,
          lock_present: false,
          stop_requested: false,
          stale_state_cleaned: false,
        })
      ),
    );
  });

  it("opens a confirmation modal when the Start button is clicked", async () => {
    const user = userEvent.setup();
    render(<PaperTradingPage />);

    // Wait for the page to render with the STOPPED state
    const startBtn = await screen.findByTestId("button-start");
    await user.click(startBtn);

    // Dialog should now be visible
    expect(await screen.findByTestId("dialog-confirm-start")).toBeInTheDocument();
  });

  it("shows the correct modal copy before confirming", async () => {
    const user = userEvent.setup();
    render(<PaperTradingPage />);

    const startBtn = await screen.findByTestId("button-start");
    await user.click(startBtn);

    // Wait for the dialog to open, then check copy WITHIN the dialog to avoid
    // false positives from the button that shares the same label text.
    const dialog = await screen.findByTestId("dialog-confirm-start");

    expect(within(dialog).getByText("Start DEMO Paper Trading")).toBeInTheDocument();
    expect(
      within(dialog).getByText(
        /This will start automatic Trading 212 DEMO paper trading\. Real-money trading remains disabled\./,
      ),
    ).toBeInTheDocument();
  });

  it("does NOT fire the POST until the user confirms in the modal", async () => {
    let postFired = false;

    server.use(
      http.post(`${BASE}/api/paper-trading/start`, () => {
        postFired = true;
        return HttpResponse.json({ status: "starting" });
      }),
    );

    const user = userEvent.setup();
    render(<PaperTradingPage />);

    const startBtn = await screen.findByTestId("button-start");
    await user.click(startBtn);

    // Modal is open but POST must not have fired yet
    await screen.findByTestId("dialog-confirm-start");
    expect(postFired).toBe(false);
  });

  it("fires POST /paper-trading/start after clicking Confirm Start", async () => {
    let postFired = false;

    server.use(
      http.post(`${BASE}/api/paper-trading/start`, () => {
        postFired = true;
        return HttpResponse.json({ status: "starting" });
      }),
    );

    const user = userEvent.setup();
    render(<PaperTradingPage />);

    const startBtn = await screen.findByTestId("button-start");
    await user.click(startBtn);

    await screen.findByTestId("dialog-confirm-start");
    await user.click(screen.getByRole("button", { name: /confirm start/i }));

    await waitFor(() => expect(postFired).toBe(true));
  });

  it("does NOT fire the POST when the user cancels", async () => {
    let postFired = false;

    server.use(
      http.post(`${BASE}/api/paper-trading/start`, () => {
        postFired = true;
        return HttpResponse.json({ status: "starting" });
      }),
    );

    const user = userEvent.setup();
    render(<PaperTradingPage />);

    const startBtn = await screen.findByTestId("button-start");
    await user.click(startBtn);

    await screen.findByTestId("dialog-confirm-start");
    await user.click(screen.getByRole("button", { name: /cancel/i }));

    await new Promise((r) => setTimeout(r, 50));
    expect(postFired).toBe(false);
  });
});

// ── Stop flow ──────────────────────────────────────────────────────────────────

describe("Paper Trading — Stop flow", () => {
  beforeEach(() => {
    // Override: worker is RUNNING
    server.use(
      http.get(`${BASE}/api/paper-trading/status`, () =>
        HttpResponse.json({
          state: "RUNNING",
          active: true,
          process_id: 12345,
          lock_present: true,
          stop_requested: false,
          stale_state_cleaned: false,
        })
      ),
    );
  });

  it("opens a confirmation modal when the Stop button is clicked", async () => {
    const user = userEvent.setup();
    render(<PaperTradingPage />);

    const stopBtn = await screen.findByTestId("button-stop");
    await user.click(stopBtn);

    expect(await screen.findByTestId("dialog-confirm-stop")).toBeInTheDocument();
  });

  it("shows the correct modal copy for the stop flow", async () => {
    const user = userEvent.setup();
    render(<PaperTradingPage />);

    const stopBtn = await screen.findByTestId("button-stop");
    await user.click(stopBtn);

    expect(
      await screen.findByText(
        /The worker will complete its current cycle before stopping\./,
      ),
    ).toBeInTheDocument();
  });

  it("does NOT fire the POST until the user confirms", async () => {
    let postFired = false;

    server.use(
      http.post(`${BASE}/api/paper-trading/stop`, () => {
        postFired = true;
        return HttpResponse.json({ status: "stopping" });
      }),
    );

    const user = userEvent.setup();
    render(<PaperTradingPage />);

    const stopBtn = await screen.findByTestId("button-stop");
    await user.click(stopBtn);

    await screen.findByTestId("dialog-confirm-stop");
    expect(postFired).toBe(false);
  });

  it("fires POST /paper-trading/stop after clicking Confirm Stop", async () => {
    let postFired = false;

    server.use(
      http.post(`${BASE}/api/paper-trading/stop`, () => {
        postFired = true;
        return HttpResponse.json({ status: "stopping" });
      }),
    );

    const user = userEvent.setup();
    render(<PaperTradingPage />);

    const stopBtn = await screen.findByTestId("button-stop");
    await user.click(stopBtn);

    await screen.findByTestId("dialog-confirm-stop");
    await user.click(screen.getByRole("button", { name: /confirm stop/i }));

    await waitFor(() => expect(postFired).toBe(true));
  });
});
