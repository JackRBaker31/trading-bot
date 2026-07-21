from datetime import datetime, timezone
from types import SimpleNamespace

from app.intelligence_snapshot import OpportunityClassification
from app.shadow_decision import ShadowAction
from app.shadow_decision_repository import ShadowDecisionRepository
from app.shadow_trading_service import ShadowTradingService


class FakeIntelligenceService:
    def get_snapshot(self):
        opportunity = SimpleNamespace(
            article_id="article-1",
            symbol="AAPL",
            score=84.0,
            classification=OpportunityClassification.CANDIDATE,
            confidence=0.9,
            sentiment="POSITIVE",
            event_type="STOCK_SHORTTERM_POSITIVE",
            is_material=True,
            headline="Example",
            eligible_for_trade=True,
            reasons=("High confidence.",),
            blocking_reasons=(),
        )
        return SimpleNamespace(top_opportunities=(opportunity,))


class EmptySnapshotStore:
    def get_by_article_id(self, article_id):
        del article_id
        return None


class EmptyOutcomeStore:
    def load_all(self):
        return []


def create_service(tmp_path) -> ShadowTradingService:
    service = ShadowTradingService(
        intelligence_service=FakeIntelligenceService(),
        repository=ShadowDecisionRepository(
            database_path=str(tmp_path / "application.db")
        ),
        snapshot_store=EmptySnapshotStore(),
        outcome_store=EmptyOutcomeStore(),
        now_provider=lambda: datetime(
            2026, 7, 20, 10, tzinfo=timezone.utc
        ),
    )
    service.initialize()
    return service


def test_creates_idempotent_shadow_decision(tmp_path) -> None:
    service = create_service(tmp_path)

    first = service.run_analysis()
    second = service.run_analysis()

    assert first.decisions_created == 1
    assert first.decisions_skipped == 0
    assert second.decisions_created == 0
    assert second.decisions_skipped == 1

    page = service.list_decisions()
    assert page["count"] == 1
    assert page["items"][0]["action"] == (
        ShadowAction.CONSIDER_LONG.value
    )


def test_summary_is_research_only(tmp_path) -> None:
    service = create_service(tmp_path)
    service.run_analysis()

    summary = service.get_summary()

    assert summary["decision_count"] == 1
    assert summary["trading_impact"] == "NONE"
    assert summary["performance_by_horizon"][0][
        "measured_count"
    ] == 0
