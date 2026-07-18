from datetime import date, timedelta

from app.historical_data import HistoricalPrice
from app.risk import RiskLimits
from app.rolling_walk_forward_optimizer import (
    RollingWalkForwardOptimizer,
)


def create_optimizer() -> RollingWalkForwardOptimizer:
    return RollingWalkForwardOptimizer(
        starting_cash=10_000.0,
        risk_limits=RiskLimits(
            max_order_value=2_000.0,
            max_position_value=3_000.0,
            max_portfolio_exposure=0.5,
            max_trades_per_session=10_000,
            approved_symbols={"AAPL"},
        ),
    )


def create_prices() -> list[HistoricalPrice]:
    values = [
        100.0,
        95.0,
        105.0,
        100.0,
        94.0,
        104.0,
        100.0,
        93.0,
        103.0,
        100.0,
    ]

    start_date = date(
        2026,
        1,
        1,
    )

    return [
        HistoricalPrice(
            trading_date=(
                start_date
                + timedelta(days=index)
            ),
            prices={
                "AAPL": value,
            },
        )
        for index, value in enumerate(
            values
        )
    ]


def test_runs_rolling_walk_forward_windows() -> None:
    optimizer = create_optimizer()

    results = optimizer.run(
        historical_prices=create_prices(),
        training_size=4,
        validation_size=2,
        step_size=2,
        drop_thresholds=[
            2.0,
            10.0,
        ],
        sma_periods=[
            None,
        ],
        rsi_settings=[
            (None, None),
        ],
        cooldown_cycles=[
            0,
        ],
        target_allocation_percent=10.0,
    )

    assert len(results) == 3

    assert [
        result.window_number
        for result in results
    ] == [
        1,
        2,
        3,
    ]

    assert all(
        result.validation_result.name
        == result.training_result.name
        for result in results
    )

    assert all(
        result.training_result.name
        for result in results
    )