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
        opportunity_ranking_runner: Callable[[], object] | None = None,
        opportunity_validation_runner: Callable[[], object] | None = None,
        universe_coverage_runner: (
            Callable[[tuple[str, ...], tuple[str, ...]], object] | None
        ) = None,
        now_provider: Callable[[], datetime] | None = None,
        stage_observer: Callable[[str], None] | None = None,
    ) -> None:
        self._news_cycle_runner = news_cycle_runner
        self._shadow_analysis_runner = shadow_analysis_runner
        self._shadow_performance_runner = shadow_performance_runner
        self._graduation_status_runner = graduation_status_runner
        self._intelligence_snapshot_runner = intelligence_snapshot_runner
        self._daily_briefing_runner = daily_briefing_runner
        self._opportunity_ranking_runner = opportunity_ranking_runner
        self._opportunity_validation_runner = opportunity_validation_runner
        self._universe_coverage_runner = universe_coverage_runner
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )
        self._stage_observer = stage_observer or (lambda stage: None)

    def run(self) -> IntelligenceCycleResult:
        stages: list[IntelligenceCycleStageResult] = []

        self._stage_observer("NEWS_RESEARCH")
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

        if self._universe_coverage_runner is not None:
            self._stage_observer("UNIVERSE_COVERAGE")
            try:
                coverage = self._universe_coverage_runner(
                    tuple(news_result.symbols),
                    tuple(observation.symbols),
                )
                coverage_warnings = tuple(
                    getattr(coverage, "warnings", ())
                )
                stages.append(
                    IntelligenceCycleStageResult(
                        stage="UNIVERSE_COVERAGE",
                        status=(
                            IntelligenceCycleStageStatus.SUCCEEDED_WITH_WARNINGS
                            if coverage_warnings
                            or getattr(coverage, "skipped_count", 0)
                            else IntelligenceCycleStageStatus.SUCCEEDED
                        ),
                        detail={
                            "version_id": coverage.version_id,
                            "requested_count": coverage.requested_count,
                            "processed_count": coverage.processed_count,
                            "skipped_count": coverage.skipped_count,
                            "coverage_percent": coverage.coverage_percent,
                        },
                        warnings=coverage_warnings,
                    )
                )
            except Exception as error:
                stages.append(
                    IntelligenceCycleStageResult(
                        stage="UNIVERSE_COVERAGE",
                        status=(
                            IntelligenceCycleStageStatus
                            .SUCCEEDED_WITH_WARNINGS
                        ),
                        detail={"coverage_percent": 0.0},
                        warnings=(
                            "Universe coverage was not captured: "
                            f"{type(error).__name__}: {error}",
                        ),
                    )
                )

        self._stage_observer("SHADOW_ANALYSIS")
        shadow = self._shadow_analysis_runner()
        stages.append(
            IntelligenceCycleStageResult(
                stage="SHADOW_ANALYSIS",
                status=IntelligenceCycleStageStatus.SUCCEEDED,
                detail=shadow.to_dictionary(),
            )
        )

        self._stage_observer("SHADOW_PERFORMANCE")
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

        self._stage_observer("GRADUATION_STATUS")
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

        self._stage_observer("INTELLIGENCE_SNAPSHOT")
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

        self._stage_observer("DAILY_BRIEFING")
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

        if self._opportunity_ranking_runner is not None:
            self._stage_observer("OPPORTUNITY_RANKING_HISTORY")
            try:
                ranking = self._opportunity_ranking_runner()
                stages.append(
                    IntelligenceCycleStageResult(
                        stage="OPPORTUNITY_RANKING_HISTORY",
                        status=IntelligenceCycleStageStatus.SUCCEEDED,
                        detail={
                            "ranking_count": ranking.ranking_count,
                            "execution_ready_count": (
                                ranking.execution_ready_count
                            ),
                            "methodology_version": (
                                ranking.methodology_version
                            ),
                        },
                    )
                )
            except Exception as error:
                stages.append(
                    IntelligenceCycleStageResult(
                        stage="OPPORTUNITY_RANKING_HISTORY",
                        status=(
                            IntelligenceCycleStageStatus
                            .SUCCEEDED_WITH_WARNINGS
                        ),
                        detail={"ranking_count": 0},
                        warnings=(
                            "Opportunity ranking history was not captured: "
                            f"{type(error).__name__}: {error}",
                        ),
                    )
                )

        if self._opportunity_validation_runner is not None:
            self._stage_observer("RANKING_FORWARD_RETURNS")
            try:
                validation = self._opportunity_validation_runner()
                validation_warnings = tuple(
                    getattr(validation, "warnings", ())
                )
                stages.append(
                    IntelligenceCycleStageResult(
                        stage="RANKING_FORWARD_RETURNS",
                        status=(
                            IntelligenceCycleStageStatus.SUCCEEDED_WITH_WARNINGS
                            if validation_warnings
                            else IntelligenceCycleStageStatus.SUCCEEDED
                        ),
                        detail={
                            "evaluated_snapshots": (
                                validation.evaluated_snapshot_count
                            ),
                            "outcomes_recorded": (
                                validation.created_outcome_count
                            ),
                            "pending_outcomes": (
                                validation.pending_outcome_count
                            ),
                            "failed_symbols": (
                                validation.failed_symbol_count
                            ),
                        },
                        warnings=validation_warnings,
                    )
                )
            except Exception as error:
                stages.append(
                    IntelligenceCycleStageResult(
                        stage="RANKING_FORWARD_RETURNS",
                        status=(
                            IntelligenceCycleStageStatus
                            .SUCCEEDED_WITH_WARNINGS
                        ),
                        detail={"outcomes_recorded": 0},
                        warnings=(
                            "Ranking forward returns were not captured: "
                            f"{type(error).__name__}: {error}",
                        ),
                    )
                )

        self._stage_observer("FINISHED")
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