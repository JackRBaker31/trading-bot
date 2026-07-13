from dataclasses import dataclass
from enum import Enum

from app.order_journal import (
    OrderJournal,
    OrderJournalEntry,
)
from app.order_polling import OrderPollingResult
from app.order_recovery import OrderRecoveryService
from app.order_verification import (
    OrderVerificationStatus,
)

class StartupRecoveryState(str, Enum):
    PENDING = "PENDING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    RECOVERY_ERROR = "RECOVERY_ERROR"


@dataclass(frozen=True)
class StartupRecoveryItem:
    journal_entry: OrderJournalEntry
    polling_result: OrderPollingResult | None
    error: str | None

    @property
    def succeeded(self) -> bool:
        return (
            self.polling_result is not None
            and self.error is None
        )

    @property
    def state(self) -> StartupRecoveryState:
        if self.error is not None:
            return (
                StartupRecoveryState.RECOVERY_ERROR
            )

        if self.polling_result is None:
            return StartupRecoveryState.UNKNOWN

        state_by_status = {
            OrderVerificationStatus.PENDING: (
                StartupRecoveryState.PENDING
            ),
            OrderVerificationStatus.PARTIALLY_FILLED: (
                StartupRecoveryState.PARTIALLY_FILLED
            ),
            OrderVerificationStatus.FILLED: (
                StartupRecoveryState.FILLED
            ),
            OrderVerificationStatus.FAILED: (
                StartupRecoveryState.FAILED
            ),
            OrderVerificationStatus.UNKNOWN: (
                StartupRecoveryState.UNKNOWN
            ),
        }

        return state_by_status.get(
            self.polling_result.status,
            StartupRecoveryState.UNKNOWN,
        )


@dataclass(frozen=True)
class StartupRecoveryReport:
    items: tuple[StartupRecoveryItem, ...]

    @property
    def total_orders(self) -> int:
        return len(self.items)

    @property
    def successful_orders(self) -> int:
        return sum(
            item.succeeded
            for item in self.items
        )

    @property
    def failed_orders(self) -> int:
        return (
            self.total_orders
            - self.successful_orders
        )


class StartupRecoveryService:
    def __init__(
        self,
        order_journal: OrderJournal,
        recovery_service: OrderRecoveryService,
    ) -> None:
        self.order_journal = order_journal
        self.recovery_service = recovery_service

    def recover_unfinished_orders(
        self,
    ) -> StartupRecoveryReport:
        items: list[StartupRecoveryItem] = []

        unfinished_orders = (
            self.order_journal
            .load_unfinished_orders()
        )

        for journal_entry in unfinished_orders:
            try:
                polling_result = (
                    self.recovery_service.recover(
                        journal_entry=journal_entry
                    )
                )
            except Exception as error:
                items.append(
                    StartupRecoveryItem(
                        journal_entry=journal_entry,
                        polling_result=None,
                        error=str(error),
                    )
                )
                continue

            items.append(
                StartupRecoveryItem(
                    journal_entry=journal_entry,
                    polling_result=polling_result,
                    error=None,
                )
            )

        return StartupRecoveryReport(
            items=tuple(items)
        )