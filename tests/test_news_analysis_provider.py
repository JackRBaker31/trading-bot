from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.news_analysis_provider import (
    InMemoryNewsAnalysisProvider,
)
from app.news_analysis_provider import (
    InMemoryNewsAnalysisProvider,
    NewsAnalysisProvider,
    WritableNewsAnalysisProvider,
)


def test_returns_analysis_for_symbol() -> None:
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

    provider = InMemoryNewsAnalysisProvider(
        analyses={
            "AAPL": analysis,
        }
    )

    assert (
        provider.get_analysis("AAPL")
        is analysis
    )


def test_normalises_symbol_before_lookup() -> None:
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

    provider = InMemoryNewsAnalysisProvider(
        analyses={
            "AAPL": analysis,
        }
    )

    assert (
        provider.get_analysis(" aapl ")
        is analysis
    )


def test_returns_none_for_unknown_symbol() -> None:
    provider = InMemoryNewsAnalysisProvider(
        analyses={}
    )

    assert (
        provider.get_analysis("MSFT")
        is None
    )
    
def test_updates_analysis_for_symbol() -> None:
    original = NewsAnalysis(
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

    updated = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("AAPL",),
        highlights=(
            "Apple received a regulatory penalty",
        ),
        sentiment=(
            NewsSentiment.NEGATIVE
        ),
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={
            "AAPL": original,
        }
    )

    provider.set_analysis(
        symbol=" aapl ",
        analysis=updated,
    )

    assert (
        provider.get_analysis("AAPL")
        is updated
    )
    
def test_in_memory_provider_matches_protocol() -> None:
    provider: NewsAnalysisProvider = (
        InMemoryNewsAnalysisProvider(
            analyses={}
        )
    )

    assert provider.get_analysis("AAPL") is None
    
def test_in_memory_provider_matches_writable_protocol() -> None:
    provider: WritableNewsAnalysisProvider = (
        InMemoryNewsAnalysisProvider(
            analyses={}
        )
    )

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

    provider.set_analysis(
        symbol="AAPL",
        analysis=analysis,
    )

    assert (
        provider.get_analysis("AAPL")
        is analysis
    )