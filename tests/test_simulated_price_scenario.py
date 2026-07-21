import pytest

from app.simulated_market_data import (
    SimulatedMarketDataProvider,
)
from app.simulated_price_scenario import (
    SimulatedPriceScenario,
)


def test_applies_prices_for_matching_cycle() -> None:
    market_data = SimulatedMarketDataProvider(
        prices={
            "AAPL": 100.0,
            "MSFT": 200.0,
        }
    )

    scenario = SimulatedPriceScenario(
        prices_by_cycle={
            2: {
                "AAPL": 95.0,
                "MSFT": 190.0,
            }
        }
    )

    scenario.apply(
        cycle_number=2,
        market_data=market_data,
    )

    assert (
        market_data.get_price(
            "AAPL"
        ).price
        == 95.0
    )
    assert (
        market_data.get_price(
            "MSFT"
        ).price
        == 190.0
    )


def test_unknown_cycle_leaves_prices_unchanged() -> None:
    market_data = SimulatedMarketDataProvider(
        prices={
            "AAPL": 100.0,
        }
    )

    scenario = SimulatedPriceScenario(
        prices_by_cycle={
            2: {
                "AAPL": 95.0,
            }
        }
    )

    scenario.apply(
        cycle_number=3,
        market_data=market_data,
    )

    assert (
        market_data.get_price(
            "AAPL"
        ).price
        == 100.0
    )


@pytest.mark.parametrize(
    "invalid_price",
    [
        0.0,
        -1.0,
    ],
)
def test_rejects_non_positive_prices(
    invalid_price: float,
) -> None:
    market_data = SimulatedMarketDataProvider(
        prices={
            "AAPL": 100.0,
        }
    )

    scenario = SimulatedPriceScenario(
        prices_by_cycle={
            2: {
                "AAPL": invalid_price,
            }
        }
    )

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        scenario.apply(
            cycle_number=2,
            market_data=market_data,
        )