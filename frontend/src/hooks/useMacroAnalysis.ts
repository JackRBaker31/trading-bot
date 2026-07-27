import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { MarketDataMetadata } from "@/lib/types";


export interface MacroMetric {
  code: string;
  label: string;
  value: number | null;
  display_value: string;
  score: number;
  maximum: number;
  stance: string;
  detail: string;
}


export interface MacroAnalysis {
  as_of_date: string;
  score: number;
  maximum: number;
  confidence: number;
  stance: string;
  regime: string;
  broad_market_trend: string;
  growth_leadership: string;
  rate_pressure: string;
  volatility_regime: string;
  metrics: MacroMetric[];
  evidence: string[];
  warnings: string[];
  market_data_health?: MarketDataMetadata;
}


export function useMacroAnalysis() {
  return useQuery({
    queryKey: ["macro-analysis"],
    queryFn: () =>
      apiClient.get<MacroAnalysis>(
        "/copilot/macro-analysis",
      ),
    staleTime: 5 * 60_000,
    refetchOnWindowFocus: false,
  });
}
