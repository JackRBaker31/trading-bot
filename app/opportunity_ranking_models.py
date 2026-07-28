from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class OpportunityRankingComponent:
    code: str
    label: str
    value: float
    maximum: float
    status: str
    detail: str

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RankedOpportunity:
    rank: int
    symbol: str
    opportunity_score: float
    category: str
    recommendation: str
    thesis_score: float
    raw_confidence: float
    calibrated_confidence: float
    confidence_sample_count: int
    expected_return_percent: float | None
    evidence_coverage_percent: float
    data_quality: str
    risk_tier: str
    eligible_for_execution: bool
    historical_match_count: int
    measured_case_count: int
    sector: str
    headline: str
    generated_at: datetime
    components: tuple[OpportunityRankingComponent, ...]
    positive_contributors: tuple[str, ...]
    penalties: tuple[str, ...]
    improvement_actions: tuple[str, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "rank": self.rank,
            "symbol": self.symbol,
            "opportunity_score": self.opportunity_score,
            "category": self.category,
            "recommendation": self.recommendation,
            "thesis_score": self.thesis_score,
            "raw_confidence": self.raw_confidence,
            "calibrated_confidence": self.calibrated_confidence,
            "confidence_sample_count": self.confidence_sample_count,
            "expected_return_percent": self.expected_return_percent,
            "evidence_coverage_percent": self.evidence_coverage_percent,
            "data_quality": self.data_quality,
            "risk_tier": self.risk_tier,
            "eligible_for_execution": self.eligible_for_execution,
            "historical_match_count": self.historical_match_count,
            "measured_case_count": self.measured_case_count,
            "sector": self.sector,
            "headline": self.headline,
            "generated_at": self.generated_at.isoformat(),
            "components": [
                component.to_dictionary()
                for component in self.components
            ],
            "positive_contributors": list(self.positive_contributors),
            "penalties": list(self.penalties),
            "improvement_actions": list(self.improvement_actions),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class OpportunityRankingReport:
    generated_at: datetime
    methodology_version: str
    methodology_summary: str
    advisory_only: bool
    performance_window_days: int
    ranking_count: int
    execution_ready_count: int
    high_potential_blocked_count: int
    market_data_status: str
    component_weights: dict[str, float]
    items: tuple[RankedOpportunity, ...]
    warnings: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "methodology_version": self.methodology_version,
            "methodology_summary": self.methodology_summary,
            "advisory_only": self.advisory_only,
            "performance_window_days": self.performance_window_days,
            "ranking_count": self.ranking_count,
            "execution_ready_count": self.execution_ready_count,
            "high_potential_blocked_count": (
                self.high_potential_blocked_count
            ),
            "market_data_status": self.market_data_status,
            "component_weights": dict(self.component_weights),
            "items": [item.to_dictionary() for item in self.items],
            "warnings": list(self.warnings),
        }
