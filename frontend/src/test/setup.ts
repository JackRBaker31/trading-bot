import "@testing-library/jest-dom";
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "./handlers";
import { setSessionExpiredHandler } from "@/lib/api-client";

// ── jsdom shims required by Radix UI components ───────────────────────────────
// Radix UI calls these APIs internally; jsdom does not implement them.
if (typeof HTMLElement !== "undefined") {
  if (!HTMLElement.prototype.hasPointerCapture) {
    HTMLElement.prototype.hasPointerCapture = () => false;
  }
  if (!HTMLElement.prototype.setPointerCapture) {
    HTMLElement.prototype.setPointerCapture = () => {};
  }
  if (!HTMLElement.prototype.releasePointerCapture) {
    HTMLElement.prototype.releasePointerCapture = () => {};
  }
}

// ResizeObserver is used by some Radix UI components for layout measurement.
if (typeof ResizeObserver === "undefined") {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

// scrollIntoView is called by Radix Select when highlighting options.
// jsdom does not implement it; stub it to prevent "not a function" errors.
if (typeof HTMLElement !== "undefined" && !HTMLElement.prototype.scrollIntoView) {
  HTMLElement.prototype.scrollIntoView = () => {};
}

beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
afterEach(() => {
  server.resetHandlers();
  setSessionExpiredHandler(null);
});
afterAll(() => server.close());
