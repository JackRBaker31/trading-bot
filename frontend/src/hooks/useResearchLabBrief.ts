import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { ResearchLabBrief } from "@/lib/types";

export function useResearchLabBrief(days: 1 | 7 | 30) {
  return useQuery({
    queryKey: ["research-lab-brief", days],
    queryFn: () => apiClient.get<ResearchLabBrief>(`/research-lab/brief?days=${days}`),
    staleTime: 60_000,
  });
}
