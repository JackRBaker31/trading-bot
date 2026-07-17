from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.refreshing_news_analysis_provider import (
    RefreshingNewsAnalysisProvider,
)


class FakeAnalyser:
    def __init__(
        self,
        analysis: NewsAnalysis,
    ) -> None:
        self.analysis = analysis
        self.article_texts: list[str] = []

    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        self.article_texts.append(
            article_text
        )

        return self.analysis


def test_refreshes_and_returns_analysis() -> None:
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

    analyser = FakeAnalyser(
        analysis=analysis
    )

    provider = RefreshingNewsAnalysisProvider(
        analyser=analyser
    )

    provider.refresh(
        symbol=" aapl ",
        article_text=(
            "Apple reported stronger revenue."
        ),
    )

    assert analyser.article_texts == [
        "Apple reported stronger revenue."
    ]
    assert (
        provider.get_analysis("AAPL")
        is analysis
    )


def test_returns_none_before_refresh() -> None:
    provider = RefreshingNewsAnalysisProvider(
        analyser=FakeAnalyser(
            analysis=NewsAnalysis(
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
        )
    )

    assert (
        provider.get_analysis("AAPL")
        is None
    )