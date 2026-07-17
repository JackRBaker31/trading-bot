import pytest
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
from app.stored_news_analysis import (
    StoredNewsAnalysis,
)


def test_stores_analysis_with_audit_metadata() -> None:
    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("AAPL",),
        highlights=(
            "Apple reported stronger revenue",
        ),
        sentiment=(
            NewsSentiment.POSITIVE
        ),
    )

    published_at = datetime(
        2026,
        7,
        17,
        9,
        30,
        tzinfo=timezone.utc,
    )

    analysed_at = datetime(
        2026,
        7,
        17,
        9,
        34,
        tzinfo=timezone.utc,
    )

    expires_at = datetime(
        2026,
        7,
        17,
        10,
        4,
        tzinfo=timezone.utc,
    )

    stored = StoredNewsAnalysis(
        analysis=analysis,
        analysed_at=analysed_at,
        expires_at=expires_at,
        article_title=(
            "Apple reports stronger revenue"
        ),
        article_url=(
            "https://example.test/apple"
        ),
        published_at=published_at,
        relevance_score=0.91,
        source_sentiment_label=(
            "Somewhat-Bullish"
        ),
        source_sentiment_score=0.35,
        model_name="fake-model",
        prompt_version="v3",
    )

    assert stored.analysis is analysis
    assert stored.analysed_at is analysed_at
    assert stored.expires_at is expires_at
    assert stored.article_title == (
        "Apple reports stronger revenue"
    )
    assert stored.article_url == (
        "https://example.test/apple"
    )
    assert stored.published_at is published_at
    assert stored.relevance_score == 0.91
    assert stored.source_sentiment_label == (
        "Somewhat-Bullish"
    )
    assert stored.source_sentiment_score == 0.35
    assert stored.model_name == "fake-model"
    assert stored.prompt_version == "v3"
    
def test_rejects_expiry_before_analysis_time() -> None:
    analysis = NewsAnalysis(
        impact_term=NewsImpactTerm.SHORTTERM,
        impact_scope=NewsImpactScope.STOCK,
        scope_items=("AAPL",),
        highlights=("Apple reported stronger revenue",),
        sentiment=NewsSentiment.POSITIVE,
    )

    analysed_at = datetime(
        2026,
        7,
        17,
        10,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValueError,
        match="Expiry time must be after",
    ):
        StoredNewsAnalysis(
            analysis=analysis,
            analysed_at=analysed_at,
            expires_at=analysed_at,
            article_title="Apple reports stronger revenue",
            article_url=None,
            published_at=analysed_at,
            relevance_score=0.91,
            source_sentiment_label=None,
            source_sentiment_score=None,
            model_name="fake-model",
            prompt_version="v3",
        )


def test_rejects_invalid_relevance_score() -> None:
    analysis = NewsAnalysis(
        impact_term=NewsImpactTerm.SHORTTERM,
        impact_scope=NewsImpactScope.STOCK,
        scope_items=("AAPL",),
        highlights=("Apple reported stronger revenue",),
        sentiment=NewsSentiment.POSITIVE,
    )

    analysed_at = datetime(
        2026,
        7,
        17,
        10,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValueError,
        match="Relevance score must be",
    ):
        StoredNewsAnalysis(
            analysis=analysis,
            analysed_at=analysed_at,
            expires_at=analysed_at.replace(
                hour=11
            ),
            article_title="Apple reports stronger revenue",
            article_url=None,
            published_at=analysed_at,
            relevance_score=1.5,
            source_sentiment_label=None,
            source_sentiment_score=None,
            model_name="fake-model",
            prompt_version="v3",
        )