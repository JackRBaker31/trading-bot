from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class DecisionTraceStage:
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
class DecisionTrace:
    trace_id: str
    created_at: datetime
    symbol: str | None
    decision: str
    confidence: float
    trading_readiness: str
    graduation_ready: bool
    summary: str
    stages: tuple[
        DecisionTraceStage,
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
            "created_at": (
                self.created_at.isoformat()
            ),
            "symbol": self.symbol,
            "decision": self.decision,
            "confidence": self.confidence,
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
