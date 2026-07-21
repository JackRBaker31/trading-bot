from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NewsSignalPriceSnapshot:
    article_id: str
    symbol: str
    captured_at: datetime
    price: float
    provider: str

    def __post_init__(self) -> None:
        article_id = self.article_id.strip()
        symbol = self.symbol.upper().strip()
        provider = self.provider.upper().strip()

        object.__setattr__(
            self,
            "article_id",
            article_id,
        )
        object.__setattr__(
            self,
            "symbol",
            symbol,
        )
        object.__setattr__(
            self,
            "provider",
            provider,
        )

        if not article_id:
            raise ValueError(
                "Article ID is required."
            )

        if not symbol:
            raise ValueError(
                "Symbol is required."
            )

        if self.price <= 0:
            raise ValueError(
                "Snapshot price must be positive."
            )

        if not provider:
            raise ValueError(
                "Snapshot provider is required."
            )