import pytest

from app.broker import BrokerOrderResult
from app.order_journal import OrderJournalEntry
from app.order_polling import OrderPollingResult
from app.order_verification import (
    OrderVerificationStatus,
)
from app.recovered_fill import (
    RecoveredFillValidator,
)
from app.recovery_plan import (
    RecoveryAction,
    RecoveryPlanItem,
)
from app.startup_recovery import StartupRecoveryItem


def create_journal_entry(
    side: str = "BUY",
    quantity: int = 2,
    broker_order_id: int = 123456,
) -> OrderJournalEntry:
    return OrderJournalEntry(
        timestamp="2026-07-13T10:00:00+00:00",
        reservation_key=(
            f"AAPL:{side}:{quantity}"
        ),
        event="PENDING",
        symbol="AAPL",
        side=side,
        quantity=quantity,
        broker_order_id=broker_order_id,
        reason="Recovered fill test.",
    )


def create_plan_item(
    raw_side: str = "BUY",
    quantity: float = 2.0,
    filled_quantity: float = 2.0,
    filled_value: float = 300.0,
    broker_order_id: int = 123456,
    status: OrderVerificationStatus = (
        OrderVerificationStatus.FILLED
    ),
    action: RecoveryAction = (
        RecoveryAction.UPDATE_PORTFOLIO
    ),
) -> RecoveryPlanItem:
    broker_order = BrokerOrderResult(
        order_id=broker_order_id,
        ticker="AAPL_US_EQ",
        quantity=quantity,
        side=raw_side,
        status="FILLED",
        order_type="MARKET",
        filled_quantity=filled_quantity,
        filled_value=filled_value,
        currency="GBP",
    )

    polling_result = OrderPollingResult(
        order=broker_order,
        status=status,
        reason="Recovered filled order.",
        attempts=1,
        timed_out=False,
    )

    recovery_item = StartupRecoveryItem(
        journal_entry=create_journal_entry(
            side=raw_side,
            quantity=int(abs(quantity)),
        ),
        polling_result=polling_result,
        error=None,
    )

    return RecoveryPlanItem(
        recovery_item=recovery_item,
        action=action,
        reason="Update recovered fill.",
    )


def test_valid_recovered_fill_is_returned() -> None:
    validator = RecoveredFillValidator()

    recovered_fill = validator.validate(
        plan_item=create_plan_item()
    )

    assert recovered_fill.broker_order_id == 123456
    assert recovered_fill.reservation_key == (
        "AAPL:BUY:2"
    )
    assert recovered_fill.symbol == "AAPL"
    assert recovered_fill.side == "BUY"
    assert recovered_fill.quantity == 2
    assert recovered_fill.filled_value == 300.0
    assert recovered_fill.average_fill_price == 150.0


def test_mismatched_filled_quantity_is_rejected() -> None:
    validator = RecoveredFillValidator()

    with pytest.raises(
        ValueError,
        match="filled quantity",
    ):
        validator.validate(
            plan_item=create_plan_item(
                filled_quantity=1.0,
            )
        )


def test_invalid_filled_value_is_rejected() -> None:
    validator = RecoveredFillValidator()

    with pytest.raises(
        ValueError,
        match="filled value",
    ):
        validator.validate(
            plan_item=create_plan_item(
                filled_value=0.0,
            )
        )


def test_non_filled_status_is_rejected() -> None:
    validator = RecoveredFillValidator()

    with pytest.raises(
        ValueError,
        match="FILLED",
    ):
        validator.validate(
            plan_item=create_plan_item(
                status=(
                    OrderVerificationStatus.PENDING
                ),
            )
        )


def test_unsupported_action_is_rejected() -> None:
    validator = RecoveredFillValidator()

    with pytest.raises(
        ValueError,
        match="does not require",
    ):
        validator.validate(
            plan_item=create_plan_item(
                action=(
                    RecoveryAction.RESUME_POLLING
                ),
            )
        )


def test_mismatched_broker_order_id_is_rejected() -> None:
    plan_item = create_plan_item(
        broker_order_id=999999,
    )

    recovery_item = plan_item.recovery_item

    mismatched_item = StartupRecoveryItem(
        journal_entry=create_journal_entry(
            broker_order_id=123456,
        ),
        polling_result=(
            recovery_item.polling_result
        ),
        error=None,
    )

    mismatched_plan = RecoveryPlanItem(
        recovery_item=mismatched_item,
        action=plan_item.action,
        reason=plan_item.reason,
    )

    validator = RecoveredFillValidator()

    with pytest.raises(
        ValueError,
        match="order ID",
    ):
        validator.validate(
            plan_item=mismatched_plan
        )


def test_negative_quantity_tolerance_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Quantity tolerance",
    ):
        RecoveredFillValidator(
            quantity_tolerance=-1,
        )