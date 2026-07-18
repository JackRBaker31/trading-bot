import pytest

from app.rolling_walk_forward_optimizer import (
    RollingWalkForwardResult,
)
from app.strategy_comparison import (
    StrategyComparisonRow,
)
from app.strategy_robustness import (
    StrategyRobustnessRow,
    rank_strategy_robustness,
)


def create_row(
    *,
    name: str,
    return_percent: float,
    drawdown_percent: float,
) -> StrategyComparisonRow:
    return StrategyComparisonRow(
        name=name,
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


def create_result(
    *,
    window_number: int,
    name: str,
    validation_return: float,
    validation_drawdown: float,
) -> RollingWalkForwardResult:
    return RollingWalkForwardResult(
        window_number=window_number,
        training_result=create_row(
            name=name,
            return_percent=1.0,
            drawdown_percent=1.0,
        ),
        validation_result=create_row(
            name=name,
            return_percent=(
                validation_return
            ),
            drawdown_percent=(
                validation_drawdown
            ),
        ),
    )


def test_ranks_strategies_by_robustness() -> None:
    results = [
        create_result(
            window_number=1,
            name="Stable",
            validation_return=2.0,
            validation_drawdown=1.0,
        ),
        create_result(
            window_number=2,
            name="Stable",
            validation_return=1.0,
            validation_drawdown=2.0,
        ),
        create_result(
            window_number=3,
            name="Volatile",
            validation_return=8.0,
            validation_drawdown=5.0,
        ),
        create_result(
            window_number=4,
            name="Volatile",
            validation_return=-4.0,
            validation_drawdown=6.0,
        ),
    ]

    rows = rank_strategy_robustness(
        results
    )

    assert rows == [
        StrategyRobustnessRow(
            name="Stable",
            selected_window_count=2,
            positive_window_count=2,
            positive_window_percent=100.0,
            average_return_percent=1.5,
            median_return_percent=1.5,
            worst_return_percent=1.0,
            best_return_percent=2.0,
            average_drawdown_percent=1.5,
        ),
        StrategyRobustnessRow(
            name="Volatile",
            selected_window_count=2,
            positive_window_count=1,
            positive_window_percent=50.0,
            average_return_percent=2.0,
            median_return_percent=2.0,
            worst_return_percent=-4.0,
            best_return_percent=8.0,
            average_drawdown_percent=5.5,
        ),
    ]


def test_uses_median_return_to_break_positive_rate_tie() -> None:
    results = [
        create_result(
            window_number=1,
            name="Lower Median",
            validation_return=1.0,
            validation_drawdown=1.0,
        ),
        create_result(
            window_number=2,
            name="Higher Median",
            validation_return=3.0,
            validation_drawdown=2.0,
        ),
    ]

    rows = rank_strategy_robustness(
        results
    )

    assert rows[0].name == "Higher Median"


def test_rejects_empty_rolling_results() -> None:
    with pytest.raises(
        ValueError,
        match="At least one rolling result",
    ):
        rank_strategy_robustness([])