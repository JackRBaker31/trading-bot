from datetime import datetime, timedelta, timezone

from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.news_confidence import NewsConfidenceEngine
from app.news_signal_classifier import NewsArticleInput

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)


def make_article(*, relevance: float, age_hours: float, provider_score: float | None) -> NewsArticleInput:
    return NewsArticleInput(
        article_id="article-1",
        symbol="AAPL",
        headline="Apple raises full-year revenue guidance after earnings beat",
        summary=(
            "Management increased its outlook after reporting stronger "
            "revenue and margin performance across key product lines."
        ),
        source="alpha_vantage",
        published_at=NOW - timedelta(hours=age_hours),
        provider_relevance=relevance,
        provider_sentiment_label="Bullish" if provider_score is not None else None,
        provider_sentiment_score=provider_score,
    )


def make_analysis(*, sentiment: NewsSentiment = NewsSentiment.POSITIVE, scope: NewsImpactScope = NewsImpactScope.STOCK, highlights: tuple[str, ...] = ("Guidance increased.", "Revenue exceeded expectations.")) -> NewsAnalysis:
    return NewsAnalysis(
        impact_term=NewsImpactTerm.LONGTERM,
        impact_scope=scope,
        scope_items=("AAPL",),
        highlights=highlights,
        sentiment=sentiment,
    )


def test_strong_confirmed_evidence_scores_highly() -> None:
    result = NewsConfidenceEngine().calculate(
        article=make_article(relevance=0.95, age_hours=1, provider_score=0.75),
        analysis=make_analysis(),
        now=NOW,
    )
    assert 0.90 < result.confidence <= 0.98
    assert any(f.code == "SENTIMENT_CONFIRMATION" and f.contribution > 0 for f in result.factors)


def test_weak_generic_evidence_scores_lower() -> None:
    result = NewsConfidenceEngine().calculate(
        article=make_article(relevance=0.52, age_hours=80, provider_score=None),
        analysis=make_analysis(sentiment=NewsSentiment.NEUTRAL, scope=NewsImpactScope.GLOBAL, highlights=()),
        now=NOW,
    )
    assert 0.35 <= result.confidence < 0.70


def test_sentiment_disagreement_reduces_confidence() -> None:
    agreeing = NewsConfidenceEngine().calculate(
        article=make_article(relevance=0.85, age_hours=2, provider_score=0.7),
        analysis=make_analysis(), now=NOW,
    )
    disagreeing = NewsConfidenceEngine().calculate(
        article=make_article(relevance=0.85, age_hours=2, provider_score=-0.7),
        analysis=make_analysis(), now=NOW,
    )
    assert disagreeing.confidence < agreeing.confidence
