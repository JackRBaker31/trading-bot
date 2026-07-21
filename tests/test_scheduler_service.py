from datetime import datetime, timedelta, timezone

from app.job import JobType
from app.job_repository import JobRepository
from app.job_service import JobService
from app.scheduled_task import CatchUpPolicy, ScheduledTask, ScheduleKind
from app.scheduled_task_repository import ScheduledTaskRepository
from app.scheduler_service import SchedulerService


def create_services(tmp_path, now: datetime):
    database = str(tmp_path / "app.db")
    schedules = ScheduledTaskRepository(database_path=database)
    jobs = JobService(
        repository=JobRepository(database_path=database),
        now_provider=lambda: now,
        job_id_provider=lambda: "job-1",
    )
    scheduler = SchedulerService(
        schedule_repository=schedules,
        job_service=jobs,
        now_provider=lambda: now,
        claim_token_provider=lambda: "claim-1",
    )
    scheduler.initialize()
    return schedules, jobs, scheduler


def test_scheduler_enqueues_due_job_and_advances_schedule(tmp_path) -> None:
    now = datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc)
    schedules, jobs, scheduler = create_services(tmp_path, now)
    schedules.add(
        task=ScheduledTask(
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
    )

    assert scheduler.run_once() is True
    saved = schedules.get(schedule_id="hourly-news")
    queued = jobs.list_recent()

    assert saved is not None
    assert saved.next_run_at == now + timedelta(hours=1)
    assert saved.last_status == "ENQUEUED"
    assert len(queued) == 1
    assert queued[0].idempotency_key is not None


def test_scheduler_skips_expired_catch_up_run(tmp_path) -> None:
    now = datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc)
    schedules, jobs, scheduler = create_services(tmp_path, now)
    schedules.add(
        task=ScheduledTask(
            schedule_id="strict-news",
            task_type=JobType.NEWS_RESEARCH_CYCLE,
            enabled=True,
            schedule_kind=ScheduleKind.INTERVAL,
            timezone_name="UTC",
            interval_seconds=3600,
            next_run_at=now - timedelta(hours=2),
            catch_up_policy=CatchUpPolicy.RUN_IF_WITHIN_WINDOW,
            catch_up_window_seconds=900,
            created_at=now,
            updated_at=now,
        )
    )

    assert scheduler.run_once() is True
    saved = schedules.get(schedule_id="strict-news")

    assert saved is not None
    assert saved.last_status == "SKIPPED_MISSED_RUN"
    assert jobs.list_recent() == ()


def test_job_enqueue_is_idempotent(tmp_path) -> None:
    database = str(tmp_path / "app.db")
    service = JobService(
        repository=JobRepository(database_path=database),
        job_id_provider=iter(("job-1", "job-2")).__next__,
    )
    service.initialize()

    first = service.enqueue(
        job_type=JobType.STRATEGY_REPORT,
        payload={},
        idempotency_key="schedule:daily:2026-07-21T20:10:00+00:00",
    )
    second = service.enqueue(
        job_type=JobType.STRATEGY_REPORT,
        payload={},
        idempotency_key="schedule:daily:2026-07-21T20:10:00+00:00",
    )

    assert first.job_id == "job-1"
    assert second.job_id == "job-1"
    assert len(service.list_recent()) == 1