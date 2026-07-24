from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.symbol_decision_history_service import (
    SymbolDecisionHistoryService,
)
from app.symbol_decision_models import (
    SymbolDecisionTrace,
)
from app.symbol_decision_repository import (
    SymbolDecisionRepository,
)


NOW = datetime(
    2026,
    7,
    24,
    13,
    0,
    tzinfo=timezone.utc,
)


def trace(
    *,
    trace_id: str,
    captured_at: datetime,
    score: float,
    confidence: float,
    rank: int,
    decision: str = "BLOCKED",
    sentiment: str = "POSITIVE",
    classification: str = "WATCH",
    blockers: tuple[str, ...] = (),
) -> SymbolDecisionTrace:
    return SymbolDecisionTrace(
        trace_id=trace_id,
        captured_at=captured_at,
        symbol="NVDA",
        rank=rank,
        decision=decision,
        classification=classification,
        score=score,
        confidence=confidence,
        headline=(
            "NVIDIA guidance update."
        ),
        event_type="EARNINGS",
        sentiment=sentiment,
        eligible_for_trade=False,
        trading_readiness=(
            "NOT_READY"
        ),
        graduation_ready=False,
        summary=(
            "NVDA remains blocked."
        ),
        stages=(),
        blockers=blockers,
    )


def create_service(
    tmp_path,
) -> tuple[
    SymbolDecisionHistoryService,
    SymbolDecisionRepository,
]:
    repository = (
        SymbolDecisionRepository(
            database_path=str(
                tmp_path
                / "application.db"
            )
        )
    )

    service = (
        SymbolDecisionHistoryService(
            repository=repository,
            now_provider=lambda: NOW,
        )
    )

    service.initialize()

    return service, repository


def test_returns_none_without_history(
    tmp_path,
) -> None:
    service, _ = create_service(
        tmp_path
    )

    assert (
        service.compare_latest(
            symbol="NVDA"
        )
        is None
    )


def test_one_snapshot_has_no_comparison(
    tmp_path,
) -> None:
    service, repository = (
        create_service(
            tmp_path
        )
    )

    repository.save(
        trace=trace(
            trace_id="trace-1",
            captured_at=NOW,
            score=70.0,
            confidence=0.80,
            rank=2,
        )
    )

    result = (
        service.compare_latest(
            symbol="nvda"
        )
    )

    assert result is not None
    assert not (
        result
        .comparison_available
    )
    assert (
        result.current.symbol
        == "NVDA"
    )


def test_compares_latest_decisions(
    tmp_path,
) -> None:
    service, repository = (
        create_service(
            tmp_path
        )
    )

    repository.save(
        trace=trace(
            trace_id="trace-1",
            captured_at=(
                NOW
                - timedelta(
                    hours=1
                )
            ),
            score=70.0,
            confidence=0.80,
            rank=3,
            blockers=(
                "Portfolio blocked.",
            ),
        )
    )

    repository.save(
        trace=trace(
            trace_id="trace-2",
            captured_at=NOW,
            score=84.5,
            confidence=0.91,
            rank=1,
            decision=(
                "TRADE_CANDIDATE"
            ),
            classification=(
                "PRIORITY"
            ),
            blockers=(),
        )
    )

    result = (
        service.compare_latest(
            symbol="NVDA"
        )
    )

    assert result is not None
    assert (
        result.comparison_available
    )
    assert (
        result.score_change
        is not None
    )
    assert (
        result.score_change.change
        == 14.5
    )
    assert (
        result.confidence_change
        is not None
    )
    assert round(
        result
        .confidence_change
        .change,
        2,
    ) == 0.11
    assert (
        result.decision_changed
    )
    assert (
        "Portfolio blocked."
        in (
            result
            .cleared_blockers
        )
    )
