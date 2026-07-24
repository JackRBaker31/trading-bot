import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  apiClient,
} from "@/lib/api-client";


export interface AdaptiveIntelligenceReport {
  generated_at: string;
  execution_mode: string;
  performance: {
    observation_count: number;
    tracked_decision_count: number;
    positive_rate: number | null;
    average_return: number | null;
    average_alpha: number | null;
    best_horizon_days: number | null;
    learning_confidence: number;
    findings: string[];
    confidence_bands: Array<{
      band: string;
      sample_count: number;
      predicted_midpoint: number;
      positive_rate: number | null;
      average_return: number | null;
      average_alpha: number | null;
      calibration_gap: number | null;
    }>;
  };
  portfolio: {
    available_cash: number;
    investable_cash: number;
    maximum_symbol_weight: number;
    unallocated_cash: number;
    warnings: string[];
    allocations: Array<{
      symbol: string;
      constrained_weight: number;
      suggested_value: number;
      score: number;
      confidence: number;
      risk_tier: string;
    }>;
  };
  risk: {
    overall_risk_score: number;
    overall_tier: string;
    dominant_risk: string | null;
    warnings: string[];
    contributions: Array<{
      code: string;
      label: string;
      contribution: number;
      severity: string;
      detail: string;
    }>;
  };
  position_sizes: Array<{
    symbol: string;
    base_value: number;
    calibrated_value: number;
    maximum_value: number;
    eligible: boolean;
    calibration_multiplier: number;
  }>;
  committee: Array<{
    symbol: string;
    final_stance: string;
    consensus_score: number;
    disagreement_score: number;
    confidence: number;
    summary: string;
  }>;
  proposals: Array<{
    proposal_id: string;
    status: string;
    title: string;
    rationale: string;
    target: string;
    proposed_value: number | null;
  }>;
  warnings: string[];
}


export function useAdaptiveIntelligence() {
  return useQuery({
    queryKey: [
      "adaptive-intelligence",
    ],
    queryFn: () =>
      apiClient.get<
        AdaptiveIntelligenceReport
      >(
        "/copilot/adaptive-intelligence",
      ),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}


export function useProposeStrategyEvolution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiClient.post(
        "/copilot/strategy-evolution/propose",
        {},
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: [
          "adaptive-intelligence",
        ],
      });
    },
  });
}
