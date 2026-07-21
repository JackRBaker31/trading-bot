from datetime import datetime, timezone
from types import SimpleNamespace

from app.intelligence_service import IntelligenceService
from app.intelligence_snapshot import (
    EvidenceQuality,
    MarketOutlook,
    OpportunityClassification,
    TradingReadiness,
)


NOW = datetime(
    2026,
    7,
    20,
    10,
    0,
    tzinfo=timezone.utc,
)


class FakeSystemStatusService:
    def get_status(self, *, request):
        del request
        return SimpleNamespace(
            application_mode="PAPER",
        )


class FakeResearchQueryService:
    def __init__(
        self,
        *,
        report=None,
        signals=(),
        outcome_count=3,
    ) -> None:
        self.report = report
        self.signals = tuple(signals)
        self.outcome_count = outcome_count

    def get_latest_report(self):
        return self.report

    def list_signals(self, **kwargs):
        del kwargs
        return SimpleNamespace(
            items=self.signals,
        )

    def get_news_summary(self):
        return {
            "signal_count": len(self.signals),
            "outcome_count": self.outcome_count,
        }


class FakeOperationsQueryService:
    def __init__(
        self,
        *,
        safe=True,
        available=True,
        unresolved=0,
        permission=True,
    ) -> None:
        self.safe = safe
        self.available = available
        self.unresolved = unresolved
        self.permission = permission

    def get_risk_status(self, *, request):
        del request
        return SimpleNamespace(
            paper_trading_enabled=True,
            broker_environment="DEMO",
            execution_permission_confirmed=(
                self.permission
            ),
            approved_symbols=(
                "AAPL",
                "MSFT",
            ),
        )

    def get_latest_reconciliation(
        self,
        *,
        request,
    ):
        del request
        return SimpleNamespace(
            available=self.available,
            safe_to_start=self.safe,
            unresolved_order_count=(
                self.unresolved
            ),
        )


class FakePaperTradingController:
    def get_status(self):
        return SimpleNamespace(
            state=SimpleNamespace(
                value="STOPPED"
            )
        )


def create_signal(
    *,
    symbol="AAPL",
    confidence=0.9,
    relevance=0.9,
    sentiment=0.8,
    material=True,
):
    return {
        "article_id": f"article-{symbol}",
        "symbol": symbol,
        "headline": f"{symbol} positive event",
        "sentiment": sentiment,
        "sentiment_name": (
            "POSITIVE"
            if sentiment > 0
            else "NEGATIVE"
        ),
        "relevance": relevance,
        "confidence": confidence,
        "event_type": (
            "STOCK_SHORTTERM_POSITIVE"
        ),
        "is_material": material,
        "published_at": (
            "2026-07-20T09:00:00+00:00"
        ),
        "expires_at": (
            "2026-07-21T09:00:00+00:00"
        ),
        "source": "test",
        "reasoning_summary": "Example.",
    }


def create_service(
    *,
    report=None,
    signals=(),
    outcome_count=3,
    operations=None,
):
    return IntelligenceService(
        system_status_service=(
            FakeSystemStatusService()
        ),
        research_query_service=(
            FakeResearchQueryService(
                report=report,
                signals=signals,
                outcome_count=outcome_count,
            )
        ),
        operations_query_service=(
            operations
            or FakeOperationsQueryService()
        ),
        paper_trading_controller=(
            FakePaperTradingController()
        ),
        now_provider=lambda: NOW,
    )


def promising_report():
    return {
        "verdict": "PROMISING",
        "generated_at": (
            "2026-07-20T08:00:00+00:00"
        ),
        "passed_check_count": 5,
        "total_check_count": 5,
    }


def test_builds_explainable_promising_snapshot():
    snapshot = create_service(
        report=promising_report(),
        signals=(create_signal(),),
        outcome_count=3,
    ).get_snapshot()

    assert snapshot.market_outlook == (
        MarketOutlook.PROMISING
    )
    assert snapshot.trading_readiness == (
        TradingReadiness.READY
    )
    assert snapshot.evidence_quality == (
        EvidenceQuality.VERY_LOW
    )
    assert snapshot.confidence <= 0.55
    assert snapshot.actionable_signal_count == 1
    assert snapshot.top_opportunities[0].symbol == (
        "AAPL"
    )
    assert (
        snapshot.top_opportunities[0]
        .classification
        == OpportunityClassification.BLOCKED
    )
    assert "limited" in (
        snapshot.top_opportunities[0]
        .blocking_reasons[-1]
    ).lower()


def test_reports_readiness_blockers():
    snapshot = create_service(
        report=promising_report(),
        signals=(create_signal(),),
        operations=(
            FakeOperationsQueryService(
                safe=False,
                available=False,
                unresolved=2,
                permission=False,
            )
        ),
    ).get_snapshot()

    assert snapshot.trading_readiness == (
        TradingReadiness.NOT_READY
    )
    assert any(
        "execution permission" in reason.lower()
        for reason in snapshot.readiness_reasons
    )
    assert any(
        "unresolved" in reason.lower()
        for reason in snapshot.readiness_reasons
    )
    assert any(
        "reconciliation" in action.lower()
        for action in snapshot.recommended_actions
    )


def test_uses_insufficient_data_without_report():
    snapshot = create_service(
        report=None,
        signals=(),
    ).get_snapshot()

    assert snapshot.market_outlook == (
        MarketOutlook.INSUFFICIENT_DATA
    )
    assert snapshot.confidence == 0.0
    assert snapshot.freshness.is_stale is True


def test_marks_stale_research_as_cautious():
    report = promising_report()
    report["generated_at"] = (
        "2026-07-18T08:00:00+00:00"
    )
    stale_signal = create_signal()
    stale_signal["published_at"] = (
        "2026-07-18T09:00:00+00:00"
    )
    stale_signal["expires_at"] = (
        "2026-07-21T09:00:00+00:00"
    )

    snapshot = create_service(
        report=report,
        signals=(stale_signal,),
    ).get_snapshot()

    assert snapshot.market_outlook == (
        MarketOutlook.CAUTIOUS
    )
    assert snapshot.freshness.is_stale is True
    assert len(
        snapshot.freshness.stale_reasons
    ) == 2
