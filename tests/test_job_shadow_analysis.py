from datetime import datetime, timezone

from app.job import JobRecord, JobStatus, JobType
from app.job_executor import JobExecutor


def test_dispatches_shadow_analysis(monkeypatch) -> None:
    executor = JobExecutor()
    expected = ({"decisions_created": 2}, False)
    monkeypatch.setattr(
        executor,
        "_execute_shadow_analysis",
        lambda payload: expected,
    )
    job = JobRecord(
        job_id="job-1",
        job_type=JobType.SHADOW_ANALYSIS,
        status=JobStatus.RUNNING,
        created_at=datetime(2026, 7, 20, 9, tzinfo=timezone.utc),
        started_at=datetime(2026, 7, 20, 9, 1, tzinfo=timezone.utc),
        payload={},
    )

    assert executor.execute(job=job) == expected
