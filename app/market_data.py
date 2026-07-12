from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone


class MarketDataError(Exception):
    """Raised when market data cannot be retrieved or validated."""


@dataclass(frozen=True)
class PriceQuote:
    symbol: str
    price: float
    timestamp: datetime | None = None
    provider: str = "UNKNOWN"

    def __post_init__(self) -> None:
        cleaned_symbol = self.symbol.upper().strip()
        cleaned_provider = self.provider.upper().strip()

        object.__setattr__(self, "symbol", cleaned_symbol)
        object.__setattr__(self, "provider", cleaned_provider)

        if not cleaned_symbol:
            raise ValueError("A stock symbol is required.")

        if self.price <= 0:
            raise ValueError("Price must be greater than zero.")

        if not cleaned_provider:
            raise ValueError("A market-data provider is required.")

        if (
            self.timestamp is not None
            and self.timestamp.tzinfo is None
        ):
            object.__setattr__(
                self,
                "timestamp",
                self.timestamp.replace(
                    tzinfo=timezone.utc
                ),
            )


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