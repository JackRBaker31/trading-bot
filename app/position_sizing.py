from dataclasses import dataclass
from math import floor


@dataclass(frozen=True)
class PositionSizingResult:
    quantity: int
    target_order_value: float
    actual_order_value: float


class PercentagePositionSizer:
    def __init__(
        self,
        target_allocation_percent: float,
    ) -> None:
        if not 0 < target_allocation_percent <= 100:
            raise ValueError(
                "Target allocation percentage must be "
                "greater than zero and no more than 100."
            )

        self.target_allocation_percent = (
            target_allocation_percent
        )

    def calculate(
        self,
        portfolio_value: float,
        price: float,
        available_cash: float,
    ) -> PositionSizingResult:
        if portfolio_value <= 0:
            raise ValueError(
                "Portfolio value must be positive."
            )

        if price <= 0:
            raise ValueError(
                "Price must be positive."
            )

        if available_cash < 0:
            raise ValueError(
                "Available cash cannot be negative."
            )

        target_order_value = (
            portfolio_value
            * self.target_allocation_percent
            / 100
        )

        spendable_value = min(
            target_order_value,
            available_cash,
        )

        quantity = floor(
            spendable_value / price
        )

        actual_order_value = (
            quantity * price
        )

        return PositionSizingResult(
            quantity=quantity,
            target_order_value=target_order_value,
            actual_order_value=actual_order_value,
        )