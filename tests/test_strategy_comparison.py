import pytest

from app.backtest_result import BacktestResult
from app.strategy_comparison import (
    StrategyComparisonRow,
    compare_strategy_results,
)


def create_result(
    *,
    total_return_percent: float,
    profit_factor: float,
    win_rate_percent: float,
    maximum_drawdown_percent: float,
) -> BacktestResult:
    return BacktestResult(
        starting_cash=10_000.0,
        ending_value=(
            10_000.0
            * (
                1
                + total_return_percent
                / 100
            )
        ),
        total_return_percent=(
            total_return_percent
        ),
        maximum_drawdown_percent=(
            maximum_drawdown_percent
        ),
        benchmark_return_percent=0.0,
        excess_return_percent=(
            total_return_percent
        ),
        average_exposure_percent=0.0,
        executed_trades=0,
        rejected_orders=0,
        profit_factor=profit_factor,
        win_rate_percent=win_rate_percent,
        maximum_consecutive_wins=0,
        maximum_consecutive_losses=0,
        average_winning_trade=0.0,
        average_losing_trade=0.0,
        largest_winning_trade=0.0,
        largest_losing_trade=0.0,
        expectancy=0.0,
        final_cash=10_000.0,
        final_positions={},
    )


def test_compares_and_ranks_strategy_results() -> None:
    baseline = create_result(
        total_return_percent=5.0,
        profit_factor=1.1,
        win_rate_percent=50.0,
        maximum_drawdown_percent=10.0,
    )
    sma_rsi = create_result(
        total_return_percent=8.0,
        profit_factor=1.5,
        win_rate_percent=60.0,
        maximum_drawdown_percent=8.0,
    )

    rows = compare_strategy_results(
        {
            "Baseline": baseline,
            "SMA + RSI": sma_rsi,
        }
    )

    assert rows == [
        StrategyComparisonRow(
            name="SMA + RSI",
            executed_trades=0,
            total_return_percent=8.0,
            profit_factor=1.5,
            win_rate_percent=60.0,
            maximum_drawdown_percent=8.0,
            calmar_ratio=1.0,
        ),
        StrategyComparisonRow(
            name="Baseline",
            executed_trades=0,
            total_return_percent=5.0,
            profit_factor=1.1,
            win_rate_percent=50.0,
            maximum_drawdown_percent=10.0,
            calmar_ratio=0.5,
        ),
    ]


def test_uses_calmar_ratio_to_break_return_tie() -> None:
    lower_calmar = create_result(
        total_return_percent=10.0,
        profit_factor=2.0,
        win_rate_percent=60.0,
        maximum_drawdown_percent=10.0,
    )
    higher_calmar = create_result(
        total_return_percent=10.0,
        profit_factor=1.5,
        win_rate_percent=55.0,
        maximum_drawdown_percent=5.0,
    )

    rows = compare_strategy_results(
        {
            "Lower Calmar": lower_calmar,
            "Higher Calmar": higher_calmar,
        }
    )

    assert rows[0].name == "Higher Calmar"
    assert rows[0].calmar_ratio == pytest.approx(
        2.0
    )


def test_rejects_empty_strategy_results() -> None:
    with pytest.raises(
        ValueError,
        match="At least one strategy result",
    ):
        compare_strategy_results({})