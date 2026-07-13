from app.order_journal import OrderJournalEntry
from app.order_polling import (
    OrderPollingResult,
    OrderPollingService,
)


class OrderRecoveryService:
    RECOVERABLE_BROKER_EVENTS = {
        "SUBMITTED",
        "PENDING",
        "PARTIALLY_FILLED",
        "UNKNOWN",
    }

    def __init__(
        self,
        polling_service: OrderPollingService,
    ) -> None:
        self.polling_service = polling_service

    def recover(
        self,
        journal_entry: OrderJournalEntry,
    ) -> OrderPollingResult:
        if (
            journal_entry.event
            not in self.RECOVERABLE_BROKER_EVENTS
        ):
            raise ValueError(
                "Journal entry is not eligible for "
                "broker recovery."
            )

        if journal_entry.broker_order_id is None:
            raise ValueError(
                "Broker recovery requires a broker "
                "order ID."
            )

        return self.polling_service.poll(
            order_id=journal_entry.broker_order_id
        )