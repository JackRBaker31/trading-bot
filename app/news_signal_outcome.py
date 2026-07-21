from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NewsSignalOutcome:
    article_id: str
    symbol: str
    horizon_name: str
    signal_published_at: datetime
    observed_at: datetime
    reference_price: float
    observed_price: float
    return_percent: float

    def __post_init__(self) -> None:
        article_id = self.article_id.strip()
        symbol = self.symbol.upper().strip()
        horizon_name = (
            self.horizon_name.upper().strip()
        )

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
            "horizon_name",
            horizon_name,
        )

        if not article_id:
            raise ValueError(
                "Article ID is required."
            )

        if not symbol:
            raise ValueError(
                "Symbol is required."
            )

        if not horizon_name:
            raise ValueError(
                "Horizon name is required."
            )

        if self.reference_price <= 0:
            raise ValueError(
                "Reference price must be positive."
            )

        if self.observed_price <= 0:
            raise ValueError(
                "Observed price must be positive."
            )

        if self.observed_at < self.signal_published_at:
            raise ValueError(
                "Observation cannot predate "
                "signal publication."
            )