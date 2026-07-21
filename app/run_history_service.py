from dataclasses import replace
from datetime import (
    datetime,
    timezone,
)
from typing import Callable, Mapping, Any
from uuid import uuid4

from app.application_errors import (
    ApplicationError,
    DataStoreError,
)
from app.run_history import (
    RunHistoryRecord,
    RunStatus,
    RunType,
)
from app.run_history_repository import (
    RunHistoryRepository,
)


class RunHistoryService:
    def __init__(
        self,
        *,
        repository: RunHistoryRepository,
        now_provider: Callable[[], datetime] | None = None,
        run_id_provider: Callable[[], str] | None = None,
    ) -> None:
        self._repository = repository
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )
        self._run_id_provider = run_id_provider or (
            lambda: str(uuid4())
        )

    def initialize(self) -> None:
        self._repository.initialize()

    def start_run(
        self,
        *,
        run_type: RunType,
        provider: str | None = None,
        symbols: tuple[str, ...] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> RunHistoryRecord:
        record = RunHistoryRecord(
            run_id=self._run_id_provider(),
            run_type=run_type,
            status=RunStatus.RUNNING,
            started_at=self._utc_now(),
            provider=provider,
            symbols=symbols,
            metadata=dict(metadata or {}),
        )
        self._repository.add(
            record=record
        )
        return record

    def complete_run(
        self,
        *,
        run_id: str,
        created_count: int = 0,
        skipped_count: int = 0,
        failure_count: int = 0,
        metadata: Mapping[str, Any] | None = None,
    ) -> RunHistoryRecord:
        current = self._require_running_record(
            run_id
        )

        completed_status = (
            RunStatus.SUCCEEDED_WITH_WARNINGS
            if failure_count > 0
            else RunStatus.SUCCEEDED
        )

        completed = replace(
            current,
            status=completed_status,
            finished_at=self._utc_now(),
            created_count=created_count,
            skipped_count=skipped_count,
            failure_count=failure_count,
            metadata={
                **dict(current.metadata),
                **dict(metadata or {}),
            },
        )
        self._repository.update(
            record=completed
        )
        return completed

    def fail_run(
        self,
        *,
        run_id: str,
        error: Exception,
        failure_count: int = 1,
        metadata: Mapping[str, Any] | None = None,
    ) -> RunHistoryRecord:
        current = self._require_running_record(
            run_id
        )

        if isinstance(
            error,
            ApplicationError,
        ):
            error_code = error.code
            error_summary = error.message
            error_context = error.context
        else:
            error_code = "UNEXPECTED_ERROR"
            error_summary = (
                "The operation failed unexpectedly."
            )
            error_context = {}

        failed = replace(
            current,
            status=RunStatus.FAILED,
            finished_at=self._utc_now(),
            failure_count=failure_count,
            error_code=error_code,
            error_summary=error_summary,
            metadata={
                **dict(current.metadata),
                **dict(metadata or {}),
                **(
                    {"error_context": error_context}
                    if error_context
                    else {}
                ),
            },
        )
        self._repository.update(
            record=failed
        )
        return failed

    def get_run(
        self,
        *,
        run_id: str,
    ) -> RunHistoryRecord | None:
        return self._repository.get(
            run_id=run_id
        )

    def list_recent(
        self,
        *,
        limit: int = 50,
        run_type: RunType | None = None,
    ) -> tuple[RunHistoryRecord, ...]:
        return self._repository.list_recent(
            limit=limit,
            run_type=run_type,
        )

    def _require_running_record(
        self,
        run_id: str,
    ) -> RunHistoryRecord:
        record = self._repository.get(
            run_id=run_id
        )

        if record is None:
            raise DataStoreError(
                "Run-history record was not found.",
                code="RUN_HISTORY_NOT_FOUND",
                context={"run_id": run_id},
            )

        if record.status != RunStatus.RUNNING:
            raise DataStoreError(
                "Run-history record is already complete.",
                code="RUN_HISTORY_ALREADY_COMPLETE",
                context={
                    "run_id": run_id,
                    "status": record.status.value,
                },
            )

        return record

    def _utc_now(
        self,
    ) -> datetime:
        value = self._now_provider()

        if value.tzinfo is None:
            raise ValueError(
                "Run-history clock must return "
                "a timezone-aware datetime."
            )

        return value.astimezone(
            timezone.utc
        )