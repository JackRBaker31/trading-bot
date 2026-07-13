import pytest

from app.broker import BrokerOrderResult
from app.order_journal import OrderJournalEntry
from app.order_polling import OrderPollingResult
from app.order_verification import (
    OrderVerificationStatus,
)
from app.recovery_plan import (
    RecoveryAction,
    RecoveryPlanner,
)
from app.startup_recovery import StartupRecoveryItem


def create_journal_entry() -> OrderJournalEntry:
    return OrderJournalEntry(
        timestamp="2026-07-13T10:00:00+00:00",
        reservation_key="AAPL:BUY:2",
        event="PENDING",
        symbol="AAPL",
        side="BUY",
        quantity=2,
        broker_order_id=123456,
        reason="Recovery planner test.",
    )


def create_polling_result(
    status: OrderVerificationStatus,
) -> OrderPollingResult:
    return OrderPollingResult(
        order=BrokerOrderResult(
            order_id=123456,
            ticker="AAPL_US_EQ",
            quantity=2.0,
            side="BUY",
            status=status.value,
            order_type="MARKET",
            filled_quantity=0.0,
            filled_value=0.0,
            currency="GBP",
        ),
        status=status,
        reason="Recovered broker state.",
        attempts=1,
        timed_out=False,
    )


def create_recovery_item(
    status: OrderVerificationStatus,
) -> StartupRecoveryItem:
    return StartupRecoveryItem(
        journal_entry=create_journal_entry(),
        polling_result=create_polling_result(
            status=status
        ),
        error=None,
    )


@pytest.mark.parametrize(
    ("status", "expected_action"),
    [
        (
            OrderVerificationStatus.PENDING,
            RecoveryAction.RESUME_POLLING,
        ),
        (
            OrderVerificationStatus.PARTIALLY_FILLED,
            RecoveryAction.RESUME_POLLING,
        ),
        (
            OrderVerificationStatus.FILLED,
            RecoveryAction.UPDATE_PORTFOLIO,
        ),
        (
            OrderVerificationStatus.FAILED,
            RecoveryAction.RECORD_FAILURE,
        ),
        (
            OrderVerificationStatus.UNKNOWN,
            (
                RecoveryAction
                .REQUIRE_MANUAL_INTERVENTION
            ),
        ),
    ],
)
def test_recovery_state_maps_to_action(
    status: OrderVerificationStatus,
    expected_action: RecoveryAction,
) -> None:
    planner = RecoveryPlanner()

    plan_item = planner.create_plan_item(
        recovery_item=create_recovery_item(
            status=status
        )
    )

    assert plan_item.action == expected_action
    assert plan_item.reason


def test_recovery_error_aborts_startup() -> None:
    recovery_item = StartupRecoveryItem(
        journal_entry=create_journal_entry(),
        polling_result=None,
        error="Broker is unavailable.",
    )

    planner = RecoveryPlanner()

    plan_item = planner.create_plan_item(
        recovery_item=recovery_item
    )

    assert plan_item.action == (
        RecoveryAction.ABORT_STARTUP
    )
    assert "startup" in plan_item.reason.lower()


def test_create_plan_preserves_item_order() -> None:
    first_item = create_recovery_item(
        status=OrderVerificationStatus.PENDING
    )
    second_item = create_recovery_item(
        status=OrderVerificationStatus.FILLED
    )

    planner = RecoveryPlanner()

    plan = planner.create_plan(
        recovery_items=(
            first_item,
            second_item,
        )
    )

    assert len(plan) == 2
    assert plan[0].recovery_item == first_item
    assert plan[0].action == (
        RecoveryAction.RESUME_POLLING
    )
    assert plan[1].recovery_item == second_item
    assert plan[1].action == (
        RecoveryAction.UPDATE_PORTFOLIO
    )


def test_create_plan_returns_empty_tuple() -> None:
    planner = RecoveryPlanner()

    plan = planner.create_plan(
        recovery_items=()
    )

    assert plan == ()