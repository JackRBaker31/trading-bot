from dataclasses import dataclass
from typing import Protocol

from app.news_analysis_provider import (
    NewsAnalysisProvider,
)


class NewsRefreshService(Protocol):
    def refresh_symbol(
        self,
        *,
        symbol: str,
    ):
        ...

    def refresh_symbols(
        self,
        *,
        symbols: list[str],
    ):
        ...


@dataclass(frozen=True)
class NewsRuntimePipeline:
    provider: NewsAnalysisProvider
    refresh_service: NewsRefreshService