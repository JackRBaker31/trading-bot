from dataclasses import dataclass

from app.recovery_coordinator import (
    RecoveryCoordinatorReport,
)


@dataclass(frozen=True)
class RecoveryStartupDecision:
    approved: bool
    reason: str


class RecoveryStartupGate:
    def evaluate(
        self,
        report: RecoveryCoordinatorReport,
    ) -> RecoveryStartupDecision:
        if report.startup_blocked:
            return RecoveryStartupDecision(
                approved=False,
                reason=(
                    "Trading refused because startup "
                    "recovery remains blocked."
                ),
            )

        if report.incomplete_items > 0:
            return RecoveryStartupDecision(
                approved=False,
                reason=(
                    "Trading refused because startup "
                    "recovery is incomplete."
                ),
            )

        return RecoveryStartupDecision(
            approved=True,
            reason=(
                "Startup recovery completed safely."
            ),
        )