from dataclasses import asdict, dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class OpportunityForwardOutcome:
    outcome_id: int
    snapshot_id: int
    captured_at: datetime
    symbol: str
    horizon_days: int
    entry_date: date
    exit_date: date
    observed_at: datetime
    entry_price: float
    observed_price: float
    return_percent: float
    benchmark_symbol: str
    benchmark_entry_price: float
    benchmark_observed_price: float
    benchmark_return_percent: float
    alpha_percent: float
    maximum_favourable_excursion_percent: float
    maximum_drawdown_percent: float
    status: str
    original_rank: int
    opportunity_score: float
    calibrated_confidence: float
    expected_return_percent: float | None
    evidence_coverage_percent: float
    eligible_for_execution: bool
    category: str
    sector: str
    historical_match_count: int
    measured_case_count: int
    universe_version_id: str | None = None
    universe_size: int | None = None

    def to_dictionary(self) -> dict[str, object]:
        return {
            "outcome_id": self.outcome_id,
            "snapshot_id": self.snapshot_id,
            "captured_at": self.captured_at.isoformat(),
            "symbol": self.symbol,
            "horizon_days": self.horizon_days,
            "entry_date": self.entry_date.isoformat(),
            "exit_date": self.exit_date.isoformat(),
            "observed_at": self.observed_at.isoformat(),
            "entry_price": self.entry_price,
            "observed_price": self.observed_price,
            "return_percent": self.return_percent,
            "benchmark_symbol": self.benchmark_symbol,
            "benchmark_entry_price": self.benchmark_entry_price,
            "benchmark_observed_price": self.benchmark_observed_price,
            "benchmark_return_percent": self.benchmark_return_percent,
            "alpha_percent": self.alpha_percent,
            "maximum_favourable_excursion_percent": (
                self.maximum_favourable_excursion_percent
            ),
            "maximum_drawdown_percent": self.maximum_drawdown_percent,
            "status": self.status,
            "original_rank": self.original_rank,
            "opportunity_score": self.opportunity_score,
            "calibrated_confidence": self.calibrated_confidence,
            "expected_return_percent": self.expected_return_percent,
            "evidence_coverage_percent": self.evidence_coverage_percent,
            "eligible_for_execution": self.eligible_for_execution,
            "category": self.category,
            "sector": self.sector,
            "historical_match_count": self.historical_match_count,
            "measured_case_count": self.measured_case_count,
            "universe_version_id": self.universe_version_id,
            "universe_size": self.universe_size,
        }


@dataclass(frozen=True)
class OpportunityValidationCaptureResult:
    evaluated_snapshot_count: int
    created_outcome_count: int
    existing_outcome_count: int
    pending_outcome_count: int
    failed_symbol_count: int
    failed_symbols: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            **asdict(self),
            "failed_symbols": list(self.failed_symbols),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class OpportunityValidationBucket:
    code: str
    label: str
    sample_count: int
    positive_count: int
    hit_rate_percent: float | None
    average_return_percent: float | None
    median_return_percent: float | None
    average_alpha_percent: float | None
    median_alpha_percent: float | None
    average_drawdown_percent: float | None

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OpportunityValidationHorizon:
    horizon_days: int
    label: str
    sample_count: int
    pending_count: int
    positive_count: int
    hit_rate_percent: float | None
    average_return_percent: float | None
    median_return_percent: float | None
    average_alpha_percent: float | None
    median_alpha_percent: float | None
    average_drawdown_percent: float | None
    top_three_average_return_percent: float | None
    other_average_return_percent: float | None
    score_return_correlation: float | None
    rank_return_correlation: float | None
    maturity: str

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OpportunityRankingValidationReport:
    generated_at: datetime
    methodology_version: str
    methodology_summary: str
    advisory_only: bool
    benchmark_symbol: str
    selected_horizon_days: int
    available_horizons: tuple[int, ...]
    tracked_snapshot_count: int
    measured_outcome_count: int
    pending_outcome_count: int
    latest_observed_at: datetime | None
    selected_horizon: OpportunityValidationHorizon
    horizons: tuple[OpportunityValidationHorizon, ...]
    score_bands: tuple[OpportunityValidationBucket, ...]
    rank_buckets: tuple[OpportunityValidationBucket, ...]
    readiness_buckets: tuple[OpportunityValidationBucket, ...]
    symbol_performance: tuple[OpportunityValidationBucket, ...]
    sector_performance: tuple[OpportunityValidationBucket, ...]
    latest_outcomes: tuple[OpportunityForwardOutcome, ...]
    warnings: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "methodology_version": self.methodology_version,
            "methodology_summary": self.methodology_summary,
            "advisory_only": self.advisory_only,
            "benchmark_symbol": self.benchmark_symbol,
            "selected_horizon_days": self.selected_horizon_days,
            "available_horizons": list(self.available_horizons),
            "tracked_snapshot_count": self.tracked_snapshot_count,
            "measured_outcome_count": self.measured_outcome_count,
            "pending_outcome_count": self.pending_outcome_count,
            "latest_observed_at": (
                None
                if self.latest_observed_at is None
                else self.latest_observed_at.isoformat()
            ),
            "selected_horizon": self.selected_horizon.to_dictionary(),
            "horizons": [item.to_dictionary() for item in self.horizons],
            "score_bands": [item.to_dictionary() for item in self.score_bands],
            "rank_buckets": [item.to_dictionary() for item in self.rank_buckets],
            "readiness_buckets": [
                item.to_dictionary() for item in self.readiness_buckets
            ],
            "symbol_performance": [
                item.to_dictionary() for item in self.symbol_performance
            ],
            "sector_performance": [
                item.to_dictionary() for item in self.sector_performance
            ],
            "latest_outcomes": [
                item.to_dictionary() for item in self.latest_outcomes
            ],
            "warnings": list(self.warnings),
        }
