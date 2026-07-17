from typing import Protocol


class HttpFetcher(Protocol):
    def fetch(
        self,
        url: str,
    ) -> str:
        ...


class HttpNewsArticleSource:
    def __init__(
        self,
        *,
        url_template: str,
        fetcher: HttpFetcher,
    ) -> None:
        self._url_template = url_template
        self._fetcher = fetcher

    def get_latest_article(
        self,
        symbol: str,
    ) -> str | None:
        normalised_symbol = (
            symbol.upper().strip()
        )

        url = self._url_template.format(
            symbol=normalised_symbol
        )

        response = self._fetcher.fetch(
            url
        )

        article_text = response.strip()

        if not article_text:
            return None

        return article_text