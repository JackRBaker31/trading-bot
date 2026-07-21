from datetime import (
    datetime,
    timezone,
)
from types import SimpleNamespace

import pytest

from app.application_errors import (
    DataStoreError,
)
from app.research_report_service import (
    ResearchReportRequest,
    ResearchReportService,
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
            metadata=kwargs.get("metadata", {}),
        )

    def complete_run(self, **kwargs):
        self.completed.append(kwargs)

    def fail_run(self, **kwargs):
        self.failed.append(kwargs)


def create_request(
    tmp_path,
) -> ResearchReportRequest:
    return ResearchReportRequest(
        starting_cash=10_000.0,
        max_order_value=2_000.0,
        max_position_value=3_000.0,
        max_portfolio_exposure=0.5,
        target_allocation_percent=20.0,
        historical_prices_path=str(
            tmp_path / "missing.csv"
        ),
        news_signals_path=str(
            tmp_path / "signals.jsonl"
        ),
        news_outcomes_path=str(
            tmp_path / "outcomes.jsonl"
        ),
        json_output_path=str(
            tmp_path / "report.json"
        ),
        csv_output_path=str(
            tmp_path / "report.csv"
        ),
        equity_curve_path=str(
            tmp_path / "equity.png"
        ),
        drawdown_path=str(
            tmp_path / "drawdown.png"
        ),
        monte_carlo_path=str(
            tmp_path / "monte.png"
        ),
        rolling_returns_path=str(
            tmp_path / "rolling.png"
        ),
    )


def test_report_records_failure(
    tmp_path,
) -> None:
    history = RecordingRunHistoryService()
    service = ResearchReportService(
        run_history_service=history
    )

    with pytest.raises(
        DataStoreError,
    ):
        service.run(
            request=create_request(
                tmp_path
            )
        )

    assert (
        history.started[0]["run_type"]
        == RunType.STRATEGY_REPORT
    )
    assert history.completed == []
    assert history.failed[0][
        "run_id"
    ] == "run-1"