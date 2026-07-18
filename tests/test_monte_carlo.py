import pytest

from app.monte_carlo import (
    MonteCarloSimulator,
)


def test_returns_requested_number_of_simulations() -> None:
    simulator = MonteCarloSimulator()

    results = simulator.run(
        trade_returns_percent=[
            5.0,
            -2.0,
            3.0,
        ],
        simulation_count=10,
        random_seed=123,
    )

    assert len(results) == 10

    assert [
        result.simulation_number
        for result in results
    ] == list(
        range(
            1,
            11,
        )
    )


def test_is_deterministic_with_fixed_seed() -> None:
    simulator = MonteCarloSimulator()

    first = simulator.run(
        trade_returns_percent=[
            5.0,
            -2.0,
            3.0,
        ],
        simulation_count=5,
        random_seed=123,
    )

    second = simulator.run(
        trade_returns_percent=[
            5.0,
            -2.0,
            3.0,
        ],
        simulation_count=5,
        random_seed=123,
    )

    assert first == second


def test_compounds_trade_returns() -> None:
    simulator = MonteCarloSimulator()

    results = simulator.run(
        trade_returns_percent=[
            10.0,
        ],
        simulation_count=1,
        random_seed=123,
    )

    assert (
        results[0].ending_return_percent
        == pytest.approx(10.0)
    )


def test_drawdown_is_never_negative() -> None:
    simulator = MonteCarloSimulator()

    results = simulator.run(
        trade_returns_percent=[
            5.0,
            -10.0,
            3.0,
        ],
        simulation_count=20,
        random_seed=123,
    )

    assert all(
        result.maximum_drawdown_percent
        >= 0
        for result in results
    )


def test_rejects_empty_trade_returns() -> None:
    simulator = MonteCarloSimulator()

    with pytest.raises(
        ValueError,
        match="At least one trade return",
    ):
        simulator.run(
            trade_returns_percent=[],
            simulation_count=10,
        )


def test_rejects_non_positive_simulation_count() -> None:
    simulator = MonteCarloSimulator()

    with pytest.raises(
        ValueError,
        match="Simulation count must be positive",
    ):
        simulator.run(
            trade_returns_percent=[
                1.0,
            ],
            simulation_count=0,
        )

def test_simulates_cash_profits_against_account_equity() -> None:
    simulator = MonteCarloSimulator()

    results = simulator.run_from_trade_profits(
        starting_equity=10_000.0,
        trade_profits=[
            100.0,
        ],
        simulation_count=1,
        random_seed=123,
    )

    assert (
        results[0].ending_return_percent
        == pytest.approx(1.0)
    )


def test_cash_profit_simulation_is_deterministic() -> None:
    simulator = MonteCarloSimulator()

    first = simulator.run_from_trade_profits(
        starting_equity=10_000.0,
        trade_profits=[
            100.0,
            -50.0,
            75.0,
        ],
        simulation_count=10,
        random_seed=123,
    )

    second = simulator.run_from_trade_profits(
        starting_equity=10_000.0,
        trade_profits=[
            100.0,
            -50.0,
            75.0,
        ],
        simulation_count=10,
        random_seed=123,
    )

    assert first == second


@pytest.mark.parametrize(
    (
        "starting_equity",
        "trade_profits",
        "simulation_count",
        "message",
    ),
    [
        (
            0.0,
            [100.0],
            10,
            "Starting equity",
        ),
        (
            10_000.0,
            [],
            10,
            "At least one trade profit",
        ),
        (
            10_000.0,
            [100.0],
            0,
            "Simulation count",
        ),
    ],
)
def test_rejects_invalid_cash_profit_simulation_inputs(
    starting_equity: float,
    trade_profits: list[float],
    simulation_count: int,
    message: str,
) -> None:
    simulator = MonteCarloSimulator()

    with pytest.raises(
        ValueError,
        match=message,
    ):
        simulator.run_from_trade_profits(
            starting_equity=starting_equity,
            trade_profits=trade_profits,
            simulation_count=simulation_count,
        )