import pytest

from app.news_source_environment import (
    load_news_source_config,
)


def test_loads_news_source_config_from_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "NEWS_SOURCE_URL_TEMPLATE",
        "https://example.test/news/{symbol}",
    )
    monkeypatch.setenv(
        "NEWS_SOURCE_TIMEOUT_SECONDS",
        "12.5",
    )
    monkeypatch.setenv(
        "NEWS_SOURCE_USER_AGENT",
        "trading-bot/2.0",
    )

    config = load_news_source_config()

    assert config.url_template == (
        "https://example.test/news/{symbol}"
    )
    assert config.timeout_seconds == 12.5
    assert config.user_agent == (
        "trading-bot/2.0"
    )


def test_rejects_missing_url_template(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "NEWS_SOURCE_URL_TEMPLATE",
        raising=False,
    )

    with pytest.raises(
        ValueError,
        match="NEWS_SOURCE_URL_TEMPLATE",
    ):
        load_news_source_config()