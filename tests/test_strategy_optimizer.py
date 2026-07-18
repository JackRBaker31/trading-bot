from datetime import date

from app.historical_data import HistoricalPrice
from app.risk import RiskLimits
from app.strategy_optimizer import (
    StrategyOptimizer,
)


def create_optimizer() -> StrategyOptimizer:
    return StrategyOptimizer(
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
    ]


def test_optimizes_generated_strategy_grid() -> None:
    optimizer = create_optimizer()

    rows = optimizer.optimize(
        historical_prices=create_prices(),
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

    assert len(rows) == 2
    assert rows[0].total_return_percent > (
        rows[1].total_return_percent
    )
    assert "Drop=2" in rows[0].name