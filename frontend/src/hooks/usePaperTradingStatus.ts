import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { PaperTradingStatus } from "@/lib/types";

export function usePaperTradingStatus() {
  return useQuery({
    queryKey: ["paper-trading-status"],
    queryFn: () => apiClient.get<PaperTradingStatus>("/paper-trading/status"),
    refetchInterval: (query) => {
      const state = query.state?.data?.state;
      // Poll every 2 s while the worker is active or transitioning
      if (state === "RUNNING" || state === "STARTING" || state === "STOP_REQUESTED") {
        return 2000;
      }
      // Slow down to 10 s when idle/stopped
      return 10_000;
    },
  });
}
