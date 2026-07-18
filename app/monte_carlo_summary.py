from dataclasses import dataclass
from statistics import mean, median

from app.monte_carlo import (
    MonteCarloResult,
)


@dataclass(frozen=True)
class MonteCarloSummary:
    simulation_count: int
    average_return_percent: float
    median_return_percent: float
    fifth_percentile_return_percent: float
    ninety_fifth_percentile_return_percent: float
    worst_return_percent: float
    best_return_percent: float
    average_drawdown_percent: float
    worst_drawdown_percent: float
    loss_probability_percent: float


def summarize_monte_carlo_results(
    results: list[MonteCarloResult],
) -> MonteCarloSummary:
    if not results:
        raise ValueError(
            "At least one Monte Carlo result is required."
        )

    returns = sorted(
        result.ending_return_percent
        for result in results
    )

    drawdowns = [
        result.maximum_drawdown_percent
        for result in results
    ]

    loss_count = sum(
        1
        for value in returns
        if value < 0
    )

    return MonteCarloSummary(
        simulation_count=len(results),
        average_return_percent=mean(
            returns
        ),
        median_return_percent=median(
            returns
        ),
        fifth_percentile_return_percent=(
            _percentile(
                values=returns,
                percentile=5.0,
            )
        ),
        ninety_fifth_percentile_return_percent=(
            _percentile(
                values=returns,
                percentile=95.0,
            )
        ),
        worst_return_percent=min(
            returns
        ),
        best_return_percent=max(
            returns
        ),
        average_drawdown_percent=mean(
            drawdowns
        ),
        worst_drawdown_percent=max(
            drawdowns
        ),
        loss_probability_percent=(
            loss_count
            / len(results)
            * 100.0
        ),
    )


def _percentile(
    *,
    values: list[float],
    percentile: float,
) -> float:
    if len(values) == 1:
        return values[0]

    position = (
        percentile
        / 100.0
        * (
            len(values) - 1
        )
    )

    lower_index = int(position)
    upper_index = min(
        lower_index + 1,
        len(values) - 1,
    )

    weight = position - lower_index

    return (
        values[lower_index]
        * (
            1.0 - weight
        )
        + values[upper_index]
        * weight
    )