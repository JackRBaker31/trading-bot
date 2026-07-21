from datetime import datetime, timezone

from app.job import JobType, JobStatus
from app.job_repository import JobRepository
from app.job_service import JobService
from app.job_worker import JobWorker


class SuccessfulExecutor:
    def execute(self, *, job):
        assert job.job_type == JobType.STRATEGY_REPORT
        return {"verdict": "PROMISING"}, False


class FailingExecutor:
    def execute(self, *, job):
        del job
        raise RuntimeError("internal detail")


def create_service(tmp_path) -> JobService:
    service = JobService(
        repository=JobRepository(
            database_path=str(tmp_path / "app.db")
        )
    )
    service.initialize()
    return service


def test_worker_processes_one_job(tmp_path) -> None:
    service = create_service(tmp_path)
    queued = service.enqueue(
        job_type=JobType.STRATEGY_REPORT,
        payload={},
    )
    worker = JobWorker(
        job_service=service,
        executor=SuccessfulExecutor(),
    )

    assert worker.run_once() is True
    completed = service.get(job_id=queued.job_id)
    assert completed is not None
    assert completed.status == JobStatus.SUCCEEDED


def test_worker_records_failure_and_continues(
    tmp_path,
) -> None:
    service = create_service(tmp_path)
    queued = service.enqueue(
        job_type=JobType.STRATEGY_REPORT,
        payload={},
    )
    worker = JobWorker(
        job_service=service,
        executor=FailingExecutor(),
    )

    assert worker.run_once() is True
    failed = service.get(job_id=queued.job_id)
    assert failed is not None
    assert failed.status == JobStatus.FAILED
    assert "internal detail" not in (
        failed.error_summary or ""
    )
