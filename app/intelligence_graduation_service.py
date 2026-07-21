from dataclasses import dataclass

from app.intelligence_graduation import (
    GraduationCheck,
    IntelligenceGraduationStatus,
)
from app.shadow_performance import (
    ShadowPerformanceReport,
)
from app.shadow_performance_service import (
    ShadowPerformanceService,
)


@dataclass(frozen=True)
class IntelligenceGraduationPolicy:
    minimum_total_decisions: int = 250
    minimum_completed_1d_decisions: int = 150
    minimum_directional_success_percent: float = 58.0
    minimum_profitable_after_cost_percent: float = 53.0
    maximum_drawdown_percent: float = 12.0
    minimum_positive_rolling_windows_percent: float = 60.0
    require_fresh_research: bool = True
    require_safe_reconciliation: bool = True


class IntelligenceGraduationService:
    def __init__(
        self,
        *,
        performance_service: (
            ShadowPerformanceService
        ),
        intelligence_service,
        policy: (
            IntelligenceGraduationPolicy | None
        ) = None,
    ) -> None:
        self._performance_service = (
            performance_service
        )
        self._intelligence_service = (
            intelligence_service
        )
        self._policy = (
            policy
            or IntelligenceGraduationPolicy()
        )

    def get_status(
        self,
    ) -> IntelligenceGraduationStatus:
        performance = (
            self._performance_service.get_report()
        )
        intelligence = (
            self._intelligence_service.get_snapshot()
        )
        one_day = next(
            horizon
            for horizon in performance.horizons
            if horizon.horizon == "1D"
        )

        checks = (
            self._check(
                name="TOTAL_SHADOW_DECISIONS",
                passed=(
                    performance.total_decision_count
                    >= self._policy
                    .minimum_total_decisions
                ),
                actual=(
                    performance.total_decision_count
                ),
                required=(
                    self._policy
                    .minimum_total_decisions
                ),
                reason=(
                    "Total shadow-decision sample "
                    "meets the minimum."
                ),
                failed_reason=(
                    f"Only "
                    f"{performance.total_decision_count} "
                    "shadow decisions are available; "
                    f"{self._policy.minimum_total_decisions} "
                    "are required."
                ),
            ),
            self._check(
                name="COMPLETED_1D_DECISIONS",
                passed=(
                    one_day.measured_count
                    >= self._policy
                    .minimum_completed_1d_decisions
                ),
                actual=one_day.measured_count,
                required=(
                    self._policy
                    .minimum_completed_1d_decisions
                ),
                reason=(
                    "Completed 1D sample meets "
                    "the minimum."
                ),
                failed_reason=(
                    f"Only {one_day.measured_count} "
                    "completed 1D decisions are "
                    f"available; "
                    f"{self._policy.minimum_completed_1d_decisions} "
                    "are required."
                ),
            ),
            self._check(
                name="DIRECTIONAL_SUCCESS",
                passed=(
                    one_day
                    .directional_success_percent
                    >= self._policy
                    .minimum_directional_success_percent
                ),
                actual=(
                    one_day
                    .directional_success_percent
                ),
                required=(
                    self._policy
                    .minimum_directional_success_percent
                ),
                reason=(
                    "Directional success meets "
                    "the minimum."
                ),
                failed_reason=(
                    "Directional success is "
                    f"{one_day.directional_success_percent:.2f}%; "
                    f"{self._policy.minimum_directional_success_percent:.2f}% "
                    "is required."
                ),
            ),
            self._check(
                name="PROFITABLE_AFTER_COST",
                passed=(
                    one_day
                    .profitable_after_cost_percent
                    >= self._policy
                    .minimum_profitable_after_cost_percent
                ),
                actual=(
                    one_day
                    .profitable_after_cost_percent
                ),
                required=(
                    self._policy
                    .minimum_profitable_after_cost_percent
                ),
                reason=(
                    "Profitable-after-cost rate "
                    "meets the minimum."
                ),
                failed_reason=(
                    "Profitable-after-cost rate is "
                    f"{one_day.profitable_after_cost_percent:.2f}%; "
                    f"{self._policy.minimum_profitable_after_cost_percent:.2f}% "
                    "is required."
                ),
            ),
            self._check(
                name="MAXIMUM_DRAWDOWN",
                passed=(
                    one_day
                    .maximum_drawdown_percent
                    <= self._policy
                    .maximum_drawdown_percent
                ),
                actual=(
                    one_day
                    .maximum_drawdown_percent
                ),
                required=(
                    self._policy
                    .maximum_drawdown_percent
                ),
                reason=(
                    "Maximum drawdown is within "
                    "the limit."
                ),
                failed_reason=(
                    "Maximum drawdown is "
                    f"{one_day.maximum_drawdown_percent:.2f}%; "
                    f"the limit is "
                    f"{self._policy.maximum_drawdown_percent:.2f}%."
                ),
            ),
            self._check(
                name="ROLLING_STABILITY",
                passed=(
                    one_day.rolling_window_count > 0
                    and one_day
                    .positive_rolling_window_percent
                    >= self._policy
                    .minimum_positive_rolling_windows_percent
                ),
                actual=(
                    one_day
                    .positive_rolling_window_percent
                ),
                required=(
                    self._policy
                    .minimum_positive_rolling_windows_percent
                ),
                reason=(
                    "Rolling positive-window rate "
                    "meets the minimum."
                ),
                failed_reason=(
                    "Rolling positive-window rate is "
                    f"{one_day.positive_rolling_window_percent:.2f}%; "
                    f"{self._policy.minimum_positive_rolling_windows_percent:.2f}% "
                    "is required."
                ),
            ),
            self._check(
                name="RESEARCH_FRESHNESS",
                passed=(
                    not self._policy.require_fresh_research
                    or not intelligence.freshness.is_stale
                ),
                actual=(
                    not intelligence.freshness.is_stale
                ),
                required=True,
                reason="Research data is fresh.",
                failed_reason=(
                    "Research data is stale and "
                    "must be refreshed."
                ),
            ),
            self._check(
                name="OPERATIONAL_READINESS",
                passed=(
                    not self._policy
                    .require_safe_reconciliation
                    or intelligence
                    .trading_readiness
                    == "READY"
                ),
                actual=(
                    intelligence.trading_readiness
                ),
                required="READY",
                reason=(
                    "Operational readiness checks "
                    "have passed."
                ),
                failed_reason=(
                    "Operational readiness has not "
                    "passed."
                ),
            ),
        )

        failed = tuple(
            check.reason
            for check in checks
            if not check.passed
        )
        passed_count = sum(
            check.passed
            for check in checks
        )
        eligible = passed_count == len(checks)

        return IntelligenceGraduationStatus(
            eligible=eligible,
            checks_passed=passed_count,
            total_checks=len(checks),
            checks=checks,
            failed_checks=failed,
            status=(
                "ELIGIBLE_FOR_PAPER_FILTER_REVIEW"
                if eligible
                else "RESEARCH_ONLY"
            ),
        )

    @staticmethod
    def _check(
        *,
        name: str,
        passed: bool,
        actual: object,
        required: object,
        reason: str,
        failed_reason: str,
    ) -> GraduationCheck:
        return GraduationCheck(
            name=name,
            passed=passed,
            actual=actual,
            required=required,
            reason=(
                reason
                if passed
                else failed_reason
            ),
        )
