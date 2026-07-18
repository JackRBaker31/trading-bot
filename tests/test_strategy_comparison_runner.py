from datetime import date

import pytest

from app.buy_the_dip import BuyTheDipStrategy
from app.historical_data import HistoricalPrice
from app.risk import RiskLimits
from app.strategy_comparison_runner import (
    StrategyComparisonRunner,
)
from app.strategy_definition import (
    StrategyDefinition,
)


def create_runner() -> StrategyComparisonRunner:
    return StrategyComparisonRunner(
        starting_cash=10_000.0,
        risk_limits=RiskLimits(
            max_order_value=2_000.0,
            max_position_value=3_000.0,
            max_portfolio_exposure=0.5,
            max_trades_per_session=10,
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


def test_runs_and_ranks_multiple_strategies() -> None:
    runner = create_runner()

    rows, results = runner.run(
        historical_prices=create_prices(),
        strategy_definitions=[
            StrategyDefinition(
                name="Loose",
                factory=lambda: BuyTheDipStrategy(
                    drop_threshold_percent=2.0,
                ),
            ),
            StrategyDefinition(
                name="Strict",
                factory=lambda: BuyTheDipStrategy(
                    drop_threshold_percent=10.0,
                ),
            ),
        ],
    )

    assert set(results) == {
        "Loose",
        "Strict",
    }
    assert len(rows) == 2
    assert rows[0].name == "Loose"
    assert (
        results["Loose"].total_return_percent
        > results["Strict"].total_return_percent
    )
    
def test_rejects_non_positive_starting_cash() -> None:
    with pytest.raises(
        ValueError,
        match="Starting cash must be positive",
    ):
        StrategyComparisonRunner(
            starting_cash=0.0,
            risk_limits=RiskLimits(
                max_order_value=1_000.0,
                max_position_value=2_000.0,
                max_portfolio_exposure=0.5,
                max_trades_per_session=10,
                approved_symbols={"AAPL"},
            ),
        )


def test_rejects_empty_strategy_factories() -> None:
    runner = create_runner()

    with pytest.raises(
        ValueError,
        match="At least one strategy definition",
    ):
        runner.run(
            historical_prices=create_prices(),
            strategy_definitions=[],
        )