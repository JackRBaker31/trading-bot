import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

export interface OpportunityRankingComponent {
  code: string;
  label: string;
  value: number;
  maximum: number;
  status: string;
  detail: string;
}

export interface RankedOpportunity {
  rank: number;
  symbol: string;
  opportunity_score: number;
  category: string;
  recommendation: string;
  thesis_score: number;
  raw_confidence: number;
  calibrated_confidence: number;
  confidence_sample_count: number;
  expected_return_percent: number | null;
  evidence_coverage_percent: number;
  data_quality: string;
  risk_tier: string;
  eligible_for_execution: boolean;
  historical_match_count: number;
  measured_case_count: number;
  sector: string;
  headline: string;
  generated_at: string;
  components: OpportunityRankingComponent[];
  positive_contributors: string[];
  penalties: string[];
  improvement_actions: string[];
  blockers: string[];
  warnings: string[];
}

export interface OpportunityRankingReport {
  generated_at: string;
  methodology_version: string;
  methodology_summary: string;
  advisory_only: boolean;
  performance_window_days: number;
  ranking_count: number;
  execution_ready_count: number;
  high_potential_blocked_count: number;
  market_data_status: string;
  component_weights: Record<string, number>;
  items: RankedOpportunity[];
  warnings: string[];
}

export function useOpportunityRanking() {
  return useQuery({
    queryKey: ["opportunity-ranking-v0.9"],
    queryFn: () =>
      apiClient.get<OpportunityRankingReport>("/opportunity-ranking"),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}
