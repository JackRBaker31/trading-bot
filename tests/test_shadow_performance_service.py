from datetime import datetime, timezone

from app.news_signal_outcome import NewsSignalOutcome
from app.news_signal_outcome_store import NewsSignalOutcomeStore
from app.shadow_decision import (
    ShadowAction,
    ShadowDecision,
)
from app.shadow_decision_repository import (
    ShadowDecisionRepository,
)
from app.shadow_performance_service import (
    ShadowPerformanceService,
)


def add_decision(
    repository,
    *,
    index: int,
    score: float,
    confidence: float,
) -> None:
    repository.add_if_missing(
        decision=ShadowDecision(
            decision_id=f"decision-{index}",
            article_id=f"article-{index}",
            symbol="AAPL",
            created_at=datetime(
                2026, 7, 20, 10, index,
                tzinfo=timezone.utc,
            ),
            model_version="KAIRO_SHADOW_V1",
            action=ShadowAction.CONSIDER_LONG,
            score=score,
            confidence=confidence,
            sentiment="POSITIVE",
            event_type="EARNINGS",
            is_material=True,
            headline="Example",
            eligible_for_trade=False,
            reasons=("Positive signal.",),
            blocking_reasons=(
                "Research only.",
            ),
        )
    )


def test_builds_shadow_performance_report(
    tmp_path,
) -> None:
    repository = ShadowDecisionRepository(
        database_path=str(
            tmp_path / "application.db"
        )
    )
    repository.initialize()
    outcome_store = NewsSignalOutcomeStore(
        file_path=str(
            tmp_path / "outcomes.jsonl"
        )
    )

    for index, return_percent in enumerate(
        (2.0, -1.0, 1.0),
        start=1,
    ):
        add_decision(
            repository,
            index=index,
            score=80.0,
            confidence=0.90,
        )
        outcome_store.append(
            outcome=NewsSignalOutcome(
                article_id=f"article-{index}",
                symbol="AAPL",
                horizon_name="1D",
                signal_published_at=datetime(
                    2026, 7, 20, 9, 0,
                    tzinfo=timezone.utc,
                ),
                observed_at=datetime(
                    2026, 7, 21, 10, index,
                    tzinfo=timezone.utc,
                ),
                reference_price=100.0,
                observed_price=(
                    100.0
                    * (1 + return_percent / 100)
                ),
                return_percent=return_percent,
            )
        )

    report = ShadowPerformanceService(
        repository=repository,
        outcome_store=outcome_store,
        execution_cost_percent=0.20,
        rolling_window_size=2,
    ).get_report()

    one_day = next(
        item
        for item in report.horizons
        if item.horizon == "1D"
    )

    assert report.total_decision_count == 3
    assert one_day.measured_count == 3
    assert (
        one_day.directional_success_percent
        == 66.67
    )
    assert (
        one_day.profitable_after_cost_percent
        == 66.67
    )
    assert one_day.rolling_window_count == 2
    assert one_day.by_event_type[0].name == (
        "EARNINGS"
    )
    assert report.trading_impact == "NONE"


def test_empty_report_is_safe(
    tmp_path,
) -> None:
    repository = ShadowDecisionRepository(
        database_path=str(
            tmp_path / "application.db"
        )
    )
    repository.initialize()

    report = ShadowPerformanceService(
        repository=repository,
        outcome_store=NewsSignalOutcomeStore(
            file_path=str(
                tmp_path / "missing.jsonl"
            )
        ),
    ).get_report()

    assert report.total_decision_count == 0
    assert all(
        item.measured_count == 0
        for item in report.horizons
    )


def test_report_dictionary_includes_frontend_compatibility_fields(
    tmp_path,
) -> None:
    repository = ShadowDecisionRepository(
        database_path=str(tmp_path / "application.db")
    )
    repository.initialize()
    outcome_store = NewsSignalOutcomeStore(
        file_path=str(tmp_path / "outcomes.jsonl")
    )

    add_decision(
        repository,
        index=1,
        score=85.0,
        confidence=0.88,
    )
    outcome_store.append(
        outcome=NewsSignalOutcome(
            article_id="article-1",
            symbol="AAPL",
            horizon_name="1D",
            signal_published_at=datetime(
                2026, 7, 20, 9, 0,
                tzinfo=timezone.utc,
            ),
            observed_at=datetime(
                2026, 7, 21, 10, 0,
                tzinfo=timezone.utc,
            ),
            reference_price=100.0,
            observed_price=101.0,
            return_percent=1.0,
        )
    )

    payload = ShadowPerformanceService(
        repository=repository,
        outcome_store=outcome_store,
    ).get_report().to_dictionary()

    assert payload["available"] is True
    assert payload["generated_at"] is None
    assert payload["periods"]["1d"]["sample_count"] == 1
    assert payload["periods"]["1d"]["coverage"] == 1.0
    assert payload["periods"]["1d"]["average_return"] == 0.01
    assert payload["horizons"][1]["average_return_percent"] == 1.0
