from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.application_errors import (
    ProviderUnavailableError,
)
from app.run_history import (
    RunStatus,
    RunType,
)
from app.run_history_repository import (
    RunHistoryRepository,
)
from app.run_history_service import (
    RunHistoryService,
)


def create_service(
    tmp_path,
) -> RunHistoryService:
    times = iter(
        [
            datetime(
                2026, 7, 19, 12, 0,
                tzinfo=timezone.utc,
            ),
            datetime(
                2026, 7, 19, 12, 0, 5,
                tzinfo=timezone.utc,
            ),
        ]
    )

    service = RunHistoryService(
        repository=RunHistoryRepository(
            database_path=str(
                tmp_path / "application.db"
            )
        ),
        now_provider=lambda: next(times),
        run_id_provider=lambda: "run-1",
    )
    service.initialize()
    return service


def test_starts_and_completes_run(
    tmp_path,
) -> None:
    service = create_service(tmp_path)

    started = service.start_run(
        run_type=(
            RunType.NEWS_RESEARCH_CYCLE
        ),
        provider="twelve_data",
        symbols=("aapl",),
    )
    completed = service.complete_run(
        run_id=started.run_id,
        created_count=3,
        skipped_count=2,
    )

    assert completed.status == (
        RunStatus.SUCCEEDED
    )
    assert completed.duration_seconds == 5.0
    assert completed.created_count == 3


def test_records_safe_application_error(
    tmp_path,
) -> None:
    service = create_service(tmp_path)
    started = service.start_run(
        run_type=RunType.STRATEGY_REPORT
    )

    failed = service.fail_run(
        run_id=started.run_id,
        error=ProviderUnavailableError(
            "Provider unavailable.",
            code="QUOTE_PROVIDER_DOWN",
            context={"provider": "TWELVE_DATA"},
        ),
    )

    assert failed.status == RunStatus.FAILED
    assert failed.error_code == (
        "QUOTE_PROVIDER_DOWN"
    )
    assert failed.error_summary == (
        "Provider unavailable."
    )
    assert failed.metadata[
        "error_context"
    ] == {
        "provider": "TWELVE_DATA"
    }


def test_records_safe_unexpected_error(
    tmp_path,
) -> None:
    service = create_service(tmp_path)
    started = service.start_run(
        run_type=RunType.ORDER_RECOVERY
    )

    failed = service.fail_run(
        run_id=started.run_id,
        error=RuntimeError(
            "secret internal detail"
        ),
    )

    assert failed.error_code == (
        "UNEXPECTED_ERROR"
    )
    assert "secret" not in (
        failed.error_summary or ""
    )

def test_completion_with_failures_records_warning(
    tmp_path,
) -> None:
    service = create_service(tmp_path)

    started = service.start_run(
        run_type=(
            RunType.NEWS_RESEARCH_CYCLE
        )
    )

    completed = service.complete_run(
        run_id=started.run_id,
        created_count=3,
        failure_count=2,
    )

    assert completed.status == (
        RunStatus.SUCCEEDED_WITH_WARNINGS
    )
    assert completed.created_count == 3
    assert completed.failure_count == 2