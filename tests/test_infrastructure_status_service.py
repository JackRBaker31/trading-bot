import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.infrastructure_status_service import (
    InfrastructureStatusService,
)
from app.worker_heartbeat import WorkerHeartbeat
from app.supervisor_status_repository import (
    SupervisorStatusRepository,
)
from app.worker_heartbeat_repository import (
    WorkerHeartbeatRepository,
)


class FakeNewsStore:
    def __init__(self, signals):
        self._signals = signals

    def load_all(self):
        return self._signals


def healthy_supervisor_repository(tmp_path, now: datetime):
    path = tmp_path / "healthy-supervisor.json"
    path.write_text(
        json.dumps(
            {
                "generated_at": now.isoformat(),
                "supervisor_status": "RUNNING",
                "supervisor_process_id": 500,
                "restart_enabled": True,
                "processes": [
                    {
                        "name": name,
                        "status": "RUNNING",
                        "restart_state": "HEALTHY",
                        "health": {"healthy": True},
                    }
                    for name in ("api", "job_worker", "scheduler")
                ],
            }
        ),
        encoding="utf-8",
    )
    return SupervisorStatusRepository(
        status_path=path,
        process_alive=lambda process_id: True,
    )


def write_config(tmp_path) -> str:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "mode": "PAPER",
                "market_data_provider": "TWELVE_DATA",
                "starting_cash": 5000,
                "symbols": ["AAPL"],
                "risk": {
                    "max_order_value": 1000,
                    "max_position_value": 2000,
                    "max_portfolio_exposure": 0.5,
                    "max_trades_per_session": 3,
                },
                "strategy": {
                    "drop_threshold_percent": 2,
                    "target_allocation_percent": 10,
                    "cooldown_cycles": 1,
                },
                "trading_loop": {
                    "cycles": 1,
                    "interval_seconds": 60,
                },
                "market_session": {
                    "enforce_market_hours": True,
                    "timezone": "America/New_York",
                    "opening_time": "09:30",
                    "closing_time": "16:00",
                    "trading_weekdays": [0, 1, 2, 3, 4],
                },
                "paper_trading": {
                    "enabled": True,
                    "broker_environment": "DEMO",
                    "order_execution_permission_confirmed": False,
                },
            }
        ),
        encoding="utf-8",
    )
    return str(path)


def register_heartbeat(
    repository: WorkerHeartbeatRepository,
    *,
    worker_name: str,
    now: datetime,
    status: str = "IDLE",
    heartbeat_age_seconds: float = 3.0,
    current_job_id: str | None = None,
    current_job_type: str | None = None,
    jobs_processed: int = 0,
) -> None:
    repository.register(
        heartbeat=WorkerHeartbeat(
            worker_name=worker_name,
            process_id=321,
            status=status,
            started_at=now - timedelta(minutes=5),
            last_heartbeat_at=(
                now - timedelta(seconds=heartbeat_age_seconds)
            ),
            current_job_id=current_job_id,
            current_job_type=current_job_type,
            jobs_processed=jobs_processed,
        )
    )


def test_reports_recent_worker_and_scheduler_as_idle(tmp_path) -> None:
    now = datetime(2026, 7, 20, 14, 0, tzinfo=timezone.utc)
    repository = WorkerHeartbeatRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    register_heartbeat(
        repository,
        worker_name="primary-job-worker",
        now=now,
        jobs_processed=7,
    )
    register_heartbeat(
        repository,
        worker_name="primary-scheduler",
        now=now,
        jobs_processed=4,
    )
    signal = SimpleNamespace(
        published_at=now - timedelta(minutes=10)
    )
    service = InfrastructureStatusService(
        heartbeat_repository=repository,
        config_path=write_config(tmp_path),
        news_signal_store=FakeNewsStore([signal]),
        supervisor_status_repository=healthy_supervisor_repository(
            tmp_path, now
        ),
        now_provider=lambda: now,
    )

    status = service.get_status().to_dictionary()

    assert status["overall_status"] == "HEALTHY"
    worker = status["services"]["job_worker"]
    assert worker["online"] is True
    assert worker["status"] == "IDLE"
    assert worker["metadata"]["jobs_processed"] == 7

    scheduler = status["services"]["scheduler"]
    assert scheduler["online"] is True
    assert scheduler["status"] == "IDLE"
    assert scheduler["metadata"]["tasks_processed"] == 4


def test_reports_stale_worker_offline(tmp_path) -> None:
    now = datetime(2026, 7, 20, 14, 0, tzinfo=timezone.utc)
    repository = WorkerHeartbeatRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    register_heartbeat(
        repository,
        worker_name="primary-job-worker",
        now=now,
        heartbeat_age_seconds=120,
        jobs_processed=7,
    )
    register_heartbeat(
        repository,
        worker_name="primary-scheduler",
        now=now,
    )
    service = InfrastructureStatusService(
        heartbeat_repository=repository,
        config_path=write_config(tmp_path),
        news_signal_store=FakeNewsStore([]),
        supervisor_status_repository=healthy_supervisor_repository(
            tmp_path, now
        ),
        now_provider=lambda: now,
    )

    status = service.get_status().to_dictionary()

    assert status["overall_status"] == "DEGRADED"
    assert status["services"]["job_worker"]["status"] == "STALE"
    assert status["services"]["job_worker"]["online"] is False


def test_reports_busy_scheduler_with_current_schedule(tmp_path) -> None:
    now = datetime(2026, 7, 20, 14, 0, tzinfo=timezone.utc)
    repository = WorkerHeartbeatRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    register_heartbeat(
        repository,
        worker_name="primary-scheduler",
        now=now,
        status="BUSY",
        current_job_id="schedule-123",
        current_job_type="NEWS_RESEARCH_CYCLE",
        jobs_processed=2,
    )
    service = InfrastructureStatusService(
        heartbeat_repository=repository,
        config_path=write_config(tmp_path),
        news_signal_store=FakeNewsStore([]),
        supervisor_status_repository=healthy_supervisor_repository(
            tmp_path, now
        ),
        now_provider=lambda: now,
    )

    scheduler = service.get_scheduler_status().to_dictionary()

    assert scheduler["name"] == "scheduler"
    assert scheduler["status"] == "BUSY"
    assert scheduler["online"] is True
    assert scheduler["metadata"]["current_schedule_id"] == "schedule-123"
    assert scheduler["metadata"]["current_task_type"] == "NEWS_RESEARCH_CYCLE"
    assert scheduler["metadata"]["tasks_processed"] == 2


def test_missing_scheduler_degrades_infrastructure(tmp_path) -> None:
    now = datetime(2026, 7, 20, 14, 0, tzinfo=timezone.utc)
    repository = WorkerHeartbeatRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    register_heartbeat(
        repository,
        worker_name="primary-job-worker",
        now=now,
    )
    service = InfrastructureStatusService(
        heartbeat_repository=repository,
        config_path=write_config(tmp_path),
        news_signal_store=FakeNewsStore([]),
        supervisor_status_repository=healthy_supervisor_repository(
            tmp_path, now
        ),
        now_provider=lambda: now,
    )

    status = service.get_status().to_dictionary()

    assert status["overall_status"] == "DEGRADED"
    scheduler = status["services"]["scheduler"]
    assert scheduler["status"] == "NOT_SEEN"
    assert scheduler["online"] is False

from app.supervisor_status_repository import SupervisorStatusRepository


