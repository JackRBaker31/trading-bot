from app.http_news_article_source import (
    HttpNewsArticleSource,
)
from app.httpx_news_fetcher import (
    HttpxNewsFetcher,
)
from app.news_source_config import (
    NewsSourceConfig,
)


def create_http_news_article_source(
    *,
    config: NewsSourceConfig,
) -> HttpNewsArticleSource:
    fetcher = HttpxNewsFetcher(
        timeout_seconds=(
            config.timeout_seconds
        ),
        user_agent=config.user_agent,
    )

    return HttpNewsArticleSource(
        url_template=config.url_template,
        fetcher=fetcher,
    )