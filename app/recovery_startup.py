from collections.abc import Callable
from dataclasses import dataclass

from app.recovery_coordinator import (
    RecoveryCoordinator,
    RecoveryCoordinatorReport,
)
from app.recovery_startup_gate import (
    RecoveryStartupDecision,
    RecoveryStartupGate,
)


@dataclass(frozen=True)
class RecoveryStartupResult:
    recovery_report: RecoveryCoordinatorReport
    decision: RecoveryStartupDecision
    trading_started: bool


class RecoveryStartupService:
    def __init__(
        self,
        recovery_coordinator: RecoveryCoordinator,
        recovery_gate: RecoveryStartupGate,
    ) -> None:
        self.recovery_coordinator = (
            recovery_coordinator
        )
        self.recovery_gate = recovery_gate

    def start(
        self,
        start_trading: Callable[[], None],
    ) -> RecoveryStartupResult:
        recovery_report = (
            self.recovery_coordinator.recover()
        )

        decision = self.recovery_gate.evaluate(
            report=recovery_report
        )

        if not decision.approved:
            return RecoveryStartupResult(
                recovery_report=recovery_report,
                decision=decision,
                trading_started=False,
            )

        start_trading()

        return RecoveryStartupResult(
            recovery_report=recovery_report,
            decision=decision,
            trading_started=True,
        )