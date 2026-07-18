import pytest

from app.rolling_walk_forward_optimizer import (
    RollingWalkForwardResult,
)
from app.rolling_walk_forward_summary import (
    summarize_rolling_results,
)
from app.strategy_comparison import (
    StrategyComparisonRow,
)


def create_row(
    *,
    return_percent: float,
    drawdown_percent: float,
) -> StrategyComparisonRow:
    return StrategyComparisonRow(
        name="Strategy",
        executed_trades=1,
        total_return_percent=return_percent,
        profit_factor=0.0,
        win_rate_percent=0.0,
        maximum_drawdown_percent=(
            drawdown_percent
        ),
        calmar_ratio=(
            0.0
            if drawdown_percent == 0
            else (
                return_percent
                / drawdown_percent
            )
        ),
    )


def test_summarizes_rolling_validation_results() -> None:
    results = [
        RollingWalkForwardResult(
            window_number=1,
            training_result=create_row(
                return_percent=1.0,
                drawdown_percent=1.0,
            ),
            validation_result=create_row(
                return_percent=4.0,
                drawdown_percent=2.0,
            ),
        ),
        RollingWalkForwardResult(
            window_number=2,
            training_result=create_row(
                return_percent=1.0,
                drawdown_percent=1.0,
            ),
            validation_result=create_row(
                return_percent=-2.0,
                drawdown_percent=4.0,
            ),
        ),
        RollingWalkForwardResult(
            window_number=3,
            training_result=create_row(
                return_percent=1.0,
                drawdown_percent=1.0,
            ),
            validation_result=create_row(
                return_percent=1.0,
                drawdown_percent=3.0,
            ),
        ),
    ]

    summary = summarize_rolling_results(
        results
    )

    assert summary.window_count == 3
    assert summary.positive_window_count == 2
    assert (
        summary.positive_window_percent
        == pytest.approx(
            200.0 / 3.0
        )
    )
    assert (
        summary.average_return_percent
        == pytest.approx(1.0)
    )
    assert summary.median_return_percent == 1.0
    assert summary.worst_return_percent == -2.0
    assert summary.best_return_percent == 4.0
    assert (
        summary.average_drawdown_percent
        == pytest.approx(3.0)
    )


def test_rejects_empty_rolling_results() -> None:
    with pytest.raises(
        ValueError,
        match="At least one rolling result",
    ):
        summarize_rolling_results([])