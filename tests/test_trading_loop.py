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

class RecordingMarketDataProvider:
    def __init__(self) -> None:
        self.requested_symbols: list[str] | None = None

    def get_prices(
        self,
        symbols: list[str],
    ) -> dict[str, float]:
        self.requested_symbols = symbols

        return {
            "AAPL": 150.00,
            "MSFT": 320.00,
        }

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

    def test_loop_uses_provider_through_market_data_interface(
    tmp_path: Path,
) -> None:
        log_file = tmp_path / "trade_log.jsonl"

    provider = RecordingMarketDataProvider()

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

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=RiskEngine(limits),
        trade_log=TradeLog(
            file_path=str(log_file)
        ),
    )

    trading_loop = TradingLoop(
        symbols=["aapl", "msft"],
        market_data=provider,  # type: ignore[arg-type]
        strategy=BuyTheDipStrategy(),
        execution_service=execution_service,
        interval_seconds=0,
    )

    trading_loop.run(cycles=1)

    assert provider.requested_symbols == [
        "AAPL",
        "MSFT",
    ]
    assert portfolio.positions == {}

def test_loop_logs_session_summary(
    tmp_path: Path,
    caplog,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    trading_loop, _, _ = create_trading_loop(
        log_file
    )

    with caplog.at_level(
        "INFO",
        logger="app.trading_loop",
    ):
        trading_loop.run(cycles=2)

    assert (
        "trading_session_finished "
        "cycles_completed=2 "
        "symbol_count=2"
        in caplog.text
    )

def test_continuous_loop_stops_when_requested(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    trading_loop, _, _ = create_trading_loop(
        log_file
    )

    completed_cycles: list[int] = []

    def before_cycle(
        cycle_number: int,
    ) -> None:
        completed_cycles.append(
            cycle_number
        )

    def stop_requested() -> bool:
        return len(completed_cycles) >= 3

    trading_loop.run(
        cycles=None,
        before_cycle=before_cycle,
        stop_requested=stop_requested,
    )

    assert completed_cycles == [
        1,
        2,
        3,
    ]

from app.active_order_manager import (
    ActiveOrderManager,
)
from app.broker import BrokerOrderResult


def test_loop_skips_symbol_with_active_order(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    trading_loop, portfolio, market_data = (
        create_trading_loop(log_file)
    )

    trading_loop.active_order_manager = (
        ActiveOrderManager(
            symbol_mapping={
                "AAPL": "AAPL_US_EQ",
                "MSFT": "MSFT_US_EQ",
            },
            active_orders=[
                BrokerOrderResult(
                    order_id=123456,
                    ticker="AAPL_US_EQ",
                    quantity=1.0,
                    side="BUY",
                    status="NEW",
                    order_type="MARKET",
                    filled_quantity=0.0,
                    filled_value=0.0,
                    currency="GBP",
                )
            ],
        )
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

def test_loop_refreshes_active_orders_each_cycle(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    trading_loop, _, _ = create_trading_loop(
        log_file
    )

    class RecordingManager:
        def __init__(self) -> None:
            self.refresh_calls = 0
            self.active_orders = []

        def refresh(self) -> None:
            self.refresh_calls += 1

        def is_symbol_blocked(
            self,
            symbol: str,
        ) -> bool:
            return False

    manager = RecordingManager()

    trading_loop.active_order_manager = manager  # type: ignore[assignment]

    trading_loop.run(
        cycles=3
    )

    assert manager.refresh_calls == 3