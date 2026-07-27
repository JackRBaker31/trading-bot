import json
import sqlite3
from datetime import datetime, timedelta, timezone

from app.job import JobStatus, JobType
from app.job_crash_reporting import JobCrashReporter
from app.job_recovery_service import JobRecoveryService
from app.job_repository import JobRepository
from app.job_service import JobService
from app.job_worker import JobWorker


class SystemExitExecutor:
    current_stage = "NEWS_RESEARCH"

    def execute(self, *, job):
        del job
        raise SystemExit("fatal stage exit")


def create_service(tmp_path):
    repository = JobRepository(
        database_path=str(tmp_path / "app.db")
    )
    service = JobService(repository=repository)
    service.initialize()
    return repository, service


def test_claim_clamps_start_to_created_time(tmp_path):
    repository, service = create_service(tmp_path)
    created = datetime.now(timezone.utc)
    queued = service.enqueue(
        job_type=JobType.INTELLIGENCE_CYCLE,
        payload={},
    )
    claimed = repository.claim_next_queued(
        started_at=created - timedelta(days=1)
    )
    assert claimed is not None
    assert claimed.started_at >= claimed.created_at


def test_worker_contains_system_exit_and_records_crash(tmp_path):
    _, service = create_service(tmp_path)
    queued = service.enqueue(
        job_type=JobType.INTELLIGENCE_CYCLE,
        payload={},
    )
    reporter = JobCrashReporter(
        crash_directory=str(tmp_path / "crashes")
    )
    worker = JobWorker(
        job_service=service,
        executor=SystemExitExecutor(),
        crash_reporter=reporter,
    )
    assert worker.run_once() is True
    failed = service.get(job_id=queued.job_id)
    assert failed.status is JobStatus.FAILED
    reports = list((tmp_path / "crashes").glob("*.json"))
    assert len(reports) == 1
    payload = json.loads(reports[0].read_text(encoding="utf-8"))
    assert payload["stage"] == "NEWS_RESEARCH"
    assert payload["exception_type"] == "SystemExit"


def test_startup_reconciles_stale_running_jobs(tmp_path):
    repository, service = create_service(tmp_path)
    queued = service.enqueue(
        job_type=JobType.INTELLIGENCE_CYCLE,
        payload={},
    )
    claimed = service.claim_next()
    assert claimed is not None
    old = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    with sqlite3.connect(tmp_path / "app.db") as connection:
        connection.execute(
            "UPDATE jobs SET started_at = ? WHERE job_id = ?",
            (old, queued.job_id),
        )
        connection.commit()
    summary = JobRecoveryService(
        repository=repository,
        stale_after_seconds=60,
    ).reconcile()
    assert summary.reconciled_count == 1
    recovered = service.get(job_id=queued.job_id)
    assert recovered.status is JobStatus.FAILED
    assert recovered.error_code == "WORKER_INTERRUPTED"
