from abc import ABC, abstractmethod
from dataclasses import dataclass


class MarketDataError(Exception):
    """Raised when market data cannot be retrieved."""


@dataclass(frozen=True)
class PriceQuote:
    symbol: str
    price: float

    def __post_init__(self) -> None:
        cleaned_symbol = self.symbol.upper().strip()
        object.__setattr__(self, "symbol", cleaned_symbol)

        if not cleaned_symbol:
            raise ValueError("A stock symbol is required.")

        if self.price <= 0:
            raise ValueError("Price must be greater than zero.")


class MarketDataProvider(ABC):
    @abstractmethod
    def get_price(self, symbol: str) -> PriceQuote:
        """Return the latest available price for one symbol."""

    def get_prices(self, symbols: list[str]) -> dict[str, float]:
        prices: dict[str, float] = {}

        for symbol in symbols:
            quote = self.get_price(symbol)
            prices[quote.symbol] = quote.price

        return prices