from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class DecisionScoreComponent:
    code: str
    label: str
    value: float
    maximum: float
    detail: str

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class InvestmentDecision:
    symbol: str
    generated_at: datetime
    recommendation: str
    score: float
    confidence: float
    risk_tier: str
    suggested_position_value: float
    eligible_for_execution: bool
    headline: str
    event_type: str
    sentiment: str
    classification: str
    components: tuple[
        DecisionScoreComponent,
        ...
    ]
    reasons: tuple[str, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "generated_at": (
                self.generated_at.isoformat()
            ),
            "recommendation": (
                self.recommendation
            ),
            "score": self.score,
            "confidence": self.confidence,
            "risk_tier": self.risk_tier,
            "suggested_position_value": (
                self.suggested_position_value
            ),
            "eligible_for_execution": (
                self.eligible_for_execution
            ),
            "headline": self.headline,
            "event_type": self.event_type,
            "sentiment": self.sentiment,
            "classification": (
                self.classification
            ),
            "components": [
                component.to_dictionary()
                for component
                in self.components
            ],
            "reasons": list(self.reasons),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class DecisionIntelligenceReport:
    generated_at: datetime
    trading_readiness: str
    graduation_eligible: bool
    decision_count: int
    executable_candidate_count: int
    decisions: tuple[
        InvestmentDecision,
        ...
    ]
    platform_blockers: tuple[
        str,
        ...
    ]
    warnings: tuple[
        str,
        ...
    ]

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "generated_at": (
                self.generated_at.isoformat()
            ),
            "trading_readiness": (
                self.trading_readiness
            ),
            "graduation_eligible": (
                self.graduation_eligible
            ),
            "decision_count": (
                self.decision_count
            ),
            "executable_candidate_count": (
                self.executable_candidate_count
            ),
            "decisions": [
                decision.to_dictionary()
                for decision
                in self.decisions
            ],
            "platform_blockers": list(
                self.platform_blockers
            ),
            "warnings": list(
                self.warnings
            ),
        }
