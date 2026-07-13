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
from app.startup_order_discovery import (
    StartupOrderDiscoveryResult,
    StartupOrderDiscoveryService,
)


@dataclass(frozen=True)
class PaperApplicationStartupResult:
    recovery_result: RecoveryStartupResult
    discovery_result: (
        StartupOrderDiscoveryResult | None
    )
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
        order_discovery_service: (
            StartupOrderDiscoveryService
        ),
        reconciliation_service: (
            PaperStartupReconciliationService
        ),
    ) -> None:
        self.recovery_startup_service = (
            recovery_startup_service
        )
        self.order_discovery_service = (
            order_discovery_service
        )
        self.reconciliation_service = (
            reconciliation_service
        )

    def start(
        self,
        start_trading: Callable[[], None],
    ) -> PaperApplicationStartupResult:
        discovery_result: (
            StartupOrderDiscoveryResult | None
        ) = None

        reconciliation_result: (
            PaperStartupReconciliationResult | None
        ) = None

        trading_started = False

        def discover_reconcile_then_trade() -> None:
            nonlocal discovery_result
            nonlocal reconciliation_result
            nonlocal trading_started

            discovery_result = (
                self.order_discovery_service
                .discover()
            )

            if not discovery_result.approved:
                return

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
                start_trading=(
                    discover_reconcile_then_trade
                )
            )
        )

        if not recovery_result.decision.approved:
            return PaperApplicationStartupResult(
                recovery_result=recovery_result,
                discovery_result=None,
                reconciliation_result=None,
                trading_started=False,
                reason=(
                    recovery_result.decision.reason
                ),
            )

        if discovery_result is None:
            raise RuntimeError(
                "PAPER startup order discovery did "
                "not run."
            )

        if not discovery_result.approved:
            return PaperApplicationStartupResult(
                recovery_result=recovery_result,
                discovery_result=discovery_result,
                reconciliation_result=None,
                trading_started=False,
                reason=discovery_result.reason,
            )

        if reconciliation_result is None:
            raise RuntimeError(
                "PAPER startup reconciliation did "
                "not run."
            )

        if not reconciliation_result.approved:
            return PaperApplicationStartupResult(
                recovery_result=recovery_result,
                discovery_result=discovery_result,
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
            discovery_result=discovery_result,
            reconciliation_result=(
                reconciliation_result
            ),
            trading_started=trading_started,
            reason=(
                "PAPER startup completed safely."
            ),
        )