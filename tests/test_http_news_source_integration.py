import httpx

from app.http_news_article_source import (
    HttpNewsArticleSource,
)
from app.httpx_news_fetcher import (
    HttpxNewsFetcher,
)


class FakeResponse:
    def __init__(
        self,
        text: str,
    ) -> None:
        self.text = text

    def raise_for_status(
        self,
    ) -> None:
        return None


def test_http_fetcher_and_article_source_work_together(
    monkeypatch,
) -> None:
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
            "Apple reported stronger revenue."
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    source = HttpNewsArticleSource(
        url_template=(
            "https://example.test/news/{symbol}"
        ),
        fetcher=HttpxNewsFetcher(
            timeout_seconds=15.0,
            user_agent="trading-bot/1.0",
        ),
    )

    result = source.get_latest_article(
        " aapl "
    )

    assert result == (
        "Apple reported stronger revenue."
    )
    assert captured["url"] == (
        "https://example.test/news/AAPL"
    )
    assert captured["timeout"] == 15.0
    assert captured["headers"] == {
        "User-Agent": "trading-bot/1.0",
    }