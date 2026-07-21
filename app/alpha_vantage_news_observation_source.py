from typing import Protocol

from app.news_article import NewsArticle
from app.news_observation_source import (
    ProviderNewsArticle,
    create_article_id,
)
from app.news_signal_classifier import (
    NewsArticleInput,
)


class LatestNewsArticleSource(Protocol):
    def get_latest_news_article(
        self,
        symbol: str,
    ) -> NewsArticle | None:
        ...


class AlphaVantageNewsObservationSource:
    def __init__(
        self,
        *,
        article_source: LatestNewsArticleSource,
    ) -> None:
        self.article_source = article_source

    def fetch_articles(
        self,
        *,
        symbols: list[str],
    ) -> list[NewsArticleInput]:
        articles: list[
            NewsArticleInput
        ] = []

        for symbol in symbols:
            article = (
                self.article_source
                .get_latest_news_article(
                    symbol
                )
            )

            if article is None:
                continue

            provider_article = (
                ProviderNewsArticle(
                    symbol=article.symbol,
                    headline=article.title,
                    summary=article.summary,
                    source=article.source,
                    published_at=(
                        article.published_at
                    ),
                    url=article.url or "",
                )
            )

            articles.append(
                NewsArticleInput(
                    article_id=create_article_id(
                        article=provider_article
                    ),
                    symbol=article.symbol,
                    headline=article.title,
                    summary=article.summary,
                    source=article.source,
                    published_at=(
                        article.published_at
                    ),
                    url=article.url or "",
                    provider_relevance=(
                        article.relevance_score
                    ),
                    provider_sentiment_label=(
                        article.source_sentiment_label
                    ),
                    provider_sentiment_score=(
                        article.source_sentiment_score
                    ),
                )
            )

        return articles