from dataclasses import asdict, dataclass
from datetime import datetime

from app.symbol_decision_models import (
    SymbolDecisionTrace,
)


@dataclass(frozen=True)
class SymbolDecisionMetricChange:
    metric: str
    previous: float
    current: float
    change: float
    direction: str

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SymbolDecisionHistorySummary:
    generated_at: datetime
    symbol: str
    comparison_available: bool
    current: SymbolDecisionTrace
    previous: SymbolDecisionTrace | None
    score_change: (
        SymbolDecisionMetricChange
        | None
    )
    confidence_change: (
        SymbolDecisionMetricChange
        | None
    )
    rank_change: (
        SymbolDecisionMetricChange
        | None
    )
    decision_changed: bool
    sentiment_changed: bool
    classification_changed: bool
    new_blockers: tuple[str, ...]
    cleared_blockers: tuple[str, ...]
    summary: str

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "generated_at": (
                self.generated_at
                .isoformat()
            ),
            "symbol": self.symbol,
            "comparison_available": (
                self.comparison_available
            ),
            "current": (
                self.current
                .to_dictionary()
            ),
            "previous": (
                self.previous
                .to_dictionary()
                if self.previous
                else None
            ),
            "score_change": (
                self.score_change
                .to_dictionary()
                if self.score_change
                else None
            ),
            "confidence_change": (
                self.confidence_change
                .to_dictionary()
                if self.confidence_change
                else None
            ),
            "rank_change": (
                self.rank_change
                .to_dictionary()
                if self.rank_change
                else None
            ),
            "decision_changed": (
                self.decision_changed
            ),
            "sentiment_changed": (
                self.sentiment_changed
            ),
            "classification_changed": (
                self
                .classification_changed
            ),
            "new_blockers": list(
                self.new_blockers
            ),
            "cleared_blockers": list(
                self.cleared_blockers
            ),
            "summary": self.summary,
        }
