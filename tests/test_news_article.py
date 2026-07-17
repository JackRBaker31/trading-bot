from datetime import (
    datetime,
    timezone,
)

from app.news_article import (
    NewsArticle,
)


def test_builds_article_text_with_metadata() -> None:
    article = NewsArticle(
        symbol="AAPL",
        title=(
            "Apple lawsuit faces complication"
        ),
        summary=(
            "A legal error could complicate "
            "Apple's initial case."
        ),
        published_at=datetime(
            2026,
            7,
            17,
            9,
            30,
            tzinfo=timezone.utc,
        ),
        source="alpha_vantage",
        url=(
            "https://example.test/apple"
        ),
        relevance_score=0.92,
        source_sentiment_label=(
            "Somewhat-Bearish"
        ),
        source_sentiment_score=-0.35,
    )

    assert article.article_text == (
        "Ticker: AAPL\n\n"
        "Source sentiment: "
        "Somewhat-Bearish (-0.35)\n\n"
        "Apple lawsuit faces complication\n\n"
        "A legal error could complicate "
        "Apple's initial case."
    )