import {
  useQuery,
} from "@tanstack/react-query";

import {
  apiClient,
} from "@/lib/api-client";


export interface AdvancedIntelligenceReport {
  generated_at: string;
  execution_mode: string;
  regime: {
    as_of_date: string;
    regime: string;
    trend_state: string;
    volatility_state: string;
    risk_state: string;
    score: number;
    confidence: number;
    buy_threshold: number;
    position_multiplier: number;
    evidence: string[];
    warnings: string[];
  };
  multi_timeframe: Array<{
    symbol: string;
    as_of_date: string;
    composite_score: number;
    confidence: number;
    alignment: string;
    conflict_penalty: number;
    blockers: string[];
    warnings: string[];
    assessments: Array<{
      timeframe: string;
      score: number;
      stance: string;
      trend: string;
      momentum: string;
    }>;
  }>;
  decisions: Array<{
    symbol: string;
    recommendation: string;
    raw_score: number;
    adjusted_score: number;
    raw_confidence: number;
    calibrated_confidence: number;
    regime: string;
    timeframe_alignment: string;
    blockers: string[];
    summary: string;
    contributions: Array<{
      code: string;
      label: string;
      contribution: number;
      direction: string;
      source: string;
      detail: string;
    }>;
  }>;
  calibration: {
    posterior_mean: number;
    credible_lower: number;
    credible_upper: number;
    sample_count: number;
    confidence_weight: number;
  };
  warnings: string[];
}


export function useAdvancedIntelligence() {
  return useQuery({
    queryKey: [
      "advanced-intelligence",
    ],
    queryFn: () =>
      apiClient.get<
        AdvancedIntelligenceReport
      >(
        "/copilot/advanced-intelligence",
      ),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}
