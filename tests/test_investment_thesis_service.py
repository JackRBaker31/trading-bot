from datetime import datetime, timezone

from app.investment_capability_providers import (
    NewsCapabilityProvider,
    PortfolioCapabilityProvider,
    RiskCapabilityProvider,
    UnavailableCapabilityProvider,
)
from app.investment_thesis_service import (
    InvestmentThesisService,
)
from app.intelligence_snapshot import (
    EvidenceQuality,
    IntelligenceFreshness,
    IntelligenceOpportunity,
    IntelligenceSnapshot,
    MarketOutlook,
    OpportunityClassification,
    TradingReadiness,
)
from app.operations_query_service import (
    PortfolioView,
    RiskStatusView,
)


NOW = datetime(
    2026,
    7,
    24,
    15,
    0,
    tzinfo=timezone.utc,
)


class Graduation:
    eligible = True
    failed_checks: tuple[str, ...] = ()


def opportunity(
) -> IntelligenceOpportunity:
    return IntelligenceOpportunity(
        article_id="article-1",
        rank=1,
        symbol="AAPL",
        score=90.0,
        classification=(
            OpportunityClassification
            .CANDIDATE
        ),
        confidence=0.92,
        sentiment="POSITIVE",
        is_material=True,
        event_type=(
            "STOCK_LONGTERM_POSITIVE"
        ),
        headline=(
            "Apple raises guidance."
        ),
        published_at=(
            NOW.isoformat()
        ),
        eligible_for_trade=True,
        reasons=(
            "Material guidance upgrade.",
        ),
        blocking_reasons=(),
        score_breakdown={},
    )


def snapshot(
) -> IntelligenceSnapshot:
    return IntelligenceSnapshot(
        generated_at=NOW.isoformat(),
        market_outlook=(
            MarketOutlook.PROMISING
        ),
        confidence=90.0,
        trading_readiness=(
            TradingReadiness.READY
        ),
        readiness_reasons=(),
        research_verdict="PROMISING",
        evidence_quality=(
            EvidenceQuality.STRONG
        ),
        evidence_sample_count=200,
        signal_count=10,
        high_confidence_signal_count=5,
        material_event_count=3,
        actionable_signal_count=2,
        paper_trading_state="RUNNING",
        top_opportunities=(
            opportunity(),
        ),
        risk_warnings=(),
        recommended_actions=(),
        freshness=(
            IntelligenceFreshness(
                is_stale=False,
                latest_research_at=(
                    NOW.isoformat()
                ),
                latest_signal_at=(
                    NOW.isoformat()
                ),
                stale_reasons=(),
            )
        ),
    )


def risk(
) -> RiskStatusView:
    return RiskStatusView(
        max_order_value=2500.0,
        max_position_value=5000.0,
        max_portfolio_exposure_ratio=0.8,
        max_portfolio_exposure_value=8000.0,
        max_trades_per_session=10,
        approved_symbols=("AAPL",),
        paper_trading_enabled=True,
        broker_environment="DEMO",
        execution_permission_confirmed=True,
        real_money_trading_enabled=False,
    )


def portfolio(
) -> PortfolioView:
    return PortfolioView(
        available=True,
        starting_cash=10000.0,
        cash=8000.0,
        position_count=0,
        positions=(),
        applied_broker_order_count=0,
    )


def test_incomplete_capabilities_block_execution(
) -> None:
    report = InvestmentThesisService(
        snapshot_provider=snapshot,
        risk_provider=risk,
        portfolio_provider=portfolio,
        graduation_provider=Graduation,
        capability_providers=(
            NewsCapabilityProvider(),
            UnavailableCapabilityProvider(
                capability="TECHNICAL",
                maximum=20.0,
                summary=(
                    "Technical provider "
                    "not connected."
                ),
            ),
            UnavailableCapabilityProvider(
                capability="MACRO",
                maximum=10.0,
                summary=(
                    "Macro provider "
                    "not connected."
                ),
            ),
            UnavailableCapabilityProvider(
                capability="VALUATION",
                maximum=10.0,
                summary=(
                    "Valuation provider "
                    "not connected."
                ),
            ),
            PortfolioCapabilityProvider(),
            RiskCapabilityProvider(),
        ),
        now_provider=lambda: NOW,
    ).get_report()

    thesis = report.theses[0]

    assert (
        thesis.recommendation
        == "INCOMPLETE"
    )
    assert not (
        thesis.eligible_for_execution
    )
    assert (
        thesis.suggested_position_value
        == 0
    )
    assert (
        thesis.confidence_coverage
        < 1.0
    )
    assert any(
        capability.status
        == "UNAVAILABLE"
        for capability
        in thesis.capabilities
    )


def test_get_thesis_returns_requested_current_symbol() -> None:
    service = InvestmentThesisService(
        snapshot_provider=snapshot,
        risk_provider=risk,
        portfolio_provider=portfolio,
        graduation_provider=Graduation,
        capability_providers=(
            NewsCapabilityProvider(),
            UnavailableCapabilityProvider(
                capability="TECHNICAL",
                maximum=20.0,
                summary="Technical provider not connected.",
            ),
            UnavailableCapabilityProvider(
                capability="MACRO",
                maximum=10.0,
                summary="Macro provider not connected.",
            ),
            UnavailableCapabilityProvider(
                capability="VALUATION",
                maximum=10.0,
                summary="Valuation provider not connected.",
            ),
            PortfolioCapabilityProvider(),
            RiskCapabilityProvider(),
        ),
        now_provider=lambda: NOW,
    )

    thesis = service.get_thesis(symbol="aapl")

    assert thesis is not None
    assert thesis.symbol == "AAPL"
    assert service.get_thesis(symbol="MSFT") is None
