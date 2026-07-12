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


class FakeBroker:
    def __init__(
        self,
        verification_order: BrokerOrderResult,
    ) -> None:
        self.verification_order = (
            verification_order
        )

        self.submission_calls: list[
            dict[str, object]
        ] = []

        self.status_calls: list[int] = []

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

        return self.verification_order


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
) -> PaperOrderWorkflow:
    execution_service = (
        PaperOrderExecutionService(
            broker=broker,
            symbol_mapping={
                "AAPL": "AAPL_US_EQ",
            },
        )
    )

    return PaperOrderWorkflow(
        execution_service=execution_service,
        status_broker=broker,
        verification_service=(
            OrderVerificationService()
        ),
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

    with pytest.raises(
        ValueError,
        match="Quantity tolerance",
    ):
        PaperOrderWorkflow(
            execution_service=execution_service,
            status_broker=broker,
            verification_service=(
                OrderVerificationService()
            ),
            portfolio=Portfolio(
                starting_cash=5_000.00
            ),
            quantity_tolerance=-1,
        )