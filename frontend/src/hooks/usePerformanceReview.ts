import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { PerformanceReview } from "@/lib/types";

export type ReviewPreset = "24h" | "weekend" | "7d" | "30d";

function rangeForPreset(preset: ReviewPreset): { start: string; end: string } {
  const end = new Date();
  const start = new Date(end);

  if (preset === "24h") start.setHours(start.getHours() - 24);
  if (preset === "7d") start.setDate(start.getDate() - 7);
  if (preset === "30d") start.setDate(start.getDate() - 30);
  if (preset === "weekend") {
    const day = start.getDay();
    const daysSinceFriday = (day + 2) % 7;
    start.setDate(start.getDate() - daysSinceFriday);
    start.setHours(17, 0, 0, 0);
  }

  return { start: start.toISOString(), end: end.toISOString() };
}

export function usePerformanceReview(preset: ReviewPreset) {
  const range = rangeForPreset(preset);
  const params = new URLSearchParams(range);

  return useQuery({
    queryKey: ["performance-review", preset, range.start.slice(0, 13)],
    queryFn: () => apiClient.get<PerformanceReview>(`/performance/review?${params}`),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}
