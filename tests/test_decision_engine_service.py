from datetime import datetime, timezone

from app.decision_engine_service import (
    DecisionEngineService,
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
    14,
    0,
    tzinfo=timezone.utc,
)


class Graduation:
    def __init__(
        self,
        *,
        eligible: bool,
        failed_checks: tuple[
            str,
            ...
        ] = (),
    ) -> None:
        self.eligible = eligible
        self.failed_checks = (
            failed_checks
        )


def opportunity(
    *,
    score: float = 92.0,
    confidence: float = 0.94,
    eligible: bool = True,
    blockers: tuple[
        str,
        ...
    ] = (),
) -> IntelligenceOpportunity:
    return IntelligenceOpportunity(
        article_id="article-1",
        rank=1,
        symbol="AAPL",
        score=score,
        classification=(
            OpportunityClassification
            .CANDIDATE
        ),
        confidence=confidence,
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
        eligible_for_trade=eligible,
        reasons=(
            "High-confidence "
            "material signal.",
        ),
        blocking_reasons=blockers,
        score_breakdown={
            "confidence": 42.3,
            "relevance": 23.0,
            "sentiment": 15.0,
            "materiality": 15.0,
        },
    )


def snapshot(
    *,
    readiness: TradingReadiness = (
        TradingReadiness.READY
    ),
    opportunities: tuple[
        IntelligenceOpportunity,
        ...
    ] | None = None,
) -> IntelligenceSnapshot:
    return IntelligenceSnapshot(
        generated_at=NOW.isoformat(),
        market_outlook=(
            MarketOutlook.PROMISING
        ),
        confidence=91.0,
        trading_readiness=readiness,
        readiness_reasons=(
            ()
            if readiness
            is TradingReadiness.READY
            else (
                "Operational checks "
                "have not passed.",
            )
        ),
        research_verdict="PROMISING",
        evidence_quality=(
            EvidenceQuality.STRONG
        ),
        evidence_sample_count=300,
        signal_count=10,
        high_confidence_signal_count=5,
        material_event_count=4,
        actionable_signal_count=3,
        paper_trading_state="RUNNING",
        top_opportunities=(
            opportunities
            if opportunities is not None
            else (
                opportunity(),
            )
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


def service(
    *,
    current_snapshot: (
        IntelligenceSnapshot
    ),
    graduation: Graduation,
) -> DecisionEngineService:
    return DecisionEngineService(
        snapshot_provider=(
            lambda: current_snapshot
        ),
        risk_provider=risk,
        portfolio_provider=portfolio,
        graduation_provider=(
            lambda: graduation
        ),
        now_provider=lambda: NOW,
    )


def test_creates_executable_buy_candidate(
) -> None:
    report = service(
        current_snapshot=snapshot(),
        graduation=Graduation(
            eligible=True
        ),
    ).get_report()

    decision = report.decisions[0]

    assert (
        decision.recommendation
        == "BUY_CANDIDATE"
    )
    assert (
        decision.eligible_for_execution
    )
    assert (
        decision.score >= 80
    )
    assert (
        decision.suggested_position_value
        > 0
    )
    assert (
        decision.suggested_position_value
        <= 2500
    )


def test_readiness_gate_blocks_candidate(
) -> None:
    report = service(
        current_snapshot=snapshot(
            readiness=(
                TradingReadiness.NOT_READY
            )
        ),
        graduation=Graduation(
            eligible=True
        ),
    ).get_report()

    decision = report.decisions[0]

    assert (
        decision.recommendation
        == "BLOCKED"
    )
    assert not (
        decision.eligible_for_execution
    )
    assert (
        decision.suggested_position_value
        == 0
    )
    assert (
        "Operational checks "
        "have not passed."
        in decision.blockers
    )


def test_graduation_gate_blocks_candidate(
) -> None:
    report = service(
        current_snapshot=snapshot(),
        graduation=Graduation(
            eligible=False,
            failed_checks=(
                "More shadow decisions "
                "are required.",
            ),
        ),
    ).get_report()

    decision = report.decisions[0]

    assert (
        decision.recommendation
        == "BLOCKED"
    )
    assert (
        "More shadow decisions "
        "are required."
        in decision.blockers
    )


def test_lower_score_becomes_watch(
) -> None:
    report = service(
        current_snapshot=snapshot(
            opportunities=(
                opportunity(
                    score=60.0,
                    confidence=0.82,
                ),
            )
        ),
        graduation=Graduation(
            eligible=True
        ),
    ).get_report()

    assert (
        report.decisions[0]
        .recommendation
        == "WATCH"
    )
    assert not (
        report.decisions[0]
        .eligible_for_execution
    )
