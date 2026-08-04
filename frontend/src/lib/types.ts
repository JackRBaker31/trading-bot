// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface AuthUser {
  user_id: string;
  username: string;
  role: string;
}

export interface LoginResponse {
  user: AuthUser;
  csrf_token: string;
  session_token: string;
  expires_at: string;
}

// ─── Health ───────────────────────────────────────────────────────────────────

export interface HealthStatus {
  status: string;
}

// ─── Paper Trading ────────────────────────────────────────────────────────────

export interface PaperTradingStatus {
  state: "STOPPED" | "STARTING" | "RUNNING" | "STOP_REQUESTED";
  active: boolean;
  process_id: number | null;
  lock_present: boolean;
  stop_requested: boolean;
  stale_state_cleaned: boolean;
}

// ─── Jobs ─────────────────────────────────────────────────────────────────────

export interface Job {
  job_id: string;
  job_type: string;
  status:
    | "QUEUED"
    | "RUNNING"
    | "SUCCEEDED"
    | "SUCCEEDED_WITH_WARNINGS"
    | "FAILED"
    | "CANCELLED";
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  duration_seconds: number | null;
  payload: Record<string, unknown>;
  result: Record<string, unknown>;
  error_code: string | null;
  error_summary: string | null;
}

// ─── Portfolio ────────────────────────────────────────────────────────────────

export interface Portfolio {
  available: boolean;
  starting_cash: number | null;
  cash: number | null;
  position_count: number;
  positions: Position[];
  applied_broker_order_count: number;
  valuation_available: boolean;
  valuation_note: string;
}

export interface Position {
  symbol: string;
  quantity: number;
}

// ─── Orders ───────────────────────────────────────────────────────────────────

export interface Order {
  timestamp: string;
  reservation_key: string;
  event: string;
  symbol: string;
  side: string;
  quantity: number | null;
  broker_order_id: string | null;
  reason: string | null;
  /** Lifecycle status returned by the backend when present (e.g. PENDING, APPLIED, EXPIRED, CANCELLED) */
  status?: string;
  [key: string]: unknown;
}

// ─── Risk ─────────────────────────────────────────────────────────────────────

export interface RiskStatus {
  max_order_value: number;
  max_position_value: number;
  max_portfolio_exposure_ratio: number;
  max_portfolio_exposure_value: number;
  max_trades_per_session: number;
  approved_symbols: string[];
  paper_trading_enabled: boolean;
  broker_environment: string;
  execution_permission_confirmed: boolean;
  real_money_trading_enabled: boolean;
}

// ─── Reconciliation ───────────────────────────────────────────────────────────

export interface ReconciliationStatus {
  available: boolean;
  latest_run: Record<string, unknown> | null;
  unresolved_order_count: number;
  safe_to_start: boolean;
}

// ─── News ─────────────────────────────────────────────────────────────────────

export interface NewsConfidenceFactor {
  code: string;
  label: string;
  contribution: number;
  detail: string;
}

export interface NewsSignal {
  article_id: string;
  symbol: string;
  headline: string;
  /** float −1.0 (negative) to +1.0 (positive) */
  sentiment: number;
  relevance: number;
  confidence: number;
  confidence_breakdown: NewsConfidenceFactor[];
  event_type: string;
  is_material: boolean;
  published_at: string;
  expires_at: string;
  source: string;
  reasoning_summary: string;
}

export interface NewsOutcome {
  article_id: string;
  symbol: string;
  horizon_name: string;
  signal_published_at: string;
  observed_at: string;
  reference_price: number;
  observed_price: number;
  return_percent: number;
}

export interface NewsSummary {
  total_signals: number;
  total_outcomes: number;
  unmatched_outcomes: number;
  [key: string]: unknown;
}

// ─── Research report ─────────────────────────────────────────────────────────

export interface ResearchReportResponse {
  available: boolean;
  report: Record<string, unknown> | null;
}

// ─── Audit ────────────────────────────────────────────────────────────────────

