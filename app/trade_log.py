import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


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

    def to_dictionary(self) -> dict[str, object]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class TradeLog:
    def __init__(self, file_path: str = "data/trade_log.jsonl") -> None:
        self.entries: list[TradeLogEntry] = []
        self.file_path = Path(file_path)

    def add(self, entry: TradeLogEntry) -> None:
        self.entries.append(entry)
        self._save_entry(entry)

    def _save_entry(self, entry: TradeLogEntry) -> None:
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.file_path.open(
            mode="a",
            encoding="utf-8",
        ) as file:
            json.dump(entry.to_dictionary(), file)
            file.write("\n")

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