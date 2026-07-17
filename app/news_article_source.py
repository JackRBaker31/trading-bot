from typing import Protocol


class NewsArticleSource(Protocol):
    def get_latest_article(
        self,
        symbol: str,
    ) -> str | None:
        ...


class InMemoryNewsArticleSource:
    def __init__(
        self,
        *,
        articles: dict[str, str],
    ) -> None:
        self._articles = {
            symbol.upper().strip(): article
            for symbol, article in articles.items()
        }

    def get_latest_article(
        self,
        symbol: str,
    ) -> str | None:
        normalised_symbol = (
            symbol.upper().strip()
        )

        return self._articles.get(
            normalised_symbol
        )