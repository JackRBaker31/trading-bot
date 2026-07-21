from datetime import datetime, timedelta, timezone
from typing import Callable
from uuid import uuid4

from app.job_service import JobService
from app.scheduled_task_repository import ScheduledTaskRepository


class SchedulerService:
    def __init__(
        self,
        *,
        schedule_repository: ScheduledTaskRepository,
        job_service: JobService,
        now_provider: Callable[[], datetime] | None = None,
        claim_token_provider: Callable[[], str] | None = None,
        claim_seconds: int = 60,
    ) -> None:
        if claim_seconds <= 0:
            raise ValueError("Scheduler claim duration must be positive.")
        self._schedule_repository = schedule_repository
        self._job_service = job_service
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))
        self._claim_token_provider = claim_token_provider or (lambda: str(uuid4()))
        self._claim_seconds = claim_seconds
        self.current_schedule_id: str | None = None
        self.current_task_type: str | None = None
        self.tasks_processed = 0
        self.last_error: str | None = None

    def initialize(self) -> None:
        self._schedule_repository.initialize()
        self._job_service.initialize()

    def run_once(self) -> bool:
        now = self._utc_now()
        token = self._claim_token_provider()
        task = self._schedule_repository.claim_next_due(
            now=now,
            claimed_until=now + timedelta(seconds=self._claim_seconds),
            claim_token=token,
        )
        if task is None:
            return False

        self.current_schedule_id = task.schedule_id
        self.current_task_type = task.task_type.value
        self.last_error = None
        try:
            should_run = task.should_run(now=now)
            job = None
            status = "SKIPPED_MISSED_RUN"
            if should_run:
                job = self._job_service.enqueue(
                    job_type=task.task_type,
                    payload=task.payload,
                    idempotency_key=task.due_run_key(),
                )
                status = "ENQUEUED"

            completed = self._schedule_repository.complete_claim(
                schedule_id=task.schedule_id,
                claim_token=token,
                next_run_at=task.calculate_next_run(after=now),
                last_run_at=now,
                last_job_id=None if job is None else job.job_id,
                last_status=status,
                updated_at=now,
            )
            if not completed:
                raise RuntimeError("Schedule claim was lost before completion.")
            self.tasks_processed += 1
            return True
        except Exception as error:
            self.last_error = f"{type(error).__name__}: {error}"
            self._schedule_repository.release_claim(
                schedule_id=task.schedule_id,
                claim_token=token,
                last_status="SCHEDULER_ERROR",
                updated_at=self._utc_now(),
            )
            raise
        finally:
            self.current_schedule_id = None
            self.current_task_type = None

    def _utc_now(self) -> datetime:
        value = self._now_provider()
        if value.tzinfo is None:
            raise ValueError("Scheduler clock must be timezone-aware.")
        return value.astimezone(timezone.utc)