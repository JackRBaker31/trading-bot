from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class ConfidenceBandPerformance:
    band: str
    sample_count: int
    predicted_midpoint: float
    positive_rate: float | None
    average_return: float | None
    average_alpha: float | None
    calibration_gap: float | None

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PerformanceIntelligence:
    observation_count: int
    tracked_decision_count: int
    positive_rate: float | None
    average_return: float | None
    average_alpha: float | None
    best_horizon_days: int | None
    confidence_bands: tuple[
        ConfidenceBandPerformance,
        ...
    ]
    learning_confidence: float
    findings: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "observation_count": self.observation_count,
            "tracked_decision_count": self.tracked_decision_count,
            "positive_rate": self.positive_rate,
            "average_return": self.average_return,
            "average_alpha": self.average_alpha,
            "best_horizon_days": self.best_horizon_days,
            "confidence_bands": [
                item.to_dictionary()
                for item in self.confidence_bands
            ],
            "learning_confidence": self.learning_confidence,
            "findings": list(self.findings),
        }


@dataclass(frozen=True)
class PortfolioAllocation:
    symbol: str
    recommendation: str
    raw_weight: float
    constrained_weight: float
    suggested_value: float
    score: float
    confidence: float
    risk_tier: str
    reasons: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            **asdict(self),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class PortfolioOptimisation:
    available_cash: float
    investable_cash: float
    maximum_symbol_weight: float
    allocations: tuple[
        PortfolioAllocation,
        ...
    ]
    unallocated_cash: float
    warnings: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "available_cash": self.available_cash,
            "investable_cash": self.investable_cash,
            "maximum_symbol_weight": self.maximum_symbol_weight,
            "allocations": [
                item.to_dictionary()
                for item in self.allocations
            ],
            "unallocated_cash": self.unallocated_cash,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class RiskContribution:
    code: str
    label: str
    contribution: float
    severity: str
    detail: str

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RiskAttribution:
    overall_risk_score: float
    overall_tier: str
    contributions: tuple[
        RiskContribution,
        ...
    ]
    dominant_risk: str | None
    warnings: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "overall_risk_score": self.overall_risk_score,
            "overall_tier": self.overall_tier,
            "contributions": [
                item.to_dictionary()
                for item in self.contributions
            ],
            "dominant_risk": self.dominant_risk,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class PositionSizeRecommendation:
    symbol: str
    base_value: float
    calibrated_value: float
    maximum_value: float
    score_multiplier: float
    confidence_multiplier: float
    risk_multiplier: float
    calibration_multiplier: float
    eligible: bool
    reasons: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            **asdict(self),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class CommitteeVote:
    agent: str
    stance: str
    confidence: float
    score: float | None
    summary: str
    evidence: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            **asdict(self),
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class InvestmentCommitteeDecision:
    symbol: str
    final_stance: str
    consensus_score: float
    disagreement_score: float
    confidence: float
    votes: tuple[
        CommitteeVote,
        ...
    ]
    blockers: tuple[str, ...]
    summary: str

    def to_dictionary(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "final_stance": self.final_stance,
            "consensus_score": self.consensus_score,
            "disagreement_score": self.disagreement_score,
            "confidence": self.confidence,
            "votes": [
                item.to_dictionary()
                for item in self.votes
            ],
            "blockers": list(self.blockers),
            "summary": self.summary,
        }


@dataclass(frozen=True)
class StrategyEvolutionProposal:
    proposal_id: str
    created_at: datetime
    status: str
    title: str
    rationale: str
    target: str
    current_value: float | None
    proposed_value: float | None
    evidence: tuple[str, ...]
    safeguards: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "title": self.title,
            "rationale": self.rationale,
            "target": self.target,
            "current_value": self.current_value,
            "proposed_value": self.proposed_value,
            "evidence": list(self.evidence),
            "safeguards": list(self.safeguards),
        }


@dataclass(frozen=True)
class AdaptiveIntelligenceReport:
    generated_at: datetime
    performance: PerformanceIntelligence
    portfolio: PortfolioOptimisation
    risk: RiskAttribution
    position_sizes: tuple[
        PositionSizeRecommendation,
        ...
    ]
    committee: tuple[
        InvestmentCommitteeDecision,
        ...
    ]
    proposals: tuple[
        StrategyEvolutionProposal,
        ...
    ]
    execution_mode: str
    warnings: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "performance": self.performance.to_dictionary(),
            "portfolio": self.portfolio.to_dictionary(),
            "risk": self.risk.to_dictionary(),
            "position_sizes": [
                item.to_dictionary()
                for item in self.position_sizes
            ],
            "committee": [
                item.to_dictionary()
                for item in self.committee
            ],
            "proposals": [
                item.to_dictionary()
                for item in self.proposals
            ],
            "execution_mode": self.execution_mode,
            "warnings": list(self.warnings),
        }
