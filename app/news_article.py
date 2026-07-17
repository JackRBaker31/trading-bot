from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NewsArticle:
    symbol: str
    title: str
    summary: str
    published_at: datetime
    source: str
    url: str | None
    relevance_score: float
    source_sentiment_label: str | None
    source_sentiment_score: float | None

    @property
    def article_text(self) -> str:
        parts = [
            f"Ticker: {self.symbol}",
        ]

        if (
            self.source_sentiment_label
            and self.source_sentiment_score
            is not None
        ):
            parts.append(
                "Source sentiment: "
                f"{self.source_sentiment_label} "
                f"({self.source_sentiment_score})"
            )

        parts.extend(
            part
            for part in (
                self.title,
                self.summary,
            )
            if part.strip()
        )

        return "\n\n".join(
            parts
        )