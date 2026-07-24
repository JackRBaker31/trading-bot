from datetime import datetime, timezone

from app.intelligence_graduation import (
    GraduationCheck,
    IntelligenceGraduationStatus,
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
from app.symbol_decision_repository import (
    SymbolDecisionRepository,
)
from app.symbol_decision_service import (
    SymbolDecisionService,
)


NOW = datetime(
    2026,
    7,
    24,
    12,
    0,
    tzinfo=timezone.utc,
)


def snapshot(
) -> IntelligenceSnapshot:
    return IntelligenceSnapshot(
        generated_at=NOW.isoformat(),
        market_outlook=(
            MarketOutlook.CAUTIOUS
        ),
        confidence=63.5,
        trading_readiness=(
            TradingReadiness.NOT_READY
        ),
        readiness_reasons=(
            "Paper trading is disabled.",
        ),
        research_verdict="CAUTIOUS",
        evidence_quality=(
            EvidenceQuality.LOW
        ),
        evidence_sample_count=10,
        signal_count=12,
        high_confidence_signal_count=4,
        material_event_count=3,
        actionable_signal_count=2,
        paper_trading_state="STOPPED",
        top_opportunities=(
            IntelligenceOpportunity(
                article_id="article-1",
                rank=1,
                symbol="NVDA",
                score=84.5,
                classification=(
                    OpportunityClassification
                    .BLOCKED
                ),
                confidence=0.91,
                sentiment="BULLISH",
                is_material=True,
                event_type="EARNINGS",
                headline=(
                    "NVIDIA raises revenue "
                    "guidance."
                ),
                published_at=(
                    "2026-07-24T10:00:00+00:00"
                ),
                eligible_for_trade=False,
                reasons=(
                    "The source event was "
                    "classified as material.",
                ),
                blocking_reasons=(
                    "Platform trading-readiness "
                    "checks have not passed.",
                ),
                score_breakdown={
                    "confidence": 40.95,
                    "relevance": 24.0,
                    "sentiment": 4.55,
                    "materiality": 15.0,
                },
            ),
        ),
        risk_warnings=(
            "Historical evidence is limited.",
        ),
        recommended_actions=(),
        freshness=IntelligenceFreshness(
            is_stale=False,
            latest_research_at=(
                "2026-07-24T10:00:00+00:00"
            ),
            latest_signal_at=(
                "2026-07-24T10:00:00+00:00"
            ),
            stale_reasons=(),
        ),
    )


def graduation(
) -> IntelligenceGraduationStatus:
    return IntelligenceGraduationStatus(
        eligible=False,
        checks_passed=1,
        total_checks=2,
        checks=(
            GraduationCheck(
                name="DECISION_SAMPLE",
                passed=False,
                actual=10,
                required=250,
                reason=(
                    "More shadow decisions "
                    "are required."
                ),
            ),
        ),
        failed_checks=(
            "More shadow decisions are "
            "required.",
        ),
        status="NOT_READY",
    )


def create_service(
    tmp_path,
) -> SymbolDecisionService:
    service = SymbolDecisionService(
        repository=SymbolDecisionRepository(
            database_path=str(
                tmp_path / "application.db"
            )
        ),
        snapshot_provider=snapshot,
        graduation_provider=graduation,
        now_provider=lambda: NOW,
    )
    service.initialize()
    return service


def test_builds_grounded_symbol_trace(
    tmp_path,
) -> None:
    trace = create_service(
        tmp_path
    ).get_current(
        symbol="nvda"
    )

    assert trace is not None
    assert trace.symbol == "NVDA"
    assert trace.decision == "BLOCKED"
    assert len(trace.stages) == 6
    assert (
        trace.stages[0].title
        == "Research Evidence"
    )
    assert (
        "More shadow decisions are "
        "required."
        in trace.blockers
    )


def test_lists_current_opportunities(
    tmp_path,
) -> None:
    traces = create_service(
        tmp_path
    ).list_current()

    assert len(traces) == 1
    assert traces[0].rank == 1
    assert traces[0].score == 84.5


def test_persists_symbol_history(
    tmp_path,
) -> None:
    service = create_service(tmp_path)
    service.capture_current()

    history = service.list_history(
        symbol="NVDA",
        limit=10,
        capture_current=False,
    )

    assert len(history) == 1
    assert history[0].headline == (
        "NVIDIA raises revenue guidance."
    )
