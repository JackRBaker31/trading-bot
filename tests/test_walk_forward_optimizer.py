from datetime import date

from app.historical_data import HistoricalPrice
from app.risk import RiskLimits
from app.walk_forward_optimizer import (
    WalkForwardOptimizer,
)


def create_optimizer() -> WalkForwardOptimizer:
    return WalkForwardOptimizer(
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
    return [
        HistoricalPrice(
            trading_date=date(2026, 1, 2),
            prices={"AAPL": 100.0},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 3),
            prices={"AAPL": 95.0},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 4),
            prices={"AAPL": 105.0},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 5),
            prices={"AAPL": 100.0},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 6),
            prices={"AAPL": 94.0},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 7),
            prices={"AAPL": 104.0},
        ),
    ]


def test_optimizes_training_and_validates_winner() -> None:
    optimizer = create_optimizer()

    training_row, validation_row = optimizer.run(
        historical_prices=create_prices(),
        training_fraction=0.5,
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

    assert "Drop=2" in training_row.name
    assert validation_row.name == training_row.name
    assert validation_row.executed_trades > 0