import os

from app.news_source_config import (
    NewsSourceConfig,
)


def load_news_source_config() -> NewsSourceConfig:
    url_template = os.getenv(
        "NEWS_SOURCE_URL_TEMPLATE",
        "",
    ).strip()

    if not url_template:
        raise ValueError(
            "NEWS_SOURCE_URL_TEMPLATE "
            "is required."
        )

    timeout_text = os.getenv(
        "NEWS_SOURCE_TIMEOUT_SECONDS",
        "15.0",
    ).strip()

    user_agent = os.getenv(
        "NEWS_SOURCE_USER_AGENT",
        "trading-bot/1.0",
    ).strip()

    try:
        timeout_seconds = float(
            timeout_text
        )
    except ValueError as error:
        raise ValueError(
            "NEWS_SOURCE_TIMEOUT_SECONDS "
            "must be a number."
        ) from error

    return NewsSourceConfig(
        url_template=url_template,
        timeout_seconds=timeout_seconds,
        user_agent=user_agent,
    )