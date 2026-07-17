import os

from app.market_data import MarketDataProvider
from app.simulated_market_data import (
    SimulatedMarketDataProvider,
)
from app.twelve_data_market_data import (
    TwelveDataMarketDataProvider,
)


def create_market_data_provider(
    provider_name: str,
    symbols: list[str],
) -> MarketDataProvider:
    cleaned_name = provider_name.upper().strip()

    if cleaned_name == "SIMULATED":
        simulated_starting_prices = {
            "AAPL": 150.00,
            "MSFT": 320.00,
            "AMZN": 250.00,
        }

        missing_symbols = [
            symbol
            for symbol in symbols
            if symbol not in simulated_starting_prices
        ]

        if missing_symbols:
            raise ValueError(
                "No simulated starting price exists for: "
                + ", ".join(missing_symbols)
            )

        return SimulatedMarketDataProvider(
            prices={
                symbol: simulated_starting_prices[symbol]
                for symbol in symbols
            }
        )

    if cleaned_name == "TWELVE_DATA":
        api_key = os.getenv(
            "TWELVE_DATA_API_KEY"
        )

        if api_key is None or not api_key.strip():
            raise RuntimeError(
                "TWELVE_DATA_API_KEY was not found "
                "in the environment."
            )

        return TwelveDataMarketDataProvider(
            api_key=api_key
        )

    raise ValueError(
        f"Unsupported market-data provider: "
        f"{provider_name}"
    )