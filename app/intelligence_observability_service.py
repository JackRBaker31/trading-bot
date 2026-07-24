from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from app.operation_diagnostics_models import (
    IntelligenceHealthOverview,
    JobDiagnosticReport,
    OperationDiagnosticEvent,
    StageDiagnostic,
)
from app.operation_diagnostics_service import (
    OperationDiagnosticsService,
)


class IntelligenceObservabilityService:
    STAGE_NAMES = {
        "NEWS_RESEARCH": "News Research",
        "CAPTURE_PRICE_OUTCOMES": (
            "Capture Price Outcomes"
        ),
        "SHADOW_ANALYSIS": "Shadow Analysis",
        "SHADOW_PERFORMANCE": (
            "Shadow Performance"
        ),
        "GRADUATION_STATUS": (
            "Graduation Status"
        ),
        "INTELLIGENCE_SNAPSHOT": (
            "Intelligence Snapshot"
        ),
        "DAILY_BRIEFING": "Daily Briefing",
    }

    def __init__(
        self,
        *,
        jobs_provider: Callable[
            [int],
            tuple[Any, ...],
        ],
        diagnostics_service: (
            OperationDiagnosticsService
        ),
    ) -> None:
        self._jobs_provider = jobs_provider
        self._diagnostics_service = (
            diagnostics_service
        )

    def job_report(
        self,
        *,
        job_id: str,
    ) -> JobDiagnosticReport:
        jobs = self._jobs_provider(500)
        job = next(
            (
                item
                for item in jobs
                if item.job_id == job_id
            ),
            None,
        )

        if job is None:
            raise ValueError(
                "Job was not found."
            )

        events = (
            self._diagnostics_service
            .for_job(
                job_id=job_id
            )
        )

        by_stage: dict[
            str,
            list[
                OperationDiagnosticEvent
            ],
        ] = defaultdict(list)

        for event in events:
            by_stage[event.stage].append(
                event
            )

        result = dict(job.result or {})
        stage_payloads = tuple(
            result.get(
                "stages",
                (),
            )
        )

        stages = tuple(
            self._stage(
                payload=dict(payload),
                events=tuple(
                    by_stage.get(
                        str(
                            payload.get(
                                "stage",
                                "UNKNOWN",
                            )
                        ),
                        (),
                    )
                ),
            )
            for payload in stage_payloads
        )

        duration_ms = self._duration_ms(
            job.started_at,
            job.finished_at,
        )
        latencies = [
            event.latency_ms
            for event in events
            if event.latency_ms is not None
        ]

        return JobDiagnosticReport(
            job_id=job.job_id,
            job_type=job.job_type.value,
            status=job.status.value,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            duration_ms=duration_ms,
            trading_impact=result.get(
                "trading_impact"
            ),
            stages=stages,
            warning_count=sum(
                len(stage.warnings)
                for stage in stages
            ),
            failure_count=sum(
                stage.failure_count
                for stage in stages
            ),
            retry_count=sum(
                stage.retry_count
                for stage in stages
            ),
            recovered_count=sum(
                stage.recovered_count
                for stage in stages
            ),
            cache_hit_count=sum(
                stage.cache_hit_count
                for stage in stages
            ),
            average_latency_ms=(
                round(
                    sum(latencies)
                    / len(latencies),
                    3,
                )
                if latencies
                else None
            ),
            diagnostics_complete=all(
                stage.diagnostics_complete
                for stage in stages
            ),
        )

    def overview(
        self,
        *,
        limit: int = 20,
    ) -> IntelligenceHealthOverview:
        jobs = self._jobs_provider(
            limit
        )
        reports = tuple(
            self.job_report(
                job_id=job.job_id
            )
            for job in jobs
        )
        recent_events = (
            self._diagnostics_service
            .recent(
                limit=500
            )
        )

        succeeded = sum(
            1
            for report in reports
            if report.status == "SUCCEEDED"
        )
        warning = sum(
            1
            for report in reports
            if (
                report.status
                == "SUCCEEDED_WITH_WARNINGS"
            )
        )
        failed = sum(
            1
            for report in reports
            if report.status == "FAILED"
        )
        active = sum(
            1
            for report in reports
            if report.status in {
                "QUEUED",
                "RUNNING",
            }
        )

        durations = [
            report.duration_ms
            for report in reports
            if report.duration_ms is not None
        ]
        latencies = [
            event.latency_ms
            for event in recent_events
            if event.latency_ms is not None
        ]
        cache_events = [
            event
            for event in recent_events
            if event.cache_status is not None
        ]
        cache_hits = sum(
            1
            for event in cache_events
            if event.cache_status == "HIT"
        )

        operation_failures = [
            event
            for event in recent_events
            if event.status == "FAILED"
        ]

        latest_warning = next(
            (
                event
                for event in recent_events
                if event.severity in {
                    "WARNING",
                    "ERROR",
                    "CRITICAL",
                }
            ),
            None,
        )

        attention: list[str] = []

        if failed:
            attention.append(
                f"{failed} recent job(s) failed."
            )

        if warning:
            attention.append(
                f"{warning} recent job(s) completed "
                "with warnings."
            )

        incomplete = sum(
            1
            for report in reports
            if not report.diagnostics_complete
        )

        if incomplete:
            attention.append(
                f"{incomplete} job(s) contain legacy "
                "warnings without detailed operation events."
            )

        health_status = (
            "CRITICAL"
            if failed >= 3
            else "DEGRADED"
            if failed or warning
            else "HEALTHY"
        )

        return IntelligenceHealthOverview(
            generated_at=datetime.now(
                timezone.utc
            ),
            health_status=health_status,
            recent_job_count=len(
                reports
            ),
            succeeded_count=succeeded,
            warning_count=warning,
            failed_count=failed,
            active_count=active,
            operation_failure_count=len(
                operation_failures
            ),
            recovered_operation_count=sum(
                1
                for event in recent_events
                if event.recovered
            ),
            average_job_duration_ms=(
                round(
                    sum(durations)
                    / len(durations),
                    3,
                )
                if durations
                else None
            ),
            average_operation_latency_ms=(
                round(
                    sum(latencies)
                    / len(latencies),
                    3,
                )
                if latencies
                else None
            ),
            cache_hit_rate=(
                round(
                    cache_hits
                    / len(cache_events),
                    6,
                )
                if cache_events
                else None
            ),
            retry_count=sum(
                event.retry_count
                for event in recent_events
            ),
            latest_warning=latest_warning,
            attention_items=tuple(
                attention
            ),
            recent_jobs=reports,
        )

    def _stage(
        self,
        *,
        payload: dict[str, object],
        events: tuple[
            OperationDiagnosticEvent,
            ...
        ],
    ) -> StageDiagnostic:
        stage = str(
            payload.get(
                "stage",
                "UNKNOWN",
            )
        )
        detail = dict(
            payload.get(
                "detail",
                {},
            )
            or {}
        )
        warnings = tuple(
            str(value)
            for value in payload.get(
                "warnings",
                (),
            )
        )

        failures = [
            event
            for event in events
            if event.status == "FAILED"
        ]
        latencies = [
            event.latency_ms
            for event in events
            if event.latency_ms is not None
        ]

        declared_failure_count = int(
            detail.get(
                "failure_count",
                0,
            )
            or 0
        )

        diagnostics_complete = (
            declared_failure_count == 0
            or len(failures)
            >= declared_failure_count
        )

        if (
            declared_failure_count > 0
            and not events
        ):
            warnings = (
                *warnings,
                (
                    "Detailed symbol/provider diagnostics "
                    "were not captured for this legacy run."
                ),
            )

        return StageDiagnostic(
            stage=stage,
            display_name=(
                self.STAGE_NAMES.get(
                    stage,
                    stage.replace(
                        "_",
                        " ",
                    ).title(),
                )
            ),
            status=str(
                payload.get(
                    "status",
                    "UNKNOWN",
                )
            ),
            duration_ms=(
                float(
                    detail["duration_ms"]
                )
                if (
                    detail.get(
                        "duration_ms"
                    )
                    is not None
                )
                else None
            ),
            detail=detail,
            warnings=warnings,
            events=events,
            event_count=len(events),
            failure_count=max(
                declared_failure_count,
                len(failures),
            ),
            retry_count=sum(
                event.retry_count
                for event in events
            ),
            recovered_count=sum(
                1
                for event in events
                if event.recovered
            ),
            cache_hit_count=sum(
                1
                for event in events
                if event.cache_status == "HIT"
            ),
            average_latency_ms=(
                round(
                    sum(latencies)
                    / len(latencies),
                    3,
                )
                if latencies
                else None
            ),
            diagnostics_complete=(
                diagnostics_complete
            ),
        )

    @staticmethod
    def _duration_ms(
        started_at,
        finished_at,
    ) -> float | None:
        if (
            started_at is None
            or finished_at is None
        ):
            return None

        return round(
            (
                finished_at
                - started_at
            ).total_seconds()
            * 1000,
            3,
        )
