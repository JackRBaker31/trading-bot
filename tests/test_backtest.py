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
        quantity=5,
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

    assert portfolio.positions["AAPL"] == 5
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
    assert result.ending_value == 10_050.00
    assert result.total_return_percent == pytest.approx(
        0.50
    )


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

    engine = BacktestEngine(
        portfolio=portfolio,
        strategy=BuyTheDipStrategy(
            drop_threshold_percent=2.0,
            quantity=5,
            cooldown_cycles=2,
        ),
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