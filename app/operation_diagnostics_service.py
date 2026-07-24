from collections.abc import Callable
from datetime import datetime, timezone
from time import perf_counter
from typing import TypeVar
from uuid import uuid4

from app.operation_diagnostics_models import (
    OperationDiagnosticEvent,
)
from app.operation_diagnostics_repository import (
    OperationDiagnosticsRepository,
)


T = TypeVar("T")


class OperationDiagnosticsService:
    def __init__(
        self,
        *,
        repository: (
            OperationDiagnosticsRepository
        ),
    ) -> None:
        self._repository = repository

    def initialize(self) -> None:
        self._repository.initialize()

    def record(
        self,
        *,
        stage: str,
        operation: str,
        status: str,
        job_id: str | None = None,
        severity: str = "INFO",
        symbol: str | None = None,
        provider: str | None = None,
        error_code: str | None = None,
        error_summary: str | None = None,
        retryable: bool = False,
        retry_count: int = 0,
        recovered: bool = False,
        latency_ms: float | None = None,
        cache_status: str | None = None,
        context: dict[str, object] | None = None,
    ) -> OperationDiagnosticEvent:
        event = OperationDiagnosticEvent(
            event_id=(
                "DIAG-"
                + uuid4().hex[:16].upper()
            ),
            job_id=job_id,
            stage=stage,
            operation=operation,
            occurred_at=datetime.now(
                timezone.utc
            ),
            severity=severity,
            status=status,
            symbol=symbol,
            provider=provider,
            error_code=error_code,
            error_summary=error_summary,
            retryable=retryable,
            retry_count=retry_count,
            recovered=recovered,
            latency_ms=latency_ms,
            cache_status=cache_status,
            context=dict(context or {}),
        )
        self._repository.save(
            event=event
        )
        return event

    def run(
        self,
        *,
        stage: str,
        operation: str,
        action: Callable[[], T],
        job_id: str | None = None,
        symbol: str | None = None,
        provider: str | None = None,
        retryable: bool = False,
        retry_count: int = 0,
        cache_status: str | None = None,
        context: dict[str, object] | None = None,
    ) -> T:
        started = perf_counter()

        try:
            result = action()
        except Exception as error:
            latency = (
                perf_counter() - started
            ) * 1000

            self.record(
                stage=stage,
                operation=operation,
                status="FAILED",
                job_id=job_id,
                severity="WARNING",
                symbol=symbol,
                provider=provider,
                error_code=type(error).__name__,
                error_summary=str(error),
                retryable=retryable,
                retry_count=retry_count,
                recovered=False,
                latency_ms=round(
                    latency,
                    3,
                ),
                cache_status=cache_status,
                context=context,
            )
            raise

        latency = (
            perf_counter() - started
        ) * 1000

        self.record(
            stage=stage,
            operation=operation,
            status="SUCCEEDED",
            job_id=job_id,
            severity="INFO",
            symbol=symbol,
            provider=provider,
            retry_count=retry_count,
            recovered=retry_count > 0,
            latency_ms=round(
                latency,
                3,
            ),
            cache_status=cache_status,
            context=context,
        )
        return result

    def for_job(
        self,
        *,
        job_id: str,
    ) -> tuple[
        OperationDiagnosticEvent,
        ...
    ]:
        return self._repository.list_for_job(
            job_id=job_id
        )

    def recent(
        self,
        *,
        limit: int = 100,
    ) -> tuple[
        OperationDiagnosticEvent,
        ...
    ]:
        return self._repository.list_recent(
            limit=limit
        )
