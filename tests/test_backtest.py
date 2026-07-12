from datetime import date
from pathlib import Path

import pytest

from app.backtest import BacktestEngine
from app.buy_the_dip import BuyTheDipStrategy
from app.execution import ExecutionService
from app.historical_data import HistoricalPrice
from app.portfolio import Portfolio
from app.risk import RiskEngine, RiskLimits
from app.trade_log import TradeLog
from app.backtest_result import EquityPoint

def create_backtest_engine(
    log_file: Path,
) -> tuple[
    BacktestEngine,
    Portfolio,
    TradeLog,
]:
    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        max_trades_per_session=10,
        approved_symbols={"AAPL"},
    )

    trade_log = TradeLog(
        file_path=str(log_file)
    )

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=RiskEngine(limits),
        trade_log=trade_log,
    )

    strategy = BuyTheDipStrategy(
        drop_threshold_percent=2.0,
        target_allocation_percent=10.0,
        cooldown_cycles=2,
    )

    engine = BacktestEngine(
        portfolio=portfolio,
        strategy=strategy,
        execution_service=execution_service,
    )

    return engine, portfolio, trade_log


def test_backtest_executes_strategy_order(
    tmp_path: Path,
) -> None:
    engine, portfolio, trade_log = (
        create_backtest_engine(
            tmp_path / "trade_log.jsonl"
        )
    )

    prices = [
        HistoricalPrice(
            trading_date=date(2026, 1, 2),
            prices={"AAPL": 150.00},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 3),
            prices={"AAPL": 146.00},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 4),
            prices={"AAPL": 150.00},
        ),
    ]

    result = engine.run(
        historical_prices=prices
    )

    assert portfolio.positions["AAPL"] == 6
    assert result.executed_trades == 1
    assert result.rejected_orders == 0
    assert len(result.equity_curve) == 3
    assert len(trade_log.entries) == 1


def test_backtest_calculates_return(
    tmp_path: Path,
) -> None:
    engine, _, _ = create_backtest_engine(
        tmp_path / "trade_log.jsonl"
    )

    prices = [
        HistoricalPrice(
            trading_date=date(2026, 1, 2),
            prices={"AAPL": 150.00},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 3),
            prices={"AAPL": 146.00},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 4),
            prices={"AAPL": 156.00},
        ),
    ]

    result = engine.run(
        historical_prices=prices
    )

    assert result.starting_cash == 10_000.00
    assert result.ending_value == 10_060.00
    assert result.total_return_percent == pytest.approx(
        0.60
    )
    assert result.maximum_drawdown_percent >= 0
    assert result.benchmark_return_percent == pytest.approx(
        4.0
    )
    assert result.excess_return_percent == pytest.approx(
        -3.4
    )
    assert result.average_exposure_percent > 0

def test_backtest_rejects_empty_history(
    tmp_path: Path,
) -> None:
    engine, _, _ = create_backtest_engine(
        tmp_path / "trade_log.jsonl"
    )

    with pytest.raises(
        ValueError,
        match="At least one historical price point",
    ):
        engine.run(
            historical_prices=[]
        )


def test_backtest_records_rejected_orders(
    tmp_path: Path,
) -> None:
    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    limits = RiskLimits(
        max_order_value=100.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        max_trades_per_session=10,
        approved_symbols={"AAPL"},
    )

    trade_log = TradeLog(
        file_path=str(
            tmp_path / "trade_log.jsonl"
        )
    )

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=RiskEngine(limits),
        trade_log=trade_log,
    )

    strategy = BuyTheDipStrategy(
        drop_threshold_percent=2.0,
        target_allocation_percent=10.0,
        cooldown_cycles=2,
    )

    engine = BacktestEngine(
        portfolio=portfolio,
        strategy=strategy,
        execution_service=execution_service,
    )

    prices = [
        HistoricalPrice(
            trading_date=date(2026, 1, 2),
            prices={"AAPL": 150.00},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 3),
            prices={"AAPL": 146.00},
        ),
    ]

    result = engine.run(
        historical_prices=prices
    )

    assert result.executed_trades == 0
    assert result.rejected_orders == 1

def test_maximum_drawdown_is_calculated() -> None:
    equity_curve = [
        EquityPoint(
            label="2026-01-01",
            portfolio_value=10_000.00,
        ),
        EquityPoint(
            label="2026-01-02",
            portfolio_value=11_000.00,
        ),
        EquityPoint(
            label="2026-01-03",
            portfolio_value=9_900.00,
        ),
        EquityPoint(
            label="2026-01-04",
            portfolio_value=10_500.00,
        ),
    ]

    drawdown = (
        BacktestEngine._calculate_maximum_drawdown(
            equity_curve
        )
    )

    assert drawdown == pytest.approx(
        10.0
    )


def test_equal_weight_benchmark_is_calculated() -> None:
    historical_prices = [
        HistoricalPrice(
            trading_date=date(2026, 1, 2),
            prices={
                "AAPL": 100.00,
                "MSFT": 200.00,
            },
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 3),
            prices={
                "AAPL": 110.00,
                "MSFT": 180.00,
            },
        ),
    ]

    benchmark_return = (
        BacktestEngine
        ._calculate_equal_weight_benchmark_return(
            historical_prices
        )
    )

    assert benchmark_return == pytest.approx(
        0.0
    )