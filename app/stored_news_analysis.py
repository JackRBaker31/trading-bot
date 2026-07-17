from dataclasses import dataclass
from datetime import datetime

from app.news_analysis import (
    NewsAnalysis,
)


@dataclass(frozen=True)
class StoredNewsAnalysis:
    analysis: NewsAnalysis
    analysed_at: datetime
    expires_at: datetime
    article_title: str
    article_url: str | None
    published_at: datetime
    relevance_score: float
    source_sentiment_label: str | None
    source_sentiment_score: float | None
    model_name: str
    prompt_version: str

    def __post_init__(
        self,
    ) -> None:
        if (
            self.expires_at
            <= self.analysed_at
        ):
            raise ValueError(
                "Expiry time must be after "
                "analysis time."
            )

        if not 0 <= self.relevance_score <= 1:
            raise ValueError(
                "Relevance score must be "
                "between zero and one."
            )

        if not self.article_title.strip():
            raise ValueError(
                "Article title is required."
            )

        if not self.model_name.strip():
            raise ValueError(
                "Model name is required."
            )

        if not self.prompt_version.strip():
            raise ValueError(
                "Prompt version is required."
            )