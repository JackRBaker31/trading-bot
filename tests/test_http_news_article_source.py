from app.http_news_article_source import (
    HttpNewsArticleSource,
)


class FakeFetcher:
    def __init__(
        self,
        responses: dict[str, str],
    ) -> None:
        self.responses = responses
        self.urls: list[str] = []

    def fetch(
        self,
        url: str,
    ) -> str:
        self.urls.append(url)

        return self.responses[url]


def test_fetches_latest_article_for_symbol() -> None:
    fetcher = FakeFetcher(
        responses={
            (
                "https://example.test/news/AAPL"
            ): (
                "Apple reported stronger revenue."
            ),
        }
    )

    source = HttpNewsArticleSource(
        url_template=(
            "https://example.test/news/{symbol}"
        ),
        fetcher=fetcher,
    )

    result = source.get_latest_article(
        " aapl "
    )

    assert result == (
        "Apple reported stronger revenue."
    )
    assert fetcher.urls == [
        "https://example.test/news/AAPL",
    ]


def test_returns_none_for_empty_response() -> None:
    fetcher = FakeFetcher(
        responses={
            (
                "https://example.test/news/MSFT"
            ): "   ",
        }
    )

    source = HttpNewsArticleSource(
        url_template=(
            "https://example.test/news/{symbol}"
        ),
        fetcher=fetcher,
    )

    assert (
        source.get_latest_article("MSFT")
        is None
    )