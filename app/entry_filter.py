from typing import Protocol


class EntryFilter(Protocol):
    def allows_entry(
        self,
        *,
        symbol: str,
        current_price: float,
        price_history: list[float],
    ) -> bool:
        ...