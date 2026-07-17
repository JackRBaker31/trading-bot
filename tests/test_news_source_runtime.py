import httpx

from app.news_source_runtime import (
    create_news_article_source_from_environment,
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


def test_creates_article_source_from_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "NEWS_SOURCE_URL_TEMPLATE",
        "https://example.test/news/{symbol}",
    )
    monkeypatch.setenv(
        "NEWS_SOURCE_TIMEOUT_SECONDS",
        "12.0",
    )
    monkeypatch.setenv(
        "NEWS_SOURCE_USER_AGENT",
        "trading-bot-runtime/1.0",
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
            "Apple reported stronger revenue."
        )

    monkeypatch.setattr(
        httpx,
        "get",
        fake_get,
    )

    source = (
        create_news_article_source_from_environment()
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
    assert captured["timeout"] == 12.0
    assert captured["headers"] == {
        "User-Agent": (
            "trading-bot-runtime/1.0"
        ),
    }