def write_supervisor_status(
    tmp_path,
    *,
    now: datetime,
    supervisor_status: str = "RUNNING",
    process_alive: bool = True,
    restart_state: str = "HEALTHY",
    process_status: str = "RUNNING",
    healthy: bool = True,
):
    path = tmp_path / "supervisor_status.json"
    path.write_text(
        json.dumps(
            {
                "generated_at": now.isoformat(),
                "supervisor_status": supervisor_status,
                "supervisor_process_id": 500,
                "restart_enabled": True,
                "processes": [
                    {
                        "name": "api",
                        "status": process_status,
                        "restart_state": restart_state,
                        "health": {"healthy": healthy},
                    },
                    {
                        "name": "job_worker",
                        "status": "RUNNING",
                        "restart_state": "HEALTHY",
                        "health": {"healthy": True},
                    },
                    {
                        "name": "scheduler",
                        "status": "RUNNING",
                        "restart_state": "HEALTHY",
                        "health": {"healthy": True},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return SupervisorStatusRepository(
        status_path=path,
        process_alive=lambda process_id: process_alive,
    )


def test_reports_healthy_supervisor_as_running(tmp_path) -> None:
    now = datetime(2026, 7, 22, 10, 0, tzinfo=timezone.utc)
    repository = WorkerHeartbeatRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    register_heartbeat(
        repository,
        worker_name="primary-job-worker",
        now=now,
    )
    register_heartbeat(
        repository,
        worker_name="primary-scheduler",
        now=now,
    )
    service = InfrastructureStatusService(
        heartbeat_repository=repository,
        config_path=write_config(tmp_path),
        news_signal_store=FakeNewsStore([]),
        supervisor_status_repository=write_supervisor_status(
            tmp_path, now=now
        ),
        now_provider=lambda: now,
    )

    supervisor = service.get_supervisor_status().to_dictionary()

    assert supervisor["status"] == "RUNNING"
    assert supervisor["online"] is True
    assert supervisor["metadata"]["managed_process_count"] == 3
    assert supervisor["metadata"]["healthy_process_count"] == 3
    assert supervisor["metadata"]["restart_enabled"] is True


def test_reports_recovering_supervisor_as_degraded(tmp_path) -> None:
    now = datetime(2026, 7, 22, 10, 0, tzinfo=timezone.utc)
    repository = WorkerHeartbeatRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    service = InfrastructureStatusService(
        heartbeat_repository=repository,
        config_path=write_config(tmp_path),
        news_signal_store=FakeNewsStore([]),
        supervisor_status_repository=write_supervisor_status(
            tmp_path,
            now=now,
            restart_state="RECOVERING",
            healthy=False,
        ),
        now_provider=lambda: now,
    )

    supervisor = service.get_supervisor_status().to_dictionary()

    assert supervisor["status"] == "DEGRADED"
    assert supervisor["online"] is True
    assert supervisor["metadata"]["recovering_process_count"] == 1


def test_reports_restart_lockout_as_failed(tmp_path) -> None:
    now = datetime(2026, 7, 22, 10, 0, tzinfo=timezone.utc)
    repository = WorkerHeartbeatRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    service = InfrastructureStatusService(
        heartbeat_repository=repository,
        config_path=write_config(tmp_path),
        news_signal_store=FakeNewsStore([]),
        supervisor_status_repository=write_supervisor_status(
            tmp_path,
            now=now,
            restart_state="FAILED",
            process_status="FAILED",
            healthy=False,
        ),
        now_provider=lambda: now,
    )

    supervisor = service.get_supervisor_status().to_dictionary()

    assert supervisor["status"] == "FAILED"
    assert supervisor["metadata"]["failed_process_count"] == 1


def test_reports_old_supervisor_status_as_stale(tmp_path) -> None:
    now = datetime(2026, 7, 22, 10, 0, tzinfo=timezone.utc)
    repository = WorkerHeartbeatRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    service = InfrastructureStatusService(
        heartbeat_repository=repository,
        config_path=write_config(tmp_path),
        news_signal_store=FakeNewsStore([]),
        supervisor_status_repository=write_supervisor_status(
            tmp_path,
            now=now - timedelta(seconds=60),
        ),
        supervisor_stale_after_seconds=15,
        now_provider=lambda: now,
    )

    supervisor = service.get_supervisor_status().to_dictionary()

    assert supervisor["status"] == "STALE"
    assert supervisor["online"] is False


def test_missing_supervisor_degrades_infrastructure(tmp_path) -> None:
    now = datetime(2026, 7, 22, 10, 0, tzinfo=timezone.utc)
    repository = WorkerHeartbeatRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    register_heartbeat(
        repository,
        worker_name="primary-job-worker",
        now=now,
    )
    register_heartbeat(
        repository,
        worker_name="primary-scheduler",
        now=now,
    )
    service = InfrastructureStatusService(
        heartbeat_repository=repository,
        config_path=write_config(tmp_path),
        news_signal_store=FakeNewsStore([]),
        supervisor_status_repository=SupervisorStatusRepository(
            status_path=tmp_path / "missing.json"
        ),
        now_provider=lambda: now,
    )

    status = service.get_status().to_dictionary()

    assert status["overall_status"] == "DEGRADED"
    assert status["services"]["supervisor"]["status"] == "NOT_SEEN"