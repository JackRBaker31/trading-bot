from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class OperationDiagnosticEvent:
    event_id: str
    job_id: str | None
    stage: str
    operation: str
    occurred_at: datetime
    severity: str
    status: str
    symbol: str | None
    provider: str | None
    error_code: str | None
    error_summary: str | None
    retryable: bool
    retry_count: int
    recovered: bool
    latency_ms: float | None
    cache_status: str | None
    context: dict[str, object]

    def to_dictionary(self) -> dict[str, object]:
        return {
            **asdict(self),
            "occurred_at": self.occurred_at.isoformat(),
        }


@dataclass(frozen=True)
class StageDiagnostic:
    stage: str
    display_name: str
    status: str
    duration_ms: float | None
    detail: dict[str, object]
    warnings: tuple[str, ...]
    events: tuple[
        OperationDiagnosticEvent,
        ...
    ]
    event_count: int
    failure_count: int
    retry_count: int
    recovered_count: int
    cache_hit_count: int
    average_latency_ms: float | None
    diagnostics_complete: bool

    def to_dictionary(self) -> dict[str, object]:
        return {
            "stage": self.stage,
            "display_name": self.display_name,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "detail": self.detail,
            "warnings": list(self.warnings),
            "events": [
                event.to_dictionary()
                for event in self.events
            ],
            "event_count": self.event_count,
            "failure_count": self.failure_count,
            "retry_count": self.retry_count,
            "recovered_count": self.recovered_count,
            "cache_hit_count": self.cache_hit_count,
            "average_latency_ms": self.average_latency_ms,
            "diagnostics_complete": self.diagnostics_complete,
        }


@dataclass(frozen=True)
class JobDiagnosticReport:
    job_id: str
    job_type: str
    status: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: float | None
    trading_impact: str | None
    stages: tuple[
        StageDiagnostic,
        ...
    ]
    warning_count: int
    failure_count: int
    retry_count: int
    recovered_count: int
    cache_hit_count: int
    average_latency_ms: float | None
    diagnostics_complete: bool

    def to_dictionary(self) -> dict[str, object]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": (
                self.started_at.isoformat()
                if self.started_at is not None
                else None
            ),
            "finished_at": (
                self.finished_at.isoformat()
                if self.finished_at is not None
                else None
            ),
            "duration_ms": self.duration_ms,
            "trading_impact": self.trading_impact,
            "stages": [
                stage.to_dictionary()
                for stage in self.stages
            ],
            "warning_count": self.warning_count,
            "failure_count": self.failure_count,
            "retry_count": self.retry_count,
            "recovered_count": self.recovered_count,
            "cache_hit_count": self.cache_hit_count,
            "average_latency_ms": self.average_latency_ms,
            "diagnostics_complete": self.diagnostics_complete,
        }


@dataclass(frozen=True)
class IntelligenceHealthOverview:
    generated_at: datetime
    health_status: str
    recent_job_count: int
    succeeded_count: int
    warning_count: int
    failed_count: int
    active_count: int
    operation_failure_count: int
    recovered_operation_count: int
    average_job_duration_ms: float | None
    average_operation_latency_ms: float | None
    cache_hit_rate: float | None
    retry_count: int
    latest_warning: OperationDiagnosticEvent | None
    attention_items: tuple[str, ...]
    recent_jobs: tuple[
        JobDiagnosticReport,
        ...
    ]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "health_status": self.health_status,
            "recent_job_count": self.recent_job_count,
            "succeeded_count": self.succeeded_count,
            "warning_count": self.warning_count,
            "failed_count": self.failed_count,
            "active_count": self.active_count,
            "operation_failure_count": self.operation_failure_count,
            "recovered_operation_count": self.recovered_operation_count,
            "average_job_duration_ms": self.average_job_duration_ms,
            "average_operation_latency_ms": self.average_operation_latency_ms,
            "cache_hit_rate": self.cache_hit_rate,
            "retry_count": self.retry_count,
            "latest_warning": (
                self.latest_warning.to_dictionary()
                if self.latest_warning is not None
                else None
            ),
            "attention_items": list(self.attention_items),
            "recent_jobs": [
                job.to_dictionary()
                for job in self.recent_jobs
            ],
        }
