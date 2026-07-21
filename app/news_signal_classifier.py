from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from app.news_signal import NewsSignal


@dataclass(frozen=True)
class NewsArticleInput:
    article_id: str
    symbol: str
    headline: str
    summary: str
    source: str
    published_at: datetime
    url: str = ""
    provider_relevance: float = 1.0
    provider_sentiment_label: str | None = None
    provider_sentiment_score: float | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.provider_relevance <= 1.0:
            raise ValueError(
                "Provider relevance must be "
                "between 0.0 and 1.0."
            )

    @property
    def article_text(self) -> str:
        parts = [
            f"Ticker: {self.symbol}",
            self.headline,
            self.summary,
        ]

        if (
            self.provider_sentiment_label
            and self.provider_sentiment_score
            is not None
        ):
            parts.insert(
                1,
                "Source sentiment: "
                f"{self.provider_sentiment_label} "
                f"({self.provider_sentiment_score})",
            )

        return "\n\n".join(
            part.strip()
            for part in parts
            if part.strip()
        )


class NewsSignalClassifier(Protocol):
    def classify(
        self,
        *,
        article: NewsArticleInput,
    ) -> NewsSignal:
        ...


@dataclass(frozen=True)
class FixedNewsSignalClassifier:
    sentiment: float
    relevance: float
    confidence: float
    event_type: str
    is_material: bool
    expiry_hours: int = 24
    reasoning_summary: str = (
        "Deterministic classifier result."
    )

    def classify(
        self,
        *,
        article: NewsArticleInput,
    ) -> NewsSignal:
        if self.expiry_hours <= 0:
            raise ValueError(
                "Expiry hours must be positive."
            )

        return NewsSignal(
            article_id=article.article_id,
            symbol=article.symbol,
            headline=article.headline,
            sentiment=self.sentiment,
            relevance=self.relevance,
            confidence=self.confidence,
            event_type=self.event_type,
            is_material=self.is_material,
            published_at=article.published_at,
            expires_at=(
                article.published_at
                + timedelta(
                    hours=self.expiry_hours
                )
            ),
            source=article.source,
            reasoning_summary=(
                self.reasoning_summary
            ),
        )