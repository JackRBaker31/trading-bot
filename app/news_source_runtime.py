from app.http_news_article_source import (
    HttpNewsArticleSource,
)
from app.news_source_environment import (
    load_news_source_config,
)
from app.news_source_factory import (
    create_http_news_article_source,
)


def create_news_article_source_from_environment(
) -> HttpNewsArticleSource:
    config = load_news_source_config()

    return create_http_news_article_source(
        config=config
    )