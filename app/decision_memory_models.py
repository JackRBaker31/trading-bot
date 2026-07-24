from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DecisionMemoryCapability:
    capability: str
    status: str
    score: float | None
    maximum: float
    confidence: float | None
    stance: str
    summary: str
    evidence: tuple[str, ...]
    blockers: tuple[str, ...]

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "capability": self.capability,
            "status": self.status,
            "score": self.score,
            "maximum": self.maximum,
            "confidence": self.confidence,
            "stance": self.stance,
            "summary": self.summary,
            "evidence": list(self.evidence),
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class DecisionMemoryRecord:
    decision_id: str
    fingerprint: str
    captured_at: datetime
    thesis_generated_at: datetime
    symbol: str
    recommendation: str
    score: float
    confidence: float
    confidence_coverage: float
    risk_tier: str
    time_horizon: str
    suggested_position_value: float
    eligible_for_execution: bool
    headline: str
    primary_driver: str
    capabilities: tuple[
        DecisionMemoryCapability,
        ...
    ]
    reasons: tuple[str, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    executed: bool
    paper_trade_id: str | None

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "fingerprint": self.fingerprint,
            "captured_at": (
                self.captured_at.isoformat()
            ),
            "thesis_generated_at": (
                self.thesis_generated_at
                .isoformat()
            ),
            "symbol": self.symbol,
            "recommendation": (
                self.recommendation
            ),
            "score": self.score,
            "confidence": self.confidence,
            "confidence_coverage": (
                self.confidence_coverage
            ),
            "risk_tier": self.risk_tier,
            "time_horizon": (
                self.time_horizon
            ),
            "suggested_position_value": (
                self.suggested_position_value
            ),
            "eligible_for_execution": (
                self.eligible_for_execution
            ),
            "headline": self.headline,
            "primary_driver": (
                self.primary_driver
            ),
            "capabilities": [
                capability.to_dictionary()
                for capability
                in self.capabilities
            ],
            "reasons": list(self.reasons),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "executed": self.executed,
            "paper_trade_id": (
                self.paper_trade_id
            ),
        }


@dataclass(frozen=True)
class DecisionMemoryCaptureResult:
    captured_count: int
    duplicate_count: int
    records: tuple[
        DecisionMemoryRecord,
        ...
    ]

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "captured_count": (
                self.captured_count
            ),
            "duplicate_count": (
                self.duplicate_count
            ),
            "records": [
                record.to_dictionary()
                for record in self.records
            ],
        }


@dataclass(frozen=True)
class DecisionMemoryOverview:
    generated_at: datetime
    total_count: int
    executable_count: int
    executed_count: int
    symbol_count: int
    latest: tuple[
        DecisionMemoryRecord,
        ...
    ]

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "generated_at": (
                self.generated_at.isoformat()
            ),
            "total_count": self.total_count,
            "executable_count": (
                self.executable_count
            ),
            "executed_count": (
                self.executed_count
            ),
            "symbol_count": (
                self.symbol_count
            ),
            "latest": [
                record.to_dictionary()
                for record in self.latest
            ],
        }
