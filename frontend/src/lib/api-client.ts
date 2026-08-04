const SESSION_STORAGE_KEY = "kairo_session_token";
const CSRF_STORAGE_KEY = "kairo_csrf_token";

let csrfTokenStore: string | null = null;
let sessionTokenStore: string | null = null;

// Called when any API request receives a 401. Registered by AuthContext so
// navigation can happen from within the React tree.
let sessionExpiredHandler: (() => void) | null = null;

export function setSessionExpiredHandler(handler: (() => void) | null) {
  sessionExpiredHandler = handler;
}

// Restore tokens from sessionStorage on module load (survives page refresh,
// cleared when the tab is closed).
try {
  sessionTokenStore = sessionStorage.getItem(SESSION_STORAGE_KEY);
  csrfTokenStore = sessionStorage.getItem(CSRF_STORAGE_KEY);
} catch {
  // sessionStorage unavailable (e.g. private-browsing restriction) — fall back to memory only.
}

export function setCsrfToken(token: string | null) {
  csrfTokenStore = token;
  try {
    if (token === null) {
      sessionStorage.removeItem(CSRF_STORAGE_KEY);
    } else {
      sessionStorage.setItem(CSRF_STORAGE_KEY, token);
    }
  } catch {
    // ignore
  }
}

export function getCsrfToken() {
  return csrfTokenStore;
}

export function setSessionToken(token: string | null) {
  sessionTokenStore = token;
  try {
    if (token === null) {
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
    } else {
      sessionStorage.setItem(SESSION_STORAGE_KEY, token);
    }
  } catch {
    // ignore
  }
}

export function getSessionToken() {
  return sessionTokenStore;
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Extract a human-readable message from a Python FastAPI or Pydantic error body. */
function extractErrorMessage(data: unknown, fallback: string): string {
  if (!data || typeof data !== "object") return fallback;
  const d = data as Record<string, unknown>;
  // FastAPI application errors: { error: { code, message, retryable } }
  if (d.error && typeof d.error === "object") {
    const e = d.error as Record<string, unknown>;
    if (typeof e.message === "string") return e.message;
  }
  // FastAPI validation errors: { detail: "..." }
  if (typeof d.detail === "string") return d.detail;
  // Pydantic v2 validation errors: { detail: [{ loc, msg, type }, ...] }
  if (Array.isArray(d.detail) && d.detail.length > 0) {
    const first = d.detail[0] as Record<string, unknown>;
    if (typeof first.msg === "string") return first.msg;
  }
  return fallback;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = path.startsWith("/health")
    ? `${BASE_URL}${path}`
    : `${BASE_URL}/api${path.startsWith("/") ? path : `/${path}`}`;

  const headers = new Headers(options.headers || {});

  // Always send the session token as a header — this bypasses SameSite=Lax
  // restrictions that block cookies on cross-origin POST requests.
  const sessionToken = getSessionToken();
  if (sessionToken) {
    headers.set("X-Session-Token", sessionToken);
  }

  if (
    options.method &&
    ["POST", "PUT", "PATCH", "DELETE"].includes(options.method.toUpperCase())
  ) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers.set("X-CSRF-Token", csrfToken);
    }
  }

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      // non-JSON body
    }

    if (response.status === 401) {
      setCsrfToken(null);
      setSessionToken(null);
      sessionExpiredHandler?.();
      throw new ApiError(401, "Session expired — please log in again.");
    }
    if (response.status === 403) {
      throw new ApiError(
        403,
        extractErrorMessage(errorData, "CSRF or permission error"),
        errorData,
      );
    }
    if (response.status === 409) {
      throw new ApiError(
        409,
        extractErrorMessage(errorData, "Conflict — worker may already be active"),
        errorData,
      );
    }
    if (response.status === 422) {
      throw new ApiError(
        422,
        extractErrorMessage(errorData, "Validation error — check the request payload"),
        errorData,
      );
    }
    if (response.status === 429) {
      throw new ApiError(429, "Market-data provider rate limit reached");
    }
    if (response.status === 503) {
      throw new ApiError(503, "Service temporarily unavailable");
    }

    throw new ApiError(
      response.status,
      extractErrorMessage(errorData, "An unexpected error occurred"),
      errorData,
    );
  }

  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return response.json();
  }

  throw new ApiError(
    response.status,
    "The API returned a non-JSON response. Check the configured API base URL.",
    { contentType },
  );
}

export const apiClient = {
  get: <T>(path: string, options?: RequestInit) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: RequestInit) =>
    request<T>(path, {
      ...options,
      method: "POST",
      body: body != null ? JSON.stringify(body) : undefined,
    }),
  put: <T>(path: string, body?: unknown, options?: RequestInit) =>
    request<T>(path, {
      ...options,
      method: "PUT",
      body: body != null ? JSON.stringify(body) : undefined,
    }),
  del: <T>(path: string, options?: RequestInit) =>
    request<T>(path, { ...options, method: "DELETE" }),
};
