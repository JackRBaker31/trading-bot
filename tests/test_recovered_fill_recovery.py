import pytest

from app.order_journal import OrderJournalEntry
from app.recovered_fill import RecoveredFill
from app.recovered_fill_applier import (
    RecoveredFillApplicationResult,
)
from app.recovered_fill_recovery import (
    RecoveredFillRecoveryService,
)
from app.recovery_plan import (
    RecoveryAction,
    RecoveryPlanItem,
)
from app.startup_recovery import StartupRecoveryItem


class FakeValidator:
    def __init__(
        self,
        recovered_fill: RecoveredFill,
        error: Exception | None = None,
    ) -> None:
        self.recovered_fill = recovered_fill
        self.error = error
        self.validate_calls: list[
            RecoveryPlanItem
        ] = []

    def validate(
        self,
        plan_item: RecoveryPlanItem,
    ) -> RecoveredFill:
        self.validate_calls.append(plan_item)

        if self.error is not None:
            raise self.error

        return self.recovered_fill


class FakeApplier:
    def __init__(
        self,
        application_result: (
            RecoveredFillApplicationResult
        ),
        error: Exception | None = None,
    ) -> None:
        self.application_result = (
            application_result
        )
        self.error = error
        self.apply_calls: list[
            RecoveredFill
        ] = []

    def apply(
        self,
        recovered_fill: RecoveredFill,
    ) -> RecoveredFillApplicationResult:
        self.apply_calls.append(recovered_fill)

        if self.error is not None:
            raise self.error

        return self.application_result


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
        reason="Recovered fill recovery test.",
    )


def create_recovered_fill() -> RecoveredFill:
    return RecoveredFill(
        broker_order_id=123456,
        reservation_key="AAPL:BUY:2",
        symbol="AAPL",
        side="BUY",
        quantity=2,
        filled_value=300.0,
        average_fill_price=150.0,
    )


def create_plan_item(
    action: RecoveryAction = (
        RecoveryAction.UPDATE_PORTFOLIO
    ),
) -> RecoveryPlanItem:
    from app.order_polling import OrderPollingResult
    from app.order_verification import (
        OrderVerificationStatus,
    )
    from app.broker import BrokerOrderResult

    polling_result = OrderPollingResult(
        order=BrokerOrderResult(
            order_id=123456,
            ticker="AAPL_US_EQ",
            quantity=2.0,
            side="BUY",
            status="FILLED",
            order_type="MARKET",
            filled_quantity=2.0,
            filled_value=300.0,
            currency="GBP",
        ),
        status=OrderVerificationStatus.FILLED,
        reason="Recovered broker order is filled.",
        attempts=1,
        timed_out=False,
    )

    recovery_item = StartupRecoveryItem(
        journal_entry=create_journal_entry(),
        polling_result=polling_result,
        error=None,
    )

    return RecoveryPlanItem(
        recovery_item=recovery_item,
        action=action,
        reason="Update recovered portfolio.",
    )


def create_application_result(
    applied: bool,
) -> RecoveredFillApplicationResult:
    return RecoveredFillApplicationResult(
        recovered_fill=create_recovered_fill(),
        applied=applied,
        reason=(
            "Recovered fill application result."
        ),
    )


def test_newly_applied_fill_is_journaled() -> None:
    plan_item = create_plan_item()
    recovered_fill = create_recovered_fill()

    validator = FakeValidator(
        recovered_fill=recovered_fill
    )

    applier = FakeApplier(
        application_result=(
            create_application_result(
                applied=True,
            )
        )
    )

    journal = FakeOrderJournal()

    service = RecoveredFillRecoveryService(
        validator=validator,
        applier=applier,
        order_journal=journal,
    )

    result = service.recover(
        plan_item=plan_item
    )

    assert result.completed is True
    assert result.application_result.applied is True

    assert journal.record_calls == [
        {
            "source_entry": (
                plan_item.recovery_item
                .journal_entry
            ),
            "event": "FILLED",
            "broker_order_id": 123456,
            "reason": (
                "Recovered broker order is filled."
            ),
            "metadata": {
                "recovered_on_startup": True,
                "recovery_action": (
                    "UPDATE_PORTFOLIO"
                ),
                "portfolio_applied": True,
            },
        }
    ]


def test_already_applied_fill_is_journaled() -> None:
    plan_item = create_plan_item()
    recovered_fill = create_recovered_fill()

    validator = FakeValidator(
        recovered_fill=recovered_fill
    )

    applier = FakeApplier(
        application_result=(
            create_application_result(
                applied=False,
            )
        )
    )

    journal = FakeOrderJournal()

    service = RecoveredFillRecoveryService(
        validator=validator,
        applier=applier,
        order_journal=journal,
    )

    result = service.recover(
        plan_item=plan_item
    )

    assert result.completed is True
    assert result.application_result.applied is False

    assert journal.record_calls[-1][
        "event"
    ] == "FILLED"

    assert journal.record_calls[-1][
        "metadata"
    ] == {
        "recovered_on_startup": True,
        "recovery_action": "UPDATE_PORTFOLIO",
        "portfolio_applied": False,
    }


def test_applier_failure_does_not_journal_filled() -> None:
    plan_item = create_plan_item()
    recovered_fill = create_recovered_fill()

    validator = FakeValidator(
        recovered_fill=recovered_fill
    )

    applier = FakeApplier(
        application_result=(
            create_application_result(
                applied=True,
            )
        ),
        error=RuntimeError(
            "Portfolio persistence failed."
        ),
    )

    journal = FakeOrderJournal()

    service = RecoveredFillRecoveryService(
        validator=validator,
        applier=applier,
        order_journal=journal,
    )

    with pytest.raises(
        RuntimeError,
        match="persistence failed",
    ):
        service.recover(
            plan_item=plan_item
        )

    assert journal.record_calls == []


def test_unsupported_action_is_rejected() -> None:
    plan_item = create_plan_item(
        action=RecoveryAction.RESUME_POLLING
    )

    recovered_fill = create_recovered_fill()

    validator = FakeValidator(
        recovered_fill=recovered_fill
    )

    applier = FakeApplier(
        application_result=(
            create_application_result(
                applied=True,
            )
        )
    )

    journal = FakeOrderJournal()

    service = RecoveredFillRecoveryService(
        validator=validator,
        applier=applier,
        order_journal=journal,
    )

    with pytest.raises(
        ValueError,
        match="does not require",
    ):
        service.recover(
            plan_item=plan_item
        )

    assert validator.validate_calls == []
    assert applier.apply_calls == []
    assert journal.record_calls == []