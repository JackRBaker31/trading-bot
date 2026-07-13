import pytest

from app.broker import (
    BrokerOrderResult,
    BrokerResourceNotFoundError,
)
from app.order_polling import OrderPollingService
from app.order_verification import (
    OrderVerificationService,
    OrderVerificationStatus,
)


def create_broker_order(
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


class FakePollingBroker:
    def __init__(
        self,
        pending_orders: list[BrokerOrderResult],
        pending_not_found: bool = False,
        historical_order: BrokerOrderResult | None = None,
    ) -> None:
        self.pending_orders = pending_orders
        self.pending_not_found = pending_not_found
        self.historical_order = historical_order
        self.pending_calls: list[int] = []
        self.history_calls: list[int] = []

    def get_pending_order(
        self,
        order_id: int,
    ) -> BrokerOrderResult:
        self.pending_calls.append(order_id)

        if self.pending_not_found:
            raise BrokerResourceNotFoundError(
                "Pending order was not found."
            )

        index = min(
            len(self.pending_calls) - 1,
            len(self.pending_orders) - 1,
        )

        return self.pending_orders[index]

    def find_historical_order(
        self,
        order_id: int,
        max_pages: int = 5,
    ) -> BrokerOrderResult | None:
        self.history_calls.append(order_id)
        return self.historical_order


def create_service(
    broker: FakePollingBroker,
    max_attempts: int = 5,
    sleep_calls: list[float] | None = None,
) -> OrderPollingService:
    if sleep_calls is None:
        sleep_calls = []

    return OrderPollingService(
        broker=broker,
        verification_service=OrderVerificationService(),
        max_attempts=max_attempts,
        poll_interval_seconds=1.0,
        sleep_function=sleep_calls.append,
    )


def test_poll_returns_filled_order_immediately() -> None:
    broker = FakePollingBroker(
        pending_orders=[
            create_broker_order(
                status="FILLED",
                filled_quantity=2.0,
                filled_value=300.0,
            )
        ]
    )

    sleep_calls: list[float] = []
    result = create_service(
        broker=broker,
        sleep_calls=sleep_calls,
    ).poll(order_id=123456)

    assert result.status == OrderVerificationStatus.FILLED
    assert result.order is not None
    assert result.attempts == 1
    assert result.timed_out is False
    assert sleep_calls == []


def test_poll_retries_pending_order_until_filled() -> None:
    broker = FakePollingBroker(
        pending_orders=[
            create_broker_order(status="NEW"),
            create_broker_order(status="NEW"),
            create_broker_order(
                status="FILLED",
                filled_quantity=2.0,
                filled_value=300.0,
            ),
        ]
    )

    sleep_calls: list[float] = []
    result = create_service(
        broker=broker,
        sleep_calls=sleep_calls,
    ).poll(order_id=123456)

    assert result.status == OrderVerificationStatus.FILLED
    assert result.attempts == 3
    assert sleep_calls == [1.0, 1.0]


def test_poll_times_out_while_order_remains_pending() -> None:
    broker = FakePollingBroker(
        pending_orders=[
            create_broker_order(status="NEW")
        ]
    )

    sleep_calls: list[float] = []
    result = create_service(
        broker=broker,
        max_attempts=3,
        sleep_calls=sleep_calls,
    ).poll(order_id=123456)

    assert result.status == OrderVerificationStatus.PENDING
    assert result.timed_out is True
    assert result.attempts == 3
    assert sleep_calls == [1.0, 1.0]


def test_poll_uses_historical_order_after_404() -> None:
    historical_order = create_broker_order(
        status="FILLED",
        filled_quantity=2.0,
        filled_value=300.0,
    )

    broker = FakePollingBroker(
        pending_orders=[],
        pending_not_found=True,
        historical_order=historical_order,
    )

    result = create_service(
        broker=broker
    ).poll(order_id=123456)

    assert result.status == OrderVerificationStatus.FILLED
    assert result.order == historical_order
    assert broker.history_calls == [123456]


def test_poll_returns_unknown_when_order_is_missing() -> None:
    broker = FakePollingBroker(
        pending_orders=[],
        pending_not_found=True,
        historical_order=None,
    )

    result = create_service(
        broker=broker
    ).poll(order_id=123456)

    assert result.status == OrderVerificationStatus.UNKNOWN
    assert result.order is None
    assert result.timed_out is False


def test_invalid_max_attempts_is_rejected() -> None:
    broker = FakePollingBroker(
        pending_orders=[
            create_broker_order(status="NEW")
        ]
    )

    with pytest.raises(
        ValueError,
        match="Maximum polling attempts",
    ):
        create_service(
            broker=broker,
            max_attempts=0,
        )


def test_negative_polling_interval_is_rejected() -> None:
    broker = FakePollingBroker(
        pending_orders=[
            create_broker_order(status="NEW")
        ]
    )

    with pytest.raises(
        ValueError,
        match="Polling interval",
    ):
        OrderPollingService(
            broker=broker,
            verification_service=(
                OrderVerificationService()
            ),
            poll_interval_seconds=-1,
        )


def test_invalid_order_id_is_rejected() -> None:
    broker = FakePollingBroker(
        pending_orders=[
            create_broker_order(status="NEW")
        ]
    )

    with pytest.raises(
        ValueError,
        match="Order ID",
    ):
        create_service(
            broker=broker
        ).poll(order_id=0)