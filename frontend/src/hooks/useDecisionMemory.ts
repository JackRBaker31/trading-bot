import {
  useQuery,
} from "@tanstack/react-query";

import {
  apiClient,
} from "@/lib/api-client";


export interface DecisionMemoryCapability {
  capability: string;
  status: string;
  score: number | null;
  maximum: number;
  confidence: number | null;
  stance: string;
  summary: string;
  evidence: string[];
  blockers: string[];
}


export interface DecisionMemoryRecord {
  decision_id: string;
  fingerprint: string;
  captured_at: string;
  thesis_generated_at: string;
  symbol: string;
  recommendation: string;
  score: number;
  confidence: number;
  confidence_coverage: number;
  risk_tier: string;
  time_horizon: string;
  suggested_position_value: number;
  eligible_for_execution: boolean;
  headline: string;
  primary_driver: string;
  capabilities:
    DecisionMemoryCapability[];
  reasons: string[];
  blockers: string[];
  warnings: string[];
  executed: boolean;
  paper_trade_id: string | null;
}


export interface DecisionMemoryOverview {
  generated_at: string;
  total_count: number;
  executable_count: number;
  executed_count: number;
  symbol_count: number;
  latest: DecisionMemoryRecord[];
}


export function useDecisionMemory() {
  return useQuery({
    queryKey: [
      "decision-memory-overview",
    ],
    queryFn: () =>
      apiClient.get<
        DecisionMemoryOverview
      >(
        "/copilot/decision-memory",
      ),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}
