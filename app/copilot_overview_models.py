from dataclasses import (
    asdict,
    dataclass,
    field,
)
from datetime import datetime

from app.copilot_intelligence_models import (
    CopilotGraduationOverview,
    CopilotIntelligenceOverview,
)


@dataclass(frozen=True)
class CopilotPlatformOverview:
    overall_status: str
    online_services: int
    required_services: int

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CopilotActivityOverview:
    running_jobs: int
    queued_jobs: int

    @property
    def active_jobs(self) -> int:
        return (
            self.running_jobs
            + self.queued_jobs
        )

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        payload = asdict(self)

        payload["active_jobs"] = (
            self.active_jobs
        )

        return payload


@dataclass(frozen=True)
class CopilotScheduleOverview:
    task_type: str
    next_run_at: datetime
    schedule_id: str

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "task_type": self.task_type,
            "next_run_at": (
                self.next_run_at.isoformat()
            ),
            "schedule_id": self.schedule_id,
        }


@dataclass(frozen=True)
class CopilotLatestFailure:
    job_id: str
    job_type: str
    error_code: str | None
    error_summary: str | None
    finished_at: datetime | None

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "error_code": self.error_code,
            "error_summary": (
                self.error_summary
            ),
            "finished_at": (
                self.finished_at.isoformat()
                if self.finished_at
                else None
            ),
        }


@dataclass(frozen=True)
class CopilotFailuresOverview:
    recent_count: int
    latest: CopilotLatestFailure | None

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "recent_count": (
                self.recent_count
            ),
            "latest": (
                self.latest.to_dictionary()
                if self.latest
                else None
            ),
        }


@dataclass(frozen=True)
class CopilotAttentionItem:
    code: str
    title: str
    detail: str
    severity: str

    def to_dictionary(
        self,
    ) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class CopilotOverview:
    generated_at: datetime
    overall_status: str
    platform: CopilotPlatformOverview
    activity: CopilotActivityOverview
    schedule: (
        CopilotScheduleOverview
        | None
    )
    failures: CopilotFailuresOverview
    trading_intelligence: (
        CopilotIntelligenceOverview
    )
    graduation: CopilotGraduationOverview
    attention_items: tuple[
        CopilotAttentionItem,
        ...
    ] = field(default_factory=tuple)

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "generated_at": (
                self.generated_at.isoformat()
            ),
            "overall_status": (
                self.overall_status
            ),
            "platform": (
                self.platform.to_dictionary()
            ),
            "activity": (
                self.activity.to_dictionary()
            ),
            "schedule": (
                self.schedule.to_dictionary()
                if self.schedule
                else None
            ),
            "failures": (
                self.failures.to_dictionary()
            ),
            "trading_intelligence": (
                self.trading_intelligence
                .to_dictionary()
            ),
            "graduation": (
                self.graduation
                .to_dictionary()
            ),
            "attention_items": [
                item.to_dictionary()
                for item
                in self.attention_items
            ],
        }