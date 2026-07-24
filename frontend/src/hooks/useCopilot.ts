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


export interface CopilotIntelligenceOverview {
  trading_readiness: string;
  market_outlook: string;
  confidence: number;
  signal_count: number;
  actionable_signal_count: number;
  evidence_quality: string;
}


export interface CopilotGraduationCheck {
  name: string;
  passed: boolean;
  reason: string | null;
}


export interface CopilotGraduationOverview {
  ready: boolean;
  passed_checks: number;
  total_checks: number;
  failed_checks: number;
  checks: CopilotGraduationCheck[];
}


export interface CopilotOverview {
  generated_at: string;
  overall_status: string;
  platform: CopilotPlatformOverview;
  activity: CopilotActivityOverview;
  schedule: CopilotScheduleOverview | null;
  failures: CopilotFailuresOverview;
  trading_intelligence: CopilotIntelligenceOverview;
  graduation: CopilotGraduationOverview;
  attention_items: CopilotAttentionItem[];
}


export interface CopilotDecisionSnapshot {
  snapshot_id: string;
  captured_at: string;
  overall_status: string;
  platform_status: string;
  trading_readiness: string;
  market_outlook: string;
  confidence: number;
  signal_count: number;
  actionable_signal_count: number;
  evidence_quality: string;
  graduation_ready: boolean;
  graduation_passed_checks: number;
  graduation_total_checks: number;
  graduation_failed_checks: number;
  decision: string;
  blockers: string[];
}


export interface CopilotMetricChange {
  metric: string;
  previous: number;
  current: number;
  change: number;
  direction: "UP" | "DOWN" | "UNCHANGED";
}


export interface CopilotChangeSummary {
  generated_at: string;
  comparison_available: boolean;
  current: CopilotDecisionSnapshot;
  previous: CopilotDecisionSnapshot | null;
  confidence_change: CopilotMetricChange | null;
  signal_count_change: CopilotMetricChange | null;
  actionable_signal_change: CopilotMetricChange | null;
  graduation_passed_change: CopilotMetricChange | null;
  new_blockers: string[];
  cleared_blockers: string[];
  summary: string;
}



export interface DecisionTraceStage {
  sequence: number;
  stage: string;
  status: string;
  title: string;
  summary: string;
  evidence: string[];
}


export interface DecisionTrace {
  trace_id: string;
  created_at: string;
  symbol: string | null;
  decision: string;
  confidence: number;
  trading_readiness: string;
  graduation_ready: boolean;
  summary: string;
  stages: DecisionTraceStage[];
  blockers: string[];
}



export interface SymbolDecisionStage {
  sequence: number;
  stage: string;
  status: string;
  title: string;
  summary: string;
  evidence: string[];
}


export interface SymbolDecisionTrace {
  trace_id: string;
  captured_at: string;
  symbol: string;
  rank: number;
  decision: string;
  classification: string;
  score: number;
  confidence: number;
  headline: string;
  event_type: string;
  sentiment: string;
  eligible_for_trade: boolean;
  trading_readiness: string;
  graduation_ready: boolean;
  summary: string;
  stages: SymbolDecisionStage[];
  blockers: string[];
}


export interface SymbolDecisionListResponse {
  items: SymbolDecisionTrace[];
}



export interface SymbolDecisionMetricChange {
  metric: string;
  previous: number;
  current: number;
  change: number;
  direction:
    | "IMPROVED"
    | "WORSENED"
    | "UNCHANGED";
}


export interface SymbolDecisionHistorySummary {
  generated_at: string;
  symbol: string;
  comparison_available: boolean;
  current: SymbolDecisionTrace;
  previous: SymbolDecisionTrace | null;
  score_change:
    SymbolDecisionMetricChange | null;
  confidence_change:
    SymbolDecisionMetricChange | null;
  rank_change:
    SymbolDecisionMetricChange | null;
  decision_changed: boolean;
  sentiment_changed: boolean;
  classification_changed: boolean;
  new_blockers: string[];
  cleared_blockers: string[];
  summary: string;
}


export interface SymbolDecisionChangeResponse {
  available: boolean;
  symbol: string;
  summary:
    SymbolDecisionHistorySummary | null;
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



export function useCopilotChangeSummary() {
  return useQuery({
    queryKey: ["copilot-change-summary"],
    queryFn: () =>
      apiClient.get<CopilotChangeSummary>(
        "/copilot/change-summary",
      ),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}



export function useLatestDecisionTrace() {
  return useQuery({
    queryKey: [
      "copilot-decision-trace-latest",
    ],
    queryFn: () =>
      apiClient.get<DecisionTrace>(
        "/copilot/decision-trace/latest",
      ),
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
  });
}



export function useSymbolDecisions() {
  return useQuery({
    queryKey: [
      "copilot-symbol-decisions",
    ],
    queryFn: () =>
      apiClient.get<
        SymbolDecisionListResponse
      >(
        "/copilot/symbol-decisions",
      ),
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
  });
}



export function useSymbolDecisionChangeSummary(
  symbol: string | null,
) {
  return useQuery({
    queryKey: [
      "copilot-symbol-decision-change",
      symbol,
    ],
    queryFn: () =>
      apiClient.get<
        SymbolDecisionChangeResponse
      >(
        `/copilot/symbol-decisions/${symbol}/change-summary`,
      ),
    enabled: Boolean(symbol),
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
}
