import { http, HttpResponse } from "msw";
import { screen } from "@testing-library/react";
import { render } from "@/test/test-utils";
import { server } from "@/test/handlers";
import OperationsPage from "@/pages/OperationsPage";

const BASE = "http://127.0.0.1:8000";

function now(offsetMs = 0) {
  return new Date(Date.now() + offsetMs).toISOString();
}

describe("Operations Centre v2", () => {
  it("renders an operational rack, current activity, timeline, upcoming work and safety state", async () => {
    server.use(
      http.get(`${BASE}/api/jobs`, () => HttpResponse.json({
        count: 2,
        items: [
          { job_id: "job-running", job_type: "NEWS_RESEARCH_CYCLE", status: "RUNNING", created_at: now(-60_000), started_at: now(-50_000), finished_at: null, duration_seconds: null, payload: {}, result: {}, error_code: null, error_summary: null },
          { job_id: "job-done", job_type: "INTELLIGENCE_CYCLE", status: "SUCCEEDED", created_at: now(-300_000), started_at: now(-290_000), finished_at: now(-250_000), duration_seconds: 40, payload: {}, result: {}, error_code: null, error_summary: null },
        ],
      })),
      http.get(`${BASE}/api/run-history`, () => HttpResponse.json({ count: 1, items: [{ run_id: "run-1", run_type: "NEWS_RESEARCH", status: "SUCCEEDED", started_at: now(-500_000), finished_at: now(-450_000), duration_seconds: 50, provider: "ALPHA_VANTAGE", symbols: ["AAPL"], created_count: 3, skipped_count: 0, failure_count: 0, error_code: null, error_summary: null, metadata: {} }] })),
      http.get(`${BASE}/api/schedules`, () => HttpResponse.json({ count: 1, items: [{ schedule_id: "hourly", task_type: "INTELLIGENCE_CYCLE", enabled: true, schedule_kind: "INTERVAL", timezone_name: "Europe/London", interval_seconds: 3600, local_hour: null, local_minute: null, weekday: null, next_run_at: now(3_600_000), last_run_at: null, last_job_id: null, last_status: null, payload: {}, catch_up_policy: "RUN_ONCE", catch_up_window_seconds: null, created_at: now(), updated_at: now() }] })),
    );

    render(<OperationsPage />);

    expect(await screen.findByText("KAIRO Operations Centre")).toBeInTheDocument();
    expect(await screen.findByText("Platform rack")).toBeInTheDocument();
    expect(await screen.findByText("Current activity")).toBeInTheDocument();
    expect(await screen.findByText("News Research Cycle")).toBeInTheDocument();
    expect(await screen.findByText("Operational timeline")).toBeInTheDocument();
    expect(await screen.findByText("Upcoming work")).toBeInTheDocument();
    expect(await screen.findByText("Safety state")).toBeInTheDocument();
    expect(await screen.findByText("Market data resilience")).toBeInTheDocument();
    expect(await screen.findByText("Supervisor health")).toBeInTheDocument();
    expect(screen.queryByText("Current intelligence")).not.toBeInTheDocument();
    expect(screen.queryByText("Graduation readiness")).not.toBeInTheDocument();
  });

  it("promotes a failed service into a full-width attention banner", async () => {
    server.use(
      http.get(`${BASE}/api/infrastructure/status`, () => HttpResponse.json({
        generated_at: now(),
        overall_status: "DEGRADED",
        services: {
          supervisor: { name: "supervisor", status: "RUNNING", online: true, detail: "Active", last_updated_at: now(), metadata: {} },
          api: { name: "api", status: "ONLINE", online: true, detail: "Active", last_updated_at: now(), metadata: {} },
          storage: { name: "storage", status: "HEALTHY", online: true, detail: "Active", last_updated_at: now(), metadata: {} },
          job_worker: { name: "job_worker", status: "FAILED", online: false, detail: "Restart lockout", last_updated_at: now(), metadata: {} },
          scheduler: { name: "scheduler", status: "IDLE", online: true, detail: "Active", last_updated_at: now(), metadata: {} },
          broker: { name: "broker", status: "CONFIGURED", online: true, detail: "Configured", last_updated_at: now(), metadata: {} },
          market_data: { name: "market_data", status: "CONFIGURED", online: true, detail: "Configured", last_updated_at: now(), metadata: {} },
          news: { name: "news", status: "CURRENT", online: true, detail: "Current", last_updated_at: now(), metadata: {} },
        },
      })),
    );

    render(<OperationsPage />);

    expect(await screen.findByText("Attention required")).toBeInTheDocument();
    expect(await screen.findByText("Job Worker Failed")).toBeInTheDocument();
    expect(await screen.findAllByText("Restart lockout")).toHaveLength(2);
  });
});
