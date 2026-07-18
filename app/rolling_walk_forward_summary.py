from dataclasses import dataclass
from statistics import median

from app.rolling_walk_forward_optimizer import (
    RollingWalkForwardResult,
)


@dataclass(frozen=True)
class RollingWalkForwardSummary:
    window_count: int
    positive_window_count: int
    positive_window_percent: float
    average_return_percent: float
    median_return_percent: float
    worst_return_percent: float
    best_return_percent: float
    average_drawdown_percent: float


def summarize_rolling_results(
    results: list[RollingWalkForwardResult],
) -> RollingWalkForwardSummary:
    if not results:
        raise ValueError(
            "At least one rolling result is required."
        )

    returns = [
        result.validation_result
        .total_return_percent
        for result in results
    ]

    drawdowns = [
        result.validation_result
        .maximum_drawdown_percent
        for result in results
    ]

    positive_window_count = sum(
        1
        for value in returns
        if value > 0
    )

    window_count = len(results)

    return RollingWalkForwardSummary(
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