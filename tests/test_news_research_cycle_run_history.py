from dataclasses import dataclass
from datetime import (
    datetime,
    timezone,
)

import pytest

from app.application_errors import (
    ResearchRunError,
)
from app.news_observation_service import (
    NewsObservationSummary,
)
from app.news_research_cycle_service import (
    NewsResearchCycleRequest,
    NewsResearchCycleService,
)
from app.run_history import (
    RunHistoryRecord,
    RunStatus,
    RunType,
)


class RecordingRunHistoryService:
    def __init__(self) -> None:
        self.started: list[dict] = []
        self.completed: list[dict] = []
        self.failed: list[dict] = []

    def start_run(self, **kwargs):
        self.started.append(kwargs)
        return RunHistoryRecord(
            run_id="run-1",
            run_type=kwargs["run_type"],
            status=RunStatus.RUNNING,
            started_at=datetime.now(
                timezone.utc
            ),
            provider=kwargs.get("provider"),
            symbols=kwargs.get("symbols", ()),
            metadata=kwargs.get("metadata", {}),
        )

    def complete_run(self, **kwargs):
        self.completed.append(kwargs)

    def fail_run(self, **kwargs):
        self.failed.append(kwargs)


class EmptyObservationService:
    def run(self, *, symbols):
        return NewsObservationSummary(
            symbols=tuple(symbols),
            article_count=0,
            signal_count=0,
            skipped_duplicate_count=0,
        )


class FailingObservationService:
    def run(self, *, symbols):
        raise RuntimeError("failure")


def test_news_cycle_records_success(
    tmp_path,
) -> None:
    history = RecordingRunHistoryService()

    service = NewsResearchCycleService(
        observation_service_factory=(
            lambda _: EmptyObservationService()
        ),
        market_data_provider_factory=(
            lambda provider, symbols: None
        ),
        run_history_service=history,
    )

    service.run(
        request=NewsResearchCycleRequest(
            symbols=("AAPL",),
            provider_name="TWELVE_DATA",
            signals_path=str(
                tmp_path / "signals.jsonl"
            ),
            snapshots_path=str(
                tmp_path / "snapshots.jsonl"
            ),
            outcomes_path=str(
                tmp_path / "outcomes.jsonl"
            ),
        )
    )

    assert (
        history.started[0]["run_type"]
        == RunType.NEWS_RESEARCH_CYCLE
    )
    assert history.completed[0][
        "created_count"
    ] == 0
    assert history.failed == []


def test_news_cycle_records_failure(
    tmp_path,
) -> None:
    history = RecordingRunHistoryService()

    service = NewsResearchCycleService(
        observation_service_factory=(
            lambda _: FailingObservationService()
        ),
        market_data_provider_factory=(
            lambda provider, symbols: None
        ),
        run_history_service=history,
    )

    with pytest.raises(
        ResearchRunError,
    ):
        service.run(
            request=NewsResearchCycleRequest(
                symbols=("AAPL",),
                provider_name="TWELVE_DATA",
                signals_path=str(
                    tmp_path / "signals.jsonl"
                ),
                snapshots_path=str(
                    tmp_path / "snapshots.jsonl"
                ),
                outcomes_path=str(
                    tmp_path / "outcomes.jsonl"
                ),
            )
        )

    assert history.completed == []
    assert history.failed[0][
        "run_id"
    ] == "run-1"