from pathlib import Path
import pytest
from app.execution import ExecutionService
from app.orders import Order, OrderSide
from app.portfolio import Portfolio
from app.risk import RiskEngine, RiskLimits
from app.trade_log import TradeLog
from app.execution_cost import (
    ExecutionCostModel,
)


def create_execution_service(
    log_file: Path,
) -> tuple[
    ExecutionService,
    Portfolio,
    TradeLog,
]:
    portfolio = Portfolio(starting_cash=10_000.00)

    limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        max_trades_per_session=3,
        approved_symbols={"AAPL", "MSFT"},
    )

    risk_engine = RiskEngine(limits=limits)

    trade_log = TradeLog(
        file_path=str(log_file),
    )

    service = ExecutionService(
        portfolio=portfolio,
        risk_engine=risk_engine,
        trade_log=trade_log,
    )

    return service, portfolio, trade_log


def test_approved_order_executes_and_is_logged(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    service, portfolio, trade_log = create_execution_service(
        log_file=log_file,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=10,
        price=150.00,
    )

    executed = service.submit_order(
        order=order,
        current_prices={"AAPL": 150.00},
    )

    assert executed is True
    assert portfolio.positions["AAPL"] == 10
    assert len(trade_log.entries) == 1
    assert trade_log.entries[0].executed is True
    assert trade_log.entries[0].approved is True
    assert log_file.exists()


def test_rejected_order_is_logged_but_not_executed(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    service, portfolio, trade_log = create_execution_service(
        log_file=log_file,
    )

    order = Order(
        symbol="TSLA",
        side=OrderSide.BUY,
        quantity=1,
        price=250.00,
    )

    executed = service.submit_order(
        order=order,
        current_prices={"TSLA": 250.00},
    )

    assert executed is False
    assert "TSLA" not in portfolio.positions
    assert len(trade_log.entries) == 1
    assert trade_log.entries[0].executed is False
    assert trade_log.entries[0].approved is False
    assert log_file.exists()


def test_sell_order_updates_portfolio_and_log(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    service, portfolio, trade_log = create_execution_service(
        log_file=log_file,
    )

    buy_order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=5,
        price=150.00,
    )

    sell_order = Order(
        symbol="AAPL",
        side=OrderSide.SELL,
        quantity=2,
        price=155.00,
    )

    service.submit_order(
        order=buy_order,
        current_prices={"AAPL": 150.00},
    )

    executed = service.submit_order(
        order=sell_order,
        current_prices={"AAPL": 155.00},
    )

    assert executed is True
    assert portfolio.positions["AAPL"] == 3
    assert len(trade_log.entries) == 2
    assert trade_log.entries[1].side == "SELL"


def test_trade_log_writes_one_line_per_order(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    service, _, _ = create_execution_service(
        log_file=log_file,
    )

    first_order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    second_order = Order(
        symbol="MSFT",
        side=OrderSide.BUY,
        quantity=1,
        price=320.00,
    )

    service.submit_order(
        order=first_order,
        current_prices={
            "AAPL": 150.00,
            "MSFT": 320.00,
        },
    )

    service.submit_order(
        order=second_order,
        current_prices={
            "AAPL": 150.00,
            "MSFT": 320.00,
        },
    )

    lines = log_file.read_text(
        encoding="utf-8",
    ).splitlines()

    assert len(lines) == 2

def test_executed_trade_increases_risk_trade_count(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    service, _, _ = create_execution_service(
        log_file=log_file,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        price=150.00,
    )

    service.submit_order(
        order=order,
        current_prices={"AAPL": 150.00},
    )

    assert service.risk_engine.executed_trade_count == 1

def test_rejected_trade_does_not_increase_trade_count(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "trade_log.jsonl"

    service, _, _ = create_execution_service(
        log_file=log_file,
    )

    order = Order(
        symbol="TSLA",
        side=OrderSide.BUY,
        quantity=1,
        price=250.00,
    )

    service.submit_order(
        order=order,
        current_prices={"TSLA": 250.00},
    )

    assert service.risk_engine.executed_trade_count == 0

def test_execution_applies_buy_costs(
    tmp_path,
) -> None:
    portfolio = Portfolio(
        starting_cash=10_000.0
    )

    service = ExecutionService(
        portfolio=portfolio,
        risk_engine=RiskEngine(
            RiskLimits(
                max_order_value=5_000.0,
                max_position_value=5_000.0,
                max_portfolio_exposure=1.0,
                max_trades_per_session=10,
                approved_symbols={"AAPL"},
            )
        ),
        trade_log=TradeLog(
            file_path=str(
                tmp_path / "trade_log.jsonl"
            )
        ),
        execution_cost_model=ExecutionCostModel(
            slippage_percent=1.0,
            commission_percent=0.5,
        ),
    )

    executed = service.submit_order(
        order=Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10,
            price=100.0,
        ),
        current_prices={
            "AAPL": 100.0,
        },
    )

    # Slippage fill: 101.00
    # Commission: 0.5% of 1,010 = 5.05
    # Effective price: 101 + 5.05 / 10 = 101.505
    assert executed is True
    assert portfolio.cash == pytest.approx(
        8_984.95
    )
    assert (
        service.trade_log.entries[-1].price
        == pytest.approx(101.505)
    )

def test_execution_applies_sell_costs(
    tmp_path,
) -> None:
    portfolio = Portfolio(
        starting_cash=10_000.0
    )

    portfolio.buy(
        symbol="AAPL",
        quantity=10,
        price=100.0,
    )

    service = ExecutionService(
        portfolio=portfolio,
        risk_engine=RiskEngine(
            RiskLimits(
                max_order_value=5_000.0,
                max_position_value=5_000.0,
                max_portfolio_exposure=1.0,
                max_trades_per_session=10,
                approved_symbols={"AAPL"},
            )
        ),
        trade_log=TradeLog(
            file_path=str(
                tmp_path / "trade_log.jsonl"
            )
        ),
        execution_cost_model=ExecutionCostModel(
            slippage_percent=1.0,
            commission_percent=0.5,
        ),
    )

    executed = service.submit_order(
        order=Order(
            symbol="AAPL",
            side=OrderSide.SELL,
            quantity=10,
            price=110.0,
        ),
        current_prices={
            "AAPL": 110.0,
        },
    )

    # Slippage fill: 108.90
    # Commission: 0.5% of 1,089 = 5.445
    # Effective price: 108.90 - 5.445 / 10
    assert executed is True
    assert portfolio.cash == pytest.approx(
        10_083.555
    )
    assert (
        service.trade_log.entries[-1].price
        == pytest.approx(108.3555)
    )