from app.orders import Order, OrderSide
from app.portfolio import Portfolio
from app.position_sizing import PercentagePositionSizer
from app.strategy import Strategy


class BuyTheDipStrategy(Strategy):
    def __init__(
        self,
        drop_threshold_percent: float = 2.0,
        target_allocation_percent: float = 10.0,
        cooldown_cycles: int = 2,
    ) -> None:
        if drop_threshold_percent <= 0:
            raise ValueError(
                "Drop threshold must be positive."
            )

        if cooldown_cycles < 0:
            raise ValueError(
                "Cooldown cycles cannot be negative."
            )

        self.drop_threshold_percent = (
            drop_threshold_percent
        )

        self.position_sizer = PercentagePositionSizer(
            target_allocation_percent=(
                target_allocation_percent
            )
        )

        self.cooldown_cycles = cooldown_cycles

        self.previous_prices: dict[str, float] = {}
        self.cooldowns: dict[str, int] = {}

    def generate_orders(
        self,
        prices: dict[str, float],
        portfolio: Portfolio,
    ) -> list[Order]:
        orders: list[Order] = []

        self._reduce_cooldowns()

        portfolio_value = portfolio.portfolio_value(
            current_prices=prices
        )

        available_cash = portfolio.cash

        for symbol, price in prices.items():
            previous_price = self.previous_prices.get(
                symbol
            )

            if previous_price is None:
                self.previous_prices[symbol] = price
                continue

            percentage_change = (
                (price - previous_price)
                / previous_price
            ) * 100

            symbol_is_on_cooldown = (
                self.cooldowns.get(symbol, 0) > 0
            )

            if (
                percentage_change
                <= -self.drop_threshold_percent
                and not symbol_is_on_cooldown
            ):
                sizing_result = (
                    self.position_sizer.calculate(
                        portfolio_value=portfolio_value,
                        price=price,
                        available_cash=available_cash,
                    )
                )

                if sizing_result.quantity > 0:
                    orders.append(
                        Order(
                            symbol=symbol,
                            side=OrderSide.BUY,
                            quantity=(
                                sizing_result.quantity
                            ),
                            price=price,
                        )
                    )

                    available_cash -= (
                        sizing_result.actual_order_value
                    )

                    self.cooldowns[symbol] = (
                        self.cooldown_cycles
                    )

            self.previous_prices[symbol] = price

        return orders

    def _reduce_cooldowns(self) -> None:
        for symbol in list(self.cooldowns):
            remaining_cycles = (
                self.cooldowns[symbol] - 1
            )

            if remaining_cycles <= 0:
                del self.cooldowns[symbol]
            else:
                self.cooldowns[symbol] = (
                    remaining_cycles
                )