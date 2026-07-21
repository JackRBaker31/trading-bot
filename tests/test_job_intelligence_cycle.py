from datetime import datetime, timezone

from app.job import JobRecord, JobStatus, JobType
from app.job_executor import JobExecutor


def test_dispatches_intelligence_cycle(monkeypatch) -> None:
    executor = JobExecutor()
    expected = ({"stage_count": 7}, False)
    monkeypatch.setattr(
        executor,
        "_execute_intelligence_cycle",
        lambda payload: expected,
    )
    job = JobRecord(
        job_id="job-1",
        job_type=JobType.INTELLIGENCE_CYCLE,
        status=JobStatus.RUNNING,
        created_at=datetime(2026, 7, 21, 9, tzinfo=timezone.utc),
        started_at=datetime(2026, 7, 21, 9, 1, tzinfo=timezone.utc),
        payload={"symbols": ["AAPL"]},
    )

    assert executor.execute(job=job) == expected