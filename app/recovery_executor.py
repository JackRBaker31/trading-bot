from dataclasses import dataclass

from app.order_journal import OrderJournal
from app.recovery_plan import (
    RecoveryAction,
    RecoveryPlanItem,
)


@dataclass(frozen=True)
class RecoveryExecutionResult:
    plan_item: RecoveryPlanItem
    completed: bool
    reason: str


class RecoveryExecutor:
    def __init__(
        self,
        order_journal: OrderJournal,
    ) -> None:
        self.order_journal = order_journal

    def execute(
        self,
        plan_item: RecoveryPlanItem,
    ) -> RecoveryExecutionResult:
        if (
            plan_item.action
            != RecoveryAction.RECORD_FAILURE
        ):
            raise ValueError(
                "Recovery action is not supported "
                "by this executor."
            )

        recovery_item = plan_item.recovery_item
        polling_result = recovery_item.polling_result

        if polling_result is None:
            raise ValueError(
                "Failure recovery requires a broker "
                "polling result."
            )

        broker_order = polling_result.order

        if broker_order is None:
            raise ValueError(
                "Failure recovery requires broker "
                "order information."
            )

        raw_status = broker_order.status.strip().upper()

        event = (
            "REJECTED"
            if raw_status == "REJECTED"
            else "FAILED"
        )

        self.order_journal.record_from_entry(
            source_entry=(
                recovery_item.journal_entry
            ),
            event=event,
            broker_order_id=broker_order.order_id,
            reason=polling_result.reason,
            metadata={
                "recovered_on_startup": True,
                "recovery_action": (
                    plan_item.action.value
                ),
            },
        )

        return RecoveryExecutionResult(
            plan_item=plan_item,
            completed=True,
            reason=(
                "Recovered terminal failure was "
                "recorded."
            ),
        )