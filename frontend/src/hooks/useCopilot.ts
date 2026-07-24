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

export interface CopilotPlatformOverview {
  overall_status: string;
  online_services: number;
  required_services: number;
}

export interface CopilotActivityOverview {
  running_jobs: number;
  queued_jobs: number;
  active_jobs: number;
}

export interface CopilotScheduleOverview {
  task_type: string;
  next_run_at: string;
  schedule_id: string;
}

export interface CopilotLatestFailure {
  job_id: string;
  job_type: string;
  error_code: string | null;
  error_summary: string | null;
  finished_at: string | null;
}

export interface CopilotFailuresOverview {
  recent_count: number;
  latest: CopilotLatestFailure | null;
}

export interface CopilotAttentionItem {
  code: string;
  title: string;
  detail: string;
  severity: string;
}

export interface CopilotOverview {
  generated_at: string;
  overall_status: string;
  platform: CopilotPlatformOverview;
  activity: CopilotActivityOverview;
  schedule: CopilotScheduleOverview | null;
  failures: CopilotFailuresOverview;
  attention_items: CopilotAttentionItem[];
}

export function useCopilotOverview() {
  return useQuery({
    queryKey: ["copilot-overview"],
    queryFn: () =>
      apiClient.get<CopilotOverview>(
        "/copilot/overview",
      ),
    refetchInterval: 15_000,
    refetchOnWindowFocus: true,
  });
}