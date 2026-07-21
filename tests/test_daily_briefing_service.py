from types import SimpleNamespace

from app.daily_briefing import BriefingActionType
from app.daily_briefing_service import DailyBriefingService
from app.intelligence_snapshot import (
    EvidenceQuality,
    IntelligenceFreshness,
    IntelligenceOpportunity,
    IntelligenceSnapshot,
    MarketOutlook,
    OpportunityClassification,
    TradingReadiness,
)
from app.shadow_performance import (
    ShadowHorizonPerformance,
    ShadowPerformanceReport,
)


class FakeIntelligenceService:
    def __init__(self, snapshot):
        self.snapshot = snapshot

    def get_snapshot(self):
        return self.snapshot


class FakePerformanceService:
    def __init__(self, report):
        self.report = report

    def get_report(self):
        return self.report


class FakeGraduationService:
    def __init__(self, status):
        self.status = status

    def get_status(self):
        return self.status


def performance_report(
    *,
    total: int = 12,
    measured_1d: int = 3,
) -> ShadowPerformanceReport:
    def horizon(name, measured=0):
        return ShadowHorizonPerformance(
            horizon=name,
            decision_count=total,
            measured_count=measured,
            coverage_percent=25.0,
            profitable_count=2,
            directional_success_percent=(
                66.67 if measured else 0.0
            ),
            profitable_after_cost_count=2,
            profitable_after_cost_percent=(
                66.67 if measured else 0.0
            ),
            average_return_percent=1.0,
            median_return_percent=1.0,
            average_net_return_percent=0.8,
            best_return_percent=2.0,
            worst_return_percent=-1.0,
            maximum_drawdown_percent=1.0,
            rolling_window_count=0,
            positive_rolling_window_percent=0.0,
            by_action=(),
            by_score_band=(),
            by_confidence_band=(),
            by_event_type=(),
            by_materiality=(),
        )

    return ShadowPerformanceReport(
        model_version="KAIRO_SHADOW_V1",
        total_decision_count=total,
        execution_cost_percent=0.2,
        horizons=(
            horizon("1H"),
            horizon("1D", measured_1d),
            horizon("5D"),
        ),
    )


def snapshot(
    *,
    stale: bool = False,
    readiness: TradingReadiness = (
        TradingReadiness.NOT_READY
    ),
) -> IntelligenceSnapshot:
    opportunity = IntelligenceOpportunity(
        article_id="article-1",
        rank=1,
        symbol="NVDA",
        score=82.0,
        classification=(
            OpportunityClassification.WATCH
        ),
        confidence=0.88,
        sentiment="POSITIVE",
        is_material=True,
        event_type="EARNINGS",
        headline="Strong guidance",
        published_at="2026-07-20T09:00:00+00:00",
        eligible_for_trade=False,
        reasons=("Positive material event.",),
        blocking_reasons=("Research only.",),
        score_breakdown={"confidence": 39.6},
    )
    return IntelligenceSnapshot(
        generated_at="2026-07-20T10:00:00+00:00",
        market_outlook=MarketOutlook.CAUTIOUS,
        confidence=0.58,
        trading_readiness=readiness,
        readiness_reasons=(
            "No successful reconciliation is available.",
        ),
        research_verdict="PROMISING",
        evidence_quality=EvidenceQuality.VERY_LOW,
        evidence_sample_count=3,
        signal_count=19,
        high_confidence_signal_count=7,
        material_event_count=3,
        actionable_signal_count=2,
        paper_trading_state="STOPPED",
        top_opportunities=(opportunity,),
        risk_warnings=(
            "AI evidence is immature.",
        ),
        recommended_actions=(),
        freshness=IntelligenceFreshness(
            is_stale=stale,
            latest_research_at=(
                "2026-07-20T08:00:00+00:00"
            ),
            latest_signal_at=(
                "2026-07-20T09:00:00+00:00"
            ),
            stale_reasons=(
                ("News research is stale.",)
                if stale
                else ()
            ),
        ),
    )


def graduation(
    *,
    eligible: bool = False,
):
    return SimpleNamespace(
        eligible=eligible,
        checks_passed=(8 if eligible else 2),
        total_checks=8,
        failed_checks=(
            ()
            if eligible
            else (
                "Only 12 shadow decisions are available; 250 are required.",
            )
        ),
        status=(
            "ELIGIBLE_FOR_PAPER_FILTER_REVIEW"
            if eligible
            else "RESEARCH_ONLY"
        ),
    )


def test_builds_explainable_daily_briefing() -> None:
    briefing = DailyBriefingService(
        intelligence_service=(
            FakeIntelligenceService(snapshot())
        ),
        shadow_performance_service=(
            FakePerformanceService(
                performance_report()
            )
        ),
        graduation_service=(
            FakeGraduationService(graduation())
        ),
    ).get_briefing()

    assert briefing.headline == "KAIRO is cautious"
    assert briefing.top_opportunity["symbol"] == "NVDA"
    assert briefing.graduation_status == "RESEARCH_ONLY"
    assert any(
        action.action
        == BriefingActionType.RUN_SHADOW_ANALYSIS
        for action in briefing.actions
    )
    assert any(
        action.action
        == BriefingActionType.RUN_RECONCILIATION
        for action in briefing.actions
    )
    assert briefing.trading_impact == "NONE"


def test_stale_briefing_recommends_news_refresh() -> None:
    briefing = DailyBriefingService(
        intelligence_service=(
            FakeIntelligenceService(
                snapshot(stale=True)
            )
        ),
        shadow_performance_service=(
            FakePerformanceService(
                performance_report()
            )
        ),
        graduation_service=(
            FakeGraduationService(graduation())
        ),
    ).get_briefing()

    assert briefing.is_stale is True
    assert any(
        action.action
        == BriefingActionType.RUN_NEWS_RESEARCH
        for action in briefing.actions
    )
    assert "News research is stale." in briefing.warnings


def test_ready_graduated_briefing_allows_review_only() -> None:
    briefing = DailyBriefingService(
        intelligence_service=(
            FakeIntelligenceService(
                snapshot(
                    readiness=TradingReadiness.READY
                )
            )
        ),
        shadow_performance_service=(
            FakePerformanceService(
                performance_report(total=250)
            )
        ),
        graduation_service=(
            FakeGraduationService(
                graduation(eligible=True)
            )
        ),
    ).get_briefing()

    assert any(
        action.action
        == BriefingActionType.START_PAPER_TRADING
        for action in briefing.actions
    )
    assert briefing.trading_impact == "NONE"
