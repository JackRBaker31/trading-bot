import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.application_errors import (
    ConfigurationError,
    DataStoreError,
)
from app.news_research_summary import (
    NewsResearchSummary,
    summarize_news_research,
)
from app.news_signal import NewsSignal
from app.news_signal_outcome import (
    NewsSignalOutcome,
)
from app.news_signal_outcome_store import (
    NewsSignalOutcomeStore,
)
from app.news_signal_store import NewsSignalStore


@dataclass(frozen=True)
class PagedResearchResult:
    total_count: int
    offset: int
    limit: int
    items: tuple[dict[str, object], ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "total_count": self.total_count,
            "offset": self.offset,
            "limit": self.limit,
            "count": len(self.items),
            "items": list(self.items),
        }


class ResearchQueryService:
    def __init__(
        self,
        *,
        report_path: str = "data/research_report.json",
        signals_path: str = "data/news_signals.jsonl",
        outcomes_path: str = (
            "data/news_signal_outcomes.jsonl"
        ),
    ) -> None:
        self._report_path = self._clean_path(
            report_path,
            "Research-report path",
        )
        self._signals_path = self._clean_path(
            signals_path,
            "News-signals path",
        )
        self._outcomes_path = self._clean_path(
            outcomes_path,
            "News-outcomes path",
        )

    def get_latest_report(self) -> dict[str, object] | None:
        path = Path(self._report_path)

        if not path.exists():
            return None

        try:
            with path.open(
                mode="r",
                encoding="utf-8",
            ) as file:
                payload = json.load(file)
        except (
            OSError,
            json.JSONDecodeError,
        ) as error:
            raise DataStoreError(
                "The latest research report could not be loaded.",
                code="RESEARCH_REPORT_LOAD_FAILED",
                context={"path": self._report_path},
            ) from error

        if not isinstance(payload, dict):
            raise DataStoreError(
                "The latest research report is invalid.",
                code="RESEARCH_REPORT_INVALID",
                context={"path": self._report_path},
            )

        return payload

    def list_signals(
        self,
        *,
        symbol: str | None = None,
        sentiment: str | None = None,
        event_type: str | None = None,
        is_material: bool | None = None,
        minimum_confidence: float | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> PagedResearchResult:
        self._validate_page(offset=offset, limit=limit)
        cleaned_symbol = self._clean_optional_upper(symbol)
        cleaned_sentiment = self._clean_sentiment(sentiment)
        cleaned_event_type = self._clean_optional_upper(
            event_type
        )

        if (
            minimum_confidence is not None
            and not 0.0 <= minimum_confidence <= 1.0
        ):
            raise ConfigurationError(
                "Minimum confidence must be between 0 and 1.",
                code="INVALID_MINIMUM_CONFIDENCE",
            )

        signals = self._load_signals()
        filtered = [
            signal
            for signal in signals
            if (
                cleaned_symbol is None
                or signal.symbol == cleaned_symbol
            )
            and (
                cleaned_sentiment is None
                or self._sentiment_name(signal)
                == cleaned_sentiment
            )
            and (
                cleaned_event_type is None
                or signal.event_type
                == cleaned_event_type
            )
            and (
                is_material is None
                or signal.is_material
                is is_material
            )
            and (
                minimum_confidence is None
                or signal.confidence
                >= minimum_confidence
            )
        ]
        filtered.sort(
            key=lambda signal: signal.published_at,
            reverse=True,
        )

        page = filtered[offset : offset + limit]
        return PagedResearchResult(
            total_count=len(filtered),
            offset=offset,
            limit=limit,
            items=tuple(
                self._signal_to_dictionary(signal)
                for signal in page
            ),
        )

    def list_outcomes(
        self,
        *,
        symbol: str | None = None,
        horizon: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> PagedResearchResult:
        self._validate_page(offset=offset, limit=limit)
        cleaned_symbol = self._clean_optional_upper(symbol)
        cleaned_horizon = self._clean_optional_upper(horizon)

        outcomes = self._load_outcomes()
        filtered = [
            outcome
            for outcome in outcomes
            if (
                cleaned_symbol is None
                or outcome.symbol == cleaned_symbol
            )
            and (
                cleaned_horizon is None
                or outcome.horizon_name
                == cleaned_horizon
            )
        ]
        filtered.sort(
            key=lambda outcome: outcome.observed_at,
            reverse=True,
        )

        page = filtered[offset : offset + limit]
        return PagedResearchResult(
            total_count=len(filtered),
            offset=offset,
            limit=limit,
            items=tuple(
                self._outcome_to_dictionary(outcome)
                for outcome in page
            ),
        )

    def get_news_summary(self) -> dict[str, object]:
        summary = summarize_news_research(
            signals=self._load_signals(),
            outcomes=self._load_outcomes(),
        )
        return self._summary_to_dictionary(summary)

    def _load_signals(self) -> list[NewsSignal]:
        try:
            return NewsSignalStore(
                file_path=self._signals_path
            ).load_all()
        except (OSError, ValueError) as error:
            raise DataStoreError(
                "News signals could not be loaded.",
                code="NEWS_SIGNALS_LOAD_FAILED",
                context={"path": self._signals_path},
            ) from error

    def _load_outcomes(self) -> list[NewsSignalOutcome]:
        try:
            return NewsSignalOutcomeStore(
                file_path=self._outcomes_path
            ).load_all()
        except (OSError, ValueError) as error:
            raise DataStoreError(
                "News outcomes could not be loaded.",
                code="NEWS_OUTCOMES_LOAD_FAILED",
                context={"path": self._outcomes_path},
            ) from error

    @staticmethod
    def _signal_to_dictionary(
        signal: NewsSignal,
    ) -> dict[str, object]:
        return {
            "article_id": signal.article_id,
            "symbol": signal.symbol,
            "headline": signal.headline,
            "sentiment": signal.sentiment,
            "sentiment_name": (
                ResearchQueryService._sentiment_name(
                    signal
                )
            ),
            "relevance": signal.relevance,
            "confidence": signal.confidence,
            "event_type": signal.event_type,
            "is_material": signal.is_material,
            "published_at": signal.published_at.isoformat(),
            "expires_at": signal.expires_at.isoformat(),
            "source": signal.source,
            "reasoning_summary": signal.reasoning_summary,
        }

    @staticmethod
    def _outcome_to_dictionary(
        outcome: NewsSignalOutcome,
    ) -> dict[str, object]:
        return {
            "article_id": outcome.article_id,
            "symbol": outcome.symbol,
            "horizon_name": outcome.horizon_name,
            "signal_published_at": (
                outcome.signal_published_at.isoformat()
            ),
            "observed_at": outcome.observed_at.isoformat(),
            "reference_price": outcome.reference_price,
            "observed_price": outcome.observed_price,
            "return_percent": outcome.return_percent,
        }

    @staticmethod
    def _summary_to_dictionary(
        summary: NewsResearchSummary,
    ) -> dict[str, object]:
        return {
            "signal_count": summary.signal_count,
            "outcome_count": summary.outcome_count,
            "unmatched_outcome_count": (
                summary.unmatched_outcome_count
            ),
            "sentiment_groups": [
                asdict(group)
                for group in summary.sentiment_groups
            ],
            "materiality_groups": [
                asdict(group)
                for group in summary.materiality_groups
            ],
            "event_type_groups": [
                asdict(group)
                for group in summary.event_type_groups
            ],
            "confidence_groups": [
                asdict(group)
                for group in summary.confidence_groups
            ],
        }

    @staticmethod
    def _sentiment_name(signal: NewsSignal) -> str:
        if signal.sentiment > 0:
            return "POSITIVE"
        if signal.sentiment < 0:
            return "NEGATIVE"
        return "NEUTRAL"

    @staticmethod
    def _clean_sentiment(value: str | None) -> str | None:
        cleaned = ResearchQueryService._clean_optional_upper(
            value
        )
        if cleaned is None:
            return None
        if cleaned not in {
            "POSITIVE",
            "NEGATIVE",
            "NEUTRAL",
        }:
            raise ConfigurationError(
                "Sentiment must be POSITIVE, NEGATIVE, or NEUTRAL.",
                code="INVALID_SENTIMENT_FILTER",
            )
        return cleaned

    @staticmethod
    def _validate_page(*, offset: int, limit: int) -> None:
        if offset < 0:
            raise ConfigurationError(
                "Offset cannot be negative.",
                code="INVALID_PAGE_OFFSET",
            )
        if limit <= 0:
            raise ConfigurationError(
                "Limit must be positive.",
                code="INVALID_PAGE_LIMIT",
            )

    @staticmethod
    def _clean_path(value: str, name: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ConfigurationError(
                f"{name} is required.",
            )
        return cleaned

    @staticmethod
    def _clean_optional_upper(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        cleaned = value.upper().strip()
        return cleaned or None
