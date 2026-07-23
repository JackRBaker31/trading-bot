import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { HealthStatus } from "@/lib/types";

export function useBackendHealth() {
  return useQuery({
    queryKey: ["health-live"],
    queryFn: () => apiClient.get<HealthStatus>("/health/live"),
    refetchInterval: 30000,
    retry: false,
  });
}
