from dataclasses import dataclass
from enum import Enum

from app.startup_recovery import (
    StartupRecoveryItem,
    StartupRecoveryState,
)


class RecoveryAction(str, Enum):
    RESUME_POLLING = "RESUME_POLLING"
    UPDATE_PORTFOLIO = "UPDATE_PORTFOLIO"
    RECORD_FAILURE = "RECORD_FAILURE"
    REQUIRE_MANUAL_INTERVENTION = (
        "REQUIRE_MANUAL_INTERVENTION"
    )
    ABORT_STARTUP = "ABORT_STARTUP"


@dataclass(frozen=True)
class RecoveryPlanItem:
    recovery_item: StartupRecoveryItem
    action: RecoveryAction
    reason: str


class RecoveryPlanner:
    def create_plan_item(
        self,
        recovery_item: StartupRecoveryItem,
    ) -> RecoveryPlanItem:
        action_by_state = {
            StartupRecoveryState.PENDING: (
                RecoveryAction.RESUME_POLLING
            ),
            StartupRecoveryState.PARTIALLY_FILLED: (
                RecoveryAction.RESUME_POLLING
            ),
            StartupRecoveryState.FILLED: (
                RecoveryAction.UPDATE_PORTFOLIO
            ),
            StartupRecoveryState.FAILED: (
                RecoveryAction.RECORD_FAILURE
            ),
            StartupRecoveryState.UNKNOWN: (
                RecoveryAction
                .REQUIRE_MANUAL_INTERVENTION
            ),
            StartupRecoveryState.RECOVERY_ERROR: (
                RecoveryAction.ABORT_STARTUP
            ),
        }

        reason_by_action = {
            RecoveryAction.RESUME_POLLING: (
                "Broker order remains active and "
                "requires continued polling."
            ),
            RecoveryAction.UPDATE_PORTFOLIO: (
                "Broker order is filled and requires "
                "a safe local portfolio update."
            ),
            RecoveryAction.RECORD_FAILURE: (
                "Broker order reached a terminal "
                "failure state."
            ),
            (
                RecoveryAction
                .REQUIRE_MANUAL_INTERVENTION
            ): (
                "Broker order state remains unknown "
                "and requires manual intervention."
            ),
            RecoveryAction.ABORT_STARTUP: (
                "Recovery failed and startup must "
                "remain blocked."
            ),
        }

        action = action_by_state[
            recovery_item.state
        ]

        return RecoveryPlanItem(
            recovery_item=recovery_item,
            action=action,
            reason=reason_by_action[action],
        )

    def create_plan(
        self,
        recovery_items: tuple[
            StartupRecoveryItem,
            ...
        ],
    ) -> tuple[RecoveryPlanItem, ...]:
        return tuple(
            self.create_plan_item(
                recovery_item=recovery_item
            )
            for recovery_item in recovery_items
        )