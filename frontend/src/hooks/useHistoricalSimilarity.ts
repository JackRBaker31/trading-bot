import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

export interface SimilarityFeatureComparison {
  code: string;
  label: string;
  current_value: string;
  historical_value: string;
  similarity_percent: number;
  weight: number;
  contribution_points: number;
}

export interface SimilarityOutcome {
  horizon_days: number;
  observed_at: string;
  raw_return_percent: number;
  directional_return_percent: number;
  alpha_percent: number;
  maximum_favourable_excursion_percent: number;
  maximum_drawdown_percent: number;
  directional_success: boolean;
  status: string;
}

export interface HistoricalSimilarityCase {
  decision_id: string;
  symbol: string;
  captured_at: string;
  thesis_generated_at: string;
  recommendation: string;
  score: number;
  confidence: number;
  risk_tier: string;
  time_horizon: string;
  headline: string;
  primary_driver: string;
  similarity_percent: number;
  same_symbol: boolean;
  matching_factors: string[];
  differing_factors: string[];
  feature_comparisons: SimilarityFeatureComparison[];
  outcome: SimilarityOutcome | null;
}

export interface HistoricalSimilarityReport {
  generated_at: string;
  symbol: string;
  current_thesis_id: string;
  current_recommendation: string;
  current_score: number;
  current_confidence: number;
  current_risk_tier: string;
  current_time_horizon: string;
  current_primary_driver: string;
  methodology_version: string;
  methodology_summary: string;
  minimum_similarity_percent: number;
  target_horizon_days: number;
  candidate_count: number;
  matched_case_count: number;
  measured_case_count: number;
  sample_quality: string;
  average_similarity_percent: number | null;
  win_rate_percent: number | null;
  average_return_percent: number | null;
  median_return_percent: number | null;
  average_directional_return_percent: number | null;
  average_alpha_percent: number | null;
  best_directional_return_percent: number | null;
  worst_directional_return_percent: number | null;
  average_holding_days: number | null;
  cases: HistoricalSimilarityCase[];
  warnings: string[];
}

export function useHistoricalSimilarity(symbol: string | null, enabled = true) {
  return useQuery({
    queryKey: ["historical-similarity-v1", symbol],
    queryFn: () =>
      apiClient.get<HistoricalSimilarityReport>(
        `/copilot/historical-similarity/${encodeURIComponent(symbol ?? "")}`,
      ),
    enabled: Boolean(symbol) && enabled,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}
