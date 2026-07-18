from datetime import date, timedelta

import pytest

from app.buy_the_dip import BuyTheDipStrategy
from app.historical_data import HistoricalPrice
from app.risk import RiskLimits
from app.strategy_definition import (
    StrategyDefinition,
)
from app.strategy_validation_matrix import (
    StrategyValidationMatrix,
)


def create_matrix() -> StrategyValidationMatrix:
    return StrategyValidationMatrix(
        starting_cash=10_000.0,
        risk_limits=RiskLimits(
            max_order_value=2_000.0,
            max_position_value=3_000.0,
            max_portfolio_exposure=0.5,
            max_trades_per_session=10_000,
            approved_symbols={"AAPL"},
        ),
    )


def create_prices() -> list[HistoricalPrice]:
    values = [
        100.0,
        95.0,
        105.0,
        100.0,
        94.0,
        104.0,
        100.0,
        93.0,
        103.0,
        100.0,
    ]

    start_date = date(
        2026,
        1,
        1,
    )

    return [
        HistoricalPrice(
            trading_date=(
                start_date
                + timedelta(days=index)
            ),
            prices={
                "AAPL": value,
            },
        )
        for index, value in enumerate(
            values
        )
    ]


def create_definitions() -> list[
    StrategyDefinition
]:
    return [
        StrategyDefinition(
            name="Loose",
            factory=lambda: BuyTheDipStrategy(
                drop_threshold_percent=2.0,
                cooldown_cycles=0,
            ),
        ),
        StrategyDefinition(
            name="Strict",
            factory=lambda: BuyTheDipStrategy(
                drop_threshold_percent=10.0,
                cooldown_cycles=0,
            ),
        ),
    ]


def test_evaluates_every_strategy_in_every_window() -> None:
    matrix = create_matrix()

    results = matrix.run(
        historical_prices=create_prices(),
        strategy_definitions=(
            create_definitions()
        ),
        training_size=4,
        validation_size=2,
        step_size=2,
    )

    assert len(results) == 6

    assert {
        result.window_number
        for result in results
    } == {
        1,
        2,
        3,
    }

    results_by_window = {
        window_number: [
            result.strategy_result.name
            for result in results
            if (
                result.window_number
                == window_number
            )
        ]
        for window_number in {
            1,
            2,
            3,
        }
    }

    assert results_by_window == {
        1: [
            "Loose",
            "Strict",
        ],
        2: [
            "Loose",
            "Strict",
        ],
        3: [
            "Loose",
            "Strict",
        ],
    }


def test_each_validation_run_uses_fresh_strategy_instances() -> None:
    matrix = create_matrix()

    results = matrix.run(
        historical_prices=create_prices(),
        strategy_definitions=(
            create_definitions()
        ),
        training_size=4,
        validation_size=2,
        step_size=2,
    )

    loose_results = [
        result.strategy_result
        for result in results
        if result.strategy_result.name == "Loose"
    ]

    assert len(loose_results) == 3


def test_rejects_empty_strategy_definitions() -> None:
    matrix = create_matrix()

    with pytest.raises(
        ValueError,
        match="At least one strategy definition",
    ):
        matrix.run(
            historical_prices=create_prices(),
            strategy_definitions=[],
            training_size=4,
            validation_size=2,
            step_size=2,
        )