import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.job import JobType


class ScheduleKind(str, Enum):
    INTERVAL = "INTERVAL"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"


class CatchUpPolicy(str, Enum):
    SKIP = "SKIP"
    RUN_ONCE = "RUN_ONCE"
    RUN_IF_WITHIN_WINDOW = "RUN_IF_WITHIN_WINDOW"


@dataclass(frozen=True)
class ScheduledTask:
    schedule_id: str
    task_type: JobType
    enabled: bool
    schedule_kind: ScheduleKind
    timezone_name: str
    next_run_at: datetime
    payload: Mapping[str, Any] = field(default_factory=dict)
    interval_seconds: int | None = None
    local_hour: int | None = None
    local_minute: int | None = None
    weekday: int | None = None
    catch_up_policy: CatchUpPolicy = CatchUpPolicy.RUN_ONCE
    catch_up_window_seconds: int | None = None
    last_run_at: datetime | None = None
    last_job_id: str | None = None
    last_status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    claim_token: str | None = None
    claimed_until: datetime | None = None

    def __post_init__(self) -> None:
        if not self.schedule_id.strip():
            raise ValueError("Schedule ID is required.")
        try:
            ZoneInfo(self.timezone_name)
        except ZoneInfoNotFoundError as error:
            raise ValueError("Schedule timezone is invalid.") from error

        for name, value in (
            ("next_run_at", self.next_run_at),
            ("last_run_at", self.last_run_at),
            ("created_at", self.created_at),
            ("updated_at", self.updated_at),
            ("claimed_until", self.claimed_until),
        ):
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware.")

        if self.schedule_kind == ScheduleKind.INTERVAL:
            if self.interval_seconds is None or self.interval_seconds <= 0:
                raise ValueError("Interval schedules require a positive interval.")
        else:
            if self.local_hour is None or not 0 <= self.local_hour <= 23:
                raise ValueError("Calendar schedules require a valid local hour.")
            if self.local_minute is None or not 0 <= self.local_minute <= 59:
                raise ValueError("Calendar schedules require a valid local minute.")

        if self.schedule_kind == ScheduleKind.WEEKLY:
            if self.weekday is None or not 0 <= self.weekday <= 6:
                raise ValueError("Weekly schedules require weekday 0 to 6.")

        if self.catch_up_policy == CatchUpPolicy.RUN_IF_WITHIN_WINDOW:
            if self.catch_up_window_seconds is None or self.catch_up_window_seconds <= 0:
                raise ValueError("Catch-up window must be positive.")

        object.__setattr__(self, "payload", dict(self.payload))

    def payload_json(self) -> str:
        return json.dumps(dict(self.payload), sort_keys=True)

    def due_run_key(self) -> str:
        due = self.next_run_at.astimezone(timezone.utc).isoformat()
        return f"schedule:{self.schedule_id}:{due}"

    def should_run(self, *, now: datetime) -> bool:
        now_utc = _utc(now)
        lateness = (now_utc - _utc(self.next_run_at)).total_seconds()
        if lateness < 0:
            return False
        if self.catch_up_policy == CatchUpPolicy.SKIP and lateness > 0:
            return False
        if self.catch_up_policy == CatchUpPolicy.RUN_IF_WITHIN_WINDOW:
            assert self.catch_up_window_seconds is not None
            return lateness <= self.catch_up_window_seconds
        return True

    def calculate_next_run(self, *, after: datetime) -> datetime:
        after_utc = _utc(after)
        if self.schedule_kind == ScheduleKind.INTERVAL:
            assert self.interval_seconds is not None
            candidate = _utc(self.next_run_at)
            step = timedelta(seconds=self.interval_seconds)
            while candidate <= after_utc:
                candidate += step
            return candidate

        zone = ZoneInfo(self.timezone_name)
        local_after = after_utc.astimezone(zone)
        assert self.local_hour is not None
        assert self.local_minute is not None

        candidate = local_after.replace(
            hour=self.local_hour,
            minute=self.local_minute,
            second=0,
            microsecond=0,
        )
        if self.schedule_kind == ScheduleKind.DAILY:
            if candidate <= local_after:
                candidate += timedelta(days=1)
            return candidate.astimezone(timezone.utc)

        assert self.weekday is not None
        days_ahead = (self.weekday - candidate.weekday()) % 7
        candidate += timedelta(days=days_ahead)
        if candidate <= local_after:
            candidate += timedelta(days=7)
        return candidate.astimezone(timezone.utc)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Schedule clock must be timezone-aware.")
    return value.astimezone(timezone.utc)