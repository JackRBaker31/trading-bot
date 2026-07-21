from datetime import datetime, timezone

from app.job import JobType
from app.scheduled_task import CatchUpPolicy, ScheduledTask, ScheduleKind


def test_interval_schedule_calculates_next_future_run() -> None:
    task = ScheduledTask(
        schedule_id="hourly-news",
        task_type=JobType.NEWS_RESEARCH_CYCLE,
        enabled=True,
        schedule_kind=ScheduleKind.INTERVAL,
        timezone_name="UTC",
        interval_seconds=3600,
        next_run_at=datetime(2026, 7, 21, 10, 0, tzinfo=timezone.utc),
    )

    result = task.calculate_next_run(
        after=datetime(2026, 7, 21, 12, 15, tzinfo=timezone.utc)
    )

    assert result == datetime(2026, 7, 21, 13, 0, tzinfo=timezone.utc)


def test_daily_schedule_respects_local_timezone() -> None:
    task = ScheduledTask(
        schedule_id="daily-report",
        task_type=JobType.STRATEGY_REPORT,
        enabled=True,
        schedule_kind=ScheduleKind.DAILY,
        timezone_name="America/New_York",
        local_hour=16,
        local_minute=10,
        next_run_at=datetime(2026, 7, 21, 20, 10, tzinfo=timezone.utc),
    )

    result = task.calculate_next_run(
        after=datetime(2026, 7, 21, 20, 11, tzinfo=timezone.utc)
    )

    assert result == datetime(2026, 7, 22, 20, 10, tzinfo=timezone.utc)


def test_catch_up_window_blocks_old_run() -> None:
    task = ScheduledTask(
        schedule_id="limited-catch-up",
        task_type=JobType.NEWS_RESEARCH_CYCLE,
        enabled=True,
        schedule_kind=ScheduleKind.INTERVAL,
        timezone_name="UTC",
        interval_seconds=3600,
        next_run_at=datetime(2026, 7, 21, 10, 0, tzinfo=timezone.utc),
        catch_up_policy=CatchUpPolicy.RUN_IF_WITHIN_WINDOW,
        catch_up_window_seconds=900,
    )

    assert task.should_run(
        now=datetime(2026, 7, 21, 10, 10, tzinfo=timezone.utc)
    ) is True
    assert task.should_run(
        now=datetime(2026, 7, 21, 10, 16, tzinfo=timezone.utc)
    ) is False