export interface AuditRecord {
  event_id: string;
  occurred_at: string;
  action: string;
  outcome: string;
  username: string | null;
  source_ip: string | null;
  request_id: string | null;
  target_id: string | null;
  metadata: Record<string, unknown>;
}

// ─── System status ────────────────────────────────────────────────────────────

export interface AppStatus {
  generated_at: string;
  application_mode: string;
  market_data_provider: string;
  configured_symbols: string[];
  real_money_trading_enabled: boolean;
  paper_trading_enabled: boolean;
  broker_environment: string;
  execution_permission_confirmed: boolean;
  market_hours_enforced: boolean;
  news_policy_mode: string;
  news_policy_shadow_mode: boolean;
  news_policy_enforce_mode: boolean;
  portfolio_exists: boolean;
  portfolio_starting_cash: number | null;
  portfolio_cash: number | null;
  position_count: number;
  positions: Record<string, number>;
  unresolved_order_count: number;
  unresolved_order_symbols: string[];
  research_report_exists: boolean;
  latest_research_report_at: string | null;
  news_signal_count: number;
  news_outcome_count: number;
}

// ─── Run history ──────────────────────────────────────────────────────────────

export interface RunHistoryRecord {
  run_id: string;
  run_type: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  duration_seconds: number | null;
  provider: string | null;
  symbols: string[];
  created_count: number;
  skipped_count: number;
  failure_count: number;
  error_code: string | null;
  error_summary: string | null;
  metadata: Record<string, unknown>;
}

// ─── Intelligence Briefing ────────────────────────────────────────────────────

export interface BriefingAction {
  /** Machine-readable type key, e.g. "RUN_NEWS_RESEARCH". Router in DashboardPage switches on this. */
  action_type?: string | null;
  label: string;
  endpoint: string;
  method: string;
  payload: Record<string, unknown> | null;
  description: string | null;
}

/**
 * The backend may return `top_opportunity` as a plain string ticker label
 * OR as a rich signal/opportunity object (shape overlaps with NewsSignal).
 * Always use `renderTopOpportunity()` from DashboardPage before rendering.
 */
export interface TopOpportunityObject {
  symbol?: string;
  ticker?: string;
  headline?: string | null;
  classification?: string | null;
  score?: number | null;
  confidence?: number | null;
  eligible_for_trade?: boolean;
  reasons?: unknown[];
  blocking_reasons?: unknown[];
  article_id?: string;
  [key: string]: unknown;
}

export interface IntelligenceBriefing {
  headline: string | null;
  summary: string | null;
  market_outlook: string | null;
  confidence: number | null;
  trading_readiness: string | null;
  evidence_quality: string | null;
  graduation_status: string | null;
  /** May be a plain string OR a TopOpportunityObject — use renderTopOpportunity() */
  top_opportunity: string | TopOpportunityObject | null;
  warnings: string[];
  actions: BriefingAction[];
  generated_at: string | null;
  [key: string]: unknown;
}

// ─── Intelligence Snapshot ────────────────────────────────────────────────────

export interface TopOpportunity {
  ticker: string;
  classification: string;
  score: number | null;
  confidence: number | null;
  /** Items may be plain strings or objects — use renderReason() before rendering */
  reasons: unknown[];
  /** Items may be plain strings or objects — use renderReason() before rendering */
  blocking_reasons: unknown[];
  material_event: boolean;
  current_status: string | null;
  [key: string]: unknown;
}

export interface IntelligenceSnapshot {
  total_signals: number;
  high_confidence_signals: number;
  material_events: number;
  actionable_signals: number;
  evidence_quality: string | null;
  research_freshness: string | null;
  top_opportunities: TopOpportunity[];
  risk_warnings: string[];
  generated_at: string | null;
  [key: string]: unknown;
}

// ─── Graduation Status ────────────────────────────────────────────────────────

export interface GraduationCheck {
  name: string;
  passed: boolean;
  description: string | null;
}

export interface GraduationStatus {
  stage: string;
  checks_passed: number;
  checks_remaining: number;
  checks: GraduationCheck[];
  [key: string]: unknown;
}

