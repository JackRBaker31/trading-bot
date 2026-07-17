import json

import httpx

from app.alpha_vantage_news_runtime import (
    create_alpha_vantage_news_article_source,
)
from datetime import (
    datetime,
    timezone,
)

class FakeResponse:
    def __init__(
        self,
        payload: dict[str, object],
    ) -> None:
        self.text = json.dumps(
            payload
        )

    def raise_for_status(
        self,
    ) -> None:
        return None


def test_creates_alpha_vantage_source_from_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "ALPHA_VANTAGE_API_KEY",
        "test-key",
    )

    captured: dict[str, object] = {}

    def fake_get(
        url,
        timeout,
        headers,
    ):
        captured["url"] = url
        captured["timeout"] = timeout
        captured["headers"] = headers

        return FakeResponse(
            {
                "feed": [
                    {
                        "title": (
                            "Apple reports "
                            "stronger revenue"
                        ),
                        "summary": (
                            "Apple raised "
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
                ],
            }
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    source = (
        create_alpha_vantage_news_article_source(
            now_provider=lambda: datetime(
                2026,
                7,
                17,
                10,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    result = source.get_latest_article(
        " aapl "
    )

    assert result == (
        "Ticker: AAPL\n\n"
        "Apple reports stronger revenue\n\n"
        "Apple raised its guidance."
    )

    assert captured["url"] == (
        "https://www.alphavantage.co/query"
        "?function=NEWS_SENTIMENT"
        "&tickers=AAPL"
        "&limit=50"
        "&apikey=test-key"
    )
    assert captured["timeout"] == 15.0
    assert captured["headers"] == {
        "User-Agent": "trading-bot/1.0",
    }