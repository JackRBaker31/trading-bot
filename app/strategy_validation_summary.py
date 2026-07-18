from collections import defaultdict
from dataclasses import dataclass
from statistics import median

from app.strategy_validation_matrix import (
    StrategyValidationResult,
)


@dataclass(frozen=True)
class StrategyValidationSummaryRow:
    name: str
    window_count: int
    positive_window_count: int
    positive_window_percent: float
    average_return_percent: float
    median_return_percent: float
    worst_return_percent: float
    best_return_percent: float
    average_drawdown_percent: float


def summarize_strategy_validation(
    results: list[StrategyValidationResult],
) -> list[StrategyValidationSummaryRow]:
    if not results:
        raise ValueError(
            "At least one validation result is required."
        )

    returns_by_strategy: dict[
        str,
        list[float],
    ] = defaultdict(list)

    drawdowns_by_strategy: dict[
        str,
        list[float],
    ] = defaultdict(list)

    for result in results:
        strategy_result = (
            result.strategy_result
        )

        returns_by_strategy[
            strategy_result.name
        ].append(
            strategy_result.total_return_percent
        )

        drawdowns_by_strategy[
            strategy_result.name
        ].append(
            strategy_result
            .maximum_drawdown_percent
        )

    rows: list[
        StrategyValidationSummaryRow
    ] = []

    for name, returns in (
        returns_by_strategy.items()
    ):
        drawdowns = (
            drawdowns_by_strategy[name]
        )

        window_count = len(returns)

        positive_window_count = sum(
            1
            for value in returns
            if value > 0
        )

        rows.append(
            StrategyValidationSummaryRow(
                name=name,
                window_count=window_count,
                positive_window_count=(
                    positive_window_count
                ),
                positive_window_percent=(
                    positive_window_count
                    / window_count
                    * 100.0
                ),
                average_return_percent=(
                    sum(returns)
                    / window_count
                ),
                median_return_percent=median(
                    returns
                ),
                worst_return_percent=min(
                    returns
                ),
                best_return_percent=max(
                    returns
                ),
                average_drawdown_percent=(
                    sum(drawdowns)
                    / window_count
                ),
            )
        )

    return sorted(
        rows,
        key=lambda row: (
            row.positive_window_percent,
            row.median_return_percent,
            row.average_return_percent,
            row.worst_return_percent,
            -row.average_drawdown_percent,
        ),
        reverse=True,
    )