from datetime import date, datetime, timedelta, timezone

from app.backtest_models import (
    HistoricalPriceBar,
)
from app.decision_memory_models import (
    DecisionMemoryRecord,
)
from app.decision_outcome_repository import (
    DecisionOutcomeRepository,
)
from app.decision_outcome_service import (
    DecisionOutcomeService,
)


NOW = datetime(
    2026,
    7,
    24,
    17,
    0,
    tzinfo=timezone.utc,
)


def decision(
) -> DecisionMemoryRecord:
    return DecisionMemoryRecord(
        decision_id=(
            "KAIRO-2026-ABC"
        ),
        fingerprint="fingerprint",
        captured_at=NOW,
        thesis_generated_at=(
            NOW
            - timedelta(
                days=10
            )
        ),
        symbol="AAPL",
        recommendation="WATCH",
        score=72.0,
        confidence=0.82,
        confidence_coverage=1.0,
        risk_tier="MEDIUM",
        time_horizon="SWING",
        suggested_position_value=0.0,
        eligible_for_execution=False,
        headline="Apple update.",
        primary_driver="NEWS",
        capabilities=(),
        reasons=(),
        blockers=(),
        warnings=(),
        executed=False,
        paper_trade_id=None,
    )


def bars(
    *,
    symbol: str,
    starting_price: float,
) -> list[HistoricalPriceBar]:
    start = date(
        2026,
        7,
        1,
    )

    return [
        HistoricalPriceBar(
            symbol=symbol,
            trading_date=(
                start
                + timedelta(
                    days=index
                )
            ),
            open_price=(
                starting_price
                + index
                - 0.2
            ),
            high_price=(
                starting_price
                + index
                + 1.0
            ),
            low_price=(
                starting_price
                + index
                - 1.0
            ),
            close_price=(
                starting_price
                + index
            ),
            volume=1_000_000,
        )
        for index in range(40)
    ]


def test_captures_due_horizons(
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

    service = DecisionOutcomeService(
        repository=repository,
        decisions_provider=(
            lambda limit: (
                decision(),
            )
        ),
        bars_provider=(
            lambda symbol, output_size: (
                bars(
                    symbol=symbol,
                    starting_price=(
                        100.0
                        if symbol == "AAPL"
                        else 500.0
                    ),
                )
            )
        ),
        now_provider=lambda: NOW,
        horizons=(1, 7, 30),
    )
    service.initialize()

    result = service.capture_due()

    assert (
        result
        .created_observation_count
        == 2
    )
    assert (
        repository
        .completed_horizons(
            decision_id=(
                "KAIRO-2026-ABC"
            )
        )
        == (1, 7)
    )

    overview = service.overview()

    assert overview.observation_count == 2
    assert (
        overview
        .tracked_decision_count
        == 1
    )


def test_second_capture_is_idempotent(
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

    service = DecisionOutcomeService(
        repository=repository,
        decisions_provider=(
            lambda limit: (
                decision(),
            )
        ),
        bars_provider=(
            lambda symbol, output_size: (
                bars(
                    symbol=symbol,
                    starting_price=100.0,
                )
            )
        ),
        now_provider=lambda: NOW,
        horizons=(1, 7),
    )
    service.initialize()

    first = service.capture_due()
    second = service.capture_due()

    assert (
        first
        .created_observation_count
        == 2
    )
    assert (
        second
        .created_observation_count
        == 0
    )
