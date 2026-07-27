from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SimilarityFeatureComparison:
    code: str
    label: str
    current_value: str
    historical_value: str
    similarity_percent: float
    weight: float
    contribution_points: float

    def to_dictionary(self) -> dict[str, object]:
        return {
            "code": self.code,
            "label": self.label,
            "current_value": self.current_value,
            "historical_value": self.historical_value,
            "similarity_percent": self.similarity_percent,
            "weight": self.weight,
            "contribution_points": self.contribution_points,
        }


@dataclass(frozen=True)
class SimilarityOutcome:
    horizon_days: int
    observed_at: datetime
    raw_return_percent: float
    directional_return_percent: float
    alpha_percent: float
    maximum_favourable_excursion_percent: float
    maximum_drawdown_percent: float
    directional_success: bool
    status: str

    def to_dictionary(self) -> dict[str, object]:
        return {
            "horizon_days": self.horizon_days,
            "observed_at": self.observed_at.isoformat(),
            "raw_return_percent": self.raw_return_percent,
            "directional_return_percent": self.directional_return_percent,
            "alpha_percent": self.alpha_percent,
            "maximum_favourable_excursion_percent": (
                self.maximum_favourable_excursion_percent
            ),
            "maximum_drawdown_percent": self.maximum_drawdown_percent,
            "directional_success": self.directional_success,
            "status": self.status,
        }


@dataclass(frozen=True)
class HistoricalSimilarityCase:
    decision_id: str
    symbol: str
    captured_at: datetime
    thesis_generated_at: datetime
    recommendation: str
    score: float
    confidence: float
    risk_tier: str
    time_horizon: str
    headline: str
    primary_driver: str
    similarity_percent: float
    same_symbol: bool
    matching_factors: tuple[str, ...]
    differing_factors: tuple[str, ...]
    feature_comparisons: tuple[SimilarityFeatureComparison, ...]
    outcome: SimilarityOutcome | None

    def to_dictionary(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "symbol": self.symbol,
            "captured_at": self.captured_at.isoformat(),
            "thesis_generated_at": self.thesis_generated_at.isoformat(),
            "recommendation": self.recommendation,
            "score": self.score,
            "confidence": self.confidence,
            "risk_tier": self.risk_tier,
            "time_horizon": self.time_horizon,
            "headline": self.headline,
            "primary_driver": self.primary_driver,
            "similarity_percent": self.similarity_percent,
            "same_symbol": self.same_symbol,
            "matching_factors": list(self.matching_factors),
            "differing_factors": list(self.differing_factors),
            "feature_comparisons": [
                item.to_dictionary() for item in self.feature_comparisons
            ],
            "outcome": self.outcome.to_dictionary() if self.outcome else None,
        }


@dataclass(frozen=True)
class HistoricalSimilarityReport:
    generated_at: datetime
    symbol: str
    current_thesis_id: str
    current_recommendation: str
    current_score: float
    current_confidence: float
    current_risk_tier: str
    current_time_horizon: str
    current_primary_driver: str
    methodology_version: str
    methodology_summary: str
    minimum_similarity_percent: float
    target_horizon_days: int
    candidate_count: int
    matched_case_count: int
    measured_case_count: int
    sample_quality: str
    average_similarity_percent: float | None
    win_rate_percent: float | None
    average_return_percent: float | None
    median_return_percent: float | None
    average_directional_return_percent: float | None
    average_alpha_percent: float | None
    best_directional_return_percent: float | None
    worst_directional_return_percent: float | None
    average_holding_days: float | None
    cases: tuple[HistoricalSimilarityCase, ...]
    warnings: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "symbol": self.symbol,
            "current_thesis_id": self.current_thesis_id,
            "current_recommendation": self.current_recommendation,
            "current_score": self.current_score,
            "current_confidence": self.current_confidence,
            "current_risk_tier": self.current_risk_tier,
            "current_time_horizon": self.current_time_horizon,
            "current_primary_driver": self.current_primary_driver,
            "methodology_version": self.methodology_version,
            "methodology_summary": self.methodology_summary,
            "minimum_similarity_percent": self.minimum_similarity_percent,
            "target_horizon_days": self.target_horizon_days,
            "candidate_count": self.candidate_count,
            "matched_case_count": self.matched_case_count,
            "measured_case_count": self.measured_case_count,
            "sample_quality": self.sample_quality,
            "average_similarity_percent": self.average_similarity_percent,
            "win_rate_percent": self.win_rate_percent,
            "average_return_percent": self.average_return_percent,
            "median_return_percent": self.median_return_percent,
            "average_directional_return_percent": (
                self.average_directional_return_percent
            ),
            "average_alpha_percent": self.average_alpha_percent,
            "best_directional_return_percent": (
                self.best_directional_return_percent
            ),
            "worst_directional_return_percent": (
                self.worst_directional_return_percent
            ),
            "average_holding_days": self.average_holding_days,
            "cases": [item.to_dictionary() for item in self.cases],
            "warnings": list(self.warnings),
        }
