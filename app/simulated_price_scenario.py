from dataclasses import dataclass

from app.simulated_market_data import (
    SimulatedMarketDataProvider,
)


@dataclass(frozen=True)
class SimulatedPriceScenario:
    prices_by_cycle: dict[
        int,
        dict[str, float],
    ]

    def apply(
        self,
        *,
        cycle_number: int,
        market_data: SimulatedMarketDataProvider,
    ) -> None:
        for symbol, price in (
            self.prices_by_cycle
            .get(cycle_number, {})
            .items()
        ):
            market_data.set_price(
                symbol,
                price,
            )