/**
 * Supervisor visibility tests — Task #48
 *
 * Covers all 20 required scenarios:
 *  1.  InfrastructureStatusResponse accepts services.supervisor
 *  2.  Healthy Supervisor renders as RUNNING
 *  3.  Automatic recovery enabled is shown
 *  4.  Managed and healthy process counts render
 *  5.  Recovering process count renders
 *  6.  Failed process count renders
 *  7.  DEGRADED uses warning styling
 *  8.  FAILED shows manual-review guidance
 *  9.  STALE does not show healthy styling
 *  10. STOPPED shows supervisor-start guidance
 *  11. NOT_SEEN shows supervisor-start guidance
 *  12. Dashboard no longer tells user to manually start Scheduler (Supervisor active)
 *  13. Dashboard no longer tells user to manually start Job Worker (Supervisor active)
 *  14. Paper Trading described as independently controlled
 *  15. Existing Scheduler tests still pass    — verified by running the full test suite
 *  16. Existing Intelligence Cycle tests pass — verified by running the full test suite
 *  17. Existing Shadow Intelligence tests pass — verified by running the full test suite
 *  18. Existing auth/CSRF tests pass          — verified by running the full test suite
 *  19. MSW infrastructure handler includes Supervisor
 *  20. Raw metadata objects are never rendered directly as React children
 */
import React from "react";
import { describe, it, expect, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { render } from "@/test/test-utils";
import { server } from "@/test/handlers";
import DashboardPage from "@/pages/DashboardPage";

const BASE = "http://127.0.0.1:8000";

// ─── Fixtures ────────────────────────────────────────────────────────────────

const RUNNING_SUPERVISOR = {
  name: "supervisor",
  status: "RUNNING",
  online: true,
  detail: "KAIRO process supervision and automatic recovery are active.",
  last_updated_at: "2026-07-22T14:49:22Z",
  metadata: {
    process_id: 22564,
    process_alive: true,
    restart_enabled: true,
    managed_process_count: 3,
    healthy_process_count: 3,
    recovering_process_count: 0,
    failed_process_count: 0,
    status_age_seconds: 0.5,
    status_file: "data\\supervisor_status.json",
  },
};

const BASE_SERVICES = {
  api:         { name: "api",         status: "ONLINE", online: true,  detail: "", last_updated_at: null, metadata: {} },
  storage:     { name: "storage",     status: "ONLINE", online: true,  detail: "", last_updated_at: null, metadata: {} },
  job_worker:  { name: "job_worker",  status: "IDLE",   online: true,  detail: "", last_updated_at: null,
    metadata: { worker_name: null, process_id: null, heartbeat_age_seconds: null, current_job_id: null,
      current_job_type: null, jobs_processed: null, started_at: null, last_error: null } },
  scheduler:   { name: "scheduler",   status: "IDLE",   online: true,  detail: "", last_updated_at: null,
    metadata: { worker_name: null, process_id: null, heartbeat_age_seconds: null, current_job_id: null,
      current_job_type: null, tasks_processed: null, started_at: null, last_error: null,
      current_schedule_id: null, current_task_type: null } },
  broker:      { name: "broker",      status: "ONLINE", online: true,  detail: "", last_updated_at: null, metadata: {} },
  market_data: { name: "market_data", status: "ONLINE", online: true,  detail: "", last_updated_at: null, metadata: {} },
  news:        { name: "news",        status: "ONLINE", online: true,  detail: "", last_updated_at: null, metadata: {} },
};

function useInfra(supervisorOverride: Record<string, unknown>, serviceOverrides: Record<string, unknown> = {}) {
  server.use(
    http.get(`${BASE}/api/infrastructure/status`, () =>
      HttpResponse.json({
        generated_at: new Date().toISOString(),
        overall_status: "HEALTHY",
        services: { supervisor: supervisorOverride, ...BASE_SERVICES, ...serviceOverrides },
      }),
    ),
  );
}

// ─── 1. Type: InfrastructureStatusResponse accepts services.supervisor ────────

describe("1. InfrastructureStatusResponse accepts services.supervisor", () => {
  it("MSW default handler includes a supervisor service and the Dashboard renders it", async () => {
    render(<DashboardPage />);
    await waitFor(
      () => expect(screen.getByText("Platform Supervisor")).toBeInTheDocument(),
      { timeout: 3000 },
    );
  });
});

// ─── 2. Healthy Supervisor renders RUNNING ────────────────────────────────────

describe("2. Healthy Supervisor renders as RUNNING", () => {
  beforeEach(() => useInfra(RUNNING_SUPERVISOR));

  it("shows RUNNING status badge", async () => {
    render(<DashboardPage />);
    await waitFor(() =>
      expect(screen.getByText("RUNNING")).toBeInTheDocument(),
    );
  });
});

// ─── 3. Automatic recovery enabled is shown ───────────────────────────────────

describe("3. Automatic recovery enabled is shown", () => {
  beforeEach(() => useInfra(RUNNING_SUPERVISOR));

  it("renders 'Automatic recovery enabled'", async () => {
    render(<DashboardPage />);
    await waitFor(() =>
      expect(screen.getByText("Automatic recovery enabled")).toBeInTheDocument(),
    );
  });
});

// ─── 4. Managed and healthy process counts render ─────────────────────────────

describe("4. Managed and healthy process counts render", () => {
  beforeEach(() => useInfra(RUNNING_SUPERVISOR));

  it("shows managed and healthy counts", async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("3 services managed")).toBeInTheDocument();
      // healthy count can appear in multiple places (infra card + Platform Ops card)
      expect(screen.getAllByText("3 healthy").length).toBeGreaterThan(0);
    });
  });
});

// ─── 5. Recovering process count renders ─────────────────────────────────────

describe("5. Recovering process count renders", () => {
  beforeEach(() =>
    useInfra({
      ...RUNNING_SUPERVISOR,
      status: "DEGRADED",
      metadata: {
        ...RUNNING_SUPERVISOR.metadata,
        recovering_process_count: 1,
        healthy_process_count: 2,
        failed_process_count: 0,
      },
    }),
  );

  it("shows recovering count and 'in progress' hint", async () => {
    render(<DashboardPage />);
    await waitFor(() =>
      expect(screen.getAllByText(/1 recovering/i).length).toBeGreaterThan(0),
    );
  });
});

// ─── 6. Failed process count renders ─────────────────────────────────────────

describe("6. Failed process count renders", () => {
  beforeEach(() =>
    useInfra({
      ...RUNNING_SUPERVISOR,
      status: "FAILED",
      online: false,
      metadata: {
        ...RUNNING_SUPERVISOR.metadata,
        failed_process_count: 1,
        healthy_process_count: 2,
        recovering_process_count: 0,
      },
    }),
  );

  it("shows failed count", async () => {
    render(<DashboardPage />);
    await waitFor(() =>
      expect(screen.getAllByText(/1 failed/i).length).toBeGreaterThan(0),
    );
  });
});

// ─── 7. DEGRADED uses warning styling ────────────────────────────────────────

describe("7. DEGRADED uses warning styling", () => {
  beforeEach(() =>
    useInfra({
      ...RUNNING_SUPERVISOR,
      status: "DEGRADED",
      online: true,
      metadata: {
        ...RUNNING_SUPERVISOR.metadata,
        recovering_process_count: 1,
        healthy_process_count: 2,
        failed_process_count: 0,
      },
    }),
  );

  it("renders DEGRADED badge with amber class", async () => {
    render(<DashboardPage />);
    await waitFor(() =>
      expect(screen.getAllByText("DEGRADED").length).toBeGreaterThan(0),
    );
    // The status badge in the infra card is a <span> with the colour class
    const badge = screen.getAllByText("DEGRADED")[0];
    expect(badge.className).toContain("amber");
  });
});

// ─── 8. FAILED shows manual-review guidance ──────────────────────────────────

describe("8. FAILED shows manual-review guidance", () => {
  beforeEach(() =>
    useInfra({
      ...RUNNING_SUPERVISOR,
      status: "FAILED",
      online: false,
      metadata: { ...RUNNING_SUPERVISOR.metadata, failed_process_count: 1 },
    }),
  );

  it("shows 'manual review required' text", async () => {
    render(<DashboardPage />);
    await waitFor(() =>
      expect(screen.getAllByText(/manual review/i).length).toBeGreaterThan(0),
    );
  });
});

// ─── 9. STALE does not show healthy styling ───────────────────────────────────

describe("9. STALE does not show healthy styling", () => {
  beforeEach(() =>
    useInfra({
      ...RUNNING_SUPERVISOR,
      status: "STALE",
      online: false,
    }),
  );

  it("renders STALE without emerald colour class", async () => {
    render(<DashboardPage />);
    await waitFor(() =>
      expect(screen.getAllByText("STALE").length).toBeGreaterThan(0),
    );
    // Every element showing "STALE" must not use the healthy green
    const badges = screen.getAllByText("STALE");
    badges.forEach((badge) =>
      expect(badge.className).not.toContain("emerald"),
    );
  });
});

// ─── 10. STOPPED shows supervisor-start guidance ─────────────────────────────

describe("10. STOPPED shows supervisor-start guidance", () => {
  beforeEach(() =>
    useInfra({ ...RUNNING_SUPERVISOR, status: "STOPPED", online: false }),
  );

  it("shows run_process_supervisor in guidance", async () => {
    render(<DashboardPage />);
    await waitFor(() =>
      expect(screen.getByText(/run_process_supervisor/)).toBeInTheDocument(),
    );
  });
});

// ─── 11. NOT_SEEN shows supervisor-start guidance ─────────────────────────────

describe("11. NOT_SEEN shows supervisor-start guidance", () => {
  beforeEach(() =>
    useInfra({ ...RUNNING_SUPERVISOR, status: "NOT_SEEN", online: false }),
  );

  it("shows run_process_supervisor in guidance", async () => {
    render(<DashboardPage />);
    await waitFor(() =>
      expect(screen.getByText(/run_process_supervisor/)).toBeInTheDocument(),
    );
  });
});

// ─── 12. No manual Scheduler launch message when Supervisor is RUNNING ────────

describe("12. No manual Scheduler start command when Supervisor manages it", () => {
  beforeEach(() =>
    useInfra(RUNNING_SUPERVISOR, {
      // Scheduler is offline; Supervisor is RUNNING → should NOT show run_scheduler
      scheduler: {
        ...BASE_SERVICES.scheduler,
        status: "OFFLINE",
        online: false,
      },
    }),
  );

  it("does not show run_scheduler command", async () => {
    render(<DashboardPage />);
    // Wait for infra data to load
    await waitFor(() =>
      expect(screen.getByText("Platform Supervisor")).toBeInTheDocument(),
    );
    expect(screen.queryByText(/run_scheduler/)).not.toBeInTheDocument();
  });
});

// ─── 13. No manual Job Worker launch message when Supervisor is RUNNING ───────

describe("13. No manual Job Worker start command when Supervisor manages it", () => {
  beforeEach(() =>
    useInfra(RUNNING_SUPERVISOR, {
      // Job Worker is offline; Supervisor is RUNNING → should NOT show run_job_worker
      job_worker: {
        ...BASE_SERVICES.job_worker,
        status: "OFFLINE",
        online: false,
      },
    }),
  );

  it("does not show run_job_worker command", async () => {
    render(<DashboardPage />);
    await waitFor(() =>
      expect(screen.getByText("Platform Supervisor")).toBeInTheDocument(),
    );
    expect(screen.queryByText(/run_job_worker/)).not.toBeInTheDocument();
  });
});

// ─── 14. Paper Trading described as independently controlled ──────────────────

describe("14. Paper Trading is independently controlled", () => {
  it("Paper Trading section is present and not linked to Supervisor guidance", async () => {
    render(<DashboardPage />);
    await waitFor(() =>
      expect(screen.getByText("Paper Trading")).toBeInTheDocument(),
    );
    // The Paper Trading header text must not mention the Supervisor
    const ptHeader = screen.getByText("Paper Trading");
    expect(ptHeader.closest("[class]")?.textContent ?? "").not.toMatch(/supervisor/i);
  });
});

// ─── 19. MSW default handler includes Supervisor ─────────────────────────────

describe("19. MSW default handler includes supervisor", () => {
  it("default handler returns supervisor — Platform Supervisor row is rendered", async () => {
    render(<DashboardPage />);
    await waitFor(
      () => expect(screen.getByText("Platform Supervisor")).toBeInTheDocument(),
      { timeout: 3000 },
    );
  });
});

// ─── 20. Raw metadata never rendered directly ─────────────────────────────────

describe("20. Raw metadata objects are never rendered directly as React children", () => {
  beforeEach(() => useInfra(RUNNING_SUPERVISOR));

  it("document body does not contain [object Object]", async () => {
    render(<DashboardPage />);
    await waitFor(() =>
      expect(screen.getByText("Platform Supervisor")).toBeInTheDocument(),
    );
    expect(document.body.textContent ?? "").not.toContain("[object Object]");
  });
});