// ─── Shadow Performance ───────────────────────────────────────────────────────

export interface ShadowPeriodStats {
  directional_success: number | null;
  profitable_after_costs: number | null;
  average_return: number | null;
  average_net_return: number | null;
  maximum_drawdown: number | null;
  rolling_stability: number | null;
  coverage: number | null;
  sample_count: number | null;
  [key: string]: unknown;
}

export interface ShadowPerformanceReport {
  available: boolean;
  generated_at: string | null;
  periods: Record<string, ShadowPeriodStats>;
  [key: string]: unknown;
}

// ─── Scheduler ────────────────────────────────────────────────────────────────

export type ScheduleKind = "INTERVAL" | "DAILY" | "WEEKLY";

export type CatchUpPolicy = "SKIP" | "RUN_ONCE" | "RUN_IF_WITHIN_WINDOW";

export type SchedulableTaskType =
  | "NEWS_RESEARCH_CYCLE"
  | "STRATEGY_REPORT"
  | "SHADOW_ANALYSIS"
  | "INTELLIGENCE_CYCLE";

export interface ScheduledTask {
  schedule_id: string;
  task_type: SchedulableTaskType;
  enabled: boolean;
  schedule_kind: ScheduleKind;
  timezone_name: string;
  interval_seconds: number | null;
  local_hour: number | null;
  local_minute: number | null;
  weekday: number | null;
  next_run_at: string | null;
  last_run_at: string | null;
  last_job_id: string | null;
  last_status: string | null;
  payload: Record<string, unknown>;
  catch_up_policy: CatchUpPolicy;
  catch_up_window_seconds: number | null;
  created_at: string;
  updated_at: string;
}

/**
 * Payload sent to POST /api/schedules.
 * Never include next_run_at — the backend calculates it.
 */
export interface ScheduleWriteRequest {
  schedule_id?: string | null;
  task_type: SchedulableTaskType;
  enabled?: boolean;
  schedule_kind: ScheduleKind;
  timezone_name: string;
  interval_seconds?: number | null;
  local_hour?: number | null;
  local_minute?: number | null;
  weekday?: number | null;
  payload: Record<string, unknown>;
  catch_up_policy: CatchUpPolicy;
  catch_up_window_seconds?: number | null;
}

/**
 * Payload sent to PUT /api/schedules/{schedule_id}.
 * All fields optional except those required for the schedule kind.
 * Never include next_run_at.
 */
export type ScheduleUpdateRequest = Partial<
  Omit<ScheduleWriteRequest, "schedule_id">
>;

// ─── Scheduler Status ─────────────────────────────────────────────────────────

export interface SchedulerMetadata {
  worker_name: string | null;
  process_id: number | null;
  heartbeat_age_seconds: number | null;
  /** Job ID currently being executed by the scheduler (not to be confused with job_worker's current_job_id) */
  current_job_id: string | null;
  current_job_type: string | null;
  tasks_processed: number | null;
  started_at: string | null;
  last_error: string | null;
  current_schedule_id: string | null;
  current_task_type: string | null;
}

/**
 * Response from GET /api/scheduler/status.
 * Mirrors InfrastructureServiceStatus shape but with typed metadata.
 */
export interface SchedulerStatusResponse {
  name: string;
  status: string;
  online: boolean;
  detail: string;
  last_updated_at: string | null;
  metadata: SchedulerMetadata;
}

// ─── Infrastructure Status ────────────────────────────────────────────────────

export interface SupervisorMetadata {
  process_id: number | null;
  process_alive: boolean | null;
  restart_enabled: boolean | null;
  managed_process_count: number | null;
  healthy_process_count: number | null;
  recovering_process_count: number | null;
  failed_process_count: number | null;
  status_age_seconds: number | null;
  /** Raw file path — shown only in tooltips, never as a clickable action. */
  status_file: string | null;
}

