from collections import defaultdict
from dataclasses import dataclass
from statistics import median

from app.rolling_walk_forward_optimizer import (
    RollingWalkForwardResult,
)


@dataclass(frozen=True)
class StrategyRobustnessRow:
    name: str
    selected_window_count: int
    positive_window_count: int
    positive_window_percent: float
    average_return_percent: float
    median_return_percent: float
    worst_return_percent: float
    best_return_percent: float
    average_drawdown_percent: float


def rank_strategy_robustness(
    results: list[RollingWalkForwardResult],
) -> list[StrategyRobustnessRow]:
    if not results:
        raise ValueError(
            "At least one rolling result is required."
        )

    validation_returns: dict[
        str,
        list[float],
    ] = defaultdict(list)

    validation_drawdowns: dict[
        str,
        list[float],
    ] = defaultdict(list)

    for result in results:
        validation = result.validation_result

        validation_returns[
            validation.name
        ].append(
            validation.total_return_percent
        )

        validation_drawdowns[
            validation.name
        ].append(
            validation.maximum_drawdown_percent
        )

    rows: list[
        StrategyRobustnessRow
    ] = []

    for name, returns in (
        validation_returns.items()
    ):
        drawdowns = (
            validation_drawdowns[name]
        )

        selected_window_count = len(
            returns
        )

        positive_window_count = sum(
            1
            for value in returns
            if value > 0
        )

        rows.append(
            StrategyRobustnessRow(
                name=name,
                selected_window_count=(
                    selected_window_count
                ),
                positive_window_count=(
                    positive_window_count
                ),
                positive_window_percent=(
                    positive_window_count
                    / selected_window_count
                    * 100.0
                ),
                average_return_percent=(
                    sum(returns)
                    / selected_window_count
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
                    / selected_window_count
                ),
            )
        )

    return sorted(
        rows,
        key=lambda row: (
            row.positive_window_percent,
            row.median_return_percent,
            row.average_return_percent,
            -row.average_drawdown_percent,
            row.selected_window_count,
        ),
        reverse=True,
    )