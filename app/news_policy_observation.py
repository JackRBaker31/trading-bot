from dataclasses import dataclass
from datetime import datetime

from app.news_analysis import (
    NewsSentiment,
)
from app.orders import (
    OrderSide,
)


@dataclass(frozen=True)
class NewsPolicyObservation:
    symbol: str
    side: OrderSide
    quantity: int
    analysis_available: bool
    analysis_sentiment: (
        NewsSentiment | None
    )
    analysis_expires_at: (
        datetime | None
    )
    would_approve: bool
    reason: str
    observed_at: datetime

    def __post_init__(
        self,
    ) -> None:
        normalised_symbol = (
            self.symbol.upper().strip()
        )

        if not normalised_symbol:
            raise ValueError(
                "Symbol is required."
            )

        if self.quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        if (
            self.analysis_available
            and self.analysis_sentiment is None
        ):
            raise ValueError(
                "Available analysis must include "
                "a sentiment."
            )

        if (
            not self.analysis_available
            and self.analysis_sentiment is not None
        ):
            raise ValueError(
                "Unavailable analysis cannot include "
                "a sentiment."
            )

        if (
            not self.analysis_available
            and self.analysis_expires_at is not None
        ):
            raise ValueError(
                "Unavailable analysis cannot include "
                "an expiry time."
            )

        if not self.reason.strip():
            raise ValueError(
                "Observation reason is required."
            )

        object.__setattr__(
            self,
            "symbol",
            normalised_symbol,
        )