import logging
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

logger = logging.getLogger(__name__)

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
        logger.info(
            "startup_recovery_started"
        )

        recovery_report = (
            self.recovery_coordinator.recover()
        )

        logger.info(
            "startup_recovery_report "
            "total_items=%s completed_items=%s "
            "incomplete_items=%s startup_blocked=%s",
            len(recovery_report.items),
            recovery_report.completed_items,
            recovery_report.incomplete_items,
            recovery_report.startup_blocked,
        )

        decision = self.recovery_gate.evaluate(
            report=recovery_report
        )

        if not decision.approved:
            logger.error(
                "startup_recovery_refused "
                "reason=%s incomplete_items=%s "
                "startup_blocked=%s",
                decision.reason,
                recovery_report.incomplete_items,
                recovery_report.startup_blocked,
            )

            return RecoveryStartupResult(
                recovery_report=recovery_report,
                decision=decision,
                trading_started=False,
            )

        logger.info(
            "startup_recovery_approved reason=%s",
            decision.reason,
        )

        start_trading()

        logger.info(
            "startup_recovery_callback_completed"
        )

        return RecoveryStartupResult(
            recovery_report=recovery_report,
            decision=decision,
            trading_started=True,
        )