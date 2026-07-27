from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone


class MarketDataError(Exception):
    """Raised when market data cannot be retrieved or validated."""


class MarketDataProviderError(MarketDataError):
    """Raised when an upstream market-data provider rejects a request."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        status_code: int | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider.upper().strip()
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds

    @property
    def rate_limited(self) -> bool:
        return self.status_code == 429


class MarketDataUnavailableError(MarketDataError):
    """Raised when neither live nor cached market data can be supplied."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "MARKET_DATA_UNAVAILABLE",
        provider: str = "TWELVE_DATA",
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code.upper().strip()
        self.provider = provider.upper().strip()
        self.retry_after_seconds = retry_after_seconds

    def to_dictionary(self) -> dict[str, object]:
        return {
            "status": "degraded",
            "code": self.code,
            "provider": self.provider,
            "data_source": "UNAVAILABLE",
            "is_stale": False,
            "retry_after_seconds": self.retry_after_seconds,
            "warning": str(self),
        }


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