export interface JobWorkerMetadata {
  worker_name: string | null;
  process_id: number | null;
  heartbeat_age_seconds: number | null;
  current_job_id: string | null;
  current_job_type: string | null;
  jobs_processed: number | null;
  started_at: string | null;
  last_error: string | null;
}

export interface MarketDataMetadata {
  provider?: string;
  status?: string;
  data_source?: string;
  is_stale?: boolean;
  last_updated_at?: string | null;
  age_seconds?: number;
  bar_count?: number;
  warning?: string | null;
  cache_hit_rate_percent?: number;
  live_requests?: number;
  cache_hits?: number;
  stale_fallbacks?: number;
  failed_requests?: number;
  rate_limit_events?: number;
  deduplicated_requests?: number;
  budget_deferrals?: number;
  requests_last_minute?: number;
  requests_today?: number;
  max_requests_per_minute?: number;
  max_requests_per_day?: number;
  cached_entries?: number;
  cached_symbols?: number;
  oldest_cache_age_seconds?: number | null;
  circuit_state?: string;
  circuit_open_until?: string | null;
  last_success_at?: string | null;
  last_failure_at?: string | null;
  last_error?: string | null;
  last_access?: Record<string, unknown>;
}

export interface InfrastructureServiceStatus {
  name: string;
  status: string;
  online: boolean;
  detail: string;
  last_updated_at: string | null;
  metadata: Record<string, unknown>;
}

export interface InfrastructureStatusResponse {
  generated_at: string;
  overall_status: string;
  services: {
    /** Optional — backends prior to supervisor release omit this key. */
    supervisor?: InfrastructureServiceStatus;
    api: InfrastructureServiceStatus;
    storage: InfrastructureServiceStatus;
    job_worker: InfrastructureServiceStatus;
    scheduler: InfrastructureServiceStatus;
    broker: InfrastructureServiceStatus;
    market_data: InfrastructureServiceStatus;
    news: InfrastructureServiceStatus;
  };
}

// ─── Response wrappers ────────────────────────────────────────────────────────

/** Simple list returned by /api/jobs, /api/run-history, /api/audit, /api/positions */
export interface ListResponse<T> {
  count: number;
  items: T[];
}

/** Paginated list returned by /api/orders, /api/news/signals, /api/news/outcomes */
export interface PagedResponse<T> {
  total_count: number;
  offset: number;
  limit: number;
  count: number;
  items: T[];
}


export interface PerformanceReview {
  generated_at: string;
  period: { start: string; end: string; hours: number };
  executive_summary: string;
  system_health: {
    total_jobs: number; intelligence_cycles: number; succeeded: number;
    succeeded_with_warnings: number; failed: number; queued: number;
    abandoned_running: number; completion_rate_percent: number;
    healthy_completion_percent: number; average_cycle_duration_seconds: number;
    longest_cycle_duration_seconds: number; warning_stages: Record<string, number>;
  };
  research_activity: {
    research_runs: number; created_count: number; skipped_count: number;
    failure_count: number; skip_rate_percent: number; articles_fetched: number;
    signals_stored: number; provider_cycles: Record<string, number>;
  };
  decision_intelligence: {
    shadow_decisions: number; eligible_decisions: number; eligibility_rate_percent: number;
    average_confidence_percent: number; actions: Record<string, number>;
    top_symbols: Array<{ symbol: string; count: number }>;
    memory_decisions: number; recommendations: Record<string, number>;
    opportunities_seen: number; decisions_skipped: number;
  };
  shadow_performance: {
    total_decisions: number; measured_1d_decisions: number;
    directional_success_percent: number; profitable_after_cost_percent: number;
    recorded_outcomes: number; outcomes_recorded_by_cycles: number;
    snapshots_captured: number; price_operation_failures: number;
    average_recorded_return_percent: number; opportunities_seen: number;
    decisions_skipped: number;
  };
  confidence_calibration: {
    snapshot_count: number; average_snapshot_confidence_percent: number;
    latest_snapshot_confidence_percent: number; stale_snapshot_percent: number;
    decision_confidence_bands: Record<string, number>;
    calibration_sample_size: number; mean_absolute_calibration_gap_points: number;
    calibration_buckets: Array<{
      label: string; decision_count: number; measured_count: number;
      expected_accuracy_percent: number; actual_accuracy_percent: number;
      calibration_gap_points: number; average_return_percent: number;
    }>;
  };
  sector_analytics: Array<{
    sector: string; decision_count: number; measured_count: number;
    average_confidence_percent: number; directional_accuracy_percent: number;
    average_return_percent: number; eligible_count: number;
  }>;
  symbol_analytics: Array<{
    symbol: string; sector: string; decision_count: number; measured_count: number;
    average_confidence_percent: number; average_score: number;
    directional_accuracy_percent: number; average_return_percent: number;
    eligible_count: number; latest_headline: string;
  }>;
  blocker_analytics: {
    total_blocker_events: number; unique_blockers: number;
    top_blockers: Array<{ reason: string; count: number; symbol_count: number; symbols: string[] }>;
  };
  trends: Array<{
    date: string; cycles: number; healthy_cycles: number; failed_cycles: number;
    created: number; skipped: number; decisions: number; measured_outcomes: number;
    cycle_duration_seconds: number;
  }>;
  maturity: {
    score_percent: number; label: string; graduation_passed_checks: number;
    graduation_total_checks: number; trading_readiness: string; evidence_quality: string;
    components: Record<string, number>;
  };
  insights: string[];
  markdown: string;
}


