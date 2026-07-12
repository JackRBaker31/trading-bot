from app.orders import Order, OrderSide
from app.strategy import Strategy


class BuyTheDipStrategy(Strategy):
    def __init__(
        self,
        drop_threshold_percent: float = 2.0,
        quantity: int = 5,
        cooldown_cycles: int = 2,
    ) -> None:
        if drop_threshold_percent <= 0:
            raise ValueError("Drop threshold must be positive.")

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        if cooldown_cycles < 0:
            raise ValueError("Cooldown cycles cannot be negative.")

        self.drop_threshold_percent = drop_threshold_percent
        self.quantity = quantity
        self.cooldown_cycles = cooldown_cycles

        self.previous_prices: dict[str, float] = {}
        self.cooldowns: dict[str, int] = {}

    def generate_orders(
        self,
        prices: dict[str, float],
    ) -> list[Order]:
        orders: list[Order] = []

        self._reduce_cooldowns()

        for symbol, price in prices.items():
            previous_price = self.previous_prices.get(symbol)

            if previous_price is None:
                self.previous_prices[symbol] = price
                continue

            percentage_change = (
                (price - previous_price) / previous_price
            ) * 100

            symbol_is_on_cooldown = self.cooldowns.get(symbol, 0) > 0

            if (
                percentage_change <= -self.drop_threshold_percent
                and not symbol_is_on_cooldown
            ):
                orders.append(
                    Order(
                        symbol=symbol,
                        side=OrderSide.BUY,
                        quantity=self.quantity,
                        price=price,
                    )
                )

                self.cooldowns[symbol] = self.cooldown_cycles

            self.previous_prices[symbol] = price

        return orders

    def _reduce_cooldowns(self) -> None:
        for symbol in list(self.cooldowns):
            remaining_cycles = self.cooldowns[symbol] - 1

            if remaining_cycles <= 0:
                del self.cooldowns[symbol]
            else:
                self.cooldowns[symbol] = remaining_cycles