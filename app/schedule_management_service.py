from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from uuid import uuid4

from app.job import JobRecord, JobType
from app.job_service import JobService
from app.scheduled_task import CatchUpPolicy, ScheduledTask, ScheduleKind
from app.scheduled_task_repository import ScheduledTaskRepository


ALLOWED_SCHEDULE_JOB_TYPES = frozenset({
    JobType.NEWS_RESEARCH_CYCLE,
    JobType.STRATEGY_REPORT,
    JobType.SHADOW_ANALYSIS,
    JobType.INTELLIGENCE_CYCLE,
})


class ScheduleManagementService:
    def __init__(
        self, *, repository: ScheduledTaskRepository, job_service: JobService,
        now_provider: Callable[[], datetime] | None = None,
        schedule_id_provider: Callable[[], str] | None = None,
    ) -> None:
        self._repository = repository
        self._job_service = job_service
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))
        self._schedule_id_provider = schedule_id_provider or (lambda: str(uuid4()))

    def initialize(self) -> None:
        self._repository.initialize()
        self._job_service.initialize()

    def list(self) -> tuple[ScheduledTask, ...]:
        return self._repository.list_all()

    def get(self, *, schedule_id: str) -> ScheduledTask | None:
        return self._repository.get(schedule_id=schedule_id)

    def create(
        self, *, task_type: JobType, enabled: bool, schedule_kind: ScheduleKind,
        timezone_name: str, payload: Mapping[str, Any],
        interval_seconds: int | None = None, local_hour: int | None = None,
        local_minute: int | None = None, weekday: int | None = None,
        catch_up_policy: CatchUpPolicy = CatchUpPolicy.RUN_ONCE,
        catch_up_window_seconds: int | None = None,
        schedule_id: str | None = None,
    ) -> ScheduledTask:
        self._validate_task_type(task_type)
        now = self._utc_now()
        identifier = (schedule_id or self._schedule_id_provider()).strip()
        seed = ScheduledTask(
            schedule_id=identifier, task_type=task_type, enabled=enabled,
            schedule_kind=schedule_kind, timezone_name=timezone_name,
            next_run_at=now, payload=payload, interval_seconds=interval_seconds,
            local_hour=local_hour, local_minute=local_minute, weekday=weekday,
            catch_up_policy=catch_up_policy,
            catch_up_window_seconds=catch_up_window_seconds,
            created_at=now, updated_at=now,
        )
        task = ScheduledTask(**{**seed.__dict__,
            "next_run_at": seed.calculate_next_run(after=now)})
        self._repository.add(task=task)
        return task

    def update(self, *, schedule_id: str, **changes: Any) -> ScheduledTask | None:
        existing = self.get(schedule_id=schedule_id)
        if existing is None:
            return None
        task_type = changes.get("task_type", existing.task_type)
        self._validate_task_type(task_type)
        now = self._utc_now()
        values = {**existing.__dict__, **changes, "schedule_id": schedule_id,
                  "updated_at": now, "claim_token": None,
                  "claimed_until": None}
        candidate = ScheduledTask(**values)
        timing_fields = {"schedule_kind", "timezone_name", "interval_seconds",
                         "local_hour", "local_minute", "weekday"}
        if timing_fields.intersection(changes):
            seed = ScheduledTask(**{**candidate.__dict__, "next_run_at": now})
            candidate = ScheduledTask(**{**seed.__dict__,
                "next_run_at": seed.calculate_next_run(after=now)})
        self._repository.update(task=candidate)
        return candidate

    def set_enabled(self, *, schedule_id: str, enabled: bool) -> ScheduledTask | None:
        if not self._repository.set_enabled(
            schedule_id=schedule_id, enabled=enabled, updated_at=self._utc_now()
        ):
            return None
        return self.get(schedule_id=schedule_id)

    def delete(self, *, schedule_id: str) -> bool:
        return self._repository.delete(schedule_id=schedule_id)

    def run_now(self, *, schedule_id: str) -> JobRecord | None:
        task = self.get(schedule_id=schedule_id)
        if task is None:
            return None
        return self._job_service.enqueue(
            job_type=task.task_type, payload=dict(task.payload),
        )

    @staticmethod
    def _validate_task_type(task_type: JobType) -> None:
        if task_type not in ALLOWED_SCHEDULE_JOB_TYPES:
            raise ValueError("This job type cannot be scheduled.")

    def _utc_now(self) -> datetime:
        value = self._now_provider()
        if value.tzinfo is None:
            raise ValueError("Schedule clock must be timezone-aware.")
        return value.astimezone(timezone.utc)