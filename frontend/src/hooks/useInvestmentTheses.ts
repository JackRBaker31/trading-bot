import {
  useQuery,
} from "@tanstack/react-query";

import {
  apiClient,
} from "@/lib/api-client";


export interface ThesisCapabilityAssessment {
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


export interface InvestmentThesis {
  thesis_id: string;
  generated_at: string;
  symbol: string;
  recommendation: string;
  score: number;
  available_score: number;
  available_maximum: number;
  confidence: number;
  confidence_coverage: number;
  risk_tier: string;
  time_horizon: string;
  suggested_position_value: number;
  eligible_for_execution: boolean;
  headline: string;
  primary_driver: string;
  capabilities:
    ThesisCapabilityAssessment[];
  reasons: string[];
  blockers: string[];
  warnings: string[];
}


export interface InvestmentThesisReport {
  generated_at: string;
  thesis_count: number;
  executable_count: number;
  complete_capability_count: number;
  required_capability_count: number;
  theses: InvestmentThesis[];
  platform_blockers: string[];
  warnings: string[];
}


export function useInvestmentTheses() {
  return useQuery({
    queryKey: [
      "investment-theses-v3",
    ],
    queryFn: () =>
      apiClient.get<
        InvestmentThesisReport
      >(
        "/copilot/investment-theses",
      ),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}
