from types import SimpleNamespace

from app.intelligence_graduation_service import (
    IntelligenceGraduationPolicy,
    IntelligenceGraduationService,
)
from app.shadow_performance import (
    ShadowHorizonPerformance,
    ShadowPerformanceReport,
)


def horizon(
    name: str,
    *,
    measured: int = 0,
    success: float = 0.0,
    profitable_after_cost: float = 0.0,
    drawdown: float = 0.0,
    rolling_windows: int = 0,
    positive_windows: float = 0.0,
) -> ShadowHorizonPerformance:
    return ShadowHorizonPerformance(
        horizon=name,
        decision_count=250,
        measured_count=measured,
        coverage_percent=60.0,
        profitable_count=0,
        directional_success_percent=success,
        profitable_after_cost_count=0,
        profitable_after_cost_percent=(
            profitable_after_cost
        ),
        average_return_percent=1.0,
        median_return_percent=1.0,
        average_net_return_percent=0.8,
        best_return_percent=4.0,
        worst_return_percent=-2.0,
        maximum_drawdown_percent=drawdown,
        rolling_window_count=rolling_windows,
        positive_rolling_window_percent=(
            positive_windows
        ),
        by_action=(),
        by_score_band=(),
        by_confidence_band=(),
        by_event_type=(),
        by_materiality=(),
    )


class FakePerformanceService:
    def __init__(self, report):
        self.report = report

    def get_report(self):
        return self.report


class FakeIntelligenceService:
    def __init__(
        self,
        *,
        stale: bool,
        readiness: str,
    ) -> None:
        self.snapshot = SimpleNamespace(
            freshness=SimpleNamespace(
                is_stale=stale
            ),
            trading_readiness=readiness,
        )

    def get_snapshot(self):
        return self.snapshot


def test_graduation_passes_all_checks() -> None:
    report = ShadowPerformanceReport(
        model_version="KAIRO_SHADOW_V1",
        total_decision_count=250,
        execution_cost_percent=0.2,
        horizons=(
            horizon("1H"),
            horizon(
                "1D",
                measured=150,
                success=60.0,
                profitable_after_cost=55.0,
                drawdown=10.0,
                rolling_windows=10,
                positive_windows=70.0,
            ),
            horizon("5D"),
        ),
    )

    status = IntelligenceGraduationService(
        performance_service=(
            FakePerformanceService(report)
        ),
        intelligence_service=(
            FakeIntelligenceService(
                stale=False,
                readiness="READY",
            )
        ),
    ).get_status()

    assert status.eligible is True
    assert status.checks_passed == 8
    assert status.status == (
        "ELIGIBLE_FOR_PAPER_FILTER_REVIEW"
    )
    assert status.trading_impact == "NONE"


def test_graduation_explains_failures() -> None:
    report = ShadowPerformanceReport(
        model_version="KAIRO_SHADOW_V1",
        total_decision_count=12,
        execution_cost_percent=0.2,
        horizons=(
            horizon("1H"),
            horizon(
                "1D",
                measured=3,
                success=50.0,
                profitable_after_cost=33.0,
                drawdown=15.0,
            ),
            horizon("5D"),
        ),
    )

    status = IntelligenceGraduationService(
        performance_service=(
            FakePerformanceService(report)
        ),
        intelligence_service=(
            FakeIntelligenceService(
                stale=True,
                readiness="NOT_READY",
            )
        ),
    ).get_status()

    assert status.eligible is False
    assert status.status == "RESEARCH_ONLY"
    assert status.checks_passed < (
        status.total_checks
    )
    assert any(
        "250" in reason
        for reason in status.failed_checks
    )
