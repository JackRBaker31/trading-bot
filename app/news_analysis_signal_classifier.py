from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.news_analysis import (
    NewsImpactScope,
    NewsSentiment,
)
from app.news_analysis_service import (
    NewsAnalysisService,
)
from app.news_confidence import (
    NewsConfidenceEngine,
)
from app.news_confidence_models import (
    NewsConfidenceFactor,
)
from app.news_signal import NewsSignal
from app.news_signal_classifier import (
    NewsArticleInput,
)


_SENTIMENT_SCORES = {
    NewsSentiment.POSITIVE: 1.0,
    NewsSentiment.NEUTRAL: 0.0,
    NewsSentiment.NEGATIVE: -1.0,
}


@dataclass(frozen=True)
class NewsAnalysisSignalClassifier:
    analyser: NewsAnalysisService
    expiry_hours: int = 24
    confidence: float | None = None
    confidence_engine: (
        NewsConfidenceEngine
    ) = field(
        default_factory=(
            NewsConfidenceEngine
        )
    )
    now_provider: Callable[
        [],
        datetime,
    ] = field(
        default=(
            lambda: datetime.now(
                timezone.utc
            )
        ),
        compare=False,
        repr=False,
    )

    def __post_init__(
        self,
    ) -> None:
        if self.expiry_hours <= 0:
            raise ValueError(
                "Expiry hours must be "
                "positive."
            )

        if (
            self.confidence is not None
            and not (
                0.0
                <= self.confidence
                <= 1.0
            )
        ):
            raise ValueError(
                "Confidence must be "
                "between 0.0 and 1.0."
            )

    def classify(
        self,
        *,
        article: NewsArticleInput,
    ) -> NewsSignal:
        analysis = (
            self.analyser.analyse(
                article.article_text
            )
        )

        event_type = (
            f"{analysis.impact_scope.value}_"
            f"{analysis.impact_term.value}_"
            f"{analysis.sentiment.value}"
        )

        is_material = (
            analysis.impact_scope
            is NewsImpactScope.STOCK
            and analysis.sentiment
            is not NewsSentiment.NEUTRAL
        )

        reasoning_summary = (
            " | ".join(
                analysis.highlights
            )
            or (
                "AI analysis returned no "
                "factual highlights."
            )
        )

        if (
            self.confidence
            is not None
        ):
            calculated_confidence = (
                self.confidence
            )
            confidence_breakdown = (
                NewsConfidenceFactor(
                    code=(
                        "CONFIGURED_OVERRIDE"
                    ),
                    label=(
                        "Configured override"
                    ),
                    contribution=(
                        self.confidence
                    ),
                    detail=(
                        "A configured "
                        "confidence override "
                        "was used."
                    ),
                ),
            )
        else:
            result = (
                self.confidence_engine
                .calculate(
                    article=article,
                    analysis=analysis,
                    now=(
                        self.now_provider()
                    ),
                )
            )
            calculated_confidence = (
                result.confidence
            )
            confidence_breakdown = (
                result.factors
            )

        return NewsSignal(
            article_id=(
                article.article_id
            ),
            symbol=article.symbol,
            headline=article.headline,
            sentiment=(
                _SENTIMENT_SCORES[
                    analysis.sentiment
                ]
            ),
            relevance=(
                article
                .provider_relevance
            ),
            confidence=(
                calculated_confidence
            ),
            event_type=event_type,
            is_material=is_material,
            published_at=(
                article.published_at
            ),
            expires_at=(
                article.published_at
                + timedelta(
                    hours=(
                        self.expiry_hours
                    )
                )
            ),
            source=article.source,
            reasoning_summary=(
                reasoning_summary
            ),
            confidence_breakdown=(
                confidence_breakdown
            ),
        )
