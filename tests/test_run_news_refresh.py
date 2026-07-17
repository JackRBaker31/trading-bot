from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.run_news_refresh import (
    refresh_symbol,
)


class FakeRefreshService:
    def __init__(
        self,
        analysis: NewsAnalysis,
    ) -> None:
        self.analysis = analysis
        self.symbols: list[str] = []

    def refresh_symbol(
        self,
        *,
        symbol: str,
    ) -> NewsAnalysis:
        self.symbols.append(symbol)

        return self.analysis


def test_refreshes_requested_symbol() -> None:
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

    service = FakeRefreshService(
        analysis=analysis
    )

    result = refresh_symbol(
        symbol=" aapl ",
        refresh_service=service,
    )

    assert result is analysis
    assert service.symbols == [
        "AAPL",
    ]
    
def test_prints_refreshed_analysis(
    capsys,
) -> None:
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

    service = FakeRefreshService(
        analysis=analysis
    )

    print_analysis = getattr(
        __import__(
            "app.run_news_refresh",
            fromlist=["print_analysis"],
        ),
        "print_analysis",
    )

    print_analysis(
        symbol="AAPL",
        analysis=analysis,
    )

    output = capsys.readouterr().out

    assert "Symbol: AAPL" in output
    assert "Sentiment: POSITIVE" in output
    assert "Impact term: SHORTTERM" in output
    assert "Impact scope: STOCK" in output
    assert "Scope items: AAPL" in output
    assert (
        "Apple reported stronger revenue"
        in output
    )