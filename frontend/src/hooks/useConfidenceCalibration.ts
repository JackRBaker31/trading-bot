import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { ConfidenceCalibrationReport } from "@/lib/types";

export function useConfidenceCalibration(days: 1 | 7 | 30) {
  return useQuery({
    queryKey: ["confidence-calibration", days],
    queryFn: () => apiClient.get<ConfidenceCalibrationReport>(`/confidence-calibration/report?days=${days}`),
    staleTime: 60_000,
  });
}
