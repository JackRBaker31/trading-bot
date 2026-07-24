from datetime import datetime, timezone

from app.news_analysis import NewsAnalysis, NewsImpactScope, NewsImpactTerm, NewsSentiment
from app.news_analysis_signal_classifier import NewsAnalysisSignalClassifier
from app.news_signal_classifier import NewsArticleInput

NOW = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)


class FakeAnalyser:
    def analyse(self, article_text: str) -> NewsAnalysis:
        assert "Apple raises guidance" in article_text
        return NewsAnalysis(
            impact_term=NewsImpactTerm.LONGTERM,
            impact_scope=NewsImpactScope.STOCK,
            scope_items=("AAPL",),
            highlights=("Guidance was raised.",),
            sentiment=NewsSentiment.POSITIVE,
        )


def make_article() -> NewsArticleInput:
    return NewsArticleInput(
        article_id="article-1", symbol="AAPL",
        headline="Apple raises guidance",
        summary="Full-year outlook increased with stronger revenue.",
        source="alpha_vantage", published_at=NOW,
        provider_relevance=0.92,
        provider_sentiment_label="Bullish",
        provider_sentiment_score=0.65,
    )


def test_calculates_explainable_confidence() -> None:
    signal = NewsAnalysisSignalClassifier(
        analyser=FakeAnalyser(), expiry_hours=12,
        now_provider=lambda: NOW,
    ).classify(article=make_article())
    assert signal.sentiment == 1.0
    assert signal.relevance == 0.92
    assert signal.confidence != 0.80
    assert signal.confidence > 0.85
    assert signal.is_material is True
    assert signal.event_type == "STOCK_LONGTERM_POSITIVE"
    assert signal.reasoning_summary == "Guidance was raised."
    assert len(signal.confidence_breakdown) >= 8


def test_explicit_confidence_override_remains_supported() -> None:
    signal = NewsAnalysisSignalClassifier(
        analyser=FakeAnalyser(), expiry_hours=12,
        confidence=0.85, now_provider=lambda: NOW,
    ).classify(article=make_article())
    assert signal.confidence == 0.85
    assert signal.confidence_breakdown[0].code == "CONFIGURED_OVERRIDE"
