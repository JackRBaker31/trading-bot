from dataclasses import dataclass

from app.order_journal import OrderJournal
from app.order_verification import (
    OrderVerificationStatus,
)
from app.recovery_plan import (
    RecoveryAction,
    RecoveryPlanItem,
)


@dataclass(frozen=True)
class ActiveOrderRecoveryResult:
    plan_item: RecoveryPlanItem
    completed: bool
    startup_blocked: bool
    event: str
    reason: str


class ActiveOrderRecoveryService:
    def __init__(
        self,
        order_journal: OrderJournal,
    ) -> None:
        self.order_journal = order_journal

    def recover(
        self,
        plan_item: RecoveryPlanItem,
    ) -> ActiveOrderRecoveryResult:
        if (
            plan_item.action
            != RecoveryAction.RESUME_POLLING
        ):
            raise ValueError(
                "Recovery action does not require "
                "continued polling."
            )

        recovery_item = plan_item.recovery_item
        polling_result = recovery_item.polling_result

        if polling_result is None:
            raise ValueError(
                "Active-order recovery requires a "
                "broker polling result."
            )

        event_by_status = {
            OrderVerificationStatus.PENDING: (
                "PENDING"
            ),
            (
                OrderVerificationStatus
                .PARTIALLY_FILLED
            ): "PARTIALLY_FILLED",
        }

        event = event_by_status.get(
            polling_result.status
        )

        if event is None:
            raise ValueError(
                "Active-order recovery requires "
                "PENDING or PARTIALLY_FILLED status."
            )

        broker_order = polling_result.order

        if broker_order is None:
            raise ValueError(
                "Active-order recovery requires "
                "broker order information."
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
                "startup_blocked": True,
            },
        )

        return ActiveOrderRecoveryResult(
            plan_item=plan_item,
            completed=False,
            startup_blocked=True,
            event=event,
            reason=(
                "Broker order remains active; "
                "startup must remain blocked."
            ),
        )