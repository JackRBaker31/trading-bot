import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

export interface UniverseVersion {
  version_id: string;
  checksum: string;
  created_at: string;
  source_path: string;
  symbol_count: number;
  groups: Record<string, string[]>;
  symbols: string[];
  previous_version_id: string | null;
  added_symbols: string[];
  removed_symbols: string[];
}

export interface UniverseCycleCoverage {
  coverage_id: number;
  captured_at: string;
  source: string;
  version_id: string;
  requested_count: number;
  processed_count: number;
  skipped_count: number;
  coverage_percent: number;
  processed_symbols: string[];
  skipped_symbols: string[];
}

export interface UniverseGroupSummary {
  name: string;
  symbol_count: number;
  share_percent: number;
  symbols: string[];
}

export interface UniverseGovernanceReport {
  generated_at: string;
  governance_version: string;
  source_path: string;
  current_version: UniverseVersion;
  previous_version: UniverseVersion | null;
  version_count: number;
  group_summaries: UniverseGroupSummary[];
  duplicate_symbols: string[];
  invalid_symbols: string[];
  eligibility_status: string;
  cached_symbol_count: number;
  uncached_symbol_count: number;
  cache_coverage_percent: number;
  cached_symbols: string[];
  uncached_symbols: string[];
  estimated_live_requests: number;
  daily_request_budget: number;
  estimated_budget_percent: number;
  latest_cycle_coverage: UniverseCycleCoverage | null;
  recent_cycle_coverage: UniverseCycleCoverage[];
  versions: UniverseVersion[];
  rank_comparability_warning: string | null;
  warnings: string[];
}

export function useUniverseGovernance() {
  return useQuery({
    queryKey: ["universe-governance-v0.12"],
    queryFn: () =>
      apiClient.get<UniverseGovernanceReport>("/universe-governance"),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}
