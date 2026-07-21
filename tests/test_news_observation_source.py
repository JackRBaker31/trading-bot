from datetime import (
    datetime,
    timezone,
)

from app.news_observation_source import (
    CallableNewsObservationSource,
    ProviderNewsArticle,
    create_article_id,
)


def create_provider_article(
) -> ProviderNewsArticle:
    return ProviderNewsArticle(
        symbol="aapl",
        headline="Apple raises guidance",
        summary="Guidance increased.",
        source="Example News",
        published_at=datetime(
            2026,
            7,
            18,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        url="https://example.test/article",
    )


def test_converts_provider_articles() -> None:
    source = CallableNewsObservationSource(
        fetcher=lambda symbols: [
            create_provider_article()
        ]
    )

    articles = source.fetch_articles(
        symbols=["AAPL"]
    )

    assert len(articles) == 1
    assert articles[0].symbol == "aapl"
    assert articles[0].headline == (
        "Apple raises guidance"
    )
    assert articles[0].article_id


def test_article_id_is_deterministic() -> None:
    article = create_provider_article()

    assert create_article_id(
        article=article
    ) == create_article_id(
        article=article
    )