from datetime import datetime, timezone

import pytest

from app.job import (
    JobRecord,
    JobStatus,
    JobType,
)


def test_creates_queued_job() -> None:
    record = JobRecord(
        job_id="job-1",
        job_type=JobType.STRATEGY_REPORT,
        status=JobStatus.QUEUED,
        created_at=datetime.now(timezone.utc),
        payload={"force": False},
    )

    assert record.to_dictionary()["status"] == "QUEUED"
    assert record.duration_seconds is None


def test_running_job_requires_start_time() -> None:
    with pytest.raises(
        ValueError,
        match="requires a start time",
    ):
        JobRecord(
            job_id="job-1",
            job_type=JobType.STRATEGY_REPORT,
            status=JobStatus.RUNNING,
            created_at=datetime.now(timezone.utc),
            payload={},
        )
