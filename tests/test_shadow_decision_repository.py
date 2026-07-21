from datetime import datetime, timezone

from app.shadow_decision import ShadowAction, ShadowDecision
from app.shadow_decision_repository import ShadowDecisionRepository


def create_decision(*, decision_id: str = "decision-1") -> ShadowDecision:
    return ShadowDecision(
        decision_id=decision_id,
        article_id="article-1",
        symbol="aapl",
        created_at=datetime(2026, 7, 20, 10, tzinfo=timezone.utc),
        model_version="KAIRO_SHADOW_V1",
        action=ShadowAction.CONSIDER_LONG,
        score=82.5,
        confidence=0.9,
        sentiment="POSITIVE",
        event_type="STOCK_SHORTTERM_POSITIVE",
        is_material=True,
        headline="Example",
        eligible_for_trade=True,
        reasons=("Strong evidence.",),
        blocking_reasons=(),
        reference_price=100.0,
        reference_captured_at=datetime(
            2026, 7, 20, 9, tzinfo=timezone.utc
        ),
    )


def test_adds_and_lists_decision(tmp_path) -> None:
    repository = ShadowDecisionRepository(
        database_path=str(tmp_path / "application.db")
    )
    repository.initialize()

    assert repository.add_if_missing(
        decision=create_decision()
    ) is True
    assert repository.add_if_missing(
        decision=create_decision(decision_id="decision-2")
    ) is False

    records = repository.list_recent()
    assert len(records) == 1
    assert records[0].symbol == "AAPL"
    assert records[0].action is ShadowAction.CONSIDER_LONG
    assert repository.count() == 1
