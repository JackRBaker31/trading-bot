from datetime import date, datetime, timezone

from app.decision_outcome_models import (
    DecisionOutcomeObservation,
)
from app.decision_outcome_repository import (
    DecisionOutcomeRepository,
)


NOW = datetime(
    2026,
    7,
    24,
    17,
    0,
    tzinfo=timezone.utc,
)


def observation(
    *,
    outcome_id: str = "OUTCOME-1",
) -> DecisionOutcomeObservation:
    return DecisionOutcomeObservation(
        outcome_id=outcome_id,
        decision_id=(
            "KAIRO-2026-ABC"
        ),
        symbol="AAPL",
        horizon_days=7,
        target_date=date(
            2026,
            7,
            20,
        ),
        observed_at=NOW,
        entry_price=100.0,
        observed_price=105.0,
        absolute_return=0.05,
        benchmark_symbol="SPY",
        benchmark_entry_price=500.0,
        benchmark_observed_price=510.0,
        benchmark_return=0.02,
        alpha=0.03,
        maximum_favourable_excursion=(
            0.07
        ),
        maximum_drawdown=-0.02,
        status="POSITIVE",
    )


def test_saves_and_reads_outcome(
    tmp_path,
) -> None:
    repository = (
        DecisionOutcomeRepository(
            database_path=str(
                tmp_path
                / "application.db"
            )
        )
    )
    repository.initialize()

    assert repository.save_if_new(
        observation=observation()
    )

    records = (
        repository
        .list_for_decision(
            decision_id=(
                "KAIRO-2026-ABC"
            )
        )
    )

    assert len(records) == 1
    assert (
        records[0].alpha
        == 0.03
    )
    assert (
        repository.count_all()
        == 1
    )


def test_duplicate_horizon_is_ignored(
    tmp_path,
) -> None:
    repository = (
        DecisionOutcomeRepository(
            database_path=str(
                tmp_path
                / "application.db"
            )
        )
    )
    repository.initialize()

    assert repository.save_if_new(
        observation=observation()
    )
    assert not repository.save_if_new(
        observation=observation(
            outcome_id="OUTCOME-2"
        )
    )
