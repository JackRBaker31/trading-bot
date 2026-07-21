from datetime import (
    datetime,
    timezone,
)

from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.news_analysis_signal_classifier import (
    NewsAnalysisSignalClassifier,
)
from app.news_signal_classifier import (
    NewsArticleInput,
)


class FakeAnalyser:
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        assert "Apple raises guidance" in article_text

        return NewsAnalysis(
            impact_term=(
                NewsImpactTerm.LONGTERM
            ),
            impact_scope=(
                NewsImpactScope.STOCK
            ),
            scope_items=("AAPL",),
            highlights=(
                "Guidance was raised.",
            ),
            sentiment=(
                NewsSentiment.POSITIVE
            ),
        )


def test_maps_existing_analysis_to_signal() -> None:
    article = NewsArticleInput(
        article_id="article-1",
        symbol="AAPL",
        headline="Apple raises guidance",
        summary="Full-year outlook increased.",
        source="alpha_vantage",
        published_at=datetime(
            2026,
            7,
            18,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        provider_relevance=0.92,
    )

    signal = NewsAnalysisSignalClassifier(
        analyser=FakeAnalyser(),
        expiry_hours=12,
        confidence=0.85,
    ).classify(
        article=article
    )

    assert signal.sentiment == 1.0
    assert signal.relevance == 0.92
    assert signal.confidence == 0.85
    assert signal.is_material is True
    assert signal.event_type == (
        "STOCK_LONGTERM_POSITIVE"
    )
    assert signal.reasoning_summary == (
        "Guidance was raised."
    )