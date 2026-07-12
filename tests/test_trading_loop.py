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
from datetime import datetime
from zoneinfo import ZoneInfo

from app.market_session import (
    MarketSession,
    MarketSessionStatus,
)


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
        max_trades_per_session=3,
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

    assert portfolio.positions["AAPL"] == 6
    assert portfolio.cash == 9_124.00
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
        max_trades_per_session=3,
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

def test_loop_skips_trading_when_market_is_closed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    trading_loop, portfolio, market_data = (
        create_trading_loop(log_file)
    )

    market_session = MarketSession(
        timezone_name="America/New_York",
        opening_time="09:30",
        closing_time="16:00",
    )

    closed_status = MarketSessionStatus(
        is_open=False,
        reason="Market has closed.",
        local_time=datetime(
            2026,
            7,
            13,
            17,
            0,
            tzinfo=ZoneInfo(
                "America/New_York"
            ),
        ),
    )

    monkeypatch.setattr(
        market_session,
        "get_status",
        lambda: closed_status,
    )

    trading_loop.market_session = (
        market_session
    )

    trading_loop.enforce_market_hours = (
        True
    )

    def change_price(
        cycle_number: int,
    ) -> None:
        if cycle_number == 2:
            market_data.set_price(
                "AAPL",
                146.00,
            )

    trading_loop.run(
        cycles=2,
        before_cycle=change_price,
    )

    assert portfolio.positions == {}
    assert portfolio.cash == 10_000.00
    assert not log_file.exists()