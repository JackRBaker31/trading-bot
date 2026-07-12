from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TradeLogEntry:
    timestamp: datetime
    symbol: str
    side: str
    quantity: int
    price: float
    order_value: float
    approved: bool
    reason: str
    executed: bool


class TradeLog:
    def __init__(self) -> None:
        self.entries: list[TradeLogEntry] = []

    def add(self, entry: TradeLogEntry) -> None:
        self.entries.append(entry)

    def display(self) -> None:
        print("\n--- TRADE LOG ---")

        if not self.entries:
            print("No orders recorded.")
            return

        for entry in self.entries:
            status = "EXECUTED" if entry.executed else "REJECTED"

            print(
                f"{entry.timestamp} | "
                f"{entry.side} {entry.quantity} {entry.symbol} "
                f"at £{entry.price:.2f} | "
                f"{status} | {entry.reason}"
            )

        print("-----------------")