import pytest

from app.strategy_comparison import (
    StrategyComparisonRow,
)
from app.strategy_validation_matrix import (
    StrategyValidationResult,
)
from app.strategy_validation_summary import (
    StrategyValidationSummaryRow,
    summarize_strategy_validation,
)


def create_result(
    *,
    window_number: int,
    name: str,
    return_percent: float,
    drawdown_percent: float,
) -> StrategyValidationResult:
    return StrategyValidationResult(
        window_number=window_number,
        strategy_result=StrategyComparisonRow(
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
        ),
    )


def test_summarizes_every_strategy_over_equal_windows() -> None:
    results = [
        create_result(
            window_number=1,
            name="Stable",
            return_percent=2.0,
            drawdown_percent=1.0,
        ),
        create_result(
            window_number=2,
            name="Stable",
            return_percent=1.0,
            drawdown_percent=2.0,
        ),
        create_result(
            window_number=1,
            name="Volatile",
            return_percent=8.0,
            drawdown_percent=5.0,
        ),
        create_result(
            window_number=2,
            name="Volatile",
            return_percent=-4.0,
            drawdown_percent=6.0,
        ),
    ]

    rows = summarize_strategy_validation(
        results
    )

    assert rows == [
        StrategyValidationSummaryRow(
            name="Stable",
            window_count=2,
            positive_window_count=2,
            positive_window_percent=100.0,
            average_return_percent=1.5,
            median_return_percent=1.5,
            worst_return_percent=1.0,
            best_return_percent=2.0,
            average_drawdown_percent=1.5,
        ),
        StrategyValidationSummaryRow(
            name="Volatile",
            window_count=2,
            positive_window_count=1,
            positive_window_percent=50.0,
            average_return_percent=2.0,
            median_return_percent=2.0,
            worst_return_percent=-4.0,
            best_return_percent=8.0,
            average_drawdown_percent=5.5,
        ),
    ]


def test_rejects_empty_validation_results() -> None:
    with pytest.raises(
        ValueError,
        match="At least one validation result",
    ):
        summarize_strategy_validation([])