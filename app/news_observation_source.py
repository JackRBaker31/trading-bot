from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import hashlib

from app.news_signal_classifier import (
    NewsArticleInput,
)


@dataclass(frozen=True)
class ProviderNewsArticle:
    symbol: str
    headline: str
    summary: str
    source: str
    published_at: datetime
    url: str = ""


class CallableNewsObservationSource:
    def __init__(
        self,
        *,
        fetcher: Callable[
            [list[str]],
            list[ProviderNewsArticle],
        ],
    ) -> None:
        self.fetcher = fetcher

    def fetch_articles(
        self,
        *,
        symbols: list[str],
    ) -> list[NewsArticleInput]:
        provider_articles = self.fetcher(
            symbols
        )

        return [
            NewsArticleInput(
                article_id=create_article_id(
                    article=article
                ),
                symbol=article.symbol,
                headline=article.headline,
                summary=article.summary,
                source=article.source,
                published_at=(
                    article.published_at
                ),
            )
            for article in provider_articles
        ]


def create_article_id(
    *,
    article: ProviderNewsArticle,
) -> str:
    identity = "\n".join(
        (
            article.symbol.upper().strip(),
            article.source.strip(),
            article.headline.strip(),
            article.url.strip(),
            article.published_at.isoformat(),
        )
    )

    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()