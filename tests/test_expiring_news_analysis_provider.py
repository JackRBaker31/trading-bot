from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.expiring_news_analysis_provider import (
    ExpiringNewsAnalysisProvider,
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

def create_analysis() -> NewsAnalysis:
    return NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("AAPL",),
        highlights=(
            "Apple received negative news",
        ),
        sentiment=(
            NewsSentiment.NEGATIVE
        ),
    )


def test_returns_unexpired_analysis() -> None:
    now = datetime(
        2026,
        7,
        17,
        12,
        0,
        tzinfo=timezone.utc,
    )

    analysis = create_analysis()

    provider = ExpiringNewsAnalysisProvider(
        time_to_live_seconds=1_800,
        now_provider=lambda: now,
    )

    provider.set_analysis(
        symbol="AAPL",
        analysis=analysis,
    )

    assert (
        provider.get_analysis("AAPL")
        is analysis
    )


def test_returns_none_after_analysis_expires() -> None:
    current_time = datetime(
        2026,
        7,
        17,
        12,
        0,
        tzinfo=timezone.utc,
    )

    provider = ExpiringNewsAnalysisProvider(
        time_to_live_seconds=1_800,
        now_provider=lambda: current_time,
    )

    provider.set_analysis(
        symbol="AAPL",
        analysis=create_analysis(),
    )

    current_time += timedelta(
        seconds=1_801
    )

    assert (
        provider.get_analysis("AAPL")
        is None
    )


def test_normalises_symbol_for_storage_and_lookup() -> None:
    now = datetime(
        2026,
        7,
        17,
        12,
        0,
        tzinfo=timezone.utc,
    )

    analysis = create_analysis()

    provider = ExpiringNewsAnalysisProvider(
        time_to_live_seconds=1_800,
        now_provider=lambda: now,
    )

    provider.set_analysis(
        symbol=" aapl ",
        analysis=analysis,
    )

    assert (
        provider.get_analysis("AAPL")
        is analysis
    )
    
def test_can_return_stored_analysis_record() -> None:
    now = datetime(
        2026,
        7,
        17,
        12,
        0,
        tzinfo=timezone.utc,
    )

    analysis = create_analysis()

    provider = ExpiringNewsAnalysisProvider(
        time_to_live_seconds=1_800,
        now_provider=lambda: now,
    )

    stored = StoredNewsAnalysis(
        analysis=analysis,
        analysed_at=now,
        expires_at=now + timedelta(
            seconds=1_800
        ),
        article_title=(
            "Apple received negative news"
        ),
        article_url=(
            "https://example.test/apple"
        ),
        published_at=now,
        relevance_score=0.91,
        source_sentiment_label=(
            "Somewhat-Bearish"
        ),
        source_sentiment_score=-0.35,
        model_name="fake-model",
        prompt_version="v3",
    )

    provider.set_stored_analysis(
        symbol="AAPL",
        stored_analysis=stored,
    )

    assert (
        provider.get_stored_analysis("AAPL")
        is stored
    )
    assert (
        provider.get_analysis("AAPL")
        is analysis
    )