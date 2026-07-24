import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  apiClient,
} from "@/lib/api-client";


export interface DecisionOutcomeObservation {
  outcome_id: string;
  decision_id: string;
  symbol: string;
  horizon_days: number;
  target_date: string;
  observed_at: string;
  entry_price: number;
  observed_price: number;
  absolute_return: number;
  benchmark_symbol: string;
  benchmark_entry_price: number;
  benchmark_observed_price: number;
  benchmark_return: number;
  alpha: number;
  maximum_favourable_excursion: number;
  maximum_drawdown: number;
  status: string;
}


export interface DecisionOutcomeOverview {
  generated_at: string;
  tracked_decision_count: number;
  observation_count: number;
  positive_outcome_count: number;
  negative_outcome_count: number;
  average_return: number | null;
  average_alpha: number | null;
  latest:
    DecisionOutcomeObservation[];
}


export interface DecisionOutcomeCaptureResult {
  evaluated_decision_count: number;
  created_observation_count: number;
  skipped_decision_count: number;
  observations:
    DecisionOutcomeObservation[];
}


export function useDecisionOutcomes() {
  return useQuery({
    queryKey: [
      "decision-outcome-overview",
    ],
    queryFn: () =>
      apiClient.get<
        DecisionOutcomeOverview
      >(
        "/copilot/decision-outcomes",
      ),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}


export function useCaptureDecisionOutcomes() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      apiClient.post<
        DecisionOutcomeCaptureResult
      >(
        "/copilot/decision-outcomes/capture",
        {},
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: [
          "decision-outcome-overview",
        ],
      });
    },
  });
}
