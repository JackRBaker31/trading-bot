from collections.abc import Callable
from dataclasses import dataclass

from app.paper_startup_reconciliation import (
    PaperStartupReconciliationResult,
    PaperStartupReconciliationService,
)
from app.recovery_startup import (
    RecoveryStartupResult,
    RecoveryStartupService,
)


@dataclass(frozen=True)
class PaperApplicationStartupResult:
    recovery_result: RecoveryStartupResult
    reconciliation_result: (
        PaperStartupReconciliationResult | None
    )
    trading_started: bool
    reason: str


class PaperApplicationStartupService:
    def __init__(
        self,
        recovery_startup_service: (
            RecoveryStartupService
        ),
        reconciliation_service: (
            PaperStartupReconciliationService
        ),
    ) -> None:
        self.recovery_startup_service = (
            recovery_startup_service
        )
        self.reconciliation_service = (
            reconciliation_service
        )

    def start(
        self,
        start_trading: Callable[[], None],
    ) -> PaperApplicationStartupResult:
        reconciliation_result: (
            PaperStartupReconciliationResult | None
        ) = None

        trading_started = False

        def reconcile_then_trade() -> None:
            nonlocal reconciliation_result
            nonlocal trading_started

            reconciliation_result = (
                self.reconciliation_service
                .reconcile()
            )

            if not reconciliation_result.approved:
                return

            start_trading()
            trading_started = True

        recovery_result = (
            self.recovery_startup_service.start(
                start_trading=reconcile_then_trade
            )
        )

        if not recovery_result.decision.approved:
            return PaperApplicationStartupResult(
                recovery_result=recovery_result,
                reconciliation_result=None,
                trading_started=False,
                reason=recovery_result.decision.reason,
            )

        if reconciliation_result is None:
            raise RuntimeError(
                "PAPER startup reconciliation did "
                "not run."
            )

        if not reconciliation_result.approved:
            return PaperApplicationStartupResult(
                recovery_result=recovery_result,
                reconciliation_result=(
                    reconciliation_result
                ),
                trading_started=False,
                reason=(
                    reconciliation_result.reason
                ),
            )

        return PaperApplicationStartupResult(
            recovery_result=recovery_result,
            reconciliation_result=(
                reconciliation_result
            ),
            trading_started=trading_started,
            reason=(
                "PAPER startup completed safely."
            ),
        )