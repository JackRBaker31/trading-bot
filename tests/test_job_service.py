from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.application_errors import (
    ProviderUnavailableError,
)
from app.job import JobStatus, JobType
from app.job_repository import JobRepository
from app.job_service import JobService


def create_service(tmp_path) -> JobService:
    times = iter(
        [
            datetime(2026, 7, 20, 10, 0, tzinfo=timezone.utc),
            datetime(2026, 7, 20, 10, 0, 1, tzinfo=timezone.utc),
            datetime(2026, 7, 20, 10, 0, 2, tzinfo=timezone.utc),
        ]
    )
    service = JobService(
        repository=JobRepository(
            database_path=str(tmp_path / "app.db")
        ),
        now_provider=lambda: next(times),
        job_id_provider=lambda: "job-1",
    )
    service.initialize()
    return service


def test_enqueues_claims_and_completes_job(
    tmp_path,
) -> None:
    service = create_service(tmp_path)
    queued = service.enqueue(
        job_type=JobType.STRATEGY_REPORT,
        payload={"force": False},
    )
    running = service.claim_next()
    completed = service.complete(
        job_id=queued.job_id,
        result={"verdict": "PROMISING"},
    )

    assert running is not None
    assert running.status == JobStatus.RUNNING
    assert completed.status == JobStatus.SUCCEEDED
    assert completed.result["verdict"] == "PROMISING"


def test_failure_uses_safe_application_error(
    tmp_path,
) -> None:
    service = create_service(tmp_path)
    queued = service.enqueue(
        job_type=JobType.NEWS_RESEARCH_CYCLE,
        payload={"symbols": ["AAPL"]},
    )
    service.claim_next()

    failed = service.fail(
        job_id=queued.job_id,
        error=ProviderUnavailableError(
            "Provider is unavailable.",
            code="PROVIDER_DOWN",
        ),
    )

    assert failed.status == JobStatus.FAILED
    assert failed.error_code == "PROVIDER_DOWN"
    assert failed.error_summary == (
        "Provider is unavailable."
    )
