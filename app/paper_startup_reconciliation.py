from dataclasses import dataclass
from typing import Protocol

from app.broker import (
    BrokerAccountSummary,
    BrokerOrderResult,
    BrokerPosition,
)
from app.portfolio import Portfolio
from app.reconciliation import (
    BrokerReconciler,
    ReconciliationReport,
)


class ReadOnlyBroker(Protocol):
    def get_account_summary(
        self,
    ) -> BrokerAccountSummary:
        """Return the broker account summary."""

    def get_positions(
        self,
    ) -> list[BrokerPosition]:
        """Return the broker positions."""

    def get_active_orders(
        self,
    ) -> list[BrokerOrderResult]:
        """Return all active broker orders."""

@dataclass(frozen=True)
class PaperStartupReconciliationResult:
    report: ReconciliationReport
    approved: bool
    reason: str


class PaperStartupReconciliationService:
    def __init__(
        self,
        broker: ReadOnlyBroker,
        reconciler: BrokerReconciler,
        portfolio: Portfolio,
    ) -> None:
        self.broker = broker
        self.reconciler = reconciler
        self.portfolio = portfolio

    def reconcile(
        self,
    ) -> PaperStartupReconciliationResult:
        account_summary = (
            self.broker.get_account_summary()
        )

        broker_positions = (
            self.broker.get_positions()
        )

        report = self.reconciler.reconcile(
            portfolio=self.portfolio,
            account_summary=account_summary,
            broker_positions=broker_positions,
        )

        active_orders = (
            self.broker.get_active_orders()
        )

        if active_orders:
            return PaperStartupReconciliationResult(
                report=report,
                approved=False,
                reason=(
                    "PAPER startup reconciliation "
                    "blocked by active broker orders."
                ),
            )

        if not report.safe_to_trade:
            return PaperStartupReconciliationResult(
                report=report,
                approved=False,
                reason=(
                    "PAPER startup reconciliation "
                    "failed."
                ),
            )

        return PaperStartupReconciliationResult(
            report=report,
            approved=True,
            reason=(
                "PAPER startup reconciliation "
                "completed safely."
            ),
        )