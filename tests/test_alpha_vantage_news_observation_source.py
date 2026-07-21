from datetime import (
    datetime,
    timezone,
)

from app.alpha_vantage_news_observation_source import (
    AlphaVantageNewsObservationSource,
)
from app.news_article import NewsArticle


class FakeArticleSource:
    def get_latest_news_article(
        self,
        symbol: str,
    ) -> NewsArticle | None:
        if symbol == "MSFT":
            return None

        return NewsArticle(
            symbol=symbol,
            title="Apple raises guidance",
            summary="Full-year outlook increased.",
            published_at=datetime(
                2026,
                7,
                18,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            source="alpha_vantage",
            url="https://example.test/article",
            relevance_score=0.91,
            source_sentiment_label="Bullish",
            source_sentiment_score=0.75,
        )


def test_converts_alpha_vantage_articles() -> None:
    articles = (
        AlphaVantageNewsObservationSource(
            article_source=FakeArticleSource()
        )
        .fetch_articles(
            symbols=[
                "AAPL",
                "MSFT",
            ]
        )
    )

    assert len(articles) == 1

    article = articles[0]

    assert article.symbol == "AAPL"
    assert article.provider_relevance == 0.91
    assert article.url == (
        "https://example.test/article"
    )
    assert article.article_id