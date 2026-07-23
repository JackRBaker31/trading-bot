/**
 * Tests for src/lib/api-client.ts
 *
 * Verifies:
 *  - X-CSRF-Token is attached to every state-changing request (POST/PUT/DELETE)
 *  - X-CSRF-Token is NOT attached to safe GET requests
 *  - 422 validation errors surface the FastAPI / Pydantic v2 detail message
 *  - 429 rate-limit errors produce a human-readable message
 */
import { describe, it, expect, beforeEach } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "@/test/handlers";
import {
  apiClient,
  setCsrfToken,
  setSessionToken,
} from "@/lib/api-client";

const BASE = "http://127.0.0.1:8000";

beforeEach(() => {
  // Reset tokens before each test
  setCsrfToken(null);
  setSessionToken(null);
});

// ── CSRF header ───────────────────────────────────────────────────────────────

describe("CSRF token", () => {
  it("is included in POST requests when a token is set", async () => {
    setCsrfToken("my-csrf-token");

    let capturedCsrf: string | null = null;

    server.use(
      http.post(`${BASE}/api/test-csrf`, ({ request }) => {
        capturedCsrf = request.headers.get("X-CSRF-Token");
        return HttpResponse.json({ ok: true });
      }),
    );

    await apiClient.post("/test-csrf", {});
    expect(capturedCsrf).toBe("my-csrf-token");
  });

  it("is included in PUT requests", async () => {
    setCsrfToken("put-csrf");

    let capturedCsrf: string | null = null;

    server.use(
      http.put(`${BASE}/api/test-put`, ({ request }) => {
        capturedCsrf = request.headers.get("X-CSRF-Token");
        return HttpResponse.json({ ok: true });
      }),
    );

    await apiClient.put("/test-put", {});
    expect(capturedCsrf).toBe("put-csrf");
  });

  it("is included in DELETE requests", async () => {
    setCsrfToken("del-csrf");

    let capturedCsrf: string | null = null;

    server.use(
      http.delete(`${BASE}/api/test-del`, ({ request }) => {
        capturedCsrf = request.headers.get("X-CSRF-Token");
        return HttpResponse.json({ ok: true });
      }),
    );

    await apiClient.del("/test-del");
    expect(capturedCsrf).toBe("del-csrf");
  });

  it("is NOT included in GET requests even when a token is set", async () => {
    setCsrfToken("should-not-appear");

    let capturedCsrf: string | null | undefined = undefined;

    server.use(
      http.get(`${BASE}/api/test-get`, ({ request }) => {
        capturedCsrf = request.headers.get("X-CSRF-Token");
        return HttpResponse.json({ ok: true });
      }),
    );

    await apiClient.get("/test-get");
    expect(capturedCsrf).toBeNull();
  });

  it("is omitted from POST when no CSRF token has been set", async () => {
    // token is null (reset in beforeEach)
    let capturedCsrf: string | null = "sentinel";

    server.use(
      http.post(`${BASE}/api/no-token`, ({ request }) => {
        capturedCsrf = request.headers.get("X-CSRF-Token");
        return HttpResponse.json({ ok: true });
      }),
    );

    await apiClient.post("/no-token", {});
    expect(capturedCsrf).toBeNull();
  });
});

// ── 422 validation errors ─────────────────────────────────────────────────────

describe("422 validation errors", () => {
  it("surfaces a FastAPI string detail message", async () => {
    server.use(
      http.post(`${BASE}/api/bad-input`, () =>
        HttpResponse.json(
          { detail: "provider must be TWELVE_DATA or ALPHA_VANTAGE" },
          { status: 422 },
        )
      ),
    );

    await expect(apiClient.post("/bad-input", {})).rejects.toMatchObject({
      status: 422,
      message: "provider must be TWELVE_DATA or ALPHA_VANTAGE",
    });
  });

  it("surfaces the first Pydantic v2 field error message", async () => {
    server.use(
      http.post(`${BASE}/api/pydantic-422`, () =>
        HttpResponse.json(
          {
            detail: [
              { loc: ["body", "symbols"], msg: "field required", type: "missing" },
            ],
          },
          { status: 422 },
        )
      ),
    );

    await expect(apiClient.post("/pydantic-422", {})).rejects.toMatchObject({
      status: 422,
      message: "field required",
    });
  });
});

// ── 429 rate-limit ────────────────────────────────────────────────────────────

describe("429 rate-limit errors", () => {
  it("renders 'Market-data provider rate limit reached'", async () => {
    server.use(
      http.post(`${BASE}/api/rate-limited`, () =>
        new HttpResponse(null, { status: 429 })
      ),
    );

    await expect(apiClient.post("/rate-limited", {})).rejects.toMatchObject({
      status: 429,
      message: "Market-data provider rate limit reached",
    });
  });
});
