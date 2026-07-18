from types import SimpleNamespace

import pytest

from app.backtest_result import EquityPoint
from app.monte_carlo import MonteCarloResult
from app.research_charts import (
    save_drawdown_chart,
    save_equity_curve_chart,
    save_monte_carlo_histogram,
    save_rolling_returns_chart,
)


def test_saves_equity_curve_chart(
    tmp_path,
) -> None:
    output_path = (
        tmp_path / "equity_curve.png"
    )

    save_equity_curve_chart(
        equity_curve=[
            EquityPoint(
                label="2026-01-01",
                portfolio_value=10_000.0,
            ),
            EquityPoint(
                label="2026-01-02",
                portfolio_value=10_100.0,
            ),
        ],
        output_path=str(output_path),
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_saves_drawdown_chart(
    tmp_path,
) -> None:
    output_path = (
        tmp_path / "drawdown.png"
    )

    save_drawdown_chart(
        equity_curve=[
            EquityPoint(
                label="2026-01-01",
                portfolio_value=10_000.0,
            ),
            EquityPoint(
                label="2026-01-02",
                portfolio_value=9_500.0,
            ),
        ],
        output_path=str(output_path),
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_saves_monte_carlo_histogram(
    tmp_path,
) -> None:
    output_path = (
        tmp_path / "monte_carlo.png"
    )

    save_monte_carlo_histogram(
        simulations=[
            MonteCarloResult(
                simulation_number=1,
                ending_return_percent=5.0,
                maximum_drawdown_percent=2.0,
            ),
            MonteCarloResult(
                simulation_number=2,
                ending_return_percent=-1.0,
                maximum_drawdown_percent=4.0,
            ),
        ],
        output_path=str(output_path),
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_saves_rolling_returns_chart(
    tmp_path,
) -> None:
    output_path = (
        tmp_path / "rolling_returns.png"
    )

    save_rolling_returns_chart(
        results=[
            SimpleNamespace(
                window_number=1,
                validation_result=SimpleNamespace(
                    total_return_percent=2.0
                ),
            ),
            SimpleNamespace(
                window_number=2,
                validation_result=SimpleNamespace(
                    total_return_percent=-1.0
                ),
            ),
        ],
        output_path=str(output_path),
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0


@pytest.mark.parametrize(
    (
        "function_name",
        "argument_name",
    ),
    [
        (
            "equity",
            "equity_curve",
        ),
        (
            "drawdown",
            "equity_curve",
        ),
        (
            "monte_carlo",
            "simulations",
        ),
        (
            "rolling",
            "results",
        ),
    ],
)
def test_rejects_empty_chart_data(
    tmp_path,
    function_name: str,
    argument_name: str,
) -> None:
    output_path = (
        tmp_path / f"{function_name}.png"
    )

    functions = {
        "equity": save_equity_curve_chart,
        "drawdown": save_drawdown_chart,
        "monte_carlo": (
            save_monte_carlo_histogram
        ),
        "rolling": save_rolling_returns_chart,
    }

    function = functions[
        function_name
    ]

    with pytest.raises(
        ValueError,
        match="At least one",
    ):
        function(
            **{
                argument_name: [],
                "output_path": str(
                    output_path
                ),
            }
        )


def test_rejects_non_png_output(
    tmp_path,
) -> None:
    with pytest.raises(
        ValueError,
        match=".png",
    ):
        save_equity_curve_chart(
            equity_curve=[
                EquityPoint(
                    label="2026-01-01",
                    portfolio_value=10_000.0,
                )
            ],
            output_path=str(
                tmp_path / "equity_curve.jpg"
            ),
        )