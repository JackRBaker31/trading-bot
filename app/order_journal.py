import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from app.orders import Order


@dataclass(frozen=True)
class OrderJournalEntry:
    timestamp: str
    reservation_key: str
    event: str
    symbol: str
    side: str
    quantity: int
    broker_order_id: int | None = None
    reason: str = ""
    metadata: dict[str, object] | None = None


class OrderJournal:
    ACTIVE_EVENTS = {
        "RESERVED",
        "SUBMITTED",
        "PENDING",
        "PARTIALLY_FILLED",
    }

    TERMINAL_EVENTS = {
        "FILLED",
        "REJECTED",
        "CANCELLED",
        "FAILED",
        "UNKNOWN",
        "RELEASED",
    }

    RECOVERABLE_EVENTS = {
        "RESERVED",
        "SUBMITTED",
        "PENDING",
        "PARTIALLY_FILLED",
        "UNKNOWN",
    }

    def __init__(
        self,
        path: str | Path,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.path = Path(path)
        self.clock = clock or (
            lambda: datetime.now(timezone.utc)
        )

    def create_reservation_key(
        self,
        order: Order,
    ) -> str:
        return (
            f"{order.symbol.strip().upper()}:"
            f"{order.side.value}:"
            f"{order.quantity}"
        )

    def record(
        self,
        order: Order,
        event: str,
        broker_order_id: int | None = None,
        reason: str = "",
        metadata: dict[str, object] | None = None,
    ) -> OrderJournalEntry:
        normalized_event = event.strip().upper()

        if not normalized_event:
            raise ValueError(
                "Journal event cannot be empty."
            )

        if broker_order_id is not None:
            if broker_order_id <= 0:
                raise ValueError(
                    "Broker order ID must be positive."
                )

        timestamp = (
            self.clock()
            .astimezone(timezone.utc)
            .isoformat()
        )

        entry = OrderJournalEntry(
            timestamp=timestamp,
            reservation_key=(
                self.create_reservation_key(order)
            ),
            event=normalized_event,
            symbol=order.symbol.strip().upper(),
            side=order.side.value,
            quantity=order.quantity,
            broker_order_id=broker_order_id,
            reason=reason,
            metadata=metadata,
        )

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as journal_file:
            journal_file.write(
                json.dumps(
                    asdict(entry),
                    separators=(",", ":"),
                )
            )
            journal_file.write("\n")
            journal_file.flush()

        return entry
    def record_from_entry(
        self,
        source_entry: OrderJournalEntry,
        event: str,
        broker_order_id: int | None = None,
        reason: str = "",
        metadata: dict[str, object] | None = None,
    ) -> OrderJournalEntry:
        normalized_event = event.strip().upper()

        if not normalized_event:
            raise ValueError(
                "Journal event cannot be empty."
            )

        if broker_order_id is not None:
            if broker_order_id <= 0:
                raise ValueError(
                    "Broker order ID must be positive."
                )

        timestamp = (
            self.clock()
            .astimezone(timezone.utc)
            .isoformat()
        )

        entry = OrderJournalEntry(
            timestamp=timestamp,
            reservation_key=(
                source_entry.reservation_key
            ),
            event=normalized_event,
            symbol=source_entry.symbol,
            side=source_entry.side,
            quantity=source_entry.quantity,
            broker_order_id=broker_order_id,
            reason=reason,
            metadata=metadata,
        )

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as journal_file:
            journal_file.write(
                json.dumps(
                    asdict(entry),
                    separators=(",", ":"),
                )
            )
            journal_file.write("\n")
            journal_file.flush()

        return entry


    def load_entries(
        self,
    ) -> list[OrderJournalEntry]:
        if not self.path.exists():
            return []

        entries: list[OrderJournalEntry] = []

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as journal_file:
            for line_number, line in enumerate(
                journal_file,
                start=1,
            ):
                stripped_line = line.strip()

                if not stripped_line:
                    continue

                try:
                    raw_entry = json.loads(
                        stripped_line
                    )
                    entry = OrderJournalEntry(
                        **raw_entry
                    )
                except (
                    json.JSONDecodeError,
                    TypeError,
                ) as exc:
                    raise ValueError(
                        "Invalid order journal entry "
                        f"on line {line_number}."
                    ) from exc

                entries.append(entry)

        return entries

    def latest_entries(
        self,
    ) -> dict[str, OrderJournalEntry]:
        latest: dict[str, OrderJournalEntry] = {}

        for entry in self.load_entries():
            latest[entry.reservation_key] = entry

        return latest

    def active_reservation_keys(
        self,
    ) -> set[str]:
        active_keys: set[str] = set()

        for reservation_key, entry in (
            self.latest_entries().items()
        ):
            if entry.event in self.ACTIVE_EVENTS:
                active_keys.add(reservation_key)

        return active_keys
    
    def load_unfinished_orders(
        self,
    ) -> list[OrderJournalEntry]:
        unfinished_entries: list[
            OrderJournalEntry
        ] = []

        for entry in self.latest_entries().values():
            if entry.event in self.RECOVERABLE_EVENTS:
                unfinished_entries.append(entry)

        return unfinished_entries