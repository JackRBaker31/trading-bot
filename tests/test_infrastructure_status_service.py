import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.infrastructure_status_service import (
    InfrastructureStatusService,
)
from app.worker_heartbeat import WorkerHeartbeat
from app.worker_heartbeat_repository import (
    WorkerHeartbeatRepository,
)


class FakeNewsStore:
    def __init__(self, signals):
        self._signals = signals

    def load_all(self):
        return self._signals


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


def test_reports_recent_worker_as_idle(tmp_path) -> None:
    now = datetime(2026, 7, 20, 14, 0, tzinfo=timezone.utc)
    repository = WorkerHeartbeatRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    repository.register(
        heartbeat=WorkerHeartbeat(
            worker_name="primary-job-worker",
            process_id=321,
            status="IDLE",
            started_at=now - timedelta(minutes=5),
            last_heartbeat_at=now - timedelta(seconds=3),
            current_job_id=None,
            current_job_type=None,
            jobs_processed=7,
        )
    )
    signal = SimpleNamespace(
        published_at=now - timedelta(minutes=10)
    )
    service = InfrastructureStatusService(
        heartbeat_repository=repository,
        config_path=write_config(tmp_path),
        news_signal_store=FakeNewsStore([signal]),
        now_provider=lambda: now,
    )

    status = service.get_status().to_dictionary()

    assert status["overall_status"] == "HEALTHY"
    worker = status["services"]["job_worker"]
    assert worker["online"] is True
    assert worker["status"] == "IDLE"
    assert worker["metadata"]["jobs_processed"] == 7


def test_reports_stale_worker_offline(tmp_path) -> None:
    now = datetime(2026, 7, 20, 14, 0, tzinfo=timezone.utc)
    repository = WorkerHeartbeatRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    repository.register(
        heartbeat=WorkerHeartbeat(
            worker_name="primary-job-worker",
            process_id=321,
            status="IDLE",
            started_at=now - timedelta(hours=1),
            last_heartbeat_at=now - timedelta(minutes=2),
            current_job_id=None,
            current_job_type=None,
            jobs_processed=7,
        )
    )
    service = InfrastructureStatusService(
        heartbeat_repository=repository,
        config_path=write_config(tmp_path),
        news_signal_store=FakeNewsStore([]),
        now_provider=lambda: now,
    )

    status = service.get_status().to_dictionary()

    assert status["overall_status"] == "DEGRADED"
    assert status["services"]["job_worker"]["status"] == "STALE"
    assert status["services"]["job_worker"]["online"] is False
