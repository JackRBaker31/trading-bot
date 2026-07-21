from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.run_history import (
    RunHistoryRecord,
    RunStatus,
    RunType,
)


def test_creates_run_history_record() -> None:
    started_at = datetime(
        2026, 7, 19, 12, 0,
        tzinfo=timezone.utc,
    )
    finished_at = started_at + timedelta(
        seconds=3
    )

    record = RunHistoryRecord(
        run_id="run-1",
        run_type=RunType.STRATEGY_REPORT,
        status=RunStatus.SUCCEEDED,
        started_at=started_at,
        finished_at=finished_at,
        provider="twelve_data",
        symbols=("aapl", "AAPL", "msft"),
        created_count=2,
        metadata={"report": "complete"},
    )

    assert record.provider == "TWELVE_DATA"
    assert record.symbols == (
        "AAPL",
        "MSFT",
    )
    assert record.duration_seconds == 3.0
    assert (
        record.to_dictionary()["run_type"]
        == "STRATEGY_REPORT"
    )


def test_running_record_rejects_finish_time() -> None:
    with pytest.raises(
        ValueError,
        match="running record",
    ):
        RunHistoryRecord(
            run_id="run-1",
            run_type=(
                RunType.NEWS_RESEARCH_CYCLE
            ),
            status=RunStatus.RUNNING,
            started_at=datetime.now(
                timezone.utc
            ),
            finished_at=datetime.now(
                timezone.utc
            ),
        )

def test_warning_record_requires_finish_time() -> None:
    with pytest.raises(
        ValueError,
        match="requires a finish time",
    ):
        RunHistoryRecord(
            run_id="run-1",
            run_type=(
                RunType.NEWS_RESEARCH_CYCLE
            ),
            status=(
                RunStatus
                .SUCCEEDED_WITH_WARNINGS
            ),
            started_at=datetime.now(
                timezone.utc
            ),
        )