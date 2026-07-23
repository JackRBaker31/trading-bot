import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Job } from "@/lib/types";

export function useJobPolling(jobId: string | null | undefined) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: () => apiClient.get<Job>(`/jobs/${jobId}`),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state?.data?.status;
      if (status === "QUEUED" || status === "RUNNING") {
        return 2000;
      }
      return false;
    },
  });
}
