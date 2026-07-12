from dataclasses import dataclass
from enum import Enum


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Order:
    symbol: str
    side: OrderSide
    quantity: int
    price: float

    def __post_init__(self) -> None:
        cleaned_symbol = self.symbol.upper().strip()
        object.__setattr__(self, "symbol", cleaned_symbol)

        if not cleaned_symbol:
            raise ValueError("A stock symbol is required.")

        if self.quantity <= 0:
            raise ValueError("Order quantity must be greater than zero.")

        if self.price <= 0:
            raise ValueError("Order price must be greater than zero.")

    @property
    def value(self) -> float:
        return self.quantity * self.price