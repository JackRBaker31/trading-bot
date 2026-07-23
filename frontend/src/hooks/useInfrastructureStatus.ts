import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { InfrastructureStatusResponse } from "@/lib/types";

export function useInfrastructureStatus() {
  return useQuery({
    queryKey: ["infrastructure-status"],
    queryFn: () => apiClient.get<InfrastructureStatusResponse>("/infrastructure/status"),
    refetchInterval: 5000,
    refetchIntervalInBackground: false,
    retry: false,
  });
}
