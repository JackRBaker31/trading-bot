from datetime import datetime, timezone

import pytest

from app.job import JobType
from app.job_repository import JobRepository
from app.job_service import JobService
from app.schedule_management_service import ScheduleManagementService
from app.scheduled_task import CatchUpPolicy, ScheduleKind
from app.scheduled_task_repository import ScheduledTaskRepository


def make_service(tmp_path):
    database = str(tmp_path / "app.db")
    now = datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc)
    service = ScheduleManagementService(
        repository=ScheduledTaskRepository(database_path=database),
        job_service=JobService(repository=JobRepository(database_path=database), now_provider=lambda: now, job_id_provider=lambda: "job-1"),
        now_provider=lambda: now, schedule_id_provider=lambda: "schedule-1",
    )
    service.initialize()
    return service, now


def test_creates_updates_enables_and_deletes_schedule(tmp_path):
    service, now = make_service(tmp_path)
    created = service.create(task_type=JobType.INTELLIGENCE_CYCLE, enabled=True, schedule_kind=ScheduleKind.INTERVAL, timezone_name="UTC", interval_seconds=3600, payload={"symbols": ["AAPL"]})
    assert created.schedule_id == "schedule-1"
    assert created.next_run_at.isoformat() == "2026-07-21T13:00:00+00:00"
    updated = service.update(schedule_id=created.schedule_id, task_type=JobType.INTELLIGENCE_CYCLE, enabled=True, schedule_kind=ScheduleKind.INTERVAL, timezone_name="UTC", interval_seconds=1800, local_hour=None, local_minute=None, weekday=None, payload={}, catch_up_policy=CatchUpPolicy.RUN_ONCE, catch_up_window_seconds=None)
    assert updated is not None and updated.next_run_at.isoformat() == "2026-07-21T12:30:00+00:00"
    assert service.set_enabled(schedule_id=created.schedule_id, enabled=False).enabled is False
    assert service.delete(schedule_id=created.schedule_id) is True
    assert service.get(schedule_id=created.schedule_id) is None


def test_run_now_queues_existing_job(tmp_path):
    service, _ = make_service(tmp_path)
    service.create(task_type=JobType.STRATEGY_REPORT, enabled=True, schedule_kind=ScheduleKind.DAILY, timezone_name="UTC", local_hour=16, local_minute=10, payload={"force": False})
    job = service.run_now(schedule_id="schedule-1")
    assert job is not None
    assert job.job_type == JobType.STRATEGY_REPORT


def test_rejects_non_research_job_type(tmp_path):
    service, _ = make_service(tmp_path)
    with pytest.raises(ValueError, match="cannot be scheduled"):
        service.create(task_type="PAPER_TRADING_START",  # type: ignore[arg-type]
             enabled=True, schedule_kind=ScheduleKind.INTERVAL, timezone_name="UTC", interval_seconds=60, payload={})