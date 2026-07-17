import pytest

from app.news_source_config import (
    NewsSourceConfig,
)


def test_builds_symbol_url() -> None:
    config = NewsSourceConfig(
        url_template=(
            "https://example.test/news/{symbol}"
        ),
        timeout_seconds=15.0,
        user_agent="trading-bot/1.0",
    )

    assert config.build_url(
        " aapl "
    ) == (
        "https://example.test/news/AAPL"
    )


def test_rejects_template_without_symbol_placeholder() -> None:
    with pytest.raises(
        ValueError,
        match="must contain",
    ):
        NewsSourceConfig(
            url_template=(
                "https://example.test/news"
            ),
            timeout_seconds=15.0,
            user_agent="trading-bot/1.0",
        )


def test_rejects_non_positive_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        NewsSourceConfig(
            url_template=(
                "https://example.test/news/{symbol}"
            ),
            timeout_seconds=0,
            user_agent="trading-bot/1.0",
        )