import {
  useQuery,
} from "@tanstack/react-query";

import {
  apiClient,
} from "@/lib/api-client";


export interface OperationDiagnosticEvent {
  event_id: string;
  job_id: string | null;
  stage: string;
  operation: string;
  occurred_at: string;
  severity: string;
  status: string;
  symbol: string | null;
  provider: string | null;
  error_code: string | null;
  error_summary: string | null;
  retryable: boolean;
  retry_count: number;
  recovered: boolean;
  latency_ms: number | null;
  cache_status: string | null;
  context: Record<string, unknown>;
}


export interface StageDiagnostic {
  stage: string;
  display_name: string;
  status: string;
  duration_ms: number | null;
  detail: Record<string, unknown>;
  warnings: string[];
  events: OperationDiagnosticEvent[];
  event_count: number;
  failure_count: number;
  retry_count: number;
  recovered_count: number;
  cache_hit_count: number;
  average_latency_ms: number | null;
  diagnostics_complete: boolean;
}


export interface JobDiagnosticReport {
  job_id: string;
  job_type: string;
  status: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  trading_impact: string | null;
  stages: StageDiagnostic[];
  warning_count: number;
  failure_count: number;
  retry_count: number;
  recovered_count: number;
  cache_hit_count: number;
  average_latency_ms: number | null;
  diagnostics_complete: boolean;
}


export interface IntelligenceHealthOverview {
  generated_at: string;
  health_status: string;
  recent_job_count: number;
  succeeded_count: number;
  warning_count: number;
  failed_count: number;
  active_count: number;
  operation_failure_count: number;
  recovered_operation_count: number;
  average_job_duration_ms: number | null;
  average_operation_latency_ms: number | null;
  cache_hit_rate: number | null;
  retry_count: number;
  latest_warning:
    OperationDiagnosticEvent | null;
  attention_items: string[];
  recent_jobs: JobDiagnosticReport[];
}


export function useIntelligenceHealth() {
  return useQuery({
    queryKey: [
      "intelligence-health",
    ],
    queryFn: () =>
      apiClient.get<
        IntelligenceHealthOverview
      >(
        "/copilot/intelligence-health",
      ),
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
  });
}


export function useJobDiagnostics(
  jobId: string | null,
) {
  return useQuery({
    queryKey: [
      "job-diagnostics",
      jobId,
    ],
    queryFn: () =>
      apiClient.get<
        JobDiagnosticReport
      >(
        `/jobs/${jobId}/diagnostics`,
      ),
    enabled: Boolean(jobId),
  });
}
