from datetime import datetime, timedelta, timezone

from app.job import JobType
from app.scheduled_task import ScheduledTask, ScheduleKind
from app.scheduled_task_repository import ScheduledTaskRepository


def create_task(now: datetime) -> ScheduledTask:
    return ScheduledTask(
        schedule_id="hourly-news",
        task_type=JobType.NEWS_RESEARCH_CYCLE,
        enabled=True,
        schedule_kind=ScheduleKind.INTERVAL,
        timezone_name="UTC",
        interval_seconds=3600,
        next_run_at=now,
        created_at=now,
        updated_at=now,
    )


def test_adds_loads_and_lists_schedule(tmp_path) -> None:
    repository = ScheduledTaskRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    now = datetime.now(timezone.utc)
    repository.add(task=create_task(now))

    assert repository.get(schedule_id="hourly-news") is not None
    assert len(repository.list_all()) == 1


def test_claims_due_schedule_once(tmp_path) -> None:
    repository = ScheduledTaskRepository(
        database_path=str(tmp_path / "app.db")
    )
    repository.initialize()
    now = datetime.now(timezone.utc)
    repository.add(task=create_task(now))

    first = repository.claim_next_due(
        now=now,
        claimed_until=now + timedelta(seconds=60),
        claim_token="claim-1",
    )
    second = repository.claim_next_due(
        now=now,
        claimed_until=now + timedelta(seconds=60),
        claim_token="claim-2",
    )

    assert first is not None
    assert second is None