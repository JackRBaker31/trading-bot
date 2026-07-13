import pytest

from app.broker import BrokerOrderResult
from app.order_journal import OrderJournalEntry
from app.order_polling import OrderPollingResult
from app.order_recovery import OrderRecoveryService
from app.order_verification import (
    OrderVerificationStatus,
)


class FakePollingService:
    def __init__(
        self,
        result: OrderPollingResult,
    ) -> None:
        self.result = result
        self.poll_calls: list[int] = []

    def poll(
        self,
        order_id: int,
    ) -> OrderPollingResult:
        self.poll_calls.append(order_id)
        return self.result


def create_broker_order(
    status: str = "NEW",
) -> BrokerOrderResult:
    return BrokerOrderResult(
        order_id=123456,
        ticker="AAPL_US_EQ",
        quantity=2.0,
        side="BUY",
        status=status,
        order_type="MARKET",
        filled_quantity=0.0,
        filled_value=0.0,
        currency="GBP",
    )


def create_polling_result() -> OrderPollingResult:
    return OrderPollingResult(
        order=create_broker_order(),
        status=OrderVerificationStatus.PENDING,
        reason=(
            "The broker order did not reach a "
            "terminal state before polling timed out."
        ),
        attempts=3,
        timed_out=True,
    )


def create_journal_entry(
    event: str = "PENDING",
    broker_order_id: int | None = 123456,
) -> OrderJournalEntry:
    return OrderJournalEntry(
        timestamp="2026-07-13T10:00:00+00:00",
        reservation_key="AAPL:BUY:2",
        event=event,
        symbol="AAPL",
        side="BUY",
        quantity=2,
        broker_order_id=broker_order_id,
        reason="Recovery test entry.",
    )


def test_recover_polls_using_broker_order_id() -> None:
    polling_result = create_polling_result()

    polling_service = FakePollingService(
        result=polling_result
    )

    recovery_service = OrderRecoveryService(
        polling_service=polling_service
    )

    result = recovery_service.recover(
        journal_entry=create_journal_entry()
    )

    assert result == polling_result
    assert polling_service.poll_calls == [
        123456,
    ]


def test_recover_rejects_missing_broker_order_id() -> None:
    polling_service = FakePollingService(
        result=create_polling_result()
    )

    recovery_service = OrderRecoveryService(
        polling_service=polling_service
    )

    with pytest.raises(
        ValueError,
        match="requires a broker order ID",
    ):
        recovery_service.recover(
            journal_entry=create_journal_entry(
                event="SUBMITTED",
                broker_order_id=None,
            )
        )

    assert polling_service.poll_calls == []


def test_recover_rejects_terminal_entry() -> None:
    polling_service = FakePollingService(
        result=create_polling_result()
    )

    recovery_service = OrderRecoveryService(
        polling_service=polling_service
    )

    with pytest.raises(
        ValueError,
        match="not eligible",
    ):
        recovery_service.recover(
            journal_entry=create_journal_entry(
                event="FILLED",
            )
        )

    assert polling_service.poll_calls == []