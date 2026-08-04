import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { FeatureContributionReport } from "@/lib/types";

export function useFeatureContributions(days: 7 | 30 | 90 | 365, horizonDays: 1 | 5 | 20) {
  return useQuery({
    queryKey: ["feature-contributions", days, horizonDays],
    queryFn: () => apiClient.get<FeatureContributionReport>(
      `/feature-contributions/report?days=${days}&horizon_days=${horizonDays}`,
    ),
    staleTime: 60_000,
  });
}
