from collections.abc import Callable
from datetime import datetime

from app.alpha_vantage_news_article_source import (
    AlphaVantageNewsArticleSource,
)
from app.alpha_vantage_news_environment import (
    load_alpha_vantage_api_key,
)
from app.httpx_news_fetcher import (
    HttpxNewsFetcher,
)
from app.news_runtime_environment import (
    load_news_maximum_age_seconds,
)


def create_alpha_vantage_news_article_source(
    *,
    now_provider: (
        Callable[[], datetime] | None
    ) = None,
) -> AlphaVantageNewsArticleSource:
    api_key = load_alpha_vantage_api_key()

    maximum_age_seconds = (
        load_news_maximum_age_seconds()
    )

    fetcher = HttpxNewsFetcher(
        timeout_seconds=15.0,
        user_agent="trading-bot/1.0",
    )

    return AlphaVantageNewsArticleSource(
        api_key=api_key,
        fetcher=fetcher,
        maximum_age_seconds=(
            maximum_age_seconds
        ),
        now_provider=now_provider,
    )