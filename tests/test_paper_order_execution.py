import pytest

from app.broker import BrokerOrderResult
from app.orders import Order, OrderSide
from app.paper_order_execution import (
    PaperOrderExecutionService,
)
from app.paper_trading_gate import GateDecision


class FakeBroker:
    def __init__(self) -> None:
        self.calls: list[
            dict[str, object]
        ] = []

    def place_market_order(
        self,
        ticker: str,
        quantity: float,
        extended_hours: bool = False,
    ) -> BrokerOrderResult:
        self.calls.append(
            {
                "ticker": ticker,
                "quantity": quantity,
                "extended_hours": extended_hours,
            }
        )

        side = (
            "BUY"
            if quantity > 0
            else "SELL"
        )

        return BrokerOrderResult(
            order_id=123456,
            ticker=ticker,
            quantity=quantity,
            side=side,
            status="NEW",
            order_type="MARKET",
            filled_quantity=0.0,
            filled_value=0.0,
            currency="GBP",
        )


def approved_gate_decision() -> GateDecision:
    return GateDecision(
        approved=True,
        reason=(
            "Paper trading safety checks passed."
        ),
    )


def test_approved_buy_order_is_submitted() -> None:
    broker = FakeBroker()

    service = PaperOrderExecutionService(
        broker=broker,
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
        },
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        price=150.00,
    )

    result = service.submit(
        order=order,
        gate_decision=approved_gate_decision(),
    )

    assert result.submitted is True
    assert result.broker_order is not None
    assert result.broker_order.side == "BUY"

    assert broker.calls == [
        {
            "ticker": "AAPL_US_EQ",
            "quantity": 2.0,
            "extended_hours": False,
        }
    ]


def test_approved_sell_uses_negative_quantity() -> None:
    broker = FakeBroker()

    service = PaperOrderExecutionService(
        broker=broker,
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
        },
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.SELL,
        quantity=2,
        price=150.00,
    )

    result = service.submit(
        order=order,
        gate_decision=approved_gate_decision(),
    )

    assert result.submitted is True

    assert broker.calls[0]["quantity"] == -2.0


def test_blocked_gate_never_calls_broker() -> None:
    broker = FakeBroker()

    service = PaperOrderExecutionService(
        broker=broker,
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
        },
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        price=150.00,
    )

    result = service.submit(
        order=order,
        gate_decision=GateDecision(
            approved=False,
            reason="Market is closed.",
        ),
    )

    assert result.submitted is False
    assert "Market is closed" in result.reason
    assert result.broker_order is None
    assert broker.calls == []


def test_unmapped_symbol_never_calls_broker() -> None:
    broker = FakeBroker()

    service = PaperOrderExecutionService(
        broker=broker,
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
        },
    )

    order = Order(
        symbol="MSFT",
        side=OrderSide.BUY,
        quantity=1,
        price=320.00,
    )

    result = service.submit(
        order=order,
        gate_decision=approved_gate_decision(),
    )

    assert result.submitted is False
    assert "No broker ticker mapping" in result.reason
    assert broker.calls == []


def test_symbol_mapping_is_cleaned() -> None:
    broker = FakeBroker()

    service = PaperOrderExecutionService(
        broker=broker,
        symbol_mapping={
            " aapl ": " aapl_us_eq ",
        },
    )

    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        price=150.00,
    )

    result = service.submit(
        order=order,
        gate_decision=approved_gate_decision(),
    )

    assert result.submitted is True
    assert (
        broker.calls[0]["ticker"]
        == "AAPL_US_EQ"
    )


def test_empty_symbol_mapping_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        PaperOrderExecutionService(
            broker=FakeBroker(),
            symbol_mapping={
                "AAPL": "",
            },
        )