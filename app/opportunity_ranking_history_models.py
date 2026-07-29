from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class OpportunityRankingSnapshot:
    snapshot_id: int
    captured_at: datetime
    last_observed_at: datetime
    source: str
    methodology_version: str
    symbol: str
    rank: int
    opportunity_score: float
    category: str
    recommendation: str
    calibrated_confidence: float
    expected_return_percent: float | None
    evidence_coverage_percent: float
    data_quality: str
    risk_tier: str
    eligible_for_execution: bool
    historical_match_count: int
    measured_case_count: int
    sector: str
    headline: str
    component_values: dict[str, float]
    component_labels: dict[str, str]
    blockers: tuple[str, ...]
    universe_version_id: str | None = None
    universe_size: int | None = None

    def to_dictionary(self) -> dict[str, object]:
        return {
            "snapshot_id": self.snapshot_id,
            "captured_at": self.captured_at.isoformat(),
            "last_observed_at": self.last_observed_at.isoformat(),
            "source": self.source,
            "methodology_version": self.methodology_version,
            "symbol": self.symbol,
            "rank": self.rank,
            "opportunity_score": self.opportunity_score,
            "category": self.category,
            "recommendation": self.recommendation,
            "calibrated_confidence": self.calibrated_confidence,
            "expected_return_percent": self.expected_return_percent,
            "evidence_coverage_percent": self.evidence_coverage_percent,
            "data_quality": self.data_quality,
            "risk_tier": self.risk_tier,
            "eligible_for_execution": self.eligible_for_execution,
            "historical_match_count": self.historical_match_count,
            "measured_case_count": self.measured_case_count,
            "sector": self.sector,
            "headline": self.headline,
            "component_values": dict(self.component_values),
            "component_labels": dict(self.component_labels),
            "blockers": list(self.blockers),
            "universe_version_id": self.universe_version_id,
            "universe_size": self.universe_size,
        }


@dataclass(frozen=True)
class OpportunityRankingCaptureResult:
    observed_count: int
    inserted_count: int
    unchanged_count: int

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OpportunityRankingChange:
    captured_at: datetime
    previous_captured_at: datetime | None
    score_change: float
    rank_change: int
    direction: str
    summary: str
    component_changes: tuple[dict[str, object], ...]
    blockers_added: tuple[str, ...]
    blockers_resolved: tuple[str, ...]
    readiness_changed: bool
    previous_eligible_for_execution: bool | None
    eligible_for_execution: bool

    def to_dictionary(self) -> dict[str, object]:
        return {
            "captured_at": self.captured_at.isoformat(),
            "previous_captured_at": (
                None
                if self.previous_captured_at is None
                else self.previous_captured_at.isoformat()
            ),
            "score_change": self.score_change,
            "rank_change": self.rank_change,
            "direction": self.direction,
            "summary": self.summary,
            "component_changes": [dict(item) for item in self.component_changes],
            "blockers_added": list(self.blockers_added),
            "blockers_resolved": list(self.blockers_resolved),
            "readiness_changed": self.readiness_changed,
            "previous_eligible_for_execution": self.previous_eligible_for_execution,
            "eligible_for_execution": self.eligible_for_execution,
        }


@dataclass(frozen=True)
class OpportunitySymbolHistoryReport:
    generated_at: datetime
    symbol: str
    window_days: int
    first_seen_at: datetime | None
    last_observed_at: datetime | None
    snapshot_count: int
    current_rank: int | None
    current_score: float | None
    score_change: float
    rank_change: int
    streak_direction: str
    snapshots: tuple[OpportunityRankingSnapshot, ...]
    changes: tuple[OpportunityRankingChange, ...]
    universe_versions: tuple[str, ...] = ()
    rank_comparability_warning: str | None = None

    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "symbol": self.symbol,
            "window_days": self.window_days,
            "first_seen_at": (
                None if self.first_seen_at is None else self.first_seen_at.isoformat()
            ),
            "last_observed_at": (
                None
                if self.last_observed_at is None
                else self.last_observed_at.isoformat()
            ),
            "snapshot_count": self.snapshot_count,
            "current_rank": self.current_rank,
            "current_score": self.current_score,
            "score_change": self.score_change,
            "rank_change": self.rank_change,
            "streak_direction": self.streak_direction,
            "snapshots": [snapshot.to_dictionary() for snapshot in self.snapshots],
            "changes": [change.to_dictionary() for change in self.changes],
            "universe_versions": list(self.universe_versions),
            "rank_comparability_warning": self.rank_comparability_warning,
        }


@dataclass(frozen=True)
class OpportunityHistoryOverviewItem:
    symbol: str
    current_rank: int
    current_score: float
    score_change: float
    rank_change: int
    eligible_for_execution: bool
    category: str
    last_observed_at: datetime

    def to_dictionary(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "current_rank": self.current_rank,
            "current_score": self.current_score,
            "score_change": self.score_change,
            "rank_change": self.rank_change,
            "eligible_for_execution": self.eligible_for_execution,
            "category": self.category,
            "last_observed_at": self.last_observed_at.isoformat(),
        }


@dataclass(frozen=True)
class OpportunityHistoryOverviewReport:
    generated_at: datetime
    window_days: int
    tracked_symbol_count: int
    snapshot_count: int
    latest_observed_at: datetime | None
    largest_risers: tuple[OpportunityHistoryOverviewItem, ...]
    largest_fallers: tuple[OpportunityHistoryOverviewItem, ...]
    items: tuple[OpportunityHistoryOverviewItem, ...]
    universe_versions: tuple[str, ...] = ()
    rank_comparability_warning: str | None = None

    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "window_days": self.window_days,
            "tracked_symbol_count": self.tracked_symbol_count,
            "snapshot_count": self.snapshot_count,
            "latest_observed_at": (
                None
                if self.latest_observed_at is None
                else self.latest_observed_at.isoformat()
            ),
            "largest_risers": [item.to_dictionary() for item in self.largest_risers],
            "largest_fallers": [item.to_dictionary() for item in self.largest_fallers],
            "items": [item.to_dictionary() for item in self.items],
            "universe_versions": list(self.universe_versions),
            "rank_comparability_warning": self.rank_comparability_warning,
        }
