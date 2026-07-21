import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


class RunType(str, Enum):
    NEWS_RESEARCH_CYCLE = "NEWS_RESEARCH_CYCLE"
    STRATEGY_REPORT = "STRATEGY_REPORT"
    PAPER_TRADING_STARTUP = "PAPER_TRADING_STARTUP"
    RECONCILIATION = "RECONCILIATION"
    ORDER_RECOVERY = "ORDER_RECOVERY"


class RunStatus(str, Enum):
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    SUCCEEDED_WITH_WARNINGS = (
        "SUCCEEDED_WITH_WARNINGS"
    )
    FAILED = "FAILED"


@dataclass(frozen=True)
class RunHistoryRecord:
    run_id: str
    run_type: RunType
    status: RunStatus
    started_at: datetime
    finished_at: datetime | None = None
    provider: str | None = None
    symbols: tuple[str, ...] = ()
    created_count: int = 0
    skipped_count: int = 0
    failure_count: int = 0
    error_code: str | None = None
    error_summary: str | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError(
                "Run ID is required."
            )

        if self.started_at.tzinfo is None:
            raise ValueError(
                "Run start time must be timezone-aware."
            )

        if (
            self.finished_at is not None
            and self.finished_at.tzinfo is None
        ):
            raise ValueError(
                "Run finish time must be timezone-aware."
            )

        if (
            self.finished_at is not None
            and self.finished_at < self.started_at
        ):
            raise ValueError(
                "Run finish time cannot precede "
                "the start time."
            )

        for name, value in (
            ("created_count", self.created_count),
            ("skipped_count", self.skipped_count),
            ("failure_count", self.failure_count),
        ):
            if value < 0:
                raise ValueError(
                    f"{name} cannot be negative."
                )

        if (
            self.status == RunStatus.RUNNING
            and self.finished_at is not None
        ):
            raise ValueError(
                "A running record cannot have "
                "a finish time."
            )

        if (
            self.status != RunStatus.RUNNING
            and self.finished_at is None
        ):
            raise ValueError(
                "A completed record requires "
                "a finish time."
            )

        cleaned_symbols = tuple(
            dict.fromkeys(
                symbol.upper().strip()
                for symbol in self.symbols
                if symbol.strip()
            )
        )
        object.__setattr__(
            self,
            "symbols",
            cleaned_symbols,
        )

        if self.provider is not None:
            cleaned_provider = (
                self.provider.upper().strip()
            )
            object.__setattr__(
                self,
                "provider",
                cleaned_provider or None,
            )

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    @property
    def duration_seconds(
        self,
    ) -> float | None:
        if self.finished_at is None:
            return None

        return (
            self.finished_at
            - self.started_at
        ).total_seconds()

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "run_type": self.run_type.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "finished_at": (
                None
                if self.finished_at is None
                else self.finished_at.isoformat()
            ),
            "duration_seconds": (
                self.duration_seconds
            ),
            "provider": self.provider,
            "symbols": list(self.symbols),
            "created_count": self.created_count,
            "skipped_count": self.skipped_count,
            "failure_count": self.failure_count,
            "error_code": self.error_code,
            "error_summary": self.error_summary,
            "metadata": dict(self.metadata),
        }

    def metadata_json(
        self,
    ) -> str:
        return json.dumps(
            dict(self.metadata),
            sort_keys=True,
        )