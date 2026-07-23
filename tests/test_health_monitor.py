from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.health_monitor import HealthMonitor, HealthMonitorConfig
from app.worker_heartbeat import WorkerHeartbeat


class FakeHeartbeatRepository:
    def __init__(self, values=None, error: Exception | None = None) -> None:
        self.values = values or {}
        self.error = error

    def get(self, *, worker_name: str):
        if self.error is not None:
            raise self.error
        return self.values.get(worker_name)


def heartbeat(
    *,
    worker_name: str,
    now: datetime,
    age_seconds: float = 1.0,
    status: str = "IDLE",
) -> WorkerHeartbeat:
    return WorkerHeartbeat(
        worker_name=worker_name,
        process_id=1234,
        status=status,
        started_at=now - timedelta(minutes=1),
        last_heartbeat_at=now - timedelta(seconds=age_seconds),
        current_job_id=None,
        current_job_type=None,
        jobs_processed=3,
        last_error=None,
    )


def make_monitor(
    *,
    now: datetime,
    repository: FakeHeartbeatRepository,
    http_ok: bool = True,
    startup_grace_seconds: float = 0.0,
    monotonic_value: float = 100.0,
    persistent_failure_count: int = 3,
):
    monotonic = [monotonic_value]
    monitor = HealthMonitor(
        heartbeat_repository=repository,
        config=HealthMonitorConfig(
            startup_grace_seconds=startup_grace_seconds,
            heartbeat_stale_seconds=20.0,
            persistent_failure_count=persistent_failure_count,
        ),
        utc_now=lambda: now,
        monotonic_clock=lambda: monotonic[0],
        http_probe=lambda url, timeout: (
            http_ok,
            12.5 if http_ok else None,
            "healthy" if http_ok else "unreachable",
        ),
    )
    return monitor, monotonic


def test_reports_healthy_api_worker_and_scheduler():
    now = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)
    repository = FakeHeartbeatRepository(
        {
            "primary-job-worker": heartbeat(
                worker_name="primary-job-worker", now=now
            ),
            "primary-scheduler": heartbeat(
                worker_name="primary-scheduler", now=now, status="BUSY"
            ),
        }
    )
    monitor, _ = make_monitor(now=now, repository=repository)

    results = monitor.check_all()

    assert results["api"].health_status == "HEALTHY"
    assert results["api"].response_time_ms == 12.5
    assert results["job_worker"].healthy is True
    assert results["scheduler"].heartbeat_status == "BUSY"


def test_reports_stale_heartbeat_without_restarting_anything():
    now = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)
    repository = FakeHeartbeatRepository(
        {
            "primary-job-worker": heartbeat(
                worker_name="primary-job-worker",
                now=now,
                age_seconds=30.0,
            ),
            "primary-scheduler": heartbeat(
                worker_name="primary-scheduler", now=now
            ),
        }
    )
    monitor, _ = make_monitor(now=now, repository=repository)

    result = monitor.check_all()["job_worker"]

    assert result.health_status == "STALE"
    assert result.healthy is False
    assert result.heartbeat_age_seconds == 30.0
    assert result.consecutive_health_failures == 1


def test_persistent_fault_after_configured_failed_checks():
    now = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)
    repository = FakeHeartbeatRepository()
    monitor, _ = make_monitor(
        now=now,
        repository=repository,
        http_ok=False,
        persistent_failure_count=2,
    )

    first = monitor.check_all()["api"]
    second = monitor.check_all()["api"]

    assert first.persistent_fault is False
    assert second.persistent_fault is True
    assert second.consecutive_health_failures == 2


def test_success_resets_consecutive_failures():
    now = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)
    repository = FakeHeartbeatRepository()
    state = {"ok": False}
    monitor = HealthMonitor(
        heartbeat_repository=repository,
        config=HealthMonitorConfig(startup_grace_seconds=0),
        utc_now=lambda: now,
        monotonic_clock=lambda: 100.0,
        http_probe=lambda url, timeout: (
            state["ok"], None, "healthy" if state["ok"] else "down"
        ),
    )

    monitor.check_all()
    state["ok"] = True
    result = monitor.check_all()["api"]

    assert result.healthy is True
    assert result.consecutive_health_failures == 0
    assert result.last_healthy_at == now.isoformat()


def test_startup_grace_reports_starting_without_counting_failure():
    now = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)
    repository = FakeHeartbeatRepository()
    monitor, monotonic = make_monitor(
        now=now,
        repository=repository,
        http_ok=False,
        startup_grace_seconds=15.0,
        monotonic_value=100.0,
    )
    monotonic[0] = 105.0

    results = monitor.check_all()

    assert results["api"].health_status == "STARTING"
    assert results["job_worker"].health_status == "STARTING"
    assert results["scheduler"].consecutive_health_failures == 0


def test_stopped_heartbeat_is_unhealthy():
    now = datetime(2026, 7, 22, 12, 0, tzinfo=timezone.utc)
    repository = FakeHeartbeatRepository(
        {
            "primary-job-worker": heartbeat(
                worker_name="primary-job-worker", now=now, status="STOPPED"
            ),
            "primary-scheduler": heartbeat(
                worker_name="primary-scheduler", now=now
            ),
        }
    )
    monitor, _ = make_monitor(now=now, repository=repository)

    result = monitor.check_all()["job_worker"]

    assert result.health_status == "STOPPED"
    assert result.healthy is False