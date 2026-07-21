from app.daily_briefing import (
    BriefingAction,
    BriefingActionType,
    BriefingPriority,
    DailyBriefing,
)
from app.intelligence_snapshot import (
    IntelligenceOpportunity,
    IntelligenceSnapshot,
)
from app.shadow_performance import (
    ShadowPerformanceReport,
)


class DailyBriefingService:
    def __init__(
        self,
        *,
        intelligence_service,
        shadow_performance_service,
        graduation_service,
    ) -> None:
        self._intelligence_service = (
            intelligence_service
        )
        self._shadow_performance_service = (
            shadow_performance_service
        )
        self._graduation_service = graduation_service

    def get_briefing(self) -> DailyBriefing:
        snapshot = (
            self._intelligence_service.get_snapshot()
        )
        performance = (
            self._shadow_performance_service
            .get_report()
        )
        graduation = (
            self._graduation_service.get_status()
        )

        top = (
            None
            if not snapshot.top_opportunities
            else snapshot.top_opportunities[0]
        )
        one_day = next(
            horizon
            for horizon in performance.horizons
            if horizon.horizon == "1D"
        )

        return DailyBriefing(
            generated_at=snapshot.generated_at,
            headline=self._headline(snapshot),
            summary=self._summary(
                snapshot=snapshot,
                performance=performance,
                graduation_status=graduation.status,
            ),
            market_outlook=(
                snapshot.market_outlook.value
            ),
            confidence=snapshot.confidence,
            trading_readiness=(
                snapshot.trading_readiness.value
            ),
            evidence_quality=(
                snapshot.evidence_quality.value
            ),
            graduation_status=graduation.status,
            graduation_checks_passed=(
                graduation.checks_passed
            ),
            graduation_total_checks=(
                graduation.total_checks
            ),
            top_opportunity=(
                None
                if top is None
                else self._top_opportunity(top)
            ),
            key_points=self._key_points(
                snapshot=snapshot,
                performance=performance,
                measured_1d=one_day.measured_count,
                directional_success=(
                    one_day
                    .directional_success_percent
                ),
            ),
            warnings=self._warnings(
                snapshot=snapshot,
                graduation_failed_checks=(
                    graduation.failed_checks
                ),
            ),
            actions=self._actions(
                snapshot=snapshot,
                performance=performance,
                top=top,
                graduation_eligible=(
                    graduation.eligible
                ),
            ),
            is_stale=snapshot.freshness.is_stale,
        )

    @staticmethod
    def _headline(
        snapshot: IntelligenceSnapshot,
    ) -> str:
        labels = {
            "PROMISING": "KAIRO sees a promising outlook",
            "CAUTIOUS": "KAIRO is cautious",
            "UNFAVOURABLE": (
                "KAIRO sees an unfavourable outlook"
            ),
            "INSUFFICIENT_DATA": (
                "KAIRO needs more current evidence"
            ),
        }
        return labels[
            snapshot.market_outlook.value
        ]

    @staticmethod
    def _summary(
        *,
        snapshot: IntelligenceSnapshot,
        performance: ShadowPerformanceReport,
        graduation_status: str,
    ) -> str:
        verdict = (
            "No current strategy verdict is available"
            if snapshot.research_verdict is None
            else (
                "The latest strategy verdict is "
                f"{snapshot.research_verdict}"
            )
        )

        if graduation_status == "RESEARCH_ONLY":
            evidence = (
                "the intelligence layer remains "
                "research-only while more shadow "
                "evidence is collected"
            )
        else:
            evidence = (
                "the evidence threshold has passed "
                "and is ready for controlled review"
            )

        return (
            f"{verdict}; {evidence}. "
            f"KAIRO currently tracks "
            f"{snapshot.signal_count} signals and "
            f"{performance.total_decision_count} "
            "shadow decisions."
        )

    @staticmethod
    def _top_opportunity(
        opportunity: IntelligenceOpportunity,
    ) -> dict[str, object]:
        return {
            "article_id": opportunity.article_id,
            "symbol": opportunity.symbol,
            "classification": (
                opportunity.classification.value
            ),
            "score": opportunity.score,
            "confidence": opportunity.confidence,
            "headline": opportunity.headline,
            "eligible_for_trade": (
                opportunity.eligible_for_trade
            ),
            "reasons": list(opportunity.reasons),
            "blocking_reasons": list(
                opportunity.blocking_reasons
            ),
        }

    @staticmethod
    def _key_points(
        *,
        snapshot: IntelligenceSnapshot,
        performance: ShadowPerformanceReport,
        measured_1d: int,
        directional_success: float,
    ) -> tuple[str, ...]:
        points = [
            (
                f"{snapshot.signal_count} active "
                "news signals are being tracked."
            ),
            (
                f"{snapshot.actionable_signal_count} "
                "current signals meet the initial "
                "actionable threshold."
            ),
            (
                f"{performance.total_decision_count} "
                "shadow decisions have been recorded."
            ),
            (
                f"{measured_1d} shadow decisions have "
                "completed a 1D measurement."
            ),
        ]

        if measured_1d > 0:
            points.append(
                "Measured 1D directional success is "
                f"{directional_success:.2f}%."
            )

        return tuple(points)

    @staticmethod
    def _warnings(
        *,
        snapshot: IntelligenceSnapshot,
        graduation_failed_checks: tuple[str, ...],
    ) -> tuple[str, ...]:
        warnings = list(snapshot.risk_warnings)
        warnings.extend(
            snapshot.freshness.stale_reasons
        )
        warnings.extend(
            graduation_failed_checks[:3]
        )
        return tuple(dict.fromkeys(warnings))

    @staticmethod
    def _actions(
        *,
        snapshot: IntelligenceSnapshot,
        performance: ShadowPerformanceReport,
        top: IntelligenceOpportunity | None,
        graduation_eligible: bool,
    ) -> tuple[BriefingAction, ...]:
        actions: list[BriefingAction] = []

        if snapshot.freshness.is_stale:
            actions.append(
                BriefingAction(
                    action=(
                        BriefingActionType
                        .RUN_NEWS_RESEARCH
                    ),
                    priority=BriefingPriority.HIGH,
                    label="Refresh news research",
                    reason=(
                        "Current intelligence data is "
                        "stale."
                    ),
                    endpoint=(
                        "/api/jobs/news-research"
                    ),
                    method="POST",
                )
            )

        readiness_text = " ".join(
            snapshot.readiness_reasons
        ).lower()

        if "unresolved" in readiness_text:
            actions.append(
                BriefingAction(
                    action=(
                        BriefingActionType
                        .REVIEW_UNRESOLVED_ORDERS
                    ),
                    priority=BriefingPriority.HIGH,
                    label="Review unresolved orders",
                    reason=(
                        "Outstanding order state is "
                        "blocking trading readiness."
                    ),
                    endpoint="/api/orders/unresolved",
                    method="GET",
                )
            )

        if "reconciliation" in readiness_text:
            actions.append(
                BriefingAction(
                    action=(
                        BriefingActionType
                        .RUN_RECONCILIATION
                    ),
                    priority=BriefingPriority.HIGH,
                    label="Review reconciliation",
                    reason=(
                        "Broker reconciliation has not "
                        "confirmed safe startup."
                    ),
                    endpoint=(
                        "/api/reconciliation/latest"
                    ),
                    method="GET",
                )
            )

        if performance.total_decision_count < 250:
            actions.append(
                BriefingAction(
                    action=(
                        BriefingActionType
                        .RUN_SHADOW_ANALYSIS
                    ),
                    priority=BriefingPriority.MEDIUM,
                    label="Run shadow analysis",
                    reason=(
                        f"Only "
                        f"{performance.total_decision_count} "
                        "shadow decisions are available; "
                        "250 are required for graduation."
                    ),
                    endpoint=(
                        "/api/jobs/shadow-analysis"
                    ),
                    method="POST",
                )
            )

        if top is not None:
            actions.append(
                BriefingAction(
                    action=(
                        BriefingActionType
                        .REVIEW_TOP_OPPORTUNITY
                    ),
                    priority=BriefingPriority.MEDIUM,
                    label=(
                        f"Review {top.symbol}"
                    ),
                    reason=(
                        "This is KAIRO's highest-ranked "
                        "current opportunity."
                    ),
                    endpoint=(
                        "/api/intelligence/snapshot"
                    ),
                    method="GET",
                    symbol=top.symbol,
                )
            )

        if (
            graduation_eligible
            and snapshot.trading_readiness.value
            == "READY"
        ):
            actions.append(
                BriefingAction(
                    action=(
                        BriefingActionType
                        .START_PAPER_TRADING
                    ),
                    priority=BriefingPriority.LOW,
                    label=(
                        "Review DEMO paper-trading start"
                    ),
                    reason=(
                        "All evidence and operational "
                        "checks have passed for manual "
                        "review."
                    ),
                    endpoint=(
                        "/api/paper-trading/start"
                    ),
                    method="POST",
                )
            )
        else:
            actions.append(
                BriefingAction(
                    action=(
                        BriefingActionType
                        .WAIT_FOR_MORE_EVIDENCE
                    ),
                    priority=BriefingPriority.LOW,
                    label="Continue research-only mode",
                    reason=(
                        "KAIRO has not graduated to an "
                        "AI-assisted paper filter."
                    ),
                )
            )

        return tuple(actions)
