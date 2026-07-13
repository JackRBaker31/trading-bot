import pytest

from app.broker import BrokerOrderResult
from app.order_journal import OrderJournalEntry
from app.order_polling import OrderPollingResult
from app.order_verification import (
    OrderVerificationStatus,
)
from app.recovery_executor import RecoveryExecutor
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
        event="PENDING",
        symbol="AAPL",
        side="BUY",
        quantity=2,
        broker_order_id=123456,
        reason="Recovery executor test.",
    )


def create_polling_result(
    raw_status: str,
) -> OrderPollingResult:
    return OrderPollingResult(
        order=BrokerOrderResult(
            order_id=123456,
            ticker="AAPL_US_EQ",
            quantity=2.0,
            side="BUY",
            status=raw_status,
            order_type="MARKET",
            filled_quantity=0.0,
            filled_value=0.0,
            currency="GBP",
        ),
        status=OrderVerificationStatus.FAILED,
        reason="Recovered terminal failure.",
        attempts=1,
        timed_out=False,
    )


def create_plan_item(
    raw_status: str,
    action: RecoveryAction = (
        RecoveryAction.RECORD_FAILURE
    ),
) -> RecoveryPlanItem:
    recovery_item = StartupRecoveryItem(
        journal_entry=create_journal_entry(),
        polling_result=create_polling_result(
            raw_status=raw_status
        ),
        error=None,
    )

    return RecoveryPlanItem(
        recovery_item=recovery_item,
        action=action,
        reason="Recovery plan test.",
    )


def test_failed_recovery_is_recorded() -> None:
    journal = FakeOrderJournal()
    executor = RecoveryExecutor(
        order_journal=journal
    )

    plan_item = create_plan_item(
        raw_status="CANCELLED"
    )

    result = executor.execute(
        plan_item=plan_item
    )

    assert result.completed is True

    assert journal.record_calls == [
        {
            "source_entry": (
                plan_item.recovery_item
                .journal_entry
            ),
            "event": "FAILED",
            "broker_order_id": 123456,
            "reason": (
                "Recovered terminal failure."
            ),
            "metadata": {
                "recovered_on_startup": True,
                "recovery_action": (
                    "RECORD_FAILURE"
                ),
            },
        }
    ]


def test_rejected_recovery_is_recorded() -> None:
    journal = FakeOrderJournal()
    executor = RecoveryExecutor(
        order_journal=journal
    )

    plan_item = create_plan_item(
        raw_status="REJECTED"
    )

    executor.execute(
        plan_item=plan_item
    )

    assert journal.record_calls[-1][
        "event"
    ] == "REJECTED"


def test_unsupported_action_is_rejected() -> None:
    journal = FakeOrderJournal()
    executor = RecoveryExecutor(
        order_journal=journal
    )

    plan_item = create_plan_item(
        raw_status="FILLED",
        action=RecoveryAction.UPDATE_PORTFOLIO,
    )

    with pytest.raises(
        ValueError,
        match="not supported",
    ):
        executor.execute(
            plan_item=plan_item
        )

    assert journal.record_calls == []