import httpx

from app.news_source_config import (
    NewsSourceConfig,
)
from app.news_source_factory import (
    create_http_news_article_source,
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


def test_builds_configured_http_article_source(
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

    config = NewsSourceConfig(
        url_template=(
            "https://example.test/news/{symbol}"
        ),
        timeout_seconds=12.0,
        user_agent="trading-bot-test/1.0",
    )

    source = create_http_news_article_source(
        config=config
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
        "User-Agent": "trading-bot-test/1.0",
    }