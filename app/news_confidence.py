from datetime import datetime, timezone

from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsSentiment,
)
from app.news_signal_classifier import (
    NewsArticleInput,
)


from app.news_confidence_models import (
    NewsConfidenceFactor,
    NewsConfidenceResult,
)


class NewsConfidenceEngine:
    def calculate(
        self,
        *,
        article: NewsArticleInput,
        analysis: NewsAnalysis,
        now: datetime | None = None,
    ) -> NewsConfidenceResult:
        current_time = (
            now
            or datetime.now(
                timezone.utc
            )
        )

        if current_time.tzinfo is None:
            raise ValueError(
                "Confidence clock must be "
                "timezone-aware."
            )

        factors: list[
            NewsConfidenceFactor
        ] = []

        self._add(
            factors,
            code="BASE",
            label="Base evidence",
            contribution=0.35,
            detail=(
                "Valid structured analysis "
                "was returned."
            ),
        )

        self._add(
            factors,
            code="PROVIDER_RELEVANCE",
            label="Provider relevance",
            contribution=(
                article.provider_relevance
                * 0.20
            ),
            detail=(
                "Provider relevance was "
                f"{article.provider_relevance * 100:.1f}%."
            ),
        )

        scope_contribution = {
            NewsImpactScope.STOCK: 0.10,
            NewsImpactScope.INDUSTRY: 0.06,
            NewsImpactScope.GLOBAL: 0.03,
        }[
            analysis.impact_scope
        ]

        self._add(
            factors,
            code="IMPACT_SCOPE",
            label="Impact specificity",
            contribution=(
                scope_contribution
            ),
            detail=(
                "Analysis scope was "
                f"{analysis.impact_scope.value}."
            ),
        )

        symbol = (
            article.symbol
            .upper()
            .strip()
        )

        symbol_confirmed = (
            symbol
            in {
                item.upper().strip()
                for item
                in analysis.scope_items
            }
        )

        self._add(
            factors,
            code="SYMBOL_CONFIRMATION",
            label="Symbol confirmation",
            contribution=(
                0.05
                if symbol_confirmed
                else 0.0
            ),
            detail=(
                "The analysed scope "
                f"explicitly included {symbol}."
                if symbol_confirmed
                else (
                    "The analysed scope did "
                    f"not explicitly include "
                    f"{symbol}."
                )
            ),
        )

        material = (
            analysis.impact_scope
            is NewsImpactScope.STOCK
            and analysis.sentiment
            is not NewsSentiment.NEUTRAL
        )

        self._add(
            factors,
            code="MATERIALITY",
            label="Materiality",
            contribution=(
                0.08
                if material
                else 0.0
            ),
            detail=(
                "Stock-specific directional "
                "news was detected."
                if material
                else (
                    "No stock-specific "
                    "directional event was "
                    "detected."
                )
            ),
        )

        highlight_count = min(
            len(
                analysis.highlights
            ),
            3,
        )

        self._add(
            factors,
            code="FACTUAL_HIGHLIGHTS",
            label="Factual highlights",
            contribution=(
                highlight_count
                * 0.025
            ),
            detail=(
                f"{len(analysis.highlights)} "
                "factual highlight(s) were "
                "extracted."
            ),
        )

        content_quality = (
            self._content_quality(
                article=article
            )
        )

        self._add(
            factors,
            code="CONTENT_QUALITY",
            label="Article detail",
            contribution=(
                content_quality
            ),
            detail=(
                "Headline and summary "
                "supplied sufficient detail."
                if content_quality > 0
                else (
                    "Article text supplied "
                    "limited detail."
                )
            ),
        )

        freshness = (
            self._freshness(
                published_at=(
                    article.published_at
                ),
                now=current_time,
            )
        )

        self._add(
            factors,
            code="FRESHNESS",
            label="Freshness",
            contribution=freshness,
            detail=(
                self._freshness_detail(
                    published_at=(
                        article.published_at
                    ),
                    now=current_time,
                )
            ),
        )

        factors.append(
            self._provider_sentiment_factor(
                article=article,
                analysis=analysis,
            )
        )

        raw_score = sum(
            factor.contribution
            for factor in factors
        )

        confidence = round(
            max(
                0.35,
                min(
                    raw_score,
                    0.98,
                ),
            ),
            4,
        )

        return NewsConfidenceResult(
            confidence=confidence,
            factors=tuple(
                factors
            ),
        )

    @staticmethod
    def _add(
        factors: list[
            NewsConfidenceFactor
        ],
        *,
        code: str,
        label: str,
        contribution: float,
        detail: str,
    ) -> None:
        factors.append(
            NewsConfidenceFactor(
                code=code,
                label=label,
                contribution=round(
                    contribution,
                    4,
                ),
                detail=detail,
            )
        )

    @staticmethod
    def _content_quality(
        *,
        article: NewsArticleInput,
    ) -> float:
        combined_length = (
            len(
                article.headline.strip()
            )
            + len(
                article.summary.strip()
            )
        )

        if combined_length >= 240:
            return 0.04

        if combined_length >= 120:
            return 0.03

        if combined_length >= 60:
            return 0.015

        return 0.0

    @staticmethod
    def _freshness(
        *,
        published_at: datetime,
        now: datetime,
    ) -> float:
        age_hours = max(
            0.0,
            (
                now
                - published_at
                .astimezone(
                    timezone.utc
                )
            ).total_seconds()
            / 3600,
        )

        if age_hours <= 2:
            return 0.06

        if age_hours <= 6:
            return 0.05

        if age_hours <= 24:
            return 0.035

        if age_hours <= 72:
            return 0.015

        return 0.0

    @staticmethod
    def _freshness_detail(
        *,
        published_at: datetime,
        now: datetime,
    ) -> str:
        age_hours = max(
            0.0,
            (
                now
                - published_at
                .astimezone(
                    timezone.utc
                )
            ).total_seconds()
            / 3600,
        )

        return (
            "Article age was "
            f"approximately "
            f"{age_hours:.1f} hour(s)."
        )

    @staticmethod
    def _provider_sentiment_factor(
        *,
        article: NewsArticleInput,
        analysis: NewsAnalysis,
    ) -> NewsConfidenceFactor:
        score = (
            article
            .provider_sentiment_score
        )

        if score is None:
            return NewsConfidenceFactor(
                code=(
                    "SENTIMENT_CONFIRMATION"
                ),
                label=(
                    "Provider sentiment "
                    "confirmation"
                ),
                contribution=0.0,
                detail=(
                    "The provider supplied "
                    "no ticker-level "
                    "sentiment score."
                ),
            )

        analysed_direction = {
            NewsSentiment.POSITIVE: 1,
            NewsSentiment.NEUTRAL: 0,
            NewsSentiment.NEGATIVE: -1,
        }[
            analysis.sentiment
        ]

        provider_direction = (
            1
            if score > 0.05
            else -1
            if score < -0.05
            else 0
        )

        if (
            provider_direction
            == analysed_direction
        ):
            contribution = min(
                abs(score) * 0.10,
                0.10,
            )
            detail = (
                "Provider and KAIRO "
                "sentiment agreed "
                f"(provider score "
                f"{score:.3f})."
            )
        else:
            contribution = -min(
                0.08,
                max(
                    abs(score) * 0.08,
                    0.03,
                ),
            )
            detail = (
                "Provider and KAIRO "
                "sentiment disagreed "
                f"(provider score "
                f"{score:.3f})."
            )

        return NewsConfidenceFactor(
            code=(
                "SENTIMENT_CONFIRMATION"
            ),
            label=(
                "Provider sentiment "
                "confirmation"
            ),
            contribution=round(
                contribution,
                4,
            ),
            detail=detail,
        )
