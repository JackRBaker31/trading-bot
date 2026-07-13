import pytest

from app.broker import BrokerOrderResult
from app.order_verification import (
    OrderVerificationService,
    OrderVerificationStatus,
)
from app.orders import Order, OrderSide
from app.paper_order_execution import (
    PaperOrderExecutionService,
)
from app.paper_order_workflow import (
    PaperOrderWorkflow,
)
from app.paper_trading_gate import GateDecision
from app.portfolio import Portfolio
from app.broker import (
    BrokerOrderResult,
    BrokerResourceNotFoundError,
)
from app.order_polling import OrderPollingService
from app.duplicate_order_guard import (DuplicateOrderGuard,
)

class FakeBroker:
    def __init__(
        self,
        verification_order: BrokerOrderResult,
        pending_order_not_found: bool = False,
        historical_order: (
            BrokerOrderResult | None
        ) = None,
    ) -> None:
        self.verification_order = (
            verification_order
        )

        self.pending_order_not_found = (
            pending_order_not_found
        )

        self.historical_order = historical_order

        self.submission_calls: list[
            dict[str, object]
        ] = []

        self.status_calls: list[int] = []
        self.history_calls: list[int] = []

    def place_market_order(
        self,
        ticker: str,
        quantity: float,
        extended_hours: bool = False,
    ) -> BrokerOrderResult:
        self.submission_calls.append(
            {
                "ticker": ticker,
                "quantity": quantity,
                "extended_hours": extended_hours,
            }
        )

        return BrokerOrderResult(
            order_id=123456,
            ticker=ticker,
            quantity=quantity,
            side=(
                "BUY"
                if quantity > 0
                else "SELL"
            ),
            status="NEW",
            order_type="MARKET",
            filled_quantity=0.0,
            filled_value=0.0,
            currency="GBP",
        )

    def get_pending_order(
        self,
        order_id: int,
    ) -> BrokerOrderResult:
        self.status_calls.append(
            order_id
        )

        if self.pending_order_not_found:
            raise BrokerResourceNotFoundError(
                "Pending order was not found."
            )

        return self.verification_order
    
    def find_historical_order(
        self,
        order_id: int,
        max_pages: int = 5,
    ) -> BrokerOrderResult | None:
        self.history_calls.append(
            order_id
        )

        return self.historical_order

class FakeOrderJournal:
    def __init__(self) -> None:
        self.record_calls: list[
            dict[str, object]
        ] = []

    def record(
        self,
        order: Order,
        event: str,
        broker_order_id: int | None = None,
        reason: str = "",
    ) -> None:
        self.record_calls.append(
            {
                "order": order,
                "event": event,
                "broker_order_id": (
                    broker_order_id
                ),
                "reason": reason,
            }
        )


def create_broker_order(
    status: str,
    quantity: float = 2.0,
    filled_quantity: float = 0.0,
    filled_value: float = 0.0,
    side: str = "BUY",
) -> BrokerOrderResult:
    return BrokerOrderResult(
        order_id=123456,
        ticker="AAPL_US_EQ",
        quantity=quantity,
        side=side,
        status=status,
        order_type="MARKET",
        filled_quantity=filled_quantity,
        filled_value=filled_value,
        currency="GBP",
    )


def approved_gate() -> GateDecision:
    return GateDecision(
        approved=True,
        reason=(
            "Paper trading safety checks passed."
        ),
    )


def create_workflow(
    broker: FakeBroker,
    portfolio: Portfolio,
    max_attempts: int = 1,
    order_journal: FakeOrderJournal | None = None,
) -> PaperOrderWorkflow:
    verification_service = (
        OrderVerificationService()
    )

    execution_service = (
        PaperOrderExecutionService(
            broker=broker,
            symbol_mapping={
                "AAPL": "AAPL_US_EQ",
            },
        )
    )

    polling_service = OrderPollingService(
        broker=broker,
        verification_service=verification_service,
        max_attempts=max_attempts,
        poll_interval_seconds=0,
        sleep_function=lambda _: None,
    )

    journal = (
        order_journal
        if order_journal is not None
        else FakeOrderJournal()
    )

    return PaperOrderWorkflow(
        execution_service=execution_service,
        polling_service=polling_service,
        verification_service=verification_service,
        duplicate_order_guard=DuplicateOrderGuard(),
        order_journal=journal,
        portfolio=portfolio,
    )

def test_filled_buy_updates_portfolio() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="FILLED",
            filled_quantity=2.0,
            filled_value=300.0,
        )
    )

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    result = workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert result.submitted is True
    assert result.portfolio_updated is True
    assert portfolio.positions == {
        "AAPL": 2,
    }
    assert portfolio.cash == 4_700.00
    assert broker.status_calls == [
        123456,
    ]


def test_pending_order_does_not_update_portfolio() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="NEW",
        )
    )

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    result = workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert result.submitted is True
    assert result.portfolio_updated is False
    assert portfolio.positions == {}
    assert portfolio.cash == 5_000.00

    assert (
        result.verification_result is not None
    )

    assert (
        result.verification_result.status
        == OrderVerificationStatus.PENDING
    )


def test_partially_filled_order_does_not_update_portfolio() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="PARTIALLY_FILLED",
            filled_quantity=1.0,
            filled_value=150.0,
        )
    )

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    result = workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert result.portfolio_updated is False
    assert portfolio.positions == {}
    assert portfolio.cash == 5_000.00


def test_failed_order_does_not_update_portfolio() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="REJECTED",
        )
    )

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    result = workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert result.portfolio_updated is False
    assert portfolio.positions == {}
    assert portfolio.cash == 5_000.00


def test_blocked_gate_never_submits() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="FILLED",
            filled_quantity=2.0,
            filled_value=300.0,
        )
    )

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    result = workflow.execute(
        order=order,
        gate_decision=GateDecision(
            approved=False,
            reason="Market is closed.",
        ),
    )

    assert result.submitted is False
    assert result.portfolio_updated is False
    assert broker.submission_calls == []
    assert broker.status_calls == []


def test_mismatched_filled_quantity_blocks_update() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="FILLED",
            filled_quantity=1.0,
            filled_value=150.0,
        )
    )

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    result = workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert result.portfolio_updated is False
    assert "does not match" in result.reason
    assert portfolio.positions == {}


def test_invalid_filled_value_blocks_update() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="FILLED",
            filled_quantity=2.0,
            filled_value=0.0,
        )
    )

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    result = workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert result.portfolio_updated is False
    assert "invalid filled value" in result.reason


def test_filled_sell_updates_portfolio() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    portfolio.buy(
        symbol="AAPL",
        quantity=2,
        price=150.00,
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="FILLED",
            quantity=-2.0,
            filled_quantity=2.0,
            filled_value=320.0,
            side="SELL",
        )
    )

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.SELL,
        quantity=2,
        price=160.00,
    )

    result = workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert result.portfolio_updated is True
    assert portfolio.positions == {}
    assert portfolio.cash == 5_020.00

def test_negative_quantity_tolerance_is_rejected() -> None:
    broker = FakeBroker(
        verification_order=create_broker_order(
            status="NEW",
        )
    )

    execution_service = (
        PaperOrderExecutionService(
            broker=broker,
            symbol_mapping={
                "AAPL": "AAPL_US_EQ",
            },
        )
    )

    verification_service = (
        OrderVerificationService()
    )

    polling_service = OrderPollingService(
        broker=broker,
        verification_service=verification_service,
        max_attempts=1,
        poll_interval_seconds=0,
        sleep_function=lambda _: None,
    )

    with pytest.raises(
        ValueError,
        match="Quantity tolerance",
    ):
        PaperOrderWorkflow(
            execution_service=execution_service,
            polling_service=polling_service,
            verification_service=verification_service,
            duplicate_order_guard=DuplicateOrderGuard(),
            order_journal=FakeOrderJournal(),
            portfolio=Portfolio(
                starting_cash=5_000.00
            ),
            quantity_tolerance=-1,
        )

def test_historical_filled_order_updates_portfolio() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    historical_order = create_broker_order(
        status="FILLED",
        filled_quantity=2.0,
        filled_value=300.0,
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="NEW",
        ),
        pending_order_not_found=True,
        historical_order=historical_order,
    )

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
    )

    result = workflow.execute(
        order=Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=2,
            price=150.00,
        ),
        gate_decision=approved_gate(),
    )

    assert result.submitted is True
    assert result.portfolio_updated is True
    assert portfolio.positions == {
        "AAPL": 2,
    }
    assert portfolio.cash == 4_700.00
    assert broker.status_calls == [
        123456,
    ]
    assert broker.history_calls == [
        123456,
    ]


def test_missing_pending_and_historical_order_is_unknown() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="NEW",
        ),
        pending_order_not_found=True,
        historical_order=None,
    )

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
    )

    result = workflow.execute(
        order=Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=2,
            price=150.00,
        ),
        gate_decision=approved_gate(),
    )

    assert result.submitted is True
    assert result.portfolio_updated is False
    assert "not found" in result.reason
    assert portfolio.positions == {}
    assert portfolio.cash == 5_000.00
    assert broker.history_calls == [
        123456,
    ]


def test_pending_order_does_not_search_history() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="NEW",
        ),
    )

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
    )

    result = workflow.execute(
        order=Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=2,
            price=150.00,
        ),
        gate_decision=approved_gate(),
    )

    assert result.portfolio_updated is False
    assert broker.status_calls == [
        123456,
    ]
    assert broker.history_calls == []

def test_duplicate_order_is_blocked() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="NEW"
        )
    )

    guard = DuplicateOrderGuard()

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    guard.reserve(order)

    verification_service = (
        OrderVerificationService()
    )

    workflow = PaperOrderWorkflow(
        execution_service=PaperOrderExecutionService(
            broker=broker,
            symbol_mapping={
                "AAPL": "AAPL_US_EQ",
            },
        ),
        polling_service=OrderPollingService(
            broker=broker,
            verification_service=verification_service,
            max_attempts=1,
            poll_interval_seconds=0,
            sleep_function=lambda _: None,
        ),
        verification_service=verification_service,
        duplicate_order_guard=guard,
        order_journal=FakeOrderJournal(),
        portfolio=portfolio,
    )

    result = workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert result.submitted is False
    assert "already being processed" in result.reason
    assert broker.submission_calls == []


def test_order_reservation_is_released_after_workflow() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="REJECTED"
        )
    )

    guard = DuplicateOrderGuard()

    verification_service = (
        OrderVerificationService()
    )

    workflow = PaperOrderWorkflow(
        execution_service=PaperOrderExecutionService(
            broker=broker,
            symbol_mapping={
                "AAPL": "AAPL_US_EQ",
            },
        ),
        polling_service=OrderPollingService(
            broker=broker,
            verification_service=verification_service,
            max_attempts=1,
            poll_interval_seconds=0,
            sleep_function=lambda _: None,
        ),
        verification_service=verification_service,
        duplicate_order_guard=guard,
        order_journal=FakeOrderJournal(),
        portfolio=portfolio,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert guard.is_reserved(order) is False

def test_approved_reservation_is_recorded() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="NEW",
        )
    )

    journal = FakeOrderJournal()

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
        order_journal=journal,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert journal.record_calls[0] == {
        "order": order,
        "event": "RESERVED",
        "broker_order_id": None,
        "reason": (
            "Order reservation created."
        ),
    }

def test_duplicate_reservation_is_not_recorded() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="NEW",
        )
    )

    guard = DuplicateOrderGuard()
    journal = FakeOrderJournal()

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    guard.reserve(order)

    verification_service = (
        OrderVerificationService()
    )

    workflow = PaperOrderWorkflow(
        execution_service=PaperOrderExecutionService(
            broker=broker,
            symbol_mapping={
                "AAPL": "AAPL_US_EQ",
            },
        ),
        polling_service=OrderPollingService(
            broker=broker,
            verification_service=verification_service,
            max_attempts=1,
            poll_interval_seconds=0,
            sleep_function=lambda _: None,
        ),
        verification_service=verification_service,
        duplicate_order_guard=guard,
        order_journal=journal,
        portfolio=portfolio,
    )

    result = workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert result.submitted is False
    assert journal.record_calls == []
    assert broker.submission_calls == []


def test_successful_submission_is_recorded() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="NEW",
        )
    )

    journal = FakeOrderJournal()

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
        order_journal=journal,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert journal.record_calls[:2] == [
        {
            "order": order,
            "event": "RESERVED",
            "broker_order_id": None,
            "reason": (
                "Order reservation created."
            ),
        },
        {
            "order": order,
            "event": "SUBMITTED",
            "broker_order_id": 123456,
            "reason": (
                "Order submitted to the Trading 212 "
                "demo environment."
            ),
        },
    ]

def test_rejected_submission_is_not_recorded_as_submitted() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="NEW",
        )
    )

    journal = FakeOrderJournal()

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
        order_journal=journal,
    )

    order = Order(
        symbol="MSFT",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    result = workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert result.submitted is False

    assert journal.record_calls == [
        {
            "order": order,
            "event": "RESERVED",
            "broker_order_id": None,
            "reason": (
                "Order reservation created."
            ),
        }
    ]

    assert broker.submission_calls == []

def test_pending_order_is_recorded() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="NEW",
        )
    )

    journal = FakeOrderJournal()

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
        order_journal=journal,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    result = workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert (
        result.verification_result is not None
    )

    assert (
        result.verification_result.status
        == OrderVerificationStatus.PENDING
    )

    assert journal.record_calls[-1] == {
        "order": order,
        "event": "PENDING",
        "broker_order_id": 123456,
        "reason": (
            "The broker order did not reach a "
            "terminal state before polling timed out."
        ),
    }

def test_filled_order_is_not_recorded_as_pending() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="FILLED",
            filled_quantity=2.0,
            filled_value=300.0,
        )
    )

    journal = FakeOrderJournal()

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
        order_journal=journal,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    result = workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert result.portfolio_updated is True

    recorded_events = [
        call["event"]
        for call in journal.record_calls
    ]

    assert "PENDING" not in recorded_events

def test_partially_filled_order_is_recorded() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="PARTIALLY_FILLED",
            filled_quantity=1.0,
            filled_value=150.0,
        )
    )

    journal = FakeOrderJournal()

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
        order_journal=journal,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    result = workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert (
        result.verification_result is not None
    )

    assert (
        result.verification_result.status
        == OrderVerificationStatus.PARTIALLY_FILLED
    )

    assert journal.record_calls[-1] == {
        "order": order,
        "event": "PARTIALLY_FILLED",
        "broker_order_id": 123456,
        "reason": (
            "The broker order did not reach a "
            "terminal state before polling timed out."
        ),
    }

def test_pending_order_is_not_recorded_as_partially_filled() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="NEW",
        )
    )

    journal = FakeOrderJournal()

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
        order_journal=journal,
    )

    workflow.execute(
        order=Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=2,
            price=150.00,
        ),
        gate_decision=approved_gate(),
    )

    recorded_events = [
        call["event"]
        for call in journal.record_calls
    ]

    assert recorded_events == [
        "RESERVED",
        "SUBMITTED",
        "PENDING",
    ]

def test_filled_order_is_recorded() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="FILLED",
            filled_quantity=2.0,
            filled_value=300.0,
        )
    )

    journal = FakeOrderJournal()

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
        order_journal=journal,
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    result = workflow.execute(
        order=order,
        gate_decision=approved_gate(),
    )

    assert result.portfolio_updated is True

    assert (
        result.verification_result is not None
    )

    assert journal.record_calls[-1] == {
        "order": order,
        "event": "FILLED",
        "broker_order_id": 123456,
        "reason": result.verification_result.reason,
    }

def test_pending_order_is_not_recorded_as_filled() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        verification_order=create_broker_order(
            status="NEW",
        )
    )

    journal = FakeOrderJournal()

    workflow = create_workflow(
        broker=broker,
        portfolio=portfolio,
        order_journal=journal,
    )

    workflow.execute(
        order=Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=2,
            price=150.00,
        ),
        gate_decision=approved_gate(),
    )

    recorded_events = [
        call["event"]
        for call in journal.record_calls
    ]

    assert "FILLED" not in recorded_events