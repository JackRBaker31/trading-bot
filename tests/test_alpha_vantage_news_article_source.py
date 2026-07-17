import json
from datetime import datetime, timezone
from app.alpha_vantage_news_article_source import (
    AlphaVantageNewsArticleSource,
)
from datetime import (
    datetime,
    timezone,
)

from app.news_article import (
    NewsArticle,
)


class FakeFetcher:
    def __init__(
        self,
        response: str,
    ) -> None:
        self.response = response
        self.urls: list[str] = []

    def fetch(
        self,
        url: str,
    ) -> str:
        self.urls.append(url)

        return self.response


def test_returns_latest_article_title_and_summary() -> None:
    response = json.dumps(
        {
            "feed": [
                {
                    "title": (
                        "Apple reports stronger revenue"
                    ),
                    "summary": (
                        "Apple reported stronger "
                        "quarterly revenue and raised "
                        "its guidance."
                    ),
                    "time_published": "20260717T093000",
                    "ticker_sentiment": [
                        {
                            "ticker": "AAPL",
                            "relevance_score": "0.90",
                        },
                    ],
                },
                {
                    "title": (
                        "Older Apple article"
                    ),
                    "summary": (
                        "This article should not "
                        "be selected."
                    ),
                    "time_published": "20260717T093000",
                    "ticker_sentiment": [
                        {
                            "ticker": "AAPL",
                            "relevance_score": "0.80",
                        },
                    ],
                },
            ]
        }
    )

    fetcher = FakeFetcher(
        response=response
    )

    source = AlphaVantageNewsArticleSource(
        api_key="test-key",
        fetcher=fetcher,
    )

    result = source.get_latest_article(
        " aapl "
    )

    assert result == (
        "Ticker: AAPL\n\n"
        "Apple reports stronger revenue\n\n"
        "Apple reported stronger quarterly "
        "revenue and raised its guidance."
    )

    assert fetcher.urls == [
        (
            "https://www.alphavantage.co/query"
            "?function=NEWS_SENTIMENT"
            "&tickers=AAPL"
            "&limit=50"
            "&apikey=test-key"
        ),
    ]


def test_returns_none_when_feed_is_empty() -> None:
    fetcher = FakeFetcher(
        response=json.dumps(
            {
                "feed": [],
            }
        )
    )

    source = AlphaVantageNewsArticleSource(
        api_key="test-key",
        fetcher=fetcher,
    )

    assert (
        source.get_latest_article("MSFT")
        is None
    )


def test_skips_article_that_does_not_match_symbol() -> None:
    response = json.dumps(
        {
            "feed": [
                {
                    "title": (
                        "Micron reports stronger demand"
                    ),
                    "summary": (
                        "Micron Technology discussed "
                        "memory-chip demand."
                    ),
                    "time_published": "20260717T093000",
                    "ticker_sentiment": [
                        {
                            "ticker": "MU",
                            "relevance_score": "0.95",
                        },
                    ],
                },
                {
                    "title": (
                        "Apple reports stronger revenue"
                    ),
                    "summary": (
                        "Apple raised its guidance."
                    ),
                    "time_published": "20260717T093000",
                    "ticker_sentiment": [
                        {
                            "ticker": "AAPL",
                            "relevance_score": "0.90",
                        },
                    ],
                },
            ],
        }
    )

    source = AlphaVantageNewsArticleSource(
        api_key="test-key",
        fetcher=FakeFetcher(
            response=response
        ),
    )

    result = source.get_latest_article(
        "AAPL"
    )

    assert result == (
        "Ticker: AAPL\n\n"
        "Apple reports stronger revenue\n\n"
        "Apple raised its guidance."
    )


def test_selects_most_relevant_article_for_symbol() -> None:
    response = json.dumps(
        {
            "feed": [
                {
                    "title": (
                        "Micron reports stronger demand"
                    ),
                    "summary": (
                        "Micron Technology discussed "
                        "memory-chip demand."
                    ),
                    "time_published": "20260717T093000",
                    "ticker_sentiment": [
                        {
                            "ticker": "AAPL",
                            "relevance_score": "0.08",
                        },
                        {
                            "ticker": "MU",
                            "relevance_score": "0.95",
                        },
                    ],
                },
                {
                    "title": (
                        "Apple reports stronger revenue"
                    ),
                    "summary": (
                        "Apple raised its guidance."
                    ),
                    "time_published": "20260717T093000",
                    "ticker_sentiment": [
                        {
                            "ticker": "AAPL",
                            "relevance_score": "0.92",
                        },
                    ],
                },
            ],
        }
    )

    source = AlphaVantageNewsArticleSource(
        api_key="test-key",
        fetcher=FakeFetcher(
            response=response
        ),
    )

    result = source.get_latest_article(
        "AAPL"
    )

    assert result == (
        "Ticker: AAPL\n\n"
        "Apple reports stronger revenue\n\n"
        "Apple raised its guidance."
    )
    
def test_includes_ticker_sentiment_metadata() -> None:
    response = json.dumps(
        {
            "feed": [
                {
                    "title": (
                        "Apple lawsuit faces complication"
                    ),
                    "summary": (
                        "A legal error could complicate "
                        "Apple's initial case."
                    ),
                    "time_published": "20260717T093000",
                    "ticker_sentiment": [
                        {
                            "ticker": "AAPL",
                            "relevance_score": "0.92",
                            "ticker_sentiment_score": "-0.35",
                            "ticker_sentiment_label": (
                                "Somewhat-Bearish"
                            ),
                        },
                    ],
                },
            ],
        }
    )

    source = AlphaVantageNewsArticleSource(
        api_key="test-key",
        fetcher=FakeFetcher(
            response=response
        ),
    )

    result = source.get_latest_article(
        "AAPL"
    )

    assert result == (
        "Ticker: AAPL\n\n"
        "Source sentiment: Somewhat-Bearish "
        "(-0.35)\n\n"
        "Apple lawsuit faces complication\n\n"
        "A legal error could complicate "
        "Apple's initial case."
    )
    
def test_ignores_article_older_than_maximum_age() -> None:
    response = json.dumps(
        {
            "feed": [
                {
                    "title": "Old Apple article",
                    "summary": (
                        "This article should be rejected "
                        "because it is stale."
                    ),
                    "time_published": "20260715T090000",
                    "ticker_sentiment": [
                        {
                            "ticker": "AAPL",
                            "relevance_score": "0.95",
                        },
                    ],
                },
            ],
        }
    )

    source = AlphaVantageNewsArticleSource(
        api_key="test-key",
        fetcher=FakeFetcher(
            response=response
        ),
        maximum_age_seconds=3_600,
        now_provider=lambda: datetime(
            2026,
            7,
            17,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert (
        source.get_latest_article("AAPL")
        is None
    )
    
def test_returns_structured_news_article() -> None:
    response = json.dumps(
        {
            "feed": [
                {
                    "title": (
                        "Apple lawsuit faces complication"
                    ),
                    "summary": (
                        "A legal error could complicate "
                        "Apple's initial case."
                    ),
                    "url": (
                        "https://example.test/apple"
                    ),
                    "time_published": (
                        "20260717T093000"
                    ),
                    "ticker_sentiment": [
                        {
                            "ticker": "AAPL",
                            "relevance_score": "0.92",
                            "ticker_sentiment_score": (
                                "-0.35"
                            ),
                            "ticker_sentiment_label": (
                                "Somewhat-Bearish"
                            ),
                        },
                    ],
                },
            ],
        }
    )

    source = AlphaVantageNewsArticleSource(
        api_key="test-key",
        fetcher=FakeFetcher(
            response=response
        ),
    )

    article = source.get_latest_news_article(
        "AAPL"
    )

    assert article == NewsArticle(
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

    assert (
        source.get_latest_article("AAPL")
        == article.article_text
    )