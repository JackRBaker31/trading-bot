from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from app.backtest_result import (
    BacktestResult,
)
from app.execution_cost import (
    ExecutionCostModel,
)
from app.monte_carlo_summary import (
    MonteCarloSummary,
)
from app.research_report_builder import (
    build_research_report,
)


def create_backtest_result(
    *,
    total_return_percent: float,
    trade_profits: list[float],
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
        completed_trade_profits=(
            trade_profits
        ),
    )


def create_summary(
    *,
    median_return_percent: float,
) -> MonteCarloSummary:
    return MonteCarloSummary(
        simulation_count=1_000,
        average_return_percent=(
            median_return_percent
        ),
        median_return_percent=(
            median_return_percent
        ),
        fifth_percentile_return_percent=(
            median_return_percent - 5.0
        ),
        ninety_fifth_percentile_return_percent=(
            median_return_percent + 5.0
        ),
        worst_return_percent=-10.0,
        best_return_percent=20.0,
        average_drawdown_percent=2.5,
        worst_drawdown_percent=8.0,
        loss_probability_percent=10.0,
    )


def test_builds_research_report() -> None:
    report = build_research_report(
        strategy_name="  Example strategy  ",
        gross_backtest_result=(
            create_backtest_result(
                total_return_percent=7.0,
                trade_profits=[
                    100.0,
                    -25.0,
                ],
            )
        ),
        net_backtest_result=(
            create_backtest_result(
                total_return_percent=5.0,
                trade_profits=[
                    80.0,
                    -35.0,
                ],
            )
        ),
        gross_monte_carlo_summary=(
            create_summary(
                median_return_percent=7.0
            )
        ),
        net_monte_carlo_summary=(
            create_summary(
                median_return_percent=5.0
            )
        ),
        net_cost_model=ExecutionCostModel(
            slippage_percent=0.1,
            commission_percent=0.1,
        ),
        walk_forward_result=SimpleNamespace(
            training_result=SimpleNamespace(
                total_return_percent=8.29
            ),
            validation_result=SimpleNamespace(
                total_return_percent=3.30
            ),
        ),
        rolling_summary=SimpleNamespace(
            window_count=5,
            positive_window_percent=60.0,
            average_return_percent=1.73,
            worst_return_percent=-2.02,
        ),
        generated_at=(
            "2026-07-18T15:00:00+01:00"
        ),
    )

    assert report.strategy_name == (
        "Example strategy"
    )
    assert report.gross_completed_trades == 2
    assert report.net_completed_trades == 2
    assert (
        report.net_backtest_return_percent
        == 5.0
    )
    assert (
        report.walk_forward_validation_return_percent
        == 3.30
    )
    assert report.rolling_window_count == 5
    assert report.slippage_percent == 0.1


def test_rejects_blank_strategy_name() -> None:
    with pytest.raises(
        ValueError,
        match="Strategy name",
    ):
        build_research_report(
            strategy_name=" ",
            gross_backtest_result=(
                create_backtest_result(
                    total_return_percent=7.0,
                    trade_profits=[100.0],
                )
            ),
            net_backtest_result=(
                create_backtest_result(
                    total_return_percent=5.0,
                    trade_profits=[80.0],
                )
            ),
            gross_monte_carlo_summary=(
                create_summary(
                    median_return_percent=7.0
                )
            ),
            net_monte_carlo_summary=(
                create_summary(
                    median_return_percent=5.0
                )
            ),
            net_cost_model=ExecutionCostModel(),
            walk_forward_result=SimpleNamespace(
                training_result=SimpleNamespace(
                    total_return_percent=1.0
                ),
                validation_result=SimpleNamespace(
                    total_return_percent=1.0
                ),
            ),
            rolling_summary=SimpleNamespace(
                window_count=1,
                positive_window_percent=100.0,
                average_return_percent=1.0,
                worst_return_percent=1.0,
            ),
        )