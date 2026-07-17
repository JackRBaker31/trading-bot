from app.orders import (
    Order,
    OrderSide,
)
from app.position_exit_policy import (
    PositionExitPolicy,
)
from app.position_state import (
    PositionState,
)
from dataclasses import dataclass

@dataclass(frozen=True)
class PositionExitOrder:
    order: Order
    reason: str

class PositionExitManager:
    def __init__(
        self,
        *,
        policy: PositionExitPolicy,
    ) -> None:
        self._policy = policy

    def generate_exit_orders(
        self,
        *,
        positions: dict[
            str,
            PositionState,
        ],
        current_prices: dict[
            str,
            float,
        ],
    ) -> list[Order]:
        orders: list[Order] = []

        for symbol, position in (
            positions.items()
        ):
            normalised_symbol = (
                symbol.upper().strip()
            )

            current_price = (
                current_prices.get(
                    normalised_symbol
                )
            )

            if current_price is None:
                continue

            position.observe_price(
                current_price
            )

            decision = (
                self._policy.evaluate(
                    position=position,
                    current_price=current_price,
                )
            )

            if not decision.should_exit:
                continue

            orders.append(
                Order(
                    symbol=normalised_symbol,
                    side=OrderSide.SELL,
                    quantity=position.quantity,
                    price=current_price,
                )
            )

        return orders