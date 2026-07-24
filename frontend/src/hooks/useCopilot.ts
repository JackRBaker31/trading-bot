import {
  useMutation,
  useQuery,
} from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";


export type CopilotSuggestionKind =
  | "warning"
  | "info"
  | "success"
  | "action";


export interface CopilotSuggestion {
  title: string;
  message: string;
  kind: CopilotSuggestionKind;
}


export interface CopilotResponse {
  summary: string;
  suggestions: CopilotSuggestion[];
}


export interface CopilotSuggestionsResponse {
  items: string[];
}


export function useCopilotSuggestions() {
  return useQuery({
    queryKey: ["copilot-suggestions"],
    queryFn: () =>
      apiClient.get<CopilotSuggestionsResponse>(
        "/copilot/suggestions",
      ),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
}


export function useCopilotQuery() {
  return useMutation({
    mutationFn: (
      question: string,
    ) =>
      apiClient.post<CopilotResponse>(
        "/copilot/query",
        {
          question,
        },
      ),
  });
}