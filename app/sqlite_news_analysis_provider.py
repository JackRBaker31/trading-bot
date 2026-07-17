from collections.abc import Callable
from datetime import datetime, timezone

from app.news_analysis import (
    NewsAnalysis,
)
from app.sqlite_news_analysis_repository import (
    SQLiteNewsAnalysisRepository,
)
from app.stored_news_analysis import (
    StoredNewsAnalysis,
)


class SQLiteNewsAnalysisProvider:
    def __init__(
        self,
        *,
        repository: SQLiteNewsAnalysisRepository,
        now_provider: (
            Callable[[], datetime] | None
        ) = None,
    ) -> None:
        self._repository = repository
        self._now_provider = (
            now_provider
            if now_provider is not None
            else lambda: datetime.now(
                timezone.utc
            )
        )

    def get_analysis(
        self,
        symbol: str,
    ) -> NewsAnalysis | None:
        stored = self.get_stored_analysis(
            symbol
        )

        if stored is None:
            return None

        return stored.analysis

    def get_stored_analysis(
        self,
        symbol: str,
    ) -> StoredNewsAnalysis | None:
        stored = self._repository.get_latest(
            symbol
        )

        if stored is None:
            return None

        if self._now_provider() >= stored.expires_at:
            return None

        return stored

    def set_stored_analysis(
        self,
        *,
        symbol: str,
        stored_analysis: StoredNewsAnalysis,
    ) -> None:
        self._repository.save(
            symbol=symbol,
            stored_analysis=stored_analysis,
        )