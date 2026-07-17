import json
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Protocol
from urllib.parse import urlencode
from app.news_article import (
    NewsArticle,
)


class HttpFetcher(Protocol):
    def fetch(
        self,
        url: str,
    ) -> str:
        ...


class AlphaVantageNewsArticleSource:
    def __init__(
        self,
        *,
        api_key: str,
        fetcher: HttpFetcher,
        minimum_relevance_score: float = 0.5,
        maximum_age_seconds: float | None = None,
        now_provider: (
            Callable[[], datetime] | None
        ) = None,
    ) -> None:
        normalised_api_key = api_key.strip()

        if not normalised_api_key:
            raise ValueError(
                "Alpha Vantage API key is required."
            )

        if not 0 <= minimum_relevance_score <= 1:
            raise ValueError(
                "Minimum relevance score must be "
                "between zero and one."
            )

        if (
            maximum_age_seconds is not None
            and maximum_age_seconds <= 0
        ):
            raise ValueError(
                "Maximum article age must be "
                "greater than zero."
            )

        self._api_key = normalised_api_key
        self._fetcher = fetcher
        self._minimum_relevance_score = (
            minimum_relevance_score
        )
        self._maximum_age_seconds = (
            maximum_age_seconds
        )
        self._now_provider = (
            now_provider
            if now_provider is not None
            else lambda: datetime.now(
                timezone.utc
            )
        )

    def get_latest_article(
        self,
        symbol: str,
    ) -> str | None:
        article = self.get_latest_news_article(
            symbol
        )

        if article is None:
            return None

        return article.article_text

    def get_latest_news_article(
        self,
        symbol: str,
    ) -> NewsArticle | None:
        normalised_symbol = (
            symbol.upper().strip()
        )

        if not normalised_symbol:
            return None

        query = urlencode(
            {
                "function": "NEWS_SENTIMENT",
                "tickers": normalised_symbol,
                "limit": 50,
                "apikey": self._api_key,
            }
        )

        url = (
            "https://www.alphavantage.co/query"
            f"?{query}"
        )

        response_text = self._fetcher.fetch(
            url
        )

        try:
            payload = json.loads(
                response_text
            )
        except json.JSONDecodeError as error:
            raise ValueError(
                "Alpha Vantage returned invalid JSON."
            ) from error

        if not isinstance(payload, dict):
            raise ValueError(
                "Alpha Vantage response must be "
                "a JSON object."
            )

        feed = payload.get(
            "feed",
            [],
        )

        if not isinstance(feed, list):
            return None

        matching_articles: list[
            tuple[
                float,
                dict[str, object],
                dict[str, object],
            ]
        ] = []

        for article in feed:
            if not isinstance(
                article,
                dict,
            ):
                continue

            if self._maximum_age_seconds is not None:
                time_published = str(
                    article.get(
                        "time_published",
                        "",
                    )
                ).strip()

                try:
                    published_at = datetime.strptime(
                        time_published,
                        "%Y%m%dT%H%M%S",
                    ).replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    continue

                article_age_seconds = (
                    self._now_provider()
                    - published_at
                ).total_seconds()

                if (
                    article_age_seconds < 0
                    or article_age_seconds
                    > self._maximum_age_seconds
                ):
                    continue

            ticker_sentiment = article.get(
                "ticker_sentiment",
                [],
            )

            if not isinstance(
                ticker_sentiment,
                list,
            ):
                continue

            for item in ticker_sentiment:
                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                ticker = str(
                    item.get(
                        "ticker",
                        "",
                    )
                ).upper().strip()

                if ticker != normalised_symbol:
                    continue

                try:
                    relevance_score = float(
                        item.get(
                            "relevance_score",
                            0,
                        )
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    relevance_score = 0.0

                matching_articles.append(
                    (
                        relevance_score,
                        article,
                        item,
                    )
                )

                break

        if not matching_articles:
            return None

        (
            relevance_score,
            latest_article,
            ticker_metadata,
        ) = max(
            matching_articles,
            key=lambda candidate: candidate[0],
        )

        if (
            relevance_score
            < self._minimum_relevance_score
        ):
            return None

        title = str(
            latest_article.get(
                "title",
                "",
            )
        ).strip()

        summary = str(
            latest_article.get(
                "summary",
                "",
            )
        ).strip()

        if not title:
            return None

        time_published = str(
            latest_article.get(
                "time_published",
                "",
            )
        ).strip()

        try:
            published_at = datetime.strptime(
                time_published,
                "%Y%m%dT%H%M%S",
            ).replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return None

        article_url = str(
            latest_article.get(
                "url",
                "",
            )
        ).strip() or None

        source_sentiment_label = str(
            ticker_metadata.get(
                "ticker_sentiment_label",
                "",
            )
        ).strip() or None

        source_sentiment_score = None

        raw_sentiment_score = (
            ticker_metadata.get(
                "ticker_sentiment_score"
            )
        )

        if raw_sentiment_score is not None:
            try:
                source_sentiment_score = float(
                    raw_sentiment_score
                )
            except (
                TypeError,
                ValueError,
            ):
                source_sentiment_score = None

        return NewsArticle(
            symbol=normalised_symbol,
            title=title,
            summary=summary,
            published_at=published_at,
            source="alpha_vantage",
            url=article_url,
            relevance_score=relevance_score,
            source_sentiment_label=(
                source_sentiment_label
            ),
            source_sentiment_score=(
                source_sentiment_score
            ),
        )