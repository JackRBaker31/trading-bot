from datetime import datetime, timezone

import pytest

from app.application_errors import (
    DataStoreError,
)
from app.run_history import (
    RunHistoryRecord,
    RunStatus,
    RunType,
)
from app.run_history_repository import (
    RunHistoryRepository,
)


def create_record(
    *,
    run_id: str,
) -> RunHistoryRecord:
    return RunHistoryRecord(
        run_id=run_id,
        run_type=RunType.STRATEGY_REPORT,
        status=RunStatus.RUNNING,
        started_at=datetime.now(
            timezone.utc
        ),
        symbols=("AAPL",),
    )


def test_adds_and_loads_record(
    tmp_path,
) -> None:
    repository = RunHistoryRepository(
        database_path=str(
            tmp_path / "application.db"
        )
    )
    repository.initialize()

    repository.add(
        record=create_record(
            run_id="run-1"
        )
    )

    loaded = repository.get(
        run_id="run-1"
    )

    assert loaded is not None
    assert loaded.run_id == "run-1"
    assert loaded.symbols == ("AAPL",)


def test_rejects_duplicate_record(
    tmp_path,
) -> None:
    repository = RunHistoryRepository(
        database_path=str(
            tmp_path / "application.db"
        )
    )
    repository.initialize()
    record = create_record(
        run_id="run-1"
    )
    repository.add(record=record)

    with pytest.raises(
        DataStoreError,
    ) as captured:
        repository.add(record=record)

    assert (
        captured.value.code
        == "RUN_HISTORY_DUPLICATE"
    )


def test_lists_most_recent_first(
    tmp_path,
) -> None:
    repository = RunHistoryRepository(
        database_path=str(
            tmp_path / "application.db"
        )
    )
    repository.initialize()

    first = create_record(run_id="first")
    second = RunHistoryRecord(
        run_id="second",
        run_type=RunType.NEWS_RESEARCH_CYCLE,
        status=RunStatus.RUNNING,
        started_at=first.started_at.replace(
            microsecond=(
                first.started_at.microsecond + 1
            )
        ),
    )
    repository.add(record=first)
    repository.add(record=second)

    records = repository.list_recent()

    assert [
        record.run_id
        for record in records
    ] == ["second", "first"]