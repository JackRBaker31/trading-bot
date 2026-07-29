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

export interface OpportunityRankingSnapshot {
  snapshot_id: number;
  captured_at: string;
  last_observed_at: string;
  source: string;
  methodology_version: string;
  symbol: string;
  rank: number;
  opportunity_score: number;
  category: string;
  recommendation: string;
  calibrated_confidence: number;
  expected_return_percent: number | null;
  evidence_coverage_percent: number;
  data_quality: string;
  risk_tier: string;
  eligible_for_execution: boolean;
  historical_match_count: number;
  measured_case_count: number;
  sector: string;
  headline: string;
  component_values: Record<string, number>;
  component_labels: Record<string, string>;
  blockers: string[];
  universe_version_id: string | null;
  universe_size: number | null;
}

export interface OpportunityRankingChange {
  captured_at: string;
  previous_captured_at: string | null;
  score_change: number;
  rank_change: number;
  direction: string;
  summary: string;
  component_changes: Array<{
    code: string;
    label: string;
    change: number;
  }>;
  blockers_added: string[];
  blockers_resolved: string[];
  readiness_changed: boolean;
  previous_eligible_for_execution: boolean | null;
  eligible_for_execution: boolean;
}

export interface OpportunitySymbolHistoryReport {
  generated_at: string;
  symbol: string;
  window_days: number;
  first_seen_at: string | null;
  last_observed_at: string | null;
  snapshot_count: number;
  current_rank: number | null;
  current_score: number | null;
  score_change: number;
  rank_change: number;
  streak_direction: string;
  snapshots: OpportunityRankingSnapshot[];
  changes: OpportunityRankingChange[];
  universe_versions: string[];
  rank_comparability_warning: string | null;
}

export interface OpportunityHistoryOverviewItem {
  symbol: string;
  current_rank: number;
  current_score: number;
  score_change: number;
  rank_change: number;
  eligible_for_execution: boolean;
  category: string;
  last_observed_at: string;
}

export interface OpportunityHistoryOverviewReport {
  generated_at: string;
  window_days: number;
  tracked_symbol_count: number;
  snapshot_count: number;
  latest_observed_at: string | null;
  largest_risers: OpportunityHistoryOverviewItem[];
  largest_fallers: OpportunityHistoryOverviewItem[];
  items: OpportunityHistoryOverviewItem[];
  universe_versions: string[];
  rank_comparability_warning: string | null;
}

export function useOpportunityRanking() {
  return useQuery({
    queryKey: ["opportunity-ranking-v0.10"],
    queryFn: () =>
      apiClient.get<OpportunityRankingReport>("/opportunity-ranking"),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}

export function useOpportunityRankingHistory(
  symbol: string,
  windowDays: 1 | 7 | 30,
) {
  return useQuery({
    queryKey: ["opportunity-ranking-history-v0.10", symbol, windowDays],
    queryFn: () =>
      apiClient.get<OpportunitySymbolHistoryReport>(
        `/opportunity-ranking/history/${encodeURIComponent(symbol)}?window_days=${windowDays}`,
      ),
    enabled: Boolean(symbol),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}

export function useOpportunityRankingHistoryOverview(
  windowDays: 1 | 7 | 30,
) {
  return useQuery({
    queryKey: ["opportunity-ranking-history-overview-v0.10", windowDays],
    queryFn: () =>
      apiClient.get<OpportunityHistoryOverviewReport>(
        `/opportunity-ranking/history?window_days=${windowDays}`,
      ),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}
