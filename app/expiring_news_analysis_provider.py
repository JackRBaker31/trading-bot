from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from app.news_analysis import (
    NewsAnalysis,
)
from app.stored_news_analysis import (
    StoredNewsAnalysis,
)


class ExpiringNewsAnalysisProvider:
    def __init__(
        self,
        *,
        time_to_live_seconds: float,
        now_provider: (
            Callable[[], datetime] | None
        ) = None,
    ) -> None:
        if time_to_live_seconds <= 0:
            raise ValueError(
                "Time to live must be greater "
                "than zero."
            )

        self._time_to_live = timedelta(
            seconds=time_to_live_seconds
        )
        self._now_provider = (
            now_provider
            if now_provider is not None
            else lambda: datetime.now(
                timezone.utc
            )
        )
        self._analyses: dict[
            str,
            StoredNewsAnalysis,
        ] = {}

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
        normalised_symbol = (
            symbol.upper().strip()
        )

        stored = self._analyses.get(
            normalised_symbol
        )

        if stored is None:
            return None

        if self._now_provider() >= stored.expires_at:
            self._analyses.pop(
                normalised_symbol,
                None,
            )

            return None

        return stored

    def set_analysis(
        self,
        *,
        symbol: str,
        analysis: NewsAnalysis,
    ) -> None:
        now = self._now_provider()

        stored = StoredNewsAnalysis(
            analysis=analysis,
            analysed_at=now,
            expires_at=(
                now + self._time_to_live
            ),
            article_title=(
                "Unknown article"
            ),
            article_url=None,
            published_at=now,
            relevance_score=0.0,
            source_sentiment_label=None,
            source_sentiment_score=None,
            model_name="unknown",
            prompt_version="unknown",
        )

        self.set_stored_analysis(
            symbol=symbol,
            stored_analysis=stored,
        )

    def set_stored_analysis(
        self,
        *,
        symbol: str,
        stored_analysis: StoredNewsAnalysis,
    ) -> None:
        normalised_symbol = (
            symbol.upper().strip()
        )

        self._analyses[
            normalised_symbol
        ] = stored_analysis