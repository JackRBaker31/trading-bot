import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

const BASE = "http://127.0.0.1:8000";

export const handlers = [
  // ── Auth ──────────────────────────────────────────────────────────────────
  http.get(`${BASE}/api/auth/me`, () =>
    new HttpResponse(null, { status: 401 })
  ),
  http.post(`${BASE}/api/auth/login`, () =>
    HttpResponse.json({
      user: { user_id: "1", username: "testuser", role: "admin" },
      csrf_token: "test-csrf-token",
      session_token: "test-session-token",
      expires_at: "2099-01-01T00:00:00Z",
    })
  ),

  // ── App status ─────────────────────────────────────────────────────────────
  http.get(`${BASE}/api/status`, () =>
    HttpResponse.json({
      generated_at: new Date().toISOString(),
      application_mode: "PAPER",
      market_data_provider: "TWELVE_DATA",
      configured_symbols: [],
      real_money_trading_enabled: false,
      paper_trading_enabled: true,
      broker_environment: "DEMO",
      execution_permission_confirmed: true,
      market_hours_enforced: false,
      news_policy_mode: "SHADOW",
      news_policy_shadow_mode: true,
      news_policy_enforce_mode: false,
      portfolio_exists: true,
      portfolio_starting_cash: 10000,
      portfolio_cash: 10000,
      position_count: 0,
      positions: {},
      unresolved_order_count: 0,
      unresolved_order_symbols: [],
      research_report_exists: false,
      latest_research_report_at: null,
      news_signal_count: 0,
      news_outcome_count: 0,
    })
  ),

  // ── Infrastructure ─────────────────────────────────────────────────────────
  http.get(`${BASE}/api/infrastructure/status`, () =>
    HttpResponse.json({
      generated_at: new Date().toISOString(),
      overall_status: "HEALTHY",
      services: {
        api: { name: "api", status: "ONLINE", online: true, detail: "", last_updated_at: null, metadata: {} },
        storage: { name: "storage", status: "ONLINE", online: true, detail: "", last_updated_at: null, metadata: {} },
        supervisor: { name: "supervisor", status: "RUNNING", online: true, detail: "KAIRO process supervision and automatic recovery are active.", last_updated_at: "2026-07-22T14:49:22Z", metadata: { process_id: 22564, process_alive: true, restart_enabled: true, managed_process_count: 3, healthy_process_count: 3, recovering_process_count: 0, failed_process_count: 0, status_age_seconds: 0.5, status_file: "data\\supervisor_status.json" } },
        job_worker: { name: "job_worker", status: "IDLE", online: true, detail: "", last_updated_at: null, metadata: { worker_name: null, process_id: null, heartbeat_age_seconds: null, current_job_id: null, current_job_type: null, jobs_processed: null, started_at: null, last_error: null } },
        scheduler: { name: "scheduler", status: "IDLE", online: true, detail: "", last_updated_at: null, metadata: { worker_name: null, process_id: null, heartbeat_age_seconds: null, current_job_id: null, current_job_type: null, tasks_processed: null, started_at: null, last_error: null, current_schedule_id: null, current_task_type: null } },
        broker: { name: "broker", status: "ONLINE", online: true, detail: "", last_updated_at: null, metadata: {} },
        market_data: { name: "market_data", status: "ONLINE", online: true, detail: "", last_updated_at: null, metadata: {} },
        news: { name: "news", status: "ONLINE", online: true, detail: "", last_updated_at: null, metadata: {} },
      },
    })
  ),

  // ── Paper trading ──────────────────────────────────────────────────────────
  http.get(`${BASE}/api/paper-trading/status`, () =>
    HttpResponse.json({
      state: "STOPPED",
      active: false,
      process_id: null,
      lock_present: false,
      stop_requested: false,
      stale_state_cleaned: false,
    })
  ),
  http.post(`${BASE}/api/paper-trading/start`, () =>
    HttpResponse.json({ status: "starting" })
  ),
  http.post(`${BASE}/api/paper-trading/stop`, () =>
    HttpResponse.json({ status: "stopping" })
  ),

  // ── Jobs ──────────────────────────────────────────────────────────────────
  http.get(`${BASE}/api/jobs`, () =>
    HttpResponse.json({ count: 0, items: [] })
  ),
  http.post(`${BASE}/api/jobs/news-research`, () =>
    HttpResponse.json({ job_id: "job-news-001" })
  ),
  http.post(`${BASE}/api/jobs/strategy-report`, () =>
    HttpResponse.json({ job_id: "job-strategy-001" })
  ),
  http.post(`${BASE}/api/jobs/shadow-analysis`, () =>
    HttpResponse.json({ job_id: "job-shadow-001" })
  ),

  // ── Research ──────────────────────────────────────────────────────────────
  http.get(`${BASE}/api/research/latest`, () =>
    HttpResponse.json({ available: false, report: null })
  ),

  // ── Reconciliation ─────────────────────────────────────────────────────────
  http.get(`${BASE}/api/reconciliation/latest`, () =>
    HttpResponse.json({
      available: true,
      latest_run: null,
      unresolved_order_count: 0,
      safe_to_start: true,
    })
  ),

  // ── Risk ──────────────────────────────────────────────────────────────────
  http.get(`${BASE}/api/risk/status`, () =>
    HttpResponse.json({ status: "OK", limits: [], approved_symbols: [] })
  ),

  // ── Market status ─────────────────────────────────────────────────────────
  http.get(`${BASE}/api/market-status`, () =>
    HttpResponse.json({ is_open: false, session: "CLOSED" })
  ),

  // ── Intelligence ──────────────────────────────────────────────────────────
  http.get(`${BASE}/api/intelligence/briefing`, () =>
    new HttpResponse(null, { status: 404 })
  ),
  http.get(`${BASE}/api/intelligence/snapshot`, () =>
    new HttpResponse(null, { status: 404 })
  ),
  http.get(`${BASE}/api/intelligence/graduation-status`, () =>
    new HttpResponse(null, { status: 404 })
  ),
  // Corrected path: backend uses /api/shadow-performance, not /api/shadow/performance
  http.get(`${BASE}/api/shadow-performance`, () =>
    new HttpResponse(null, { status: 404 })
  ),
  http.get(`${BASE}/api/shadow-decisions`, () =>
    HttpResponse.json({ count: 0, items: [] })
  ),
  http.get(`${BASE}/api/shadow-decisions/summary`, () =>
    new HttpResponse(null, { status: 404 })
  ),

  // ── Scheduler ─────────────────────────────────────────────────────────────
  http.get(`${BASE}/api/scheduler/status`, () =>
    HttpResponse.json({
      name: "scheduler",
      status: "IDLE",
      online: true,
      detail: "",
      last_updated_at: null,
      metadata: {
        worker_name: null,
        process_id: null,
        heartbeat_age_seconds: null,
        current_job_id: null,
        current_job_type: null,
        tasks_processed: null,
        started_at: null,
        last_error: null,
        current_schedule_id: null,
        current_task_type: null,
      },
    })
  ),
  http.get(`${BASE}/api/schedules`, () =>
    HttpResponse.json({ count: 0, items: [] })
  ),
  http.get(`${BASE}/api/schedules/:scheduleId`, ({ params }) =>
    new HttpResponse(null, { status: 404 })
  ),
  http.post(`${BASE}/api/schedules`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({
      schedule_id: body.schedule_id ?? "new-schedule",
      task_type: body.task_type ?? "INTELLIGENCE_CYCLE",
      enabled: body.enabled ?? true,
      schedule_kind: body.schedule_kind ?? "INTERVAL",
      timezone_name: body.timezone_name ?? "UTC",
      interval_seconds: body.interval_seconds ?? null,
      local_hour: body.local_hour ?? null,
      local_minute: body.local_minute ?? null,
      weekday: body.weekday ?? null,
      next_run_at: new Date(Date.now() + 3600_000).toISOString(),
      last_run_at: null,
      last_job_id: null,
      last_status: null,
      payload: body.payload ?? {},
      catch_up_policy: body.catch_up_policy ?? "SKIP",
      catch_up_window_seconds: body.catch_up_window_seconds ?? null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }, { status: 201 });
  }),
  http.put(`${BASE}/api/schedules/:scheduleId`, async ({ params, request }) => {
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json({
      schedule_id: params.scheduleId,
      task_type: body.task_type ?? "INTELLIGENCE_CYCLE",
      enabled: body.enabled ?? true,
      schedule_kind: body.schedule_kind ?? "INTERVAL",
      timezone_name: body.timezone_name ?? "UTC",
      interval_seconds: body.interval_seconds ?? null,
      local_hour: body.local_hour ?? null,
      local_minute: body.local_minute ?? null,
      weekday: body.weekday ?? null,
      next_run_at: new Date(Date.now() + 3600_000).toISOString(),
      last_run_at: null,
      last_job_id: null,
      last_status: null,
      payload: body.payload ?? {},
      catch_up_policy: body.catch_up_policy ?? "SKIP",
      catch_up_window_seconds: body.catch_up_window_seconds ?? null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  }),
  http.post(`${BASE}/api/schedules/:scheduleId/enable`, ({ params }) =>
    HttpResponse.json({
      schedule_id: params.scheduleId,
      task_type: "INTELLIGENCE_CYCLE",
      enabled: true,
      schedule_kind: "INTERVAL",
      timezone_name: "UTC",
      interval_seconds: 3600,
      local_hour: null,
      local_minute: null,
      weekday: null,
      next_run_at: new Date(Date.now() + 3600_000).toISOString(),
      last_run_at: null,
      last_job_id: null,
      last_status: null,
      payload: {},
      catch_up_policy: "SKIP",
      catch_up_window_seconds: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
  ),
  http.post(`${BASE}/api/schedules/:scheduleId/disable`, ({ params }) =>
    HttpResponse.json({
      schedule_id: params.scheduleId,
      task_type: "INTELLIGENCE_CYCLE",
      enabled: false,
      schedule_kind: "INTERVAL",
      timezone_name: "UTC",
      interval_seconds: 3600,
      local_hour: null,
      local_minute: null,
      weekday: null,
      next_run_at: null,
      last_run_at: null,
      last_job_id: null,
      last_status: null,
      payload: {},
      catch_up_policy: "SKIP",
      catch_up_window_seconds: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
  ),
  http.post(`${BASE}/api/schedules/:scheduleId/run-now`, ({ params }) =>
    HttpResponse.json({ job_id: `job-runnow-${params.scheduleId}` })
  ),
  http.delete(`${BASE}/api/schedules/:scheduleId`, () =>
    new HttpResponse(null, { status: 204 })
  ),

  // ── Intelligence Cycle job ─────────────────────────────────────────────────
  http.post(`${BASE}/api/jobs/intelligence-cycle`, () =>
    HttpResponse.json({ job_id: "job-ic-001" })
  ),

  // ── Intelligence Cycle job detail (for stage breakdown test) ───────────────
  http.get(`${BASE}/api/jobs/job-ic-complete`, () =>
    HttpResponse.json({
      job_id: "job-ic-complete",
      job_type: "INTELLIGENCE_CYCLE",
      status: "SUCCEEDED",
      created_at: "2026-07-21T08:00:00Z",
      started_at: "2026-07-21T08:00:01Z",
      finished_at: "2026-07-21T08:05:00Z",
      payload: {},
      result: {
        trading_impact: "NONE",
        stages: [
          { stage_name: "NEWS_RESEARCH", status: "SUCCESS", summary: "Fetched 42 articles", warning_text: null, error_text: null },
          { stage_name: "CAPTURE_PRICE_OUTCOMES", status: "SUCCESS", summary: "Captured prices for 10 symbols", warning_text: null, error_text: null },
          { stage_name: "SHADOW_ANALYSIS", status: "SUCCESS", summary: "Analysed 30 decisions", warning_text: null, error_text: null },
          { stage_name: "SHADOW_PERFORMANCE", status: "SUCCESS", summary: "Performance updated", warning_text: null, error_text: null },
          { stage_name: "GRADUATION_STATUS", status: "SUCCESS", summary: "12/14 checks passed", warning_text: null, error_text: null },
          { stage_name: "INTELLIGENCE_SNAPSHOT", status: "SUCCESS", summary: "Snapshot stored", warning_text: null, error_text: null },
          { stage_name: "DAILY_BRIEFING", status: "SUCCESS", summary: "Briefing generated", warning_text: null, error_text: null },
        ],
      },
      error_code: null,
      error_summary: null,
    })
  ),

  // ── Run history ───────────────────────────────────────────────────────────
  http.get(`${BASE}/api/run-history`, () =>
    HttpResponse.json({ count: 0, items: [] })
  ),

  // ── Portfolio ─────────────────────────────────────────────────────────────
  http.get(`${BASE}/api/portfolio`, () =>
    new HttpResponse(null, { status: 404 })
  ),
  http.get(`${BASE}/api/orders`, () =>
    HttpResponse.json({ count: 0, items: [] })
  ),
  http.get(`${BASE}/api/orders/unresolved`, () =>
    HttpResponse.json({ count: 0, items: [] })
  ),
];

export const server = setupServer(...handlers);
