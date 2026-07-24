from datetime import datetime, timezone

from app.decision_memory_models import (
    DecisionMemoryCapability,
    DecisionMemoryRecord,
)
from app.decision_memory_repository import (
    DecisionMemoryRepository,
)


NOW = datetime(
    2026,
    7,
    24,
    16,
    0,
    tzinfo=timezone.utc,
)


def record(
    *,
    decision_id: str = (
        "KAIRO-2026-ABC"
    ),
    fingerprint: str = "fingerprint-1",
) -> DecisionMemoryRecord:
    return DecisionMemoryRecord(
        decision_id=decision_id,
        fingerprint=fingerprint,
        captured_at=NOW,
        thesis_generated_at=NOW,
        symbol="AAPL",
        recommendation="INCOMPLETE",
        score=84.5,
        confidence=0.91,
        confidence_coverage=0.83,
        risk_tier="HIGH",
        time_horizon="POSITION",
        suggested_position_value=0.0,
        eligible_for_execution=False,
        headline=(
            "Apple raises guidance."
        ),
        primary_driver="NEWS",
        capabilities=(
            DecisionMemoryCapability(
                capability="NEWS",
                status="AVAILABLE",
                score=22.0,
                maximum=25.0,
                confidence=0.91,
                stance="BULLISH",
                summary=(
                    "News was supportive."
                ),
                evidence=(
                    "Guidance increased.",
                ),
                blockers=(),
            ),
        ),
        reasons=("Strong news.",),
        blockers=(
            "Valuation unavailable.",
        ),
        warnings=(),
        executed=False,
        paper_trade_id=None,
    )


def test_saves_and_reads_record(
    tmp_path,
) -> None:
    repository = (
        DecisionMemoryRepository(
            database_path=str(
                tmp_path
                / "application.db"
            )
        )
    )
    repository.initialize()

    assert repository.save_if_new(
        record=record()
    )

    records = (
        repository.list_recent()
    )

    assert len(records) == 1
    assert (
        records[0].symbol
        == "AAPL"
    )
    assert (
        records[0]
        .capabilities[0]
        .capability
        == "NEWS"
    )
    assert (
        repository.count_all()
        == 1
    )


def test_duplicate_fingerprint_is_ignored(
    tmp_path,
) -> None:
    repository = (
        DecisionMemoryRepository(
            database_path=str(
                tmp_path
                / "application.db"
            )
        )
    )
    repository.initialize()

    assert repository.save_if_new(
        record=record()
    )
    assert not repository.save_if_new(
        record=record(
            decision_id=(
                "KAIRO-2026-DEF"
            )
        )
    )
    assert (
        repository.count_all()
        == 1
    )
