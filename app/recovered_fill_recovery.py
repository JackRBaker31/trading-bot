from dataclasses import dataclass

from app.order_journal import OrderJournal
from app.recovered_fill import (
    RecoveredFill,
    RecoveredFillValidator,
)
from app.recovered_fill_applier import (
    RecoveredFillApplier,
    RecoveredFillApplicationResult,
)
from app.recovery_plan import (
    RecoveryAction,
    RecoveryPlanItem,
)


@dataclass(frozen=True)
class RecoveredFillRecoveryResult:
    plan_item: RecoveryPlanItem
    recovered_fill: RecoveredFill
    application_result: (
        RecoveredFillApplicationResult
    )
    completed: bool
    reason: str


class RecoveredFillRecoveryService:
    def __init__(
        self,
        validator: RecoveredFillValidator,
        applier: RecoveredFillApplier,
        order_journal: OrderJournal,
    ) -> None:
        self.validator = validator
        self.applier = applier
        self.order_journal = order_journal

    def recover(
        self,
        plan_item: RecoveryPlanItem,
    ) -> RecoveredFillRecoveryResult:
        if (
            plan_item.action
            != RecoveryAction.UPDATE_PORTFOLIO
        ):
            raise ValueError(
                "Recovery action does not require "
                "a portfolio update."
            )

        recovered_fill = self.validator.validate(
            plan_item=plan_item
        )

        application_result = self.applier.apply(
            recovered_fill=recovered_fill
        )

        recovery_item = plan_item.recovery_item
        polling_result = recovery_item.polling_result

        if polling_result is None:
            raise ValueError(
                "Recovered fill requires a broker "
                "polling result."
            )

        self.order_journal.record_from_entry(
            source_entry=(
                recovery_item.journal_entry
            ),
            event="FILLED",
            broker_order_id=(
                recovered_fill.broker_order_id
            ),
            reason=polling_result.reason,
            metadata={
                "recovered_on_startup": True,
                "recovery_action": (
                    plan_item.action.value
                ),
                "portfolio_applied": (
                    application_result.applied
                ),
            },
        )

        return RecoveredFillRecoveryResult(
            plan_item=plan_item,
            recovered_fill=recovered_fill,
            application_result=application_result,
            completed=True,
            reason=(
                "Recovered fill was finalized."
            ),
        )