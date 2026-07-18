import pytest

from app.strategy_comparison import (
    StrategyComparisonRow,
)
from app.strategy_comparison_report import (
    format_strategy_comparison,
)


def test_formats_ranked_strategy_comparison() -> None:
    rows = [
        StrategyComparisonRow(
            name="SMA + RSI",
            total_return_percent=8.0,
            profit_factor=1.5,
            win_rate_percent=60.0,
            maximum_drawdown_percent=4.0,
            calmar_ratio=2.0,
            executed_trades=0,
        ),
        StrategyComparisonRow(
            name="Baseline",
            total_return_percent=5.0,
            profit_factor=1.1,
            win_rate_percent=50.0,
            maximum_drawdown_percent=10.0,
            calmar_ratio=0.5,
            executed_trades=0,
        ),
    ]

    report = format_strategy_comparison(
        rows
    )

    assert "Strategy | Trades | Return %" in report
    assert (
        "SMA + RSI | 0 | 8.00 | 1.50 | "
        "60.00 | 4.00 | 2.00"
        in report
    )
    assert (
        "Baseline | 0 | 5.00 | 1.10 | "
        "50.00 | 10.00 | 0.50"
        in report
    )
    assert report.endswith(
        "Winner: SMA + RSI"
    )


def test_rejects_empty_comparison_rows() -> None:
    with pytest.raises(
        ValueError,
        match="At least one comparison row",
    ):
        format_strategy_comparison([])