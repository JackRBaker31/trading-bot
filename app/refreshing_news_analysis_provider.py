from typing import Protocol

from app.news_analysis import (
    NewsAnalysis,
)


class NewsAnalyser(Protocol):
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        ...


class RefreshingNewsAnalysisProvider:
    def __init__(
        self,
        *,
        analyser: NewsAnalyser,
    ) -> None:
        self._analyser = analyser
        self._analyses: dict[
            str,
            NewsAnalysis,
        ] = {}

    def refresh(
        self,
        *,
        symbol: str,
        article_text: str,
    ) -> NewsAnalysis:
        normalised_symbol = (
            symbol.upper().strip()
        )

        analysis = self._analyser.analyse(
            article_text
        )

        self._analyses[
            normalised_symbol
        ] = analysis

        return analysis

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