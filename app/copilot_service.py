from collections.abc import (
    Callable,
    Mapping,
    Sequence,
)
from typing import Any
from datetime import datetime, timezone

from app.copilot_models import (
    CopilotResponse,
    CopilotSuggestion,
)
from app.infrastructure_status import (
    InfrastructureStatus,
)
from app.job import (
    JobRecord,
    JobStatus,
)
from app.scheduled_task import ScheduledTask
from app.copilot_overview_models import (
    CopilotActivityOverview,
    CopilotAttentionItem,
    CopilotFailuresOverview,
    CopilotLatestFailure,
    CopilotOverview,
    CopilotPlatformOverview,
    CopilotScheduleOverview,
)
from app.copilot_intelligence_models import (
    CopilotGraduationCheck,
    CopilotGraduationOverview,
    CopilotIntelligenceOverview,
    CopilotTradingIntelligence,
)

InfrastructureStatusProvider = Callable[
    [],
    InfrastructureStatus,
]

RecentJobsProvider = Callable[
    [],
    Sequence[JobRecord],
]

SchedulesProvider = Callable[
    [],
    Sequence[ScheduledTask],
]

NowProvider = Callable[[], datetime]

IntelligenceSnapshotProvider = Callable[
    [],
    Mapping[str, Any],
]

GraduationStatusProvider = Callable[
    [],
    Mapping[str, Any],
]


class CopilotService:
    def __init__(
        self,
        *,
        infrastructure_status_provider: (
            InfrastructureStatusProvider
        ),
        recent_jobs_provider: RecentJobsProvider,
        schedules_provider: SchedulesProvider,
        now_provider: NowProvider | None = None,
        intelligence_snapshot_provider: (
            IntelligenceSnapshotProvider
            | None
        ) = None,
        graduation_status_provider: (
            GraduationStatusProvider
            | None
        ) = None,
    ) -> None:
        self._infrastructure_status_provider = (
            infrastructure_status_provider
        )
        self._recent_jobs_provider = (
            recent_jobs_provider
        )
        self._schedules_provider = schedules_provider
        self._now_provider = now_provider or (
            lambda: datetime.now(
                timezone.utc
            )
        )

        self._intelligence_snapshot_provider = (
            intelligence_snapshot_provider
        )

        self._graduation_status_provider = (
            graduation_status_provider
        )
        

    def answer(
        self,
        *,
        question: str,
    ) -> CopilotResponse:
        cleaned_question = " ".join(
            question.strip().split()
        )

        if not cleaned_question:
            raise ValueError(
                "Copilot question is required."
            )

        lowered = cleaned_question.lower()

        if self._asks_about_health(lowered):
            return self.platform_health()

        if self._asks_about_failures(lowered):
            return self.recent_failures()

        if self._asks_about_activity(lowered):
            return self.current_activity()

        if self._asks_about_schedule(lowered):
            return self.upcoming_work()

        if self._asks_why_no_trade(
            lowered
        ):
            return (
                self.no_trade_explanation()
            )

        if self._asks_about_graduation(
            lowered
        ):
            return (
                self.graduation_explanation()
            )

        if self._asks_about_intelligence(
            lowered
        ):
            return (
                self.intelligence_explanation()
            )
        return self.operational_overview()

    def dashboard_overview(
        self,
    ) -> CopilotOverview:
        now = self._utc_now()

        infrastructure = (
            self._infrastructure_status_provider()
        )

        jobs = tuple(
            self._recent_jobs_provider()
        )

        schedules = tuple(
            self._schedules_provider()
        )

        required_service_names = {
            "api",
            "storage",
            "supervisor",
            "job_worker",
            "scheduler",
        }

        required_services = tuple(
            service
            for service
            in infrastructure.services
            if service.name
            in required_service_names
        )

        online_services = sum(
            1
            for service
            in required_services
            if service.online
        )

        running_jobs = tuple(
            job
            for job
            in jobs
            if job.status
            == JobStatus.RUNNING
        )

        queued_jobs = tuple(
            job
            for job
            in jobs
            if job.status
            == JobStatus.QUEUED
        )

        failed_jobs = tuple(
            job
            for job
            in jobs
            if job.status
            == JobStatus.FAILED
        )

        enabled_schedules = tuple(
            sorted(
                (
                    schedule
                    for schedule
                    in schedules
                    if schedule.enabled
                ),
                key=lambda item: (
                    item.next_run_at
                ),
            )
        )

        schedule_overview = None

        if enabled_schedules:
            next_schedule = (
                enabled_schedules[0]
            )

            schedule_overview = (
                CopilotScheduleOverview(
                    task_type=(
                        next_schedule
                        .task_type
                        .value
                    ),
                    next_run_at=(
                        next_schedule
                        .next_run_at
                    ),
                    schedule_id=(
                        next_schedule
                        .schedule_id
                    ),
                )
            )

        latest_failure = None

        if failed_jobs:
            latest_job = max(
                failed_jobs,
                key=lambda job: (
                    job.finished_at
                    or job.started_at
                    or job.created_at
                ),
            )

            latest_failure = (
                CopilotLatestFailure(
                    job_id=latest_job.job_id,
                    job_type=(
                        latest_job
                        .job_type
                        .value
                    ),
                    error_code=(
                        latest_job.error_code
                    ),
                    error_summary=(
                        latest_job
                        .error_summary
                    ),
                    finished_at=(
                        latest_job.finished_at
                    ),
                )
            )

        attention_items: list[
            CopilotAttentionItem
        ] = []

        offline_services = tuple(
            service
            for service
            in required_services
            if not service.online
        )

        if offline_services:
            service_names = ", ".join(
                self._display_name(
                    service.name
                )
                for service
                in offline_services
            )

            attention_items.append(
                CopilotAttentionItem(
                    code=(
                        "INFRASTRUCTURE_DEGRADED"
                    ),
                    title=(
                        "Infrastructure requires "
                        "attention"
                    ),
                    detail=(
                        "Unavailable required "
                        f"services: {service_names}."
                    ),
                    severity="WARNING",
                )
            )

        if failed_jobs:
            attention_items.append(
                CopilotAttentionItem(
                    code="RECENT_JOB_FAILURES",
                    title=(
                        "Review recent job failures"
                    ),
                    detail=(
                        f"{len(failed_jobs)} recent "
                        "job failure(s) were found."
                    ),
                    severity="WARNING",
                )
            )

        if not enabled_schedules:
            attention_items.append(
                CopilotAttentionItem(
                    code="NO_ENABLED_SCHEDULES",
                    title=(
                        "No enabled schedules"
                    ),
                    detail=(
                        "KAIRO will remain idle "
                        "unless a job is manually "
                        "queued."
                    ),
                    severity="INFO",
                )
            )

        overall_status = (
            "HEALTHY"
            if (
                infrastructure.overall_status
                == "HEALTHY"
                and not failed_jobs
            )
            else "ATTENTION"
        )
        trading = (
            self.trading_intelligence()
        )
        return CopilotOverview(
            generated_at=now,
            overall_status=overall_status,
            platform=(
                CopilotPlatformOverview(
                    overall_status=(
                        infrastructure
                        .overall_status
                    ),
                    online_services=(
                        online_services
                    ),
                    required_services=(
                        len(required_services)
                    ),
                )
            ),
            activity=(
                CopilotActivityOverview(
                    running_jobs=(
                        len(running_jobs)
                    ),
                    queued_jobs=(
                        len(queued_jobs)
                    ),
                )
            ),
            schedule=schedule_overview,
            failures=(
                CopilotFailuresOverview(
                    recent_count=(
                        len(failed_jobs)
                    ),
                    latest=latest_failure,
                )
            ),
            attention_items=tuple(
                attention_items
            ),
            trading_intelligence=(
                trading.intelligence
            ),

            graduation=(
                trading.graduation
            ),
        )

    def operational_overview(
        self,
    ) -> CopilotResponse:
        infrastructure = (
            self._infrastructure_status_provider()
        )
        jobs = tuple(
            self._recent_jobs_provider()
        )
        schedules = tuple(
            self._schedules_provider()
        )

        suggestions: list[
            CopilotSuggestion
        ] = []

        offline_services = tuple(
            service
            for service in infrastructure.services
            if not service.online
            and service.name
            in {
                "api",
                "storage",
                "supervisor",
                "job_worker",
                "scheduler",
            }
        )

        failed_jobs = tuple(
            job
            for job in jobs
            if job.status == JobStatus.FAILED
        )

        active_jobs = tuple(
            job
            for job in jobs
            if job.status
            in {
                JobStatus.QUEUED,
                JobStatus.RUNNING,
            }
        )

        enabled_schedules = tuple(
            schedule
            for schedule in schedules
            if schedule.enabled
        )

        if offline_services:
            service_names = ", ".join(
                self._display_name(
                    service.name
                )
                for service
                in offline_services
            )

            suggestions.append(
                CopilotSuggestion(
                    title="Infrastructure attention",
                    message=(
                        "The following required "
                        "services are unavailable: "
                        f"{service_names}."
                    ),
                    kind="warning",
                )
            )
        else:
            suggestions.append(
                CopilotSuggestion(
                    title="Platform health",
                    message=(
                        "All required KAIRO services "
                        "are online."
                    ),
                    kind="success",
                )
            )

        if failed_jobs:
            suggestions.append(
                CopilotSuggestion(
                    title="Recent job failures",
                    message=(
                        f"{len(failed_jobs)} recent "
                        "job failure(s) require "
                        "review."
                    ),
                    kind="warning",
                )
            )

        if active_jobs:
            suggestions.append(
                CopilotSuggestion(
                    title="Current activity",
                    message=(
                        f"{len(active_jobs)} job(s) "
                        "are currently running or "
                        "queued."
                    ),
                    kind="info",
                )
            )
        else:
            suggestions.append(
                CopilotSuggestion(
                    title="Current activity",
                    message=(
                        "No jobs are currently "
                        "running or queued."
                    ),
                    kind="info",
                )
            )

        if enabled_schedules:
            next_schedule = min(
                enabled_schedules,
                key=lambda item: (
                    item.next_run_at
                ),
            )

            suggestions.append(
                CopilotSuggestion(
                    title="Next scheduled task",
                    message=(
                        f"{next_schedule.task_type.value} "
                        "is due at "
                        f"{self._format_datetime(next_schedule.next_run_at)}."
                    ),
                    kind="info",
                )
            )
        else:
            suggestions.append(
                CopilotSuggestion(
                    title="Scheduler",
                    message=(
                        "No enabled schedules are "
                        "currently configured."
                    ),
                    kind="warning",
                )
            )

        healthy = (
            infrastructure.overall_status
            == "HEALTHY"
            and not failed_jobs
        )

        summary = (
            "KAIRO is operating normally."
            if healthy
            else (
                "KAIRO is operating, but one or "
                "more items require attention."
            )
        )

        return CopilotResponse(
            summary=summary,
            suggestions=tuple(suggestions),
        )

    def platform_health(
        self,
    ) -> CopilotResponse:
        infrastructure = (
            self._infrastructure_status_provider()
        )

        required_services = tuple(
            service
            for service in infrastructure.services
            if service.name
            in {
                "api",
                "storage",
                "supervisor",
                "job_worker",
                "scheduler",
            }
        )

        suggestions = tuple(
            CopilotSuggestion(
                title=self._display_name(
                    service.name
                ),
                message=service.detail,
                kind=(
                    "success"
                    if service.online
                    else "warning"
                ),
            )
            for service in required_services
        )

        online_count = sum(
            1
            for service in required_services
            if service.online
        )

        summary = (
            f"{online_count} of "
            f"{len(required_services)} required "
            "services are online. "
            f"Overall status is "
            f"{infrastructure.overall_status}."
        )

        return CopilotResponse(
            summary=summary,
            suggestions=suggestions,
        )

    def recent_failures(
        self,
    ) -> CopilotResponse:
        jobs = tuple(
            self._recent_jobs_provider()
        )

        failed_jobs = tuple(
            job
            for job in jobs
            if job.status == JobStatus.FAILED
        )

        if not failed_jobs:
            return CopilotResponse(
                summary=(
                    "No failed jobs were found in "
                    "the recent job history."
                ),
                suggestions=(
                    CopilotSuggestion(
                        title="Job history",
                        message=(
                            f"{len(jobs)} recent "
                            "job(s) were checked."
                        ),
                        kind="success",
                    ),
                ),
            )

        suggestions = tuple(
            CopilotSuggestion(
                title=job.job_type.value,
                message=(
                    job.error_summary
                    or job.error_code
                    or "The job failed."
                ),
                kind="warning",
            )
            for job in failed_jobs
        )

        return CopilotResponse(
            summary=(
                f"{len(failed_jobs)} failed "
                "job(s) were found."
            ),
            suggestions=suggestions,
        )

    def current_activity(
        self,
    ) -> CopilotResponse:
        jobs = tuple(
            self._recent_jobs_provider()
        )

        active_jobs = tuple(
            job
            for job in jobs
            if job.status
            in {
                JobStatus.RUNNING,
                JobStatus.QUEUED,
            }
        )

        if not active_jobs:
            return CopilotResponse(
                summary=(
                    "KAIRO currently has no "
                    "running or queued jobs."
                ),
                suggestions=(
                    CopilotSuggestion(
                        title="Job worker",
                        message=(
                            "The worker is waiting "
                            "for its next job."
                        ),
                        kind="info",
                    ),
                ),
            )

        suggestions = tuple(
            CopilotSuggestion(
                title=job.job_type.value,
                message=(
                    f"Status: {job.status.value}. "
                    f"Job ID: {job.job_id}."
                ),
                kind="info",
            )
            for job in active_jobs
        )

        return CopilotResponse(
            summary=(
                f"{len(active_jobs)} job(s) are "
                "currently active."
            ),
            suggestions=suggestions,
        )

    def upcoming_work(
        self,
    ) -> CopilotResponse:
        now = self._utc_now()

        schedules = tuple(
            schedule
            for schedule
            in self._schedules_provider()
            if schedule.enabled
        )

        schedules = tuple(
            sorted(
                schedules,
                key=lambda item: (
                    item.next_run_at
                ),
            )
        )

        if not schedules:
            return CopilotResponse(
                summary=(
                    "No enabled schedules are "
                    "currently configured."
                ),
                suggestions=(
                    CopilotSuggestion(
                        title="Scheduler",
                        message=(
                            "KAIRO will remain idle "
                            "until a job is manually "
                            "queued or a schedule is "
                            "enabled."
                        ),
                        kind="warning",
                    ),
                ),
            )

        suggestions = tuple(
            CopilotSuggestion(
                title=schedule.task_type.value,
                message=(
                    f"Due at "
                    f"{self._format_datetime(schedule.next_run_at)} "
                    f"({self._relative_time(now, schedule.next_run_at)})."
                ),
                kind="info",
            )
            for schedule in schedules[:5]
        )

        return CopilotResponse(
            summary=(
                f"{len(schedules)} enabled "
                "schedule(s) were found. The next "
                "operation is "
                f"{schedules[0].task_type.value}."
            ),
            suggestions=suggestions,
        )

    @staticmethod
    def _asks_about_health(
        question: str,
    ) -> bool:
        return any(
            phrase in question
            for phrase in (
                "healthy",
                "health",
                "infrastructure",
                "online",
                "services",
            )
        )

    @staticmethod
    def _asks_about_failures(
        question: str,
    ) -> bool:
        return any(
            phrase in question
            for phrase in (
                "failed",
                "failure",
                "failures",
                "error",
                "errors",
                "went wrong",
            )
        )

    @staticmethod
    def _asks_about_activity(
        question: str,
    ) -> bool:
        return any(
            phrase in question
            for phrase in (
                "running",
                "current activity",
                "doing now",
                "active job",
                "queued",
            )
        )

    @staticmethod
    def _asks_about_schedule(
        question: str,
    ) -> bool:
        return any(
            phrase in question
            for phrase in (
                "what happens next",
                "next task",
                "next job",
                "upcoming",
                "schedule",
                "scheduled",
            )
        )

    @staticmethod
    def _asks_about_intelligence(
        question: str,
    ) -> bool:
        return any(
            phrase in question
            for phrase in (
                "intelligence",
                "signal strength",
                "signals",
                "confidence",
                "market outlook",
                "research strength",
            )
        )


    @staticmethod
    def _asks_about_graduation(
        question: str,
    ) -> bool:
        return any(
            phrase in question
            for phrase in (
                "graduation",
                "graduate",
                "not ready to trade",
                "ready to trade",
                "blocking graduation",
                "graduation blockers",
            )
        )


    @staticmethod
    def _asks_why_no_trade(
        question: str,
    ) -> bool:
        return any(
            phrase in question
            for phrase in (
                "why was no trade",
                "why no trade",
                "why didn't we trade",
                "why did we not trade",
                "why haven't we traded",
                "no trade placed",
            )
        )

    @staticmethod
    def _display_name(
        value: str,
    ) -> str:
        return value.replace(
            "_",
            " ",
        ).title()

    @staticmethod
    def _format_datetime(
        value: datetime,
    ) -> str:
        return value.astimezone(
            timezone.utc
        ).strftime(
            "%Y-%m-%d %H:%M UTC"
        )

    @staticmethod
    def _relative_time(
        now: datetime,
        future: datetime,
    ) -> str:
        seconds = max(
            0,
            int(
                (
                    future.astimezone(
                        timezone.utc
                    )
                    - now
                ).total_seconds()
            ),
        )

        if seconds < 60:
            return f"in {seconds} seconds"

        minutes = seconds // 60

        if minutes < 60:
            return f"in {minutes} minutes"

        hours = minutes // 60
        remaining_minutes = minutes % 60

        if remaining_minutes:
            return (
                f"in {hours} hours "
                f"{remaining_minutes} minutes"
            )

        return f"in {hours} hours"
    
    @staticmethod
    def _as_int(
        value: object,
    ) -> int:
        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0


    @staticmethod
    def _as_float(
        value: object,
    ) -> float:
        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0


    @staticmethod
    def _optional_text(
        value: object,
    ) -> str | None:
        if value is None:
            return None

        cleaned = str(value).strip()

        return cleaned or None

    def _utc_now(
        self,
    ) -> datetime:
        value = self._now_provider()

        if value.tzinfo is None:
            raise ValueError(
                "Copilot clock must be "
                "timezone-aware."
            )

        return value.astimezone(
            timezone.utc
        )
        
    def trading_intelligence(
        self,
    ) -> CopilotTradingIntelligence:
        if (
            self
            ._intelligence_snapshot_provider
            is None
        ):
            raise ValueError(
                "Intelligence snapshot provider "
                "is not configured."
            )

        if (
            self
            ._graduation_status_provider
            is None
        ):
            raise ValueError(
                "Graduation status provider "
                "is not configured."
            )

        snapshot = dict(
            self
            ._intelligence_snapshot_provider()
        )

        graduation_payload = dict(
            self
            ._graduation_status_provider()
        )

        confidence = self._as_float(
            snapshot.get(
                "confidence",
                snapshot.get(
                    "overall_confidence",
                    0.0,
                ),
            )
        )

        signal_count = self._as_int(
            snapshot.get(
                "signal_count",
                snapshot.get(
                    "total_signals",
                    0,
                ),
            )
        )

        actionable_signal_count = (
            self._as_int(
                snapshot.get(
                    "actionable_signal_count",
                    snapshot.get(
                        "actionable_signals",
                        0,
                    ),
                )
            )
        )

        raw_checks = (
            graduation_payload.get(
                "checks",
                (),
            )
            or ()
        )

        checks: list[
            CopilotGraduationCheck
        ] = []

        for raw_check in raw_checks:
            if not isinstance(
                raw_check,
                Mapping,
            ):
                continue

            checks.append(
                CopilotGraduationCheck(
                    name=str(
                        raw_check.get(
                            "name",
                            raw_check.get(
                                "code",
                                "Requirement",
                            ),
                        )
                    ),
                    passed=bool(
                        raw_check.get(
                            "passed",
                            False,
                        )
                    ),
                    reason=self._optional_text(
                        raw_check.get(
                            "reason",
                            raw_check.get(
                                "detail",
                            ),
                        )
                    ),
                )
            )

        ready = bool(
            graduation_payload.get(
                "ready",
                graduation_payload.get(
                    "graduated",
                    False,
                ),
            )
        )

        passed_checks = sum(
            1
            for check in checks
            if check.passed
        )

        blockers: list[str] = []

        trading_readiness = str(
            snapshot.get(
                "trading_readiness",
                "UNKNOWN",
            )
        ).upper()

        evidence_quality = str(
            snapshot.get(
                "evidence_quality",
                "UNKNOWN",
            )
        ).upper()

        if trading_readiness != "READY":
            blockers.append(
                "Trading readiness has not "
                "reached READY."
            )

        if actionable_signal_count <= 0:
            blockers.append(
                "No actionable signals are "
                "currently available."
            )

        if confidence <= 0:
            blockers.append(
                "Intelligence confidence is "
                "unavailable or zero."
            )

        if evidence_quality in {
            "LOW",
            "INSUFFICIENT",
            "UNKNOWN",
        }:
            blockers.append(
                "Evidence quality is not "
                "strong enough."
            )

        blockers.extend(
            check.reason
            or (
                f"{check.name} has not "
                "passed."
            )
            for check in checks
            if not check.passed
        )

        return CopilotTradingIntelligence(
            intelligence=(
                CopilotIntelligenceOverview(
                    trading_readiness=(
                        trading_readiness
                    ),
                    market_outlook=str(
                        snapshot.get(
                            "market_outlook",
                            "UNKNOWN",
                        )
                    ).upper(),
                    confidence=confidence,
                    signal_count=signal_count,
                    actionable_signal_count=(
                        actionable_signal_count
                    ),
                    evidence_quality=(
                        evidence_quality
                    ),
                )
            ),
            graduation=(
                CopilotGraduationOverview(
                    ready=ready,
                    passed_checks=(
                        passed_checks
                    ),
                    total_checks=len(
                        checks
                    ),
                    checks=tuple(
                        checks
                    ),
                )
            ),
            blockers=tuple(
                dict.fromkeys(
                    blocker
                    for blocker in blockers
                    if blocker
                )
            ),
        )
        
    def intelligence_explanation(
    self,
) -> CopilotResponse:
        state = (
            self.trading_intelligence()
        )

        intelligence = (
            state.intelligence
        )

        suggestions = [
            CopilotSuggestion(
                title="Trading readiness",
                message=(
                    intelligence
                    .trading_readiness
                ),
                kind=(
                    "success"
                    if (
                        intelligence
                        .trading_readiness
                        == "READY"
                    )
                    else "warning"
                ),
            ),
            CopilotSuggestion(
                title="Confidence",
                message=(
                    f"{intelligence.confidence:.1f}"
                ),
                kind=(
                    "success"
                    if (
                        intelligence.confidence
                        >= 80
                    )
                    else "info"
                ),
            ),
            CopilotSuggestion(
                title="Signals",
                message=(
                    f"{intelligence.signal_count} "
                    "total signal(s), "
                    f"{intelligence.actionable_signal_count} "
                    "actionable."
                ),
                kind=(
                    "success"
                    if (
                        intelligence
                        .actionable_signal_count
                        > 0
                    )
                    else "warning"
                ),
            ),
            CopilotSuggestion(
                title="Evidence quality",
                message=(
                    intelligence
                    .evidence_quality
                ),
                kind=(
                    "success"
                    if (
                        intelligence
                        .evidence_quality
                        in {
                            "HIGH",
                            "STRONG",
                        }
                    )
                    else "warning"
                ),
            ),
        ]

        return CopilotResponse(
        summary=(
            "Current intelligence is "
            f"{intelligence.trading_readiness}. "
            f"Confidence is "
            f"{intelligence.confidence:.1f}, "
            f"with "
            f"{intelligence.actionable_signal_count} "
            "actionable signal(s)."
        ),
        suggestions=tuple(
            suggestions
        ),
    )


    def graduation_explanation(
        self,
    ) -> CopilotResponse:
        state = (
            self.trading_intelligence()
        )

        graduation = state.graduation

        if graduation.ready:
            return CopilotResponse(
                summary=(
                    "Intelligence currently "
                    "meets the graduation "
                    "requirements."
                ),
                suggestions=(
                    CopilotSuggestion(
                        title="Graduation",
                        message=(
                            f"{graduation.passed_checks} "
                            f"of "
                            f"{graduation.total_checks} "
                            "checks passed."
                        ),
                        kind="success",
                    ),
                ),
            )

        failed_checks = (
            graduation.failed_checks
        )

        suggestions = tuple(
            CopilotSuggestion(
                title=check.name,
                message=(
                    check.reason
                    or (
                        "This graduation "
                        "requirement has not "
                        "passed."
                    )
                ),
                kind="warning",
            )
            for check in failed_checks
        )

        return CopilotResponse(
            summary=(
                "Intelligence is not ready "
                "to graduate. "
                f"{len(failed_checks)} of "
                f"{graduation.total_checks} "
                "requirement(s) remain "
                "blocked."
            ),
            suggestions=(
                suggestions
                or (
                    CopilotSuggestion(
                        title="Graduation",
                        message=(
                            "Graduation status is "
                            "not ready, but no "
                            "individual failed "
                            "checks were supplied."
                        ),
                        kind="warning",
                    ),
                )
            ),
        )


    def no_trade_explanation(
        self,
    ) -> CopilotResponse:
        state = (
            self.trading_intelligence()
        )

        if not state.blockers:
            return CopilotResponse(
                summary=(
                    "No intelligence or "
                    "graduation blocker was "
                    "identified. Order, risk "
                    "and market-session evidence "
                    "must also be reviewed."
                ),
                suggestions=(
                    CopilotSuggestion(
                        title="Further evidence",
                        message=(
                            "Review risk decisions, "
                            "order history and market "
                            "session status."
                        ),
                        kind="info",
                    ),
                ),
            )

        return CopilotResponse(
            summary=(
                "No trade was justified by "
                "the current intelligence "
                "state because one or more "
                "requirements remain blocked."
            ),
            suggestions=tuple(
                CopilotSuggestion(
                    title="Trading blocker",
                    message=blocker,
                    kind="warning",
                )
                for blocker
                in state.blockers
            ),
        )