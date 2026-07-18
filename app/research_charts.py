from pathlib import Path

import matplotlib

matplotlib.use(
    "Agg"
)

import matplotlib.pyplot as plt

from app.backtest_result import EquityPoint
from app.monte_carlo import MonteCarloResult
from app.rolling_walk_forward_optimizer import (
    RollingWalkForwardResult,
)


def save_equity_curve_chart(
    *,
    equity_curve: list[EquityPoint],
    output_path: str,
) -> None:
    if not equity_curve:
        raise ValueError(
            "At least one equity point is required."
        )

    path = _prepare_output_path(
        output_path
    )

    labels = [
        point.label
        for point in equity_curve
    ]
    values = [
        point.portfolio_value
        for point in equity_curve
    ]

    figure, axis = plt.subplots()
    axis.plot(
        labels,
        values,
    )
    axis.set_title(
        "Equity Curve"
    )
    axis.set_xlabel(
        "Date"
    )
    axis.set_ylabel(
        "Portfolio Value"
    )
    axis.tick_params(
        axis="x",
        rotation=45,
    )
    figure.tight_layout()
    figure.savefig(
        path,
    )
    plt.close(
        figure
    )


def save_drawdown_chart(
    *,
    equity_curve: list[EquityPoint],
    output_path: str,
) -> None:
    if not equity_curve:
        raise ValueError(
            "At least one equity point is required."
        )

    path = _prepare_output_path(
        output_path
    )

    labels = [
        point.label
        for point in equity_curve
    ]

    drawdowns: list[float] = []
    peak_value = (
        equity_curve[0]
        .portfolio_value
    )

    for point in equity_curve:
        peak_value = max(
            peak_value,
            point.portfolio_value,
        )

        drawdown_percent = (
            (
                peak_value
                - point.portfolio_value
            )
            / peak_value
            * 100.0
        )

        drawdowns.append(
            drawdown_percent
        )

    figure, axis = plt.subplots()
    axis.plot(
        labels,
        drawdowns,
    )
    axis.set_title(
        "Drawdown"
    )
    axis.set_xlabel(
        "Date"
    )
    axis.set_ylabel(
        "Drawdown %"
    )
    axis.tick_params(
        axis="x",
        rotation=45,
    )
    figure.tight_layout()
    figure.savefig(
        path,
    )
    plt.close(
        figure
    )


def save_monte_carlo_histogram(
    *,
    simulations: list[MonteCarloResult],
    output_path: str,
) -> None:
    if not simulations:
        raise ValueError(
            "At least one simulation is required."
        )

    path = _prepare_output_path(
        output_path
    )

    returns = [
        result.ending_return_percent
        for result in simulations
    ]

    figure, axis = plt.subplots()
    axis.hist(
        returns,
        bins=30,
    )
    axis.set_title(
        "Monte Carlo Return Distribution"
    )
    axis.set_xlabel(
        "Ending Return %"
    )
    axis.set_ylabel(
        "Frequency"
    )
    figure.tight_layout()
    figure.savefig(
        path,
    )
    plt.close(
        figure
    )


def save_rolling_returns_chart(
    *,
    results: list[
        RollingWalkForwardResult
    ],
    output_path: str,
) -> None:
    if not results:
        raise ValueError(
            "At least one rolling result is required."
        )

    path = _prepare_output_path(
        output_path
    )

    windows = [
        result.window_number
        for result in results
    ]
    returns = [
        result.validation_result
        .total_return_percent
        for result in results
    ]

    figure, axis = plt.subplots()
    axis.bar(
        windows,
        returns,
    )
    axis.set_title(
        "Rolling Validation Returns"
    )
    axis.set_xlabel(
        "Window"
    )
    axis.set_ylabel(
        "Validation Return %"
    )
    figure.tight_layout()
    figure.savefig(
        path,
    )
    plt.close(
        figure
    )


def _prepare_output_path(
    output_path: str,
) -> Path:
    path = Path(
        output_path
    )

    if path.suffix.lower() != ".png":
        raise ValueError(
            "Chart output path must end in .png."
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path