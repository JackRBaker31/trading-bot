from pathlib import Path

import pytest

from app.buy_the_dip import BuyTheDipStrategy
from app.execution import ExecutionService
from app.portfolio import Portfolio
from app.risk import RiskEngine, RiskLimits
from app.simulated_market_data import (
    SimulatedMarketDataProvider,
)
from app.trade_log import TradeLog
from app.trading_loop import TradingLoop


def create_trading_loop(
    log_file: Path,
) -> tuple[
    TradingLoop,
    Portfolio,
    SimulatedMarketDataProvider,
]:
    market_data = SimulatedMarketDataProvider(
        prices={
            "AAPL": 150.00,
            "MSFT": 320.00,
        }
    )

    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        approved_symbols={"AAPL", "MSFT"},
    )

    risk_engine = RiskEngine(
        limits=limits
    )

    trade_log = TradeLog(
        file_path=str(log_file)
    )

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=risk_engine,
        trade_log=trade_log,
    )

    strategy = BuyTheDipStrategy()

    trading_loop = TradingLoop(
        symbols=["AAPL", "MSFT"],
        market_data=market_data,
        strategy=strategy,
        execution_service=execution_service,
        interval_seconds=0,
    )

    return trading_loop, portfolio, market_data


def test_loop_executes_strategy_order(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    trading_loop, portfolio, market_data = (
        create_trading_loop(log_file)
    )

    def change_price(cycle_number: int) -> None:
        if cycle_number == 2:
            market_data.set_price(
                "AAPL",
                146.00,
            )

    trading_loop.run(
        cycles=2,
        before_cycle=change_price,
    )

    assert portfolio.positions["AAPL"] == 5
    assert portfolio.cash == 9_270.00
    assert log_file.exists()


def test_loop_with_no_price_drop_executes_nothing(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    trading_loop, portfolio, _ = (
        create_trading_loop(log_file)
    )

    trading_loop.run(cycles=2)

    assert portfolio.positions == {}
    assert portfolio.cash == 10_000.00
    assert not log_file.exists()


def test_loop_rejects_invalid_cycle_count(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    trading_loop, _, _ = create_trading_loop(
        log_file
    )

    with pytest.raises(
        ValueError,
        match="Cycles must be greater than zero",
    ):
        trading_loop.run(cycles=0)


def test_loop_rejects_empty_symbol_list(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    market_data = SimulatedMarketDataProvider(
        prices={"AAPL": 150.00}
    )

    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        approved_symbols={"AAPL"},
    )

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=RiskEngine(limits),
        trade_log=TradeLog(
            file_path=str(log_file)
        ),
    )

    with pytest.raises(
        ValueError,
        match="At least one symbol",
    ):
        TradingLoop(
            symbols=[],
            market_data=market_data,
            strategy=BuyTheDipStrategy(),
            execution_service=execution_service,
            interval_seconds=0,
        )