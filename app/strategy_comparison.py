from dataclasses import dataclass

from app.backtest_result import BacktestResult


@dataclass(frozen=True)
class StrategyComparisonRow:
    name: str
    total_return_percent: float
    profit_factor: float
    win_rate_percent: float
    maximum_drawdown_percent: float
    calmar_ratio: float
    executed_trades: int


def compare_strategy_results(
    results: dict[str, BacktestResult],
) -> list[StrategyComparisonRow]:
    if not results:
        raise ValueError(
            "At least one strategy result is required."
        )

    rows = [
        StrategyComparisonRow(
            name=name,
            executed_trades=(
                result.executed_trades
            ),
            total_return_percent=(
                result.total_return_percent
            ),
            profit_factor=result.profit_factor,
            win_rate_percent=(
                result.win_rate_percent
            ),
            maximum_drawdown_percent=(
                result.maximum_drawdown_percent
            ),
            calmar_ratio=result.calmar_ratio,
        )
        
        for name, result in results.items()
    ]

    return sorted(
        rows,
        key=lambda row: (
            row.total_return_percent,
            row.calmar_ratio,
            row.profit_factor,
        ),
        reverse=True,
    )