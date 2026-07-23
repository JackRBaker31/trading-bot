import React from "react";
import { render, RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Router } from "wouter";
import { Toaster } from "@/components/ui/toaster";

/** Build a fresh QueryClient for every test — no shared cache, no retries. */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });
}

/** Minimal wrapper: QueryClient + in-memory Router. Suitable for most component tests. */
function Providers({ children }: { children: React.ReactNode }) {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <Router base="">
        {children}
        <Toaster />
      </Router>
    </QueryClientProvider>
  );
}

/**
 * Custom render — wraps every test with QueryClient and a wouter Router.
 * Re-exports everything from @testing-library/react so tests only need
 * to import from this file.
 */
const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) => render(ui, { wrapper: Providers, ...options });

export * from "@testing-library/react";
export { customRender as render };
