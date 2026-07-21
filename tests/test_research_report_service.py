from types import SimpleNamespace

import pytest

from app.application_errors import (
    ConfigurationError,
    DataStoreError,
    ResearchRunError,
)
from app.backtest_result import BacktestResult
from app.execution_cost import ExecutionCostModel
from app.historical_data import HistoricalPrice
from app.monte_carlo_summary import (
    MonteCarloSummary,
)
from app.news_research_summary import (
    NewsResearchSummary,
)
from app.research_report_service import (
    ResearchReportRequest,
    ResearchReportService,
)
from app.rolling_walk_forward_summary import (
    RollingWalkForwardSummary,
)


def create_backtest_result(
    *,
    total_return_percent: float,
) -> BacktestResult:
    return BacktestResult(
        starting_cash=10_000.0,
        ending_value=(
            10_000.0
            * (
                1.0
                + total_return_percent
                / 100.0
            )
        ),
        total_return_percent=(
            total_return_percent
        ),
        maximum_drawdown_percent=2.0,
        benchmark_return_percent=1.0,
        excess_return_percent=(
            total_return_percent - 1.0
        ),
        average_exposure_percent=20.0,
        executed_trades=10,
        rejected_orders=0,
        profit_factor=1.5,
        win_rate_percent=60.0,
        average_winning_trade=100.0,
        average_losing_trade=-50.0,
        largest_winning_trade=150.0,
        largest_losing_trade=-80.0,
        expectancy=25.0,
        maximum_consecutive_wins=3,
        maximum_consecutive_losses=2,
        final_cash=10_000.0,
        final_positions={},
        completed_trade_profits=[
            100.0,
            -25.0,
        ],
    )


def create_monte_carlo_summary(
    *,
    median_return_percent: float,
) -> MonteCarloSummary:
    return MonteCarloSummary(
        simulation_count=1,
        average_return_percent=(
            median_return_percent
        ),
        median_return_percent=(
            median_return_percent
        ),
        fifth_percentile_return_percent=-2.0,
        ninety_fifth_percentile_return_percent=12.0,
        worst_return_percent=-3.0,
        best_return_percent=13.0,
        average_drawdown_percent=2.0,
        worst_drawdown_percent=8.0,
        loss_probability_percent=10.0,
    )


def create_request(
    tmp_path,
) -> ResearchReportRequest:
    return ResearchReportRequest(
        starting_cash=10_000.0,
        max_order_value=2_000.0,
        max_position_value=3_000.0,
        max_portfolio_exposure=0.5,
        target_allocation_percent=25.0,
        historical_prices_path=str(
            tmp_path / "prices.csv"
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


def configure_service(
    service: ResearchReportService,
    monkeypatch,
) -> None:
    historical_prices = [
        HistoricalPrice(
            trading_date=__import__(
                "datetime"
            ).date(2026, 1, 1),
            prices={"AAPL": 100.0},
        )
    ]

    backtests = iter(
        [
            create_backtest_result(
                total_return_percent=7.0
            ),
            create_backtest_result(
                total_return_percent=5.0
            ),
        ]
    )

    monte_carlo = iter(
        [
            (
                [SimpleNamespace()],
                create_monte_carlo_summary(
                    median_return_percent=7.0
                ),
            ),
            (
                [SimpleNamespace()],
                create_monte_carlo_summary(
                    median_return_percent=5.0
                ),
            ),
        ]
    )

    monkeypatch.setattr(
        service,
        "_load_historical_prices",
        lambda _: historical_prices,
    )
    monkeypatch.setattr(
        service,
        "_run_backtest_case",
        lambda **_: next(backtests),
    )
    monkeypatch.setattr(
        service,
        "_summarize_trade_profits",
        lambda **_: next(monte_carlo),
    )
    monkeypatch.setattr(
        service,
        "_run_walk_forward",
        lambda **_: (
            SimpleNamespace(
                total_return_percent=8.0
            ),
            SimpleNamespace(
                total_return_percent=3.0
            ),
        ),
    )
    monkeypatch.setattr(
        service,
        "_run_rolling",
        lambda **_: [],
    )
    monkeypatch.setattr(
        service,
        "_summarize_rolling",
        lambda _: RollingWalkForwardSummary(
            window_count=5,
            positive_window_count=3,
            positive_window_percent=60.0,
            average_return_percent=1.7,
            median_return_percent=1.5,
            worst_return_percent=-2.0,
            best_return_percent=4.0,
            average_drawdown_percent=1.0,
        ),
    )
    monkeypatch.setattr(
        service,
        "_load_news_summary",
        lambda **_: NewsResearchSummary(
            signal_count=2,
            outcome_count=1,
            unmatched_outcome_count=0,
            sentiment_groups=(),
            materiality_groups=(),
            event_type_groups=(),
            confidence_groups=(),
        ),
    )
    monkeypatch.setattr(
        service,
        "_save_report",
        lambda **_: None,
    )
    monkeypatch.setattr(
        service,
        "_save_charts",
        lambda **_: None,
    )


def test_builds_structured_research_result(
    tmp_path,
    monkeypatch,
) -> None:
    service = ResearchReportService()
    configure_service(
        service,
        monkeypatch,
    )

    result = service.run(
        request=create_request(tmp_path)
    )

    assert result.report.verdict == "PROMISING"
    assert (
        result.report.net_backtest_return_percent
        == 5.0
    )
    assert result.news_summary.signal_count == 2
    assert result.artifacts.json_path.endswith(
        "report.json"
    )


def test_rejects_invalid_request() -> None:
    with pytest.raises(
        ConfigurationError,
        match="Starting cash",
    ):
        ResearchReportRequest(
            starting_cash=0.0,
            max_order_value=2_000.0,
            max_position_value=3_000.0,
            max_portfolio_exposure=0.5,
            target_allocation_percent=25.0,
        )


def test_wraps_historical_data_failure(
    tmp_path,
    monkeypatch,
) -> None:
    service = ResearchReportService()

    def fail(_):
        raise OSError("Read failed.")

    monkeypatch.setattr(
        service,
        "_load_historical_prices",
        fail,
    )

    with pytest.raises(
        DataStoreError,
        match="prices",
    ) as captured:
        service.run(
            request=create_request(tmp_path)
        )

    assert isinstance(
        captured.value.__cause__,
        OSError,
    )


def test_rejects_empty_price_history(
    tmp_path,
    monkeypatch,
) -> None:
    service = ResearchReportService()
    monkeypatch.setattr(
        service,
        "_load_historical_prices",
        lambda _: [],
    )

    with pytest.raises(
        ResearchRunError,
        match="No research prices",
    ):
        service.run(
            request=create_request(tmp_path)
        )