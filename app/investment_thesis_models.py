from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class ThesisCapabilityAssessment:
    capability: str
    status: str
    score: float | None
    maximum: float
    confidence: float | None
    stance: str
    summary: str
    evidence: tuple[str, ...]
    blockers: tuple[str, ...] = ()

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
class InvestmentThesis:
    thesis_id: str
    generated_at: datetime
    symbol: str
    recommendation: str
    score: float
    available_score: float
    available_maximum: float
    confidence: float
    confidence_coverage: float
    risk_tier: str
    time_horizon: str
    suggested_position_value: float
    eligible_for_execution: bool
    headline: str
    primary_driver: str
    capabilities: tuple[
        ThesisCapabilityAssessment,
        ...
    ]
    reasons: tuple[str, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "thesis_id": self.thesis_id,
            "generated_at": (
                self.generated_at.isoformat()
            ),
            "symbol": self.symbol,
            "recommendation": self.recommendation,
            "score": self.score,
            "available_score": (
                self.available_score
            ),
            "available_maximum": (
                self.available_maximum
            ),
            "confidence": self.confidence,
            "confidence_coverage": (
                self.confidence_coverage
            ),
            "risk_tier": self.risk_tier,
            "time_horizon": self.time_horizon,
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
                item.to_dictionary()
                for item in self.capabilities
            ],
            "reasons": list(self.reasons),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class InvestmentThesisReport:
    generated_at: datetime
    thesis_count: int
    executable_count: int
    complete_capability_count: int
    required_capability_count: int
    theses: tuple[
        InvestmentThesis,
        ...
    ]
    platform_blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "generated_at": (
                self.generated_at.isoformat()
            ),
            "thesis_count": self.thesis_count,
            "executable_count": (
                self.executable_count
            ),
            "complete_capability_count": (
                self.complete_capability_count
            ),
            "required_capability_count": (
                self.required_capability_count
            ),
            "theses": [
                thesis.to_dictionary()
                for thesis in self.theses
            ],
            "platform_blockers": list(
                self.platform_blockers
            ),
            "warnings": list(self.warnings),
        }
