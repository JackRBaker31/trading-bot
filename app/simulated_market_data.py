from datetime import datetime, timezone

from app.market_data import (
    MarketDataError,
    MarketDataProvider,
    PriceQuote,
)


class SimulatedMarketDataProvider(MarketDataProvider):
    def __init__(self, prices: dict[str, float]) -> None:
        self._prices: dict[str, float] = {}

        for symbol, price in prices.items():
            self.set_price(symbol, price)

    def get_price(self, symbol: str) -> PriceQuote:
        cleaned_symbol = symbol.upper().strip()

        if not cleaned_symbol:
            raise ValueError("A stock symbol is required.")

        if cleaned_symbol not in self._prices:
            raise MarketDataError(
                f"No simulated price is available for {cleaned_symbol}."
            )

        return PriceQuote(
            symbol=cleaned_symbol,
            price=self._prices[cleaned_symbol],
            timestamp=datetime.now(timezone.utc),
            provider="SIMULATED",
        )

    def set_price(self, symbol: str, price: float) -> None:
        quote = PriceQuote(
            symbol=symbol,
            price=price,
            provider="SIMULATED",
        )

        self._prices[quote.symbol] = quote.price