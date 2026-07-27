import {
  useQuery,
} from "@tanstack/react-query";

import {
  apiClient,
} from "@/lib/api-client";
import { MarketDataMetadata } from "@/lib/types";


export interface TechnicalMetric {
  code: string;
  label: string;
  value: number | null;
  display_value: string;
  score: number;
  maximum: number;
  stance: string;
  detail: string;
}


export interface TechnicalAnalysis {
  symbol: string;
  as_of_date: string;
  bar_count: number;
  score: number;
  maximum: number;
  confidence: number;
  stance: string;
  trend: string;
  momentum: string;
  volatility: string;
  volume_confirmation: string;
  price_structure: string;
  latest_close: number;
  metrics: TechnicalMetric[];
  evidence: string[];
  warnings: string[];
  market_data?: MarketDataMetadata;
}


export function useTechnicalAnalysis(
  symbol: string | null,
) {
  return useQuery({
    queryKey: [
      "technical-analysis",
      symbol,
    ],
    queryFn: () =>
      apiClient.get<
        TechnicalAnalysis
      >(
        `/copilot/technical-analysis/${symbol}`,
      ),
    enabled: Boolean(symbol),
    staleTime: 5 * 60_000,
    refetchOnWindowFocus: false,
  });
}
