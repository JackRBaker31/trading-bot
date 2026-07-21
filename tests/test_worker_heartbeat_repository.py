from datetime import datetime, timezone

from app.worker_heartbeat import WorkerHeartbeat
from app.worker_heartbeat_repository import (
    WorkerHeartbeatRepository,
)


def test_saves_and_loads_worker_heartbeat(
    tmp_path,
) -> None:
    repository = WorkerHeartbeatRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    now = datetime.now(timezone.utc)

    repository.register(
        heartbeat=WorkerHeartbeat(
            worker_name="primary-job-worker",
            process_id=123,
            status="IDLE",
            started_at=now,
            last_heartbeat_at=now,
            current_job_id=None,
            current_job_type=None,
            jobs_processed=4,
        )
    )

    saved = repository.get(
        worker_name="primary-job-worker"
    )

    assert saved is not None
    assert saved.process_id == 123
    assert saved.jobs_processed == 4
    assert repository.ping() is True


def test_marks_worker_stopped(tmp_path) -> None:
    repository = WorkerHeartbeatRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    now = datetime.now(timezone.utc)
    repository.register(
        heartbeat=WorkerHeartbeat(
            worker_name="primary-job-worker",
            process_id=123,
            status="BUSY",
            started_at=now,
            last_heartbeat_at=now,
            current_job_id="job-1",
            current_job_type="STRATEGY_REPORT",
            jobs_processed=1,
        )
    )

    repository.mark_stopped(
        worker_name="primary-job-worker",
        stopped_at=now,
        jobs_processed=2,
    )

    saved = repository.get(
        worker_name="primary-job-worker"
    )
    assert saved is not None
    assert saved.status == "STOPPED"
    assert saved.current_job_id is None
