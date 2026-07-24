from collections.abc import Callable
from datetime import datetime, timezone

from app.symbol_decision_history_models import (
    SymbolDecisionHistorySummary,
    SymbolDecisionMetricChange,
)
from app.symbol_decision_models import (
    SymbolDecisionTrace,
)
from app.symbol_decision_repository import (
    SymbolDecisionRepository,
)


NowProvider = Callable[
    [],
    datetime,
]


class SymbolDecisionHistoryService:
    def __init__(
        self,
        *,
        repository: (
            SymbolDecisionRepository
        ),
        now_provider: (
            NowProvider | None
        ) = None,
    ) -> None:
        self._repository = repository
        self._now_provider = (
            now_provider
            or (
                lambda: datetime.now(
                    timezone.utc
                )
            )
        )

    def initialize(self) -> None:
        self._repository.initialize()

    def list_history(
        self,
        *,
        symbol: str,
        limit: int = 100,
    ) -> tuple[
        SymbolDecisionTrace,
        ...
    ]:
        return (
            self._repository.list_recent(
                symbol=symbol,
                limit=limit,
            )
        )

    def compare_latest(
        self,
        *,
        symbol: str,
    ) -> (
        SymbolDecisionHistorySummary
        | None
    ):
        cleaned_symbol = (
            symbol.upper().strip()
        )

        history = (
            self._repository.list_recent(
                symbol=cleaned_symbol,
                limit=2,
            )
        )

        if not history:
            return None

        current = history[0]

        if len(history) == 1:
            return (
                SymbolDecisionHistorySummary(
                    generated_at=(
                        self._utc_now()
                    ),
                    symbol=(
                        cleaned_symbol
                    ),
                    comparison_available=(
                        False
                    ),
                    current=current,
                    previous=None,
                    score_change=None,
                    confidence_change=None,
                    rank_change=None,
                    decision_changed=False,
                    sentiment_changed=False,
                    classification_changed=(
                        False
                    ),
                    new_blockers=(),
                    cleared_blockers=(),
                    summary=(
                        "Only one recorded "
                        f"decision exists for "
                        f"{cleaned_symbol}. "
                        "A second decision is "
                        "required for comparison."
                    ),
                )
            )

        previous = history[1]

        score_change = (
            self._metric_change(
                metric="score",
                previous=(
                    previous.score
                ),
                current=current.score,
            )
        )

        confidence_change = (
            self._metric_change(
                metric="confidence",
                previous=(
                    previous.confidence
                ),
                current=(
                    current.confidence
                ),
            )
        )

        rank_change = (
            self._metric_change(
                metric="rank",
                previous=float(
                    previous.rank
                ),
                current=float(
                    current.rank
                ),
                lower_is_better=True,
            )
        )

        new_blockers = tuple(
            sorted(
                set(current.blockers)
                - set(
                    previous.blockers
                )
            )
        )

        cleared_blockers = tuple(
            sorted(
                set(
                    previous.blockers
                )
                - set(
                    current.blockers
                )
            )
        )

        decision_changed = (
            current.decision
            != previous.decision
        )

        sentiment_changed = (
            current.sentiment
            != previous.sentiment
        )

        classification_changed = (
            current.classification
            != previous.classification
        )

        summary = (
            self._summary(
                current=current,
                previous=previous,
                score_change=(
                    score_change
                ),
                confidence_change=(
                    confidence_change
                ),
                rank_change=(
                    rank_change
                ),
                decision_changed=(
                    decision_changed
                ),
                sentiment_changed=(
                    sentiment_changed
                ),
                classification_changed=(
                    classification_changed
                ),
                new_blockers=(
                    new_blockers
                ),
                cleared_blockers=(
                    cleared_blockers
                ),
            )
        )

        return (
            SymbolDecisionHistorySummary(
                generated_at=(
                    self._utc_now()
                ),
                symbol=cleaned_symbol,
                comparison_available=True,
                current=current,
                previous=previous,
                score_change=(
                    score_change
                ),
                confidence_change=(
                    confidence_change
                ),
                rank_change=(
                    rank_change
                ),
                decision_changed=(
                    decision_changed
                ),
                sentiment_changed=(
                    sentiment_changed
                ),
                classification_changed=(
                    classification_changed
                ),
                new_blockers=(
                    new_blockers
                ),
                cleared_blockers=(
                    cleared_blockers
                ),
                summary=summary,
            )
        )

    @staticmethod
    def _metric_change(
        *,
        metric: str,
        previous: float,
        current: float,
        lower_is_better: bool = False,
    ) -> SymbolDecisionMetricChange:
        change = current - previous

        if change == 0:
            direction = "UNCHANGED"
        elif lower_is_better:
            direction = (
                "IMPROVED"
                if change < 0
                else "WORSENED"
            )
        else:
            direction = (
                "IMPROVED"
                if change > 0
                else "WORSENED"
            )

        return (
            SymbolDecisionMetricChange(
                metric=metric,
                previous=previous,
                current=current,
                change=change,
                direction=direction,
            )
        )

    @staticmethod
    def _summary(
        *,
        current: SymbolDecisionTrace,
        previous: SymbolDecisionTrace,
        score_change: (
            SymbolDecisionMetricChange
        ),
        confidence_change: (
            SymbolDecisionMetricChange
        ),
        rank_change: (
            SymbolDecisionMetricChange
        ),
        decision_changed: bool,
        sentiment_changed: bool,
        classification_changed: bool,
        new_blockers: tuple[
            str,
            ...
        ],
        cleared_blockers: tuple[
            str,
            ...
        ],
    ) -> str:
        parts: list[str] = []

        if decision_changed:
            parts.append(
                "The decision changed "
                f"from {previous.decision} "
                f"to {current.decision}."
            )

        if score_change.change != 0:
            verb = (
                "increased"
                if (
                    score_change.change
                    > 0
                )
                else "decreased"
            )
            parts.append(
                "Opportunity score "
                f"{verb} by "
                f"{abs(score_change.change):.2f}."
            )

        if (
            confidence_change.change
            != 0
        ):
            percentage_points = (
                abs(
                    confidence_change
                    .change
                )
                * 100
            )
            verb = (
                "increased"
                if (
                    confidence_change
                    .change
                    > 0
                )
                else "decreased"
            )
            parts.append(
                "Confidence "
                f"{verb} by "
                f"{percentage_points:.1f} "
                "percentage points."
            )

        if rank_change.change != 0:
            parts.append(
                "Ranking moved "
                f"from #{previous.rank} "
                f"to #{current.rank}."
            )

        if sentiment_changed:
            parts.append(
                "Sentiment changed "
                f"from "
                f"{previous.sentiment} "
                f"to "
                f"{current.sentiment}."
            )

        if classification_changed:
            parts.append(
                "Classification changed "
                f"from "
                f"{previous.classification} "
                f"to "
                f"{current.classification}."
            )

        if new_blockers:
            parts.append(
                f"{len(new_blockers)} "
                "new blocker(s) appeared."
            )

        if cleared_blockers:
            parts.append(
                f"{len(cleared_blockers)} "
                "blocker(s) cleared."
            )

        if not parts:
            return (
                "No material change was "
                "detected between the two "
                "latest symbol decisions."
            )

        return " ".join(parts)

    def _utc_now(
        self,
    ) -> datetime:
        value = self._now_provider()

        if value.tzinfo is None:
            raise ValueError(
                "Symbol Decision History "
                "clock must be "
                "timezone-aware."
            )

        return value.astimezone(
            timezone.utc
        )
