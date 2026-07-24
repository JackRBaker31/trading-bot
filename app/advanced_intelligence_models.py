from dataclasses import asdict, dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class MarketRegimeAssessment:
    as_of_date: date
    regime: str
    trend_state: str
    volatility_state: str
    risk_state: str
    score: float
    confidence: float
    buy_threshold: float
    position_multiplier: float
    evidence: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "as_of_date": self.as_of_date.isoformat(),
            "regime": self.regime,
            "trend_state": self.trend_state,
            "volatility_state": self.volatility_state,
            "risk_state": self.risk_state,
            "score": self.score,
            "confidence": self.confidence,
            "buy_threshold": self.buy_threshold,
            "position_multiplier": self.position_multiplier,
            "evidence": list(self.evidence),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class TimeframeAssessment:
    timeframe: str
    bar_count: int
    score: float
    confidence: float
    stance: str
    trend: str
    momentum: str
    latest_close: float
    evidence: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            **asdict(self),
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class MultiTimeframeAssessment:
    symbol: str
    as_of_date: date
    composite_score: float
    confidence: float
    alignment: str
    conflict_penalty: float
    assessments: tuple[
        TimeframeAssessment,
        ...
    ]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "as_of_date": self.as_of_date.isoformat(),
            "composite_score": self.composite_score,
            "confidence": self.confidence,
            "alignment": self.alignment,
            "conflict_penalty": self.conflict_penalty,
            "assessments": [
                item.to_dictionary()
                for item in self.assessments
            ],
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class ExplanationContribution:
    code: str
    label: str
    contribution: float
    direction: str
    source: str
    detail: str

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ExplainableDecision:
    symbol: str
    recommendation: str
    raw_score: float
    adjusted_score: float
    raw_confidence: float
    calibrated_confidence: float
    regime: str
    timeframe_alignment: str
    contributions: tuple[
        ExplanationContribution,
        ...
    ]
    blockers: tuple[str, ...]
    summary: str

    def to_dictionary(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "recommendation": self.recommendation,
            "raw_score": self.raw_score,
            "adjusted_score": self.adjusted_score,
            "raw_confidence": self.raw_confidence,
            "calibrated_confidence": self.calibrated_confidence,
            "regime": self.regime,
            "timeframe_alignment": self.timeframe_alignment,
            "contributions": [
                item.to_dictionary()
                for item in self.contributions
            ],
            "blockers": list(self.blockers),
            "summary": self.summary,
        }


@dataclass(frozen=True)
class BayesianCalibrationResult:
    prior_alpha: float
    prior_beta: float
    successes: int
    failures: int
    posterior_alpha: float
    posterior_beta: float
    posterior_mean: float
    credible_lower: float
    credible_upper: float
    sample_count: int
    confidence_weight: float

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AdvancedIntelligenceReport:
    generated_at: datetime
    execution_mode: str
    regime: MarketRegimeAssessment
    multi_timeframe: tuple[
        MultiTimeframeAssessment,
        ...
    ]
    decisions: tuple[
        ExplainableDecision,
        ...
    ]
    calibration: BayesianCalibrationResult
    warnings: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "execution_mode": self.execution_mode,
            "regime": self.regime.to_dictionary(),
            "multi_timeframe": [
                item.to_dictionary()
                for item in self.multi_timeframe
            ],
            "decisions": [
                item.to_dictionary()
                for item in self.decisions
            ],
            "calibration": self.calibration.to_dictionary(),
            "warnings": list(self.warnings),
        }