export interface ResearchLabBrief {
  generated_at: string;
  period: { start: string; end: string; hours: number };
  status: "EVIDENCE_BUILDING" | "REVIEW_READY";
  trading_impact: "NONE";
  headline: string;
  summary: string;
  evidence: {
    shadow_decisions: number; measured_1d_decisions: number;
    directional_success_percent: number; profitable_after_cost_percent: number;
    calibration_sample_size: number; healthy_completion_percent: number;
  };
  findings: Array<{ kind: string; title: string; statement: string; sample_size: number; confidence: string }>;
  suggested_experiments: Array<{
    experiment_id: string; title: string; hypothesis: string; status: string; risk: string;
    required_sample: number; current_sample: number; automatic_change: boolean;
  }>;
  sector_leaders: Array<{ sector: string; decision_count: number; measured_count: number; average_confidence_percent: number; directional_accuracy_percent: number; average_return_percent: number; eligible_count: number }>;
  confidence_buckets: Array<{ label: string; decision_count: number; measured_count: number; expected_accuracy_percent: number; actual_accuracy_percent: number; calibration_gap_points: number; average_return_percent: number }>;
  timeline: Array<{ date: string; decisions: number; measured_outcomes: number; healthy_cycles: number; failed_cycles: number }>;
  methodology: { deterministic: boolean; external_language_model: boolean; automatic_model_changes: boolean; minimum_serious_review_sample: number; source: string };
}

export interface ConfidenceCalibrationBucket {
  name: string;
  label: string;
  measured_count: number;
  expected_accuracy_percent: number;
  observed_accuracy_percent: number;
  calibration_gap_points: number;
  absolute_gap_points: number;
  assessment: string;
}

export interface ConfidenceCalibrationReport {
  generated_at: string;
  period_days: 1 | 7 | 30;
  status: string;
  trading_impact: "NONE";
  automatic_model_changes: false;
  summary: {
    sample_size: number;
    mean_absolute_error_points: number;
    previous_error_points: number;
    drift_points: number;
    drift_status: string;
    best_band: string | null;
    weakest_band: string | null;
  };
  buckets: ConfidenceCalibrationBucket[];
  recommendations: Array<{
    code: string;
    title: string;
    reason: string;
    automatic_change: false;
  }>;
  methodology: {
    outcome_horizon: string;
    expected_measure: string;
    observed_measure: string;
    minimum_review_sample: number;
    minimum_band_sample: number;
    deterministic: boolean;
    external_language_model: boolean;
  };
}
