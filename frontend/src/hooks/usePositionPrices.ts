import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { PagedResponse, NewsOutcome } from "@/lib/types";

/**
 * For a list of symbols, fetches the most recent observed price from news
 * outcomes. Returns a map of symbol -> latest observed_price, or an empty map
 * if no outcome data is available.
 *
 * This is the best available price source without a dedicated prices endpoint
 * — outcomes are recorded when the research cycle runs and carry the real
 * market price at that moment.
 */
export function usePositionPrices(
  symbols: string[],
  refetchInterval = 30000,
) {
  return useQuery({
    queryKey: ["position-prices", symbols.slice().sort().join(",")],
    queryFn: async (): Promise<Record<string, number>> => {
      if (symbols.length === 0) return {};

      // Fetch up to 200 outcomes so we can find the most recent per symbol.
      const resp = await apiClient.get<PagedResponse<NewsOutcome>>(
        "/news/outcomes?limit=200",
      );
      const outcomes = resp?.items ?? [];

      // Build symbol -> latest observed_price (most recent observed_at wins).
      const priceMap: Record<string, { price: number; at: string }> = {};
      for (const o of outcomes) {
        if (!symbols.includes(o.symbol)) continue;
        const existing = priceMap[o.symbol];
        if (!existing || o.observed_at > existing.at) {
          priceMap[o.symbol] = { price: o.observed_price, at: o.observed_at };
        }
      }

      return Object.fromEntries(
        Object.entries(priceMap).map(([sym, v]) => [sym, v.price]),
      );
    },
    enabled: symbols.length > 0,
    refetchInterval,
    // Don't throw — return empty map on any error so callers fall back cleanly.
    retry: false,
  });
}
