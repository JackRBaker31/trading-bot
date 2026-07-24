from dataclasses import dataclass, field
from datetime import datetime

from app.news_confidence_models import (
    NewsConfidenceFactor,
)


@dataclass(frozen=True)
class NewsSignal:
    article_id: str
    symbol: str
    headline: str
    sentiment: float
    relevance: float
    confidence: float
    event_type: str
    is_material: bool
    published_at: datetime
    expires_at: datetime
    source: str
    reasoning_summary: str
    confidence_breakdown: tuple[
        NewsConfidenceFactor,
        ...
    ] = field(
        default_factory=tuple
    )

    def __post_init__(
        self,
    ) -> None:
        cleaned_article_id = (
            self.article_id.strip()
        )
        cleaned_symbol = (
            self.symbol
            .upper()
            .strip()
        )
        cleaned_headline = (
            self.headline.strip()
        )
        cleaned_event_type = (
            self.event_type
            .upper()
            .strip()
        )
        cleaned_source = (
            self.source.strip()
        )
        cleaned_reasoning = (
            self.reasoning_summary
            .strip()
        )

        object.__setattr__(
            self,
            "article_id",
            cleaned_article_id,
        )
        object.__setattr__(
            self,
            "symbol",
            cleaned_symbol,
        )
        object.__setattr__(
            self,
            "headline",
            cleaned_headline,
        )
        object.__setattr__(
            self,
            "event_type",
            cleaned_event_type,
        )
        object.__setattr__(
            self,
            "source",
            cleaned_source,
        )
        object.__setattr__(
            self,
            "reasoning_summary",
            cleaned_reasoning,
        )

        if not cleaned_article_id:
            raise ValueError(
                "Article ID is required."
            )

        if not cleaned_symbol:
            raise ValueError(
                "Symbol is required."
            )

        if not cleaned_headline:
            raise ValueError(
                "Headline is required."
            )

        if not cleaned_event_type:
            raise ValueError(
                "Event type is required."
            )

        if not cleaned_source:
            raise ValueError(
                "Source is required."
            )

        if not (
            -1.0
            <= self.sentiment
            <= 1.0
        ):
            raise ValueError(
                "Sentiment must be "
                "between -1.0 and 1.0."
            )

        if not (
            0.0
            <= self.relevance
            <= 1.0
        ):
            raise ValueError(
                "Relevance must be "
                "between 0.0 and 1.0."
            )

        if not (
            0.0
            <= self.confidence
            <= 1.0
        ):
            raise ValueError(
                "Confidence must be "
                "between 0.0 and 1.0."
            )

        if (
            self.expires_at
            <= self.published_at
        ):
            raise ValueError(
                "Expiry must be later "
                "than publication."
            )
