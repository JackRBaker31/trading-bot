import pytest

from app.monte_carlo import (
    MonteCarloResult,
)
from app.monte_carlo_summary import (
    summarize_monte_carlo_results,
)


def test_summarizes_monte_carlo_results() -> None:
    results = [
        MonteCarloResult(
            simulation_number=1,
            ending_return_percent=-10.0,
            maximum_drawdown_percent=12.0,
        ),
        MonteCarloResult(
            simulation_number=2,
            ending_return_percent=0.0,
            maximum_drawdown_percent=5.0,
        ),
        MonteCarloResult(
            simulation_number=3,
            ending_return_percent=10.0,
            maximum_drawdown_percent=3.0,
        ),
    ]

    summary = summarize_monte_carlo_results(
        results
    )

    assert summary.simulation_count == 3
    assert (
        summary.average_return_percent
        == pytest.approx(0.0)
    )
    assert summary.median_return_percent == 0.0
    assert (
        summary.fifth_percentile_return_percent
        == pytest.approx(-9.0)
    )
    assert (
        summary.ninety_fifth_percentile_return_percent
        == pytest.approx(9.0)
    )
    assert summary.worst_return_percent == -10.0
    assert summary.best_return_percent == 10.0
    assert (
        summary.average_drawdown_percent
        == pytest.approx(
            20.0 / 3.0
        )
    )
    assert summary.worst_drawdown_percent == 12.0
    assert (
        summary.loss_probability_percent
        == pytest.approx(
            100.0 / 3.0
        )
    )


def test_handles_single_result() -> None:
    result = MonteCarloResult(
        simulation_number=1,
        ending_return_percent=5.0,
        maximum_drawdown_percent=2.0,
    )

    summary = summarize_monte_carlo_results(
        [
            result,
        ]
    )

    assert (
        summary.fifth_percentile_return_percent
        == 5.0
    )
    assert (
        summary.ninety_fifth_percentile_return_percent
        == 5.0
    )


def test_rejects_empty_results() -> None:
    with pytest.raises(
        ValueError,
        match="At least one Monte Carlo result",
    ):
        summarize_monte_carlo_results([])