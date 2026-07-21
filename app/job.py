import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


class JobType(str, Enum):
    NEWS_RESEARCH_CYCLE = "NEWS_RESEARCH_CYCLE"
    STRATEGY_REPORT = "STRATEGY_REPORT"
    SHADOW_ANALYSIS = "SHADOW_ANALYSIS"


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    SUCCEEDED_WITH_WARNINGS = (
        "SUCCEEDED_WITH_WARNINGS"
    )
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    job_type: JobType
    status: JobStatus
    created_at: datetime
    payload: Mapping[str, Any]
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: Mapping[str, Any] = field(
        default_factory=dict
    )
    error_code: str | None = None
    error_summary: str | None = None
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if not self.job_id.strip():
            raise ValueError(
                "Job ID is required."
            )

        for name, value in (
            ("created_at", self.created_at),
            ("started_at", self.started_at),
            ("finished_at", self.finished_at),
        ):
            if (
                value is not None
                and value.tzinfo is None
            ):
                raise ValueError(
                    f"{name} must be timezone-aware."
                )

        if (
            self.started_at is not None
            and self.started_at < self.created_at
        ):
            raise ValueError(
                "Job start time cannot precede "
                "creation time."
            )

        if (
            self.finished_at is not None
            and self.started_at is None
        ):
            raise ValueError(
                "A finished job requires a start time."
            )

        if (
            self.finished_at is not None
            and self.started_at is not None
            and self.finished_at < self.started_at
        ):
            raise ValueError(
                "Job finish time cannot precede "
                "start time."
            )

        if self.status == JobStatus.QUEUED:
            if (
                self.started_at is not None
                or self.finished_at is not None
            ):
                raise ValueError(
                    "A queued job cannot have start "
                    "or finish times."
                )

        if self.status == JobStatus.RUNNING:
            if self.started_at is None:
                raise ValueError(
                    "A running job requires a start time."
                )
            if self.finished_at is not None:
                raise ValueError(
                    "A running job cannot have a "
                    "finish time."
                )

        if self.status in {
            JobStatus.SUCCEEDED,
            JobStatus.SUCCEEDED_WITH_WARNINGS,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        }:
            if self.finished_at is None:
                raise ValueError(
                    "A completed job requires a "
                    "finish time."
                )

        if self.idempotency_key is not None:
            cleaned_key = self.idempotency_key.strip()
            if not cleaned_key:
                raise ValueError("Idempotency key cannot be blank.")
            object.__setattr__(self, "idempotency_key", cleaned_key)

        object.__setattr__(
            self,
            "payload",
            dict(self.payload),
        )
        object.__setattr__(
            self,
            "result",
            dict(self.result),
        )

    @property
    def duration_seconds(
        self,
    ) -> float | None:
        if (
            self.started_at is None
            or self.finished_at is None
        ):
            return None

        return (
            self.finished_at
            - self.started_at
        ).total_seconds()

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": (
                None
                if self.started_at is None
                else self.started_at.isoformat()
            ),
            "finished_at": (
                None
                if self.finished_at is None
                else self.finished_at.isoformat()
            ),
            "duration_seconds": self.duration_seconds,
            "payload": dict(self.payload),
            "result": dict(self.result),
            "error_code": self.error_code,
            "error_summary": self.error_summary,
            "idempotency_key": self.idempotency_key,
        }

    def payload_json(self) -> str:
        return json.dumps(
            dict(self.payload),
            sort_keys=True,
        )

    def result_json(self) -> str:
        return json.dumps(
            dict(self.result),
            sort_keys=True,
        )