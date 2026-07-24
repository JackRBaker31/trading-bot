import {
  useQuery,
} from "@tanstack/react-query";

import {
  apiClient,
} from "@/lib/api-client";

export interface DecisionScoreComponent {
  code: string;
  label: string;
  value: number;
  maximum: number;
  detail: string;
}


export interface InvestmentDecision {
  symbol: string;
  generated_at: string;
  recommendation: string;
  score: number;
  confidence: number;
  risk_tier: string;
  suggested_position_value: number;
  eligible_for_execution: boolean;
  headline: string;
  event_type: string;
  sentiment: string;
  classification: string;
  components: DecisionScoreComponent[];
  reasons: string[];
  blockers: string[];
  warnings: string[];
}


export interface DecisionIntelligenceReport {
  generated_at: string;
  trading_readiness: string;
  graduation_eligible: boolean;
  decision_count: number;
  executable_candidate_count: number;
  decisions: InvestmentDecision[];
  platform_blockers: string[];
  warnings: string[];
}


export function useDecisionIntelligence() {
  return useQuery({
    queryKey: [
      "decision-intelligence-v2",
    ],
    queryFn: () =>
      apiClient.get<
        DecisionIntelligenceReport
      >(
        "/copilot/investment-decisions",
      ),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}
