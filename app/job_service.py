from dataclasses import replace
from datetime import (
    datetime,
    timezone,
)
from typing import Any, Callable, Mapping
from uuid import uuid4

from app.application_errors import (
    ApplicationError,
    DataStoreError,
)
from app.job import (
    JobRecord,
    JobStatus,
    JobType,
)
from app.job_repository import JobRepository


class JobService:
    def __init__(
        self,
        *,
        repository: JobRepository,
        now_provider: Callable[[], datetime] | None = None,
        job_id_provider: Callable[[], str] | None = None,
    ) -> None:
        self._repository = repository
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )
        self._job_id_provider = job_id_provider or (
            lambda: str(uuid4())
        )

    def initialize(self) -> None:
        self._repository.initialize()

    def enqueue(
        self,
        *,
        job_type: JobType,
        payload: Mapping[str, Any],
        idempotency_key: str | None = None,
    ) -> JobRecord:
        if idempotency_key is not None:
            existing = self._repository.get_by_idempotency_key(
                idempotency_key=idempotency_key
            )
            if existing is not None:
                return existing

        record = JobRecord(
            job_id=self._job_id_provider(),
            job_type=job_type,
            status=JobStatus.QUEUED,
            created_at=self._utc_now(),
            payload=dict(payload),
            idempotency_key=idempotency_key,
        )
        try:
            self._repository.add(record=record)
        except DataStoreError as error:
            if idempotency_key is None or error.code != "JOB_DUPLICATE":
                raise
            existing = self._repository.get_by_idempotency_key(
                idempotency_key=idempotency_key
            )
            if existing is None:
                raise
            return existing
        return record

    def claim_next(
        self,
    ) -> JobRecord | None:
        return self._repository.claim_next_queued(
            started_at=self._utc_now()
        )

    def complete(
        self,
        *,
        job_id: str,
        result: Mapping[str, Any],
        with_warnings: bool = False,
    ) -> JobRecord:
        current = self._require_running(job_id)
        completed = replace(
            current,
            status=(
                JobStatus.SUCCEEDED_WITH_WARNINGS
                if with_warnings
                else JobStatus.SUCCEEDED
            ),
            finished_at=self._utc_now(),
            result=dict(result),
        )
        self._repository.update(record=completed)
        return completed

    def fail(
        self,
        *,
        job_id: str,
        error: Exception,
    ) -> JobRecord:
        current = self._require_running(job_id)

        if isinstance(error, ApplicationError):
            error_code = error.code
            error_summary = error.message
        else:
            error_code = "UNEXPECTED_ERROR"
            error_summary = (
                "The job failed unexpectedly."
            )

        failed = replace(
            current,
            status=JobStatus.FAILED,
            finished_at=self._utc_now(),
            error_code=error_code,
            error_summary=error_summary,
        )
        self._repository.update(record=failed)
        return failed

    def get(
        self,
        *,
        job_id: str,
    ) -> JobRecord | None:
        return self._repository.get(job_id=job_id)

    def list_recent(
        self,
        *,
        limit: int = 50,
        status: JobStatus | None = None,
        job_type: JobType | None = None,
    ) -> tuple[JobRecord, ...]:
        return self._repository.list_recent(
            limit=limit,
            status=status,
            job_type=job_type,
        )

    def _require_running(
        self,
        job_id: str,
    ) -> JobRecord:
        record = self._repository.get(job_id=job_id)

        if record is None:
            raise DataStoreError(
                "Job was not found.",
                code="JOB_NOT_FOUND",
                context={"job_id": job_id},
            )

        if record.status != JobStatus.RUNNING:
            raise DataStoreError(
                "Job is not running.",
                code="JOB_NOT_RUNNING",
                context={
                    "job_id": job_id,
                    "status": record.status.value,
                },
            )

        return record

    def _utc_now(self) -> datetime:
        value = self._now_provider()

        if value.tzinfo is None:
            raise ValueError(
                "Job clock must return a timezone-aware "
                "datetime."
            )

        return value.astimezone(timezone.utc)