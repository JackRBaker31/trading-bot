from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Mapping


class IntelligenceCycleStageStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    SUCCEEDED_WITH_WARNINGS = "SUCCEEDED_WITH_WARNINGS"


@dataclass(frozen=True)
class IntelligenceCycleStageResult:
    stage: str
    status: IntelligenceCycleStageStatus
    detail: Mapping[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def to_dictionary(self) -> dict[str, object]:
        return {
            "stage": self.stage,
            "status": self.status.value,
            "detail": dict(self.detail),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class IntelligenceCycleResult:
    generated_at: datetime
    stages: tuple[IntelligenceCycleStageResult, ...]

    @property
    def has_warnings(self) -> bool:
        return any(
            stage.status
            is IntelligenceCycleStageStatus.SUCCEEDED_WITH_WARNINGS
            for stage in self.stages
        )

    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "status": (
                "SUCCEEDED_WITH_WARNINGS"
                if self.has_warnings
                else "SUCCEEDED"
            ),
            "stage_count": len(self.stages),
            "stages": [stage.to_dictionary() for stage in self.stages],
            "trading_impact": "NONE",
        }


class IntelligenceCycleService:
    """Runs the research-only intelligence pipeline in a fixed order.

    The news-research cycle already captures reference prices and due outcomes.
    It is invoked once and represented as two stage results to keep provider
    requests bounded and preserve the existing research implementation.
    """

    def __init__(
        self,
        *,
        news_cycle_runner: Callable[[], object],
        shadow_analysis_runner: Callable[[], object],
        shadow_performance_runner: Callable[[], object],
        graduation_status_runner: Callable[[], object],
        intelligence_snapshot_runner: Callable[[], object],
        daily_briefing_runner: Callable[[], object],
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._news_cycle_runner = news_cycle_runner
        self._shadow_analysis_runner = shadow_analysis_runner
        self._shadow_performance_runner = shadow_performance_runner
        self._graduation_status_runner = graduation_status_runner
        self._intelligence_snapshot_runner = intelligence_snapshot_runner
        self._daily_briefing_runner = daily_briefing_runner
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )

    def run(self) -> IntelligenceCycleResult:
        stages: list[IntelligenceCycleStageResult] = []

        news_result = self._news_cycle_runner()
        observation = news_result.observation_summary
        snapshot = news_result.snapshot_summary
        outcome = news_result.outcome_summary

        stages.append(
            IntelligenceCycleStageResult(
                stage="NEWS_RESEARCH",
                status=IntelligenceCycleStageStatus.SUCCEEDED,
                detail={
                    "provider": news_result.provider_name,
                    "symbols": list(news_result.symbols),
                    "articles_fetched": observation.article_count,
                    "signals_stored": observation.signal_count,
                },
            )
        )

        outcome_warnings: list[str] = []
        failure_count = (
            (0 if snapshot is None else snapshot.failed_count)
            + (0 if outcome is None else outcome.failed_count)
        )
        stale_count = (
            0 if outcome is None else outcome.stale_quote_count
        )
        if failure_count:
            outcome_warnings.append(
                f"{failure_count} price operations failed or were deferred."
            )
        if stale_count:
            outcome_warnings.append(
                f"{stale_count} due outcomes were deferred because quotes were stale."
            )
        stages.append(
            IntelligenceCycleStageResult(
                stage="CAPTURE_PRICE_OUTCOMES",
                status=(
                    IntelligenceCycleStageStatus.SUCCEEDED_WITH_WARNINGS
                    if outcome_warnings
                    else IntelligenceCycleStageStatus.SUCCEEDED
                ),
                detail={
                    "snapshots_captured": (
                        0 if snapshot is None else snapshot.captured_count
                    ),
                    "outcomes_recorded": (
                        0 if outcome is None else outcome.recorded_count
                    ),
                    "failure_count": failure_count,
                    "stale_outcomes_deferred": stale_count,
                },
                warnings=tuple(outcome_warnings),
            )
        )

        shadow = self._shadow_analysis_runner()
        stages.append(
            IntelligenceCycleStageResult(
                stage="SHADOW_ANALYSIS",
                status=IntelligenceCycleStageStatus.SUCCEEDED,
                detail=shadow.to_dictionary(),
            )
        )

        performance = self._shadow_performance_runner()
        one_day = next(
            horizon
            for horizon in performance.horizons
            if horizon.horizon == "1D"
        )
        stages.append(
            IntelligenceCycleStageResult(
                stage="SHADOW_PERFORMANCE",
                status=IntelligenceCycleStageStatus.SUCCEEDED,
                detail={
                    "total_decisions": performance.total_decision_count,
                    "measured_1d_decisions": one_day.measured_count,
                    "directional_success_percent": (
                        one_day.directional_success_percent
                    ),
                    "profitable_after_cost_percent": (
                        one_day.profitable_after_cost_percent
                    ),
                },
            )
        )

        graduation = self._graduation_status_runner()
        stages.append(
            IntelligenceCycleStageResult(
                stage="GRADUATION_STATUS",
                status=IntelligenceCycleStageStatus.SUCCEEDED,
                detail={
                    "status": graduation.status,
                    "eligible": graduation.eligible,
                    "checks_passed": graduation.checks_passed,
                    "total_checks": graduation.total_checks,
                },
            )
        )

        intelligence = self._intelligence_snapshot_runner()
        stages.append(
            IntelligenceCycleStageResult(
                stage="INTELLIGENCE_SNAPSHOT",
                status=IntelligenceCycleStageStatus.SUCCEEDED,
                detail={
                    "market_outlook": intelligence.market_outlook.value,
                    "confidence": intelligence.confidence,
                    "trading_readiness": (
                        intelligence.trading_readiness.value
                    ),
                    "evidence_quality": (
                        intelligence.evidence_quality.value
                    ),
                    "signal_count": intelligence.signal_count,
                    "opportunity_count": len(
                        intelligence.top_opportunities
                    ),
                    "is_stale": intelligence.freshness.is_stale,
                },
            )
        )

        briefing = self._daily_briefing_runner()
        stages.append(
            IntelligenceCycleStageResult(
                stage="DAILY_BRIEFING",
                status=IntelligenceCycleStageStatus.SUCCEEDED,
                detail={
                    "headline": briefing.headline,
                    "market_outlook": briefing.market_outlook,
                    "trading_readiness": briefing.trading_readiness,
                    "graduation_status": briefing.graduation_status,
                    "is_stale": briefing.is_stale,
                    "action_count": len(briefing.actions),
                    "warning_count": len(briefing.warnings),
                },
            )
        )

        return IntelligenceCycleResult(
            generated_at=self._utc_now(),
            stages=tuple(stages),
        )

    def _utc_now(self) -> datetime:
        value = self._now_provider()
        if value.tzinfo is None:
            raise ValueError(
                "Intelligence-cycle clock must be timezone-aware."
            )
        return value.astimezone(timezone.utc)