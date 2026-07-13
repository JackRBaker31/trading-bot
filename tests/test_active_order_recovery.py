import pytest

from app.active_order_recovery import (
    ActiveOrderRecoveryService,
)
from app.broker import BrokerOrderResult
from app.order_journal import OrderJournalEntry
from app.order_polling import OrderPollingResult
from app.order_verification import (
    OrderVerificationStatus,
)
from app.recovery_plan import (
    RecoveryAction,
    RecoveryPlanItem,
)
from app.startup_recovery import StartupRecoveryItem


class FakeOrderJournal:
    def __init__(self) -> None:
        self.record_calls: list[
            dict[str, object]
        ] = []

    def record_from_entry(
        self,
        source_entry: OrderJournalEntry,
        event: str,
        broker_order_id: int | None = None,
        reason: str = "",
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.record_calls.append(
            {
                "source_entry": source_entry,
                "event": event,
                "broker_order_id": (
                    broker_order_id
                ),
                "reason": reason,
                "metadata": metadata,
            }
        )


def create_journal_entry() -> OrderJournalEntry:
    return OrderJournalEntry(
        timestamp="2026-07-13T10:00:00+00:00",
        reservation_key="AAPL:BUY:2",
        event="SUBMITTED",
        symbol="AAPL",
        side="BUY",
        quantity=2,
        broker_order_id=123456,
        reason="Active-order recovery test.",
    )


def create_plan_item(
    status: OrderVerificationStatus,
    action: RecoveryAction = (
        RecoveryAction.RESUME_POLLING
    ),
) -> RecoveryPlanItem:
    raw_status = (
        "PARTIALLY_FILLED"
        if status
        == OrderVerificationStatus.PARTIALLY_FILLED
        else "NEW"
    )

    polling_result = OrderPollingResult(
        order=BrokerOrderResult(
            order_id=123456,
            ticker="AAPL_US_EQ",
            quantity=2.0,
            side="BUY",
            status=raw_status,
            order_type="MARKET",
            filled_quantity=(
                1.0
                if status
                == (
                    OrderVerificationStatus
                    .PARTIALLY_FILLED
                )
                else 0.0
            ),
            filled_value=(
                150.0
                if status
                == (
                    OrderVerificationStatus
                    .PARTIALLY_FILLED
                )
                else 0.0
            ),
            currency="GBP",
        ),
        status=status,
        reason=(
            "The broker order did not reach a "
            "terminal state before polling timed out."
        ),
        attempts=3,
        timed_out=True,
    )

    recovery_item = StartupRecoveryItem(
        journal_entry=create_journal_entry(),
        polling_result=polling_result,
        error=None,
    )

    return RecoveryPlanItem(
        recovery_item=recovery_item,
        action=action,
        reason=(
            "Broker order remains active and "
            "requires continued polling."
        ),
    )


@pytest.mark.parametrize(
    ("status", "expected_event"),
    [
        (
            OrderVerificationStatus.PENDING,
            "PENDING",
        ),
        (
            (
                OrderVerificationStatus
                .PARTIALLY_FILLED
            ),
            "PARTIALLY_FILLED",
        ),
    ],
)
def test_active_order_state_is_journaled(
    status: OrderVerificationStatus,
    expected_event: str,
) -> None:
    journal = FakeOrderJournal()

    service = ActiveOrderRecoveryService(
        order_journal=journal
    )

    plan_item = create_plan_item(
        status=status
    )

    result = service.recover(
        plan_item=plan_item
    )

    assert result.completed is False
    assert result.startup_blocked is True
    assert result.event == expected_event

    assert journal.record_calls == [
        {
            "source_entry": (
                plan_item.recovery_item
                .journal_entry
            ),
            "event": expected_event,
            "broker_order_id": 123456,
            "reason": (
                "The broker order did not reach a "
                "terminal state before polling "
                "timed out."
            ),
            "metadata": {
                "recovered_on_startup": True,
                "recovery_action": (
                    "RESUME_POLLING"
                ),
                "startup_blocked": True,
            },
        }
    ]


def test_non_active_status_is_rejected() -> None:
    journal = FakeOrderJournal()

    service = ActiveOrderRecoveryService(
        order_journal=journal
    )

    plan_item = create_plan_item(
        status=OrderVerificationStatus.FILLED
    )

    with pytest.raises(
        ValueError,
        match="PENDING or PARTIALLY_FILLED",
    ):
        service.recover(
            plan_item=plan_item
        )

    assert journal.record_calls == []


def test_unsupported_action_is_rejected() -> None:
    journal = FakeOrderJournal()

    service = ActiveOrderRecoveryService(
        order_journal=journal
    )

    plan_item = create_plan_item(
        status=OrderVerificationStatus.PENDING,
        action=RecoveryAction.UPDATE_PORTFOLIO,
    )

    with pytest.raises(
        ValueError,
        match="does not require",
    ):
        service.recover(
            plan_item=plan_item
        )

    assert journal.record_calls == []