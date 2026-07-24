from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class SymbolDecisionStage:
    sequence: int
    stage: str
    status: str
    title: str
    summary: str
    evidence: tuple[str, ...] = field(
        default_factory=tuple
    )

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence"] = list(
            self.evidence
        )
        return payload


@dataclass(frozen=True)
class SymbolDecisionTrace:
    trace_id: str
    captured_at: datetime
    symbol: str
    rank: int
    decision: str
    classification: str
    score: float
    confidence: float
    headline: str
    event_type: str
    sentiment: str
    eligible_for_trade: bool
    trading_readiness: str
    graduation_ready: bool
    summary: str
    stages: tuple[
        SymbolDecisionStage,
        ...
    ]
    blockers: tuple[str, ...] = field(
        default_factory=tuple
    )

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "trace_id": self.trace_id,
            "captured_at": (
                self.captured_at.isoformat()
            ),
            "symbol": self.symbol,
            "rank": self.rank,
            "decision": self.decision,
            "classification": (
                self.classification
            ),
            "score": self.score,
            "confidence": self.confidence,
            "headline": self.headline,
            "event_type": self.event_type,
            "sentiment": self.sentiment,
            "eligible_for_trade": (
                self.eligible_for_trade
            ),
            "trading_readiness": (
                self.trading_readiness
            ),
            "graduation_ready": (
                self.graduation_ready
            ),
            "summary": self.summary,
            "stages": [
                stage.to_dictionary()
                for stage in self.stages
            ],
            "blockers": list(
                self.blockers
            ),
        }
