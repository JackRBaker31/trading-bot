from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.job_repository import JobRepository


@dataclass(frozen=True)
class JobRecoverySummary:
    reconciled_count: int
    cutoff: datetime
    recovered_at: datetime


class JobRecoveryService:
    def __init__(
        self,
        *,
        repository: JobRepository,
        stale_after_seconds: float = 300.0,
    ) -> None:
        if stale_after_seconds <= 0:
            raise ValueError("Stale-job threshold must be positive.")
        self._repository = repository
        self._stale_after_seconds = stale_after_seconds

    def reconcile(self) -> JobRecoverySummary:
        recovered_at = datetime.now(timezone.utc)
        cutoff = recovered_at - timedelta(
            seconds=self._stale_after_seconds
        )
        count = self._repository.reconcile_stale_running(
            cutoff=cutoff,
            finished_at=recovered_at,
        )
        return JobRecoverySummary(
            reconciled_count=count,
            cutoff=cutoff,
            recovered_at=recovered_at,
        )
