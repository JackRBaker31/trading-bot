from dataclasses import dataclass

from app.orders import (
    Order,
    OrderSide,
)


@dataclass(frozen=True)
class ExecutionCostResult:
    fill_price: float
    fee: float

    @property
    def total_cost_adjustment(self) -> float:
        return self.fee


@dataclass(frozen=True)
class ExecutionCostModel:
    slippage_percent: float = 0.0
    commission_percent: float = 0.0
    minimum_fee: float = 0.0

    def __post_init__(self) -> None:
        if self.slippage_percent < 0:
            raise ValueError(
                "Slippage percentage cannot be negative."
            )

        if self.commission_percent < 0:
            raise ValueError(
                "Commission percentage cannot be negative."
            )

        if self.minimum_fee < 0:
            raise ValueError(
                "Minimum fee cannot be negative."
            )

    def calculate(
        self,
        *,
        order: Order,
    ) -> ExecutionCostResult:
        slippage_fraction = (
            self.slippage_percent
            / 100.0
        )

        if order.side is OrderSide.BUY:
            fill_price = (
                order.price
                * (
                    1.0
                    + slippage_fraction
                )
            )
        else:
            fill_price = (
                order.price
                * (
                    1.0
                    - slippage_fraction
                )
            )

        gross_value = (
            order.quantity
            * fill_price
        )

        percentage_fee = (
            gross_value
            * self.commission_percent
            / 100.0
        )

        fee = max(
            percentage_fee,
            self.minimum_fee,
        )

        return ExecutionCostResult(
            fill_price=fill_price,
            fee=fee,
        )