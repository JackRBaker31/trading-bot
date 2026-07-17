from app.backtest_result import BacktestResult


def create_result(
    *,
    total_return_percent: float,
    maximum_drawdown_percent: float,
) -> BacktestResult:
    return BacktestResult(
        starting_cash=10_000.0,
        ending_value=10_000.0,
        total_return_percent=total_return_percent,
        maximum_drawdown_percent=(
            maximum_drawdown_percent
        ),
        benchmark_return_percent=0.0,
        excess_return_percent=0.0,
        average_exposure_percent=0.0,
        executed_trades=0,
        rejected_orders=0,
        profit_factor=0.0,
        win_rate_percent=0.0,
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


def test_calculates_calmar_ratio() -> None:
    result = create_result(
        total_return_percent=12.0,
        maximum_drawdown_percent=4.0,
    )

    assert result.calmar_ratio == 3.0


def test_calmar_ratio_is_infinite_for_positive_return_without_drawdown() -> None:
    result = create_result(
        total_return_percent=5.0,
        maximum_drawdown_percent=0.0,
    )

    assert result.calmar_ratio == float("inf")


def test_calmar_ratio_is_zero_without_return_or_drawdown() -> None:
    result = create_result(
        total_return_percent=0.0,
        maximum_drawdown_percent=0.0,
    )

    assert result.calmar_ratio == 0.0