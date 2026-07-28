import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

export type RankingValidationHorizon = 1 | 5 | 20;

export interface OpportunityForwardOutcome {
  outcome_id: number;
  snapshot_id: number;
  captured_at: string;
  symbol: string;
  horizon_days: number;
  entry_date: string;
  exit_date: string;
  observed_at: string;
  entry_price: number;
  observed_price: number;
  return_percent: number;
  benchmark_symbol: string;
  benchmark_return_percent: number;
  alpha_percent: number;
  maximum_favourable_excursion_percent: number;
  maximum_drawdown_percent: number;
  status: string;
  original_rank: number;
  opportunity_score: number;
  calibrated_confidence: number;
  expected_return_percent: number | null;
  evidence_coverage_percent: number;
  eligible_for_execution: boolean;
  category: string;
  sector: string;
  historical_match_count: number;
  measured_case_count: number;
}

export interface OpportunityValidationBucket {
  code: string;
  label: string;
  sample_count: number;
  positive_count: number;
  hit_rate_percent: number | null;
  average_return_percent: number | null;
  median_return_percent: number | null;
  average_alpha_percent: number | null;
  median_alpha_percent: number | null;
  average_drawdown_percent: number | null;
}

export interface OpportunityValidationHorizonSummary {
  horizon_days: number;
  label: string;
  sample_count: number;
  pending_count: number;
  positive_count: number;
  hit_rate_percent: number | null;
  average_return_percent: number | null;
  median_return_percent: number | null;
  average_alpha_percent: number | null;
  median_alpha_percent: number | null;
  average_drawdown_percent: number | null;
  top_three_average_return_percent: number | null;
  other_average_return_percent: number | null;
  score_return_correlation: number | null;
  rank_return_correlation: number | null;
  maturity: string;
}

export interface OpportunityRankingValidationReport {
  generated_at: string;
  methodology_version: string;
  methodology_summary: string;
  advisory_only: boolean;
  benchmark_symbol: string;
  selected_horizon_days: RankingValidationHorizon;
  available_horizons: RankingValidationHorizon[];
  tracked_snapshot_count: number;
  measured_outcome_count: number;
  pending_outcome_count: number;
  latest_observed_at: string | null;
  selected_horizon: OpportunityValidationHorizonSummary;
  horizons: OpportunityValidationHorizonSummary[];
  score_bands: OpportunityValidationBucket[];
  rank_buckets: OpportunityValidationBucket[];
  readiness_buckets: OpportunityValidationBucket[];
  symbol_performance: OpportunityValidationBucket[];
  sector_performance: OpportunityValidationBucket[];
  latest_outcomes: OpportunityForwardOutcome[];
  warnings: string[];
}

export function useRankingValidation(horizonDays: RankingValidationHorizon) {
  return useQuery({
    queryKey: ["ranking-validation-v0.11", horizonDays],
    queryFn: () =>
      apiClient.get<OpportunityRankingValidationReport>(
        `/opportunity-ranking/validation?horizon_days=${horizonDays}`,
      ),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}
