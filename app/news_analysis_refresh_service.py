import logging
from typing import Protocol

from app.news_analysis import (
    NewsAnalysis,
)
from app.news_analysis_provider import (
    WritableNewsAnalysisProvider,
)
from app.news_analysis_validator import (
    NewsAnalysisValidator,
)
from app.news_article_source import (
    NewsArticleSource,
)
from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsSentiment,
)
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from app.news_article import (
    NewsArticle,
)
from app.stored_news_analysis import (
    StoredNewsAnalysis,
)

logger = logging.getLogger(__name__)

class NewsAnalyser(Protocol):
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        ...

def _normalise_verified_ticker(
    *,
    analysis: NewsAnalysis,
    article_text: str,
    symbol: str,
) -> NewsAnalysis:
    normalised_symbol = (
        symbol.upper().strip()
    )

    ticker_marker = (
        f"Ticker: {normalised_symbol}"
    )

    if ticker_marker not in article_text:
        return analysis

    return NewsAnalysis(
        impact_term=analysis.impact_term,
        impact_scope=NewsImpactScope.STOCK,
        scope_items=(
            normalised_symbol,
        ),
        highlights=analysis.highlights,
        sentiment=analysis.sentiment,
    )

def _normalise_verified_source_sentiment(
    *,
    analysis: NewsAnalysis,
    article_text: str,
) -> NewsAnalysis:
    normalised_text = article_text.lower()

    bearish_labels = (
        "source sentiment: bearish",
        "source sentiment: somewhat-bearish",
    )

    bullish_labels = (
        "source sentiment: bullish",
        "source sentiment: somewhat-bullish",
    )

    if any(
        label in normalised_text
        for label in bearish_labels
    ):
        sentiment = NewsSentiment.NEGATIVE
    elif any(
        label in normalised_text
        for label in bullish_labels
    ):
        sentiment = NewsSentiment.POSITIVE
    else:
        return analysis

    return NewsAnalysis(
        impact_term=analysis.impact_term,
        impact_scope=analysis.impact_scope,
        scope_items=analysis.scope_items,
        highlights=analysis.highlights,
        sentiment=sentiment,
    )

class NewsAnalysisRefreshService:
    def __init__(
        self,
        *,
        analyser: NewsAnalyser,
        validator: NewsAnalysisValidator,
        provider: WritableNewsAnalysisProvider,
        article_source: (
            NewsArticleSource | None
        ) = None,
        now_provider: (
            Callable[[], datetime] | None
        ) = None,
        analysis_ttl_seconds: float = 1_800,
    ) -> None:
        if analysis_ttl_seconds <= 0:
            raise ValueError(
                "Analysis TTL must be greater than zero."
            )

        self._analyser = analyser
        self._validator = validator
        self._provider = provider
        self._article_source = article_source
        self._now_provider = (
            now_provider
            if now_provider is not None
            else lambda: datetime.now(
                timezone.utc
            )
        )
        self._analysis_ttl = timedelta(
            seconds=analysis_ttl_seconds
        )

    def refresh_article(
        self,
        *,
        article: NewsArticle,
        model_name: str,
        prompt_version: str,
    ) -> NewsAnalysis:
        analysis = self._analyser.analyse(
            article.article_text
        )

        analysis = _normalise_verified_ticker(
            analysis=analysis,
            article_text=article.article_text,
            symbol=article.symbol,
        )

        analysis = _normalise_verified_source_sentiment(
            analysis=analysis,
            article_text=article.article_text,
        )

        validation = self._validator.validate(
            article_text=article.article_text,
            analysis=analysis,
            allowed_symbols={
                article.symbol.upper().strip(),
            },
        )

        if not validation.approved:
            raise ValueError(
                "News analysis failed validation: "
                + "; ".join(
                    validation.reasons
                )
            )

        analysed_at = self._now_provider()

        stored = StoredNewsAnalysis(
            analysis=analysis,
            analysed_at=analysed_at,
            expires_at=(
                analysed_at
                + self._analysis_ttl
            ),
            article_title=article.title,
            article_url=article.url,
            published_at=article.published_at,
            relevance_score=(
                article.relevance_score
            ),
            source_sentiment_label=(
                article.source_sentiment_label
            ),
            source_sentiment_score=(
                article.source_sentiment_score
            ),
            model_name=model_name,
            prompt_version=prompt_version,
        )

        set_stored_analysis = getattr(
            self._provider,
            "set_stored_analysis",
            None,
        )

        if set_stored_analysis is None:
            self._provider.set_analysis(
                symbol=article.symbol,
                analysis=analysis,
            )
        else:
            set_stored_analysis(
                symbol=article.symbol,
                stored_analysis=stored,
            )

        return analysis

    def refresh(
        self,
        *,
        symbol: str,
        article_text: str,
    ) -> NewsAnalysis:
        normalised_symbol = (
            symbol.upper().strip()
        )

        analysis = self._analyser.analyse(
            article_text
        )

        analysis = _normalise_verified_ticker(
            analysis=analysis,
            article_text=article_text,
            symbol=normalised_symbol,
        )

        analysis = (
            _normalise_verified_source_sentiment(
                analysis=analysis,
                article_text=article_text,
            )
        )

        validation = self._validator.validate(
            article_text=article_text,
            analysis=analysis,
            allowed_symbols={
                normalised_symbol,
            },
        )

        if not validation.approved:
            raise ValueError(
                "News analysis failed validation: "
                + "; ".join(
                    validation.reasons
                )
            )

        self._provider.set_analysis(
            symbol=normalised_symbol,
            analysis=analysis,
        )

        return analysis

    def refresh_symbol(
        self,
        *,
        symbol: str,
        model_name: str = "unknown",
        prompt_version: str = "unknown",
    ) -> NewsAnalysis:
        if self._article_source is None:
            raise RuntimeError(
                "No news article source was supplied."
            )

        normalised_symbol = (
            symbol.upper().strip()
        )

        get_structured_article = getattr(
            self._article_source,
            "get_latest_news_article",
            None,
        )

        if get_structured_article is not None:
            article = get_structured_article(
                normalised_symbol
            )

            if article is None:
                raise ValueError(
                    "No news article was found for "
                    f"{normalised_symbol}."
                )

            return self.refresh_article(
                article=article,
                model_name=model_name,
                prompt_version=prompt_version,
            )

        article_text = (
            self._article_source
            .get_latest_article(
                normalised_symbol
            )
        )

        if article_text is None:
            raise ValueError(
                "No news article was found for "
                f"{normalised_symbol}."
            )

        return self.refresh(
            symbol=normalised_symbol,
            article_text=article_text,
        )
        
    def refresh_symbols(
        self,
        *,
        symbols: list[str],
        model_name: str = "unknown",
        prompt_version: str = "unknown",
    ) -> dict[str, NewsAnalysis | None]:
        results: dict[
            str,
            NewsAnalysis | None,
        ] = {}

        for symbol in symbols:
            normalised_symbol = (
                symbol.upper().strip()
            )

            try:
                results[
                    normalised_symbol
                ] = self.refresh_symbol(
                    symbol=normalised_symbol,
                    model_name=model_name,
                    prompt_version=prompt_version,
                )
            except (
                RuntimeError,
                ValueError,
            ) as error:
                logger.warning(
                    "news_analysis_refresh_failed "
                    "symbol=%s error=%s",
                    normalised_symbol,
                    error,
                )

                results[
                    normalised_symbol
                ] = None

        return results