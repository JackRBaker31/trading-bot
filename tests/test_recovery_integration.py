from pathlib import Path

from app.broker import BrokerOrderResult
from app.order_journal import OrderJournal
from app.order_polling import OrderPollingService
from app.order_verification import (
    OrderVerificationService,
)
from app.orders import Order, OrderSide
from app.portfolio import Portfolio
from app.portfolio_store import PortfolioStore
from app.recovery_factory import (
    create_recovery_startup_service,
)


class FakeBroker:
    def __init__(
        self,
        broker_order: BrokerOrderResult,
    ) -> None:
        self.broker_order = broker_order
        self.pending_calls: list[int] = []
        self.history_calls: list[int] = []

    def get_pending_order(
        self,
        order_id: int,
    ) -> BrokerOrderResult:
        self.pending_calls.append(order_id)
        return self.broker_order

    def find_historical_order(
        self,
        order_id: int,
        max_pages: int = 5,
    ) -> BrokerOrderResult | None:
        self.history_calls.append(order_id)
        return None


def create_broker_order(
    *,
    status: str,
    filled_quantity: float = 0.0,
    filled_value: float = 0.0,
) -> BrokerOrderResult:
    return BrokerOrderResult(
        order_id=123456,
        ticker="AAPL_US_EQ",
        quantity=2.0,
        side="BUY",
        status=status,
        order_type="MARKET",
        filled_quantity=filled_quantity,
        filled_value=filled_value,
        currency="GBP",
    )


def create_submitted_journal(
    tmp_path: Path,
) -> OrderJournal:
    journal = OrderJournal(
        path=tmp_path / "order_journal.jsonl"
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    journal.record(
        order=order,
        event="RESERVED",
        reason="Order reservation created.",
    )

    journal.record(
        order=order,
        event="SUBMITTED",
        broker_order_id=123456,
        reason="Order submitted to Demo.",
    )

    return journal


def create_recovery_service(
    *,
    tmp_path: Path,
    broker: FakeBroker,
    journal: OrderJournal,
    portfolio: Portfolio,
    portfolio_store: PortfolioStore,
):
    polling_service = OrderPollingService(
        broker=broker,
        verification_service=(
            OrderVerificationService()
        ),
        max_attempts=1,
        poll_interval_seconds=0,
        sleep_function=lambda _: None,
    )

    return create_recovery_startup_service(
        order_journal=journal,
        polling_service=polling_service,
        portfolio=portfolio,
        portfolio_store=portfolio_store,
    )


def test_filled_order_is_recovered_end_to_end(
    tmp_path: Path,
) -> None:
    journal = create_submitted_journal(
        tmp_path=tmp_path
    )

    portfolio_store = PortfolioStore(
        file_path=str(
            tmp_path / "portfolio.json"
        )
    )

    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        broker_order=create_broker_order(
            status="FILLED",
            filled_quantity=2.0,
            filled_value=300.0,
        )
    )

    service = create_recovery_service(
        tmp_path=tmp_path,
        broker=broker,
        journal=journal,
        portfolio=portfolio,
        portfolio_store=portfolio_store,
    )

    trading_calls = 0

    def start_trading() -> None:
        nonlocal trading_calls
        trading_calls += 1

    result = service.start(
        start_trading=start_trading
    )

    assert result.trading_started is True
    assert trading_calls == 1

    assert portfolio.cash == 4_700.00
    assert portfolio.positions == {
        "AAPL": 2,
    }
    assert (
        portfolio.applied_broker_order_ids
        == {123456}
    )

    persisted_portfolio = (
        portfolio_store.load()
    )

    assert persisted_portfolio.cash == 4_700.00
    assert persisted_portfolio.positions == {
        "AAPL": 2,
    }
    assert (
        persisted_portfolio
        .applied_broker_order_ids
        == {123456}
    )

    latest_entries = journal.latest_entries()

    assert (
        latest_entries["AAPL:BUY:2"].event
        == "FILLED"
    )

    assert broker.pending_calls == [
        123456,
    ]


def test_pending_order_blocks_startup_end_to_end(
    tmp_path: Path,
) -> None:
    journal = create_submitted_journal(
        tmp_path=tmp_path
    )

    portfolio_store = PortfolioStore(
        file_path=str(
            tmp_path / "portfolio.json"
        )
    )

    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        broker_order=create_broker_order(
            status="NEW",
        )
    )

    service = create_recovery_service(
        tmp_path=tmp_path,
        broker=broker,
        journal=journal,
        portfolio=portfolio,
        portfolio_store=portfolio_store,
    )

    trading_calls = 0

    def start_trading() -> None:
        nonlocal trading_calls
        trading_calls += 1

    result = service.start(
        start_trading=start_trading
    )

    assert result.trading_started is False
    assert trading_calls == 0

    assert result.decision.approved is False
    assert (
        result.recovery_report.startup_blocked
        is True
    )

    assert portfolio.cash == 5_000.00
    assert portfolio.positions == {}
    assert (
        portfolio.applied_broker_order_ids
        == set()
    )

    latest_entries = journal.latest_entries()

    assert (
        latest_entries["AAPL:BUY:2"].event
        == "PENDING"
    )

    assert broker.pending_calls == [
        123456,
    ]


def test_failed_order_is_recovered_end_to_end(
    tmp_path: Path,
) -> None:
    journal = create_submitted_journal(
        tmp_path=tmp_path
    )

    portfolio_store = PortfolioStore(
        file_path=str(
            tmp_path / "portfolio.json"
        )
    )

    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        broker_order=create_broker_order(
            status="CANCELLED",
        )
    )

    service = create_recovery_service(
        tmp_path=tmp_path,
        broker=broker,
        journal=journal,
        portfolio=portfolio,
        portfolio_store=portfolio_store,
    )

    trading_calls = 0

    def start_trading() -> None:
        nonlocal trading_calls
        trading_calls += 1

    result = service.start(
        start_trading=start_trading
    )

    assert result.trading_started is True
    assert trading_calls == 1

    assert portfolio.cash == 5_000.00
    assert portfolio.positions == {}
    assert (
        portfolio.applied_broker_order_ids
        == set()
    )

    latest_entries = journal.latest_entries()

    assert (
        latest_entries["AAPL:BUY:2"].event
        == "FAILED"
    )

    assert broker.pending_calls == [
        123456,
    ]