from typing import Protocol

from app.news_analysis import (
    NewsAnalysis,
)


class NewsAnalysisProvider(Protocol):
    def get_analysis(
        self,
        symbol: str,
    ) -> NewsAnalysis | None:
        ...


class WritableNewsAnalysisProvider(
    NewsAnalysisProvider,
    Protocol,
):
    def set_analysis(
        self,
        *,
        symbol: str,
        analysis: NewsAnalysis,
    ) -> None:
        ...


class InMemoryNewsAnalysisProvider:
    def __init__(
        self,
        *,
        analyses: dict[str, NewsAnalysis],
    ) -> None:
        self._analyses = {
            symbol.upper().strip(): analysis
            for symbol, analysis in analyses.items()
        }

    def get_analysis(
        self,
        symbol: str,
    ) -> NewsAnalysis | None:
        normalised_symbol = (
            symbol.upper().strip()
        )

        return self._analyses.get(
            normalised_symbol
        )

    def set_analysis(
        self,
        *,
        symbol: str,
        analysis: NewsAnalysis,
    ) -> None:
        normalised_symbol = (
            symbol.upper().strip()
        )

        self._analyses[
            normalised_symbol
        ] = analysis