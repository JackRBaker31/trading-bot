from dataclasses import dataclass
from typing import Protocol

from app.broker import BrokerOrderResult
from app.order_journal import OrderJournalEntry


class ActiveOrderBroker(Protocol):
    def get_active_orders(
        self,
    ) -> list[BrokerOrderResult]:
        """Return all active broker orders."""


class UnfinishedOrderJournal(Protocol):
    def find_unfinished_order_by_broker_order_id(
        self,
        broker_order_id: int,
    ) -> OrderJournalEntry | None:
        """Return a matching unfinished journal entry."""


@dataclass(frozen=True)
class StartupOrderDiscoveryResult:
    approved: bool
    known_order_ids: tuple[int, ...]
    unknown_order_ids: tuple[int, ...]
    reason: str

    @property
    def known_order_count(
        self,
    ) -> int:
        return len(
            self.known_order_ids
        )

    @property
    def unknown_order_count(
        self,
    ) -> int:
        return len(
            self.unknown_order_ids
        )

class StartupOrderDiscoveryService:
    def __init__(
        self,
        broker: ActiveOrderBroker,
        journal: UnfinishedOrderJournal,
    ) -> None:
        self.broker = broker
        self.journal = journal

    def discover(
        self,
    ) -> StartupOrderDiscoveryResult:
        known_order_ids: list[int] = []
        unknown_order_ids: list[int] = []

        for order in self.broker.get_active_orders():
            journal_entry = (
                self.journal
                .find_unfinished_order_by_broker_order_id(
                    order.order_id
                )
            )

            if journal_entry is None:
                unknown_order_ids.append(
                    order.order_id
                )
            else:
                known_order_ids.append(
                    order.order_id
                )

        if unknown_order_ids:
            return StartupOrderDiscoveryResult(
                approved=False,
                known_order_ids=tuple(
                    known_order_ids
                ),
                unknown_order_ids=tuple(
                    unknown_order_ids
                ),
                reason=(
                    "PAPER startup blocked by unknown "
                    "active broker orders."
                ),
            )

        return StartupOrderDiscoveryResult(
            approved=True,
            known_order_ids=tuple(
                known_order_ids
            ),
            unknown_order_ids=(),
            reason=(
                "PAPER startup order discovery "
                "completed safely."
            ),
        )