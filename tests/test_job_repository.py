from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.job import (
    JobRecord,
    JobStatus,
    JobType,
)
from app.job_repository import JobRepository


def create_job(
    *,
    job_id: str,
    created_at: datetime,
) -> JobRecord:
    return JobRecord(
        job_id=job_id,
        job_type=JobType.NEWS_RESEARCH_CYCLE,
        status=JobStatus.QUEUED,
        created_at=created_at,
        payload={"symbols": ["AAPL"]},
    )


def test_adds_and_loads_job(tmp_path) -> None:
    repository = JobRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    record = create_job(
        job_id="job-1",
        created_at=datetime.now(timezone.utc),
    )

    repository.add(record=record)

    assert repository.get(job_id="job-1") == record


def test_claims_oldest_queued_job_atomically(
    tmp_path,
) -> None:
    repository = JobRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    now = datetime.now(timezone.utc)
    repository.add(
        record=create_job(
            job_id="first",
            created_at=now,
        )
    )
    repository.add(
        record=create_job(
            job_id="second",
            created_at=now + timedelta(seconds=1),
        )
    )

    claimed = repository.claim_next_queued(
        started_at=now + timedelta(seconds=2)
    )

    assert claimed is not None
    assert claimed.job_id == "first"
    assert claimed.status == JobStatus.RUNNING
    assert repository.get(job_id="second").status == (
        JobStatus.QUEUED
    )
