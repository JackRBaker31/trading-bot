from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class CopilotDecisionSnapshot:
    snapshot_id: str
    captured_at: datetime
    overall_status: str
    platform_status: str
    trading_readiness: str
    market_outlook: str
    confidence: float
    signal_count: int
    actionable_signal_count: int
    evidence_quality: str
    graduation_ready: bool
    graduation_passed_checks: int
    graduation_total_checks: int
    graduation_failed_checks: int
    decision: str
    blockers: tuple[str, ...] = field(default_factory=tuple)

    def to_dictionary(self) -> dict[str, object]:
        payload = asdict(self)
        payload["captured_at"] = self.captured_at.isoformat()
        payload["blockers"] = list(self.blockers)
        return payload


@dataclass(frozen=True)
class CopilotMetricChange:
    metric: str
    previous: float
    current: float
    change: float
    direction: str

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CopilotChangeSummary:
    generated_at: datetime
    comparison_available: bool
    current: CopilotDecisionSnapshot
    previous: CopilotDecisionSnapshot | None
    confidence_change: CopilotMetricChange | None
    signal_count_change: CopilotMetricChange | None
    actionable_signal_change: CopilotMetricChange | None
    graduation_passed_change: CopilotMetricChange | None
    new_blockers: tuple[str, ...] = field(default_factory=tuple)
    cleared_blockers: tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""

    def to_dictionary(self) -> dict[str, object]:
        def item(value):
            return None if value is None else value.to_dictionary()

        return {
            "generated_at": self.generated_at.isoformat(),
            "comparison_available": self.comparison_available,
            "current": self.current.to_dictionary(),
            "previous": item(self.previous),
            "confidence_change": item(self.confidence_change),
            "signal_count_change": item(self.signal_count_change),
            "actionable_signal_change": item(self.actionable_signal_change),
            "graduation_passed_change": item(self.graduation_passed_change),
            "new_blockers": list(self.new_blockers),
            "cleared_blockers": list(self.cleared_blockers),
            "summary": self.summary,
        }
