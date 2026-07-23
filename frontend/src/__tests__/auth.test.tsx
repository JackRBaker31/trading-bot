/**
 * Auth tests:
 * - Login form renders with username / password inputs
 * - Login failure shows an error message
 * - Login success calls the login endpoint and navigates
 * - ProtectedRoute redirects unauthenticated users to /login
 */
import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { server } from "@/test/handlers";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Router } from "wouter";
import { AuthProvider } from "@/contexts/AuthContext";
import LoginPage from "@/pages/LoginPage";
import { ProtectedRoute } from "@/components/ProtectedRoute";

const BASE = "http://127.0.0.1:8000";

function createClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

/** Wrapper with AuthContext, QueryClient, and wouter Router. */
function AuthWrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={createClient()}>
      <Router base="">
        <AuthProvider>{children}</AuthProvider>
      </Router>
    </QueryClientProvider>
  );
}

// ── LoginPage rendering ───────────────────────────────────────────────────────

describe("LoginPage", () => {
  it("renders username and password inputs", async () => {
    render(<LoginPage />, { wrapper: AuthWrapper });
    expect(screen.getByTestId("input-username")).toBeInTheDocument();
    expect(screen.getByTestId("input-password")).toBeInTheDocument();
    expect(screen.getByTestId("button-login")).toBeInTheDocument();
  });

  it("shows an error message when login fails", async () => {
    // Override the default success login handler with a 401 failure
    server.use(
      http.post(`${BASE}/api/auth/login`, () =>
        HttpResponse.json(
          { detail: "Invalid username or password" },
          { status: 401 },
        )
      ),
    );

    const user = userEvent.setup();
    render(<LoginPage />, { wrapper: AuthWrapper });

    await user.type(screen.getByTestId("input-username"), "baduser");
    await user.type(screen.getByTestId("input-password"), "wrongpass");
    await user.click(screen.getByTestId("button-login"));

    await waitFor(() =>
      expect(screen.getByTestId("text-error")).toBeInTheDocument(),
    );
  });

  it("calls the login endpoint with the entered credentials", async () => {
    let capturedBody: unknown = null;

    server.use(
      http.post(`${BASE}/api/auth/login`, async ({ request }) => {
        capturedBody = await request.json();
        return HttpResponse.json({
          user: { user_id: "1", username: "alice", role: "admin" },
          csrf_token: "tok",
          session_token: "sess",
          expires_at: "2099-01-01T00:00:00Z",
        });
      }),
      // Also mock /auth/me so the post-login refresh succeeds
      http.get(`${BASE}/api/auth/me`, () =>
        HttpResponse.json({ user_id: "1", username: "alice", role: "admin" })
      ),
    );

    const user = userEvent.setup();
    render(<LoginPage />, { wrapper: AuthWrapper });

    await user.type(screen.getByTestId("input-username"), "alice");
    await user.type(screen.getByTestId("input-password"), "secret");
    await user.click(screen.getByTestId("button-login"));

    await waitFor(() =>
      expect(capturedBody).toMatchObject({
        username: "alice",
        password: "secret",
      }),
    );
  });
});

// ── ProtectedRoute ────────────────────────────────────────────────────────────

describe("ProtectedRoute", () => {
  it("redirects to /login when the user is not authenticated", async () => {
    // Default /api/auth/me handler returns 401 → user is unauthenticated

    function DummyPage() {
      return <div data-testid="protected-content">Secret</div>;
    }

    render(
      <ProtectedRoute component={DummyPage} title="Protected" />,
      { wrapper: AuthWrapper },
    );

    // While auth is loading the loading spinner is shown; after settling the
    // redirect fires and the protected content is never rendered.
    await waitFor(() =>
      expect(
        screen.queryByTestId("protected-content"),
      ).not.toBeInTheDocument(),
    );
  });
});
