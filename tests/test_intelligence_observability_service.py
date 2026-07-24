from datetime import datetime, timezone
from enum import Enum

from app.intelligence_observability_service import (
    IntelligenceObservabilityService,
)
from app.operation_diagnostics_repository import (
    OperationDiagnosticsRepository,
)
from app.operation_diagnostics_service import (
    OperationDiagnosticsService,
)


NOW = datetime(
    2026,
    7,
    24,
    20,
    0,
    tzinfo=timezone.utc,
)


class Value(Enum):
    INTELLIGENCE_CYCLE = (
        "INTELLIGENCE_CYCLE"
    )
    SUCCEEDED_WITH_WARNINGS = (
        "SUCCEEDED_WITH_WARNINGS"
    )


class Job:
    job_id = "JOB-1"
    job_type = Value.INTELLIGENCE_CYCLE
    status = Value.SUCCEEDED_WITH_WARNINGS
    created_at = NOW
    started_at = NOW
    finished_at = NOW
    result = {
        "trading_impact": "NONE",
        "stages": [
            {
                "stage": (
                    "CAPTURE_PRICE_OUTCOMES"
                ),
                "status": (
                    "SUCCEEDED_WITH_WARNINGS"
                ),
                "detail": {
                    "failure_count": 2,
                    "outcomes_recorded": 3,
                },
                "warnings": [
                    (
                        "2 price operations "
                        "failed or were deferred."
                    )
                ],
            }
        ],
    }


def test_marks_legacy_warning_as_incomplete(
    tmp_path,
) -> None:
    diagnostics = (
        OperationDiagnosticsService(
            repository=(
                OperationDiagnosticsRepository(
                    database_path=str(
                        tmp_path
                        / "application.db"
                    )
                )
            )
        )
    )
    diagnostics.initialize()

    service = (
        IntelligenceObservabilityService(
            jobs_provider=(
                lambda limit: (
                    Job(),
                )
            ),
            diagnostics_service=(
                diagnostics
            ),
        )
    )

    report = service.job_report(
        job_id="JOB-1"
    )

    assert (
        report.stages[0]
        .display_name
        == "Capture Price Outcomes"
    )
    assert (
        report.stages[0]
        .diagnostics_complete
        is False
    )
    assert (
        "legacy run"
        in report.stages[0]
        .warnings[-1]
    )


def test_exact_failure_event_completes_diagnostics(
    tmp_path,
) -> None:
    diagnostics = (
        OperationDiagnosticsService(
            repository=(
                OperationDiagnosticsRepository(
                    database_path=str(
                        tmp_path
                        / "application.db"
                    )
                )
            )
        )
    )
    diagnostics.initialize()

    for symbol in (
        "AAPL",
        "NVDA",
    ):
        diagnostics.record(
            job_id="JOB-1",
            stage=(
                "CAPTURE_PRICE_OUTCOMES"
            ),
            operation="FETCH_QUOTE",
            status="FAILED",
            severity="WARNING",
            symbol=symbol,
            provider="TWELVE_DATA",
            error_code="ReadTimeout",
            error_summary=(
                "Request timed out."
            ),
            retryable=True,
            retry_count=2,
        )

    service = (
        IntelligenceObservabilityService(
            jobs_provider=(
                lambda limit: (
                    Job(),
                )
            ),
            diagnostics_service=(
                diagnostics
            ),
        )
    )

    report = service.job_report(
        job_id="JOB-1"
    )

    assert (
        report.stages[0]
        .diagnostics_complete
        is True
    )
    assert (
        len(
            report.stages[0]
            .events
        )
        == 2
    )
