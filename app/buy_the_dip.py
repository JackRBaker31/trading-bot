from app.orders import Order, OrderSide
from app.portfolio import Portfolio
from app.position_sizing import PercentagePositionSizer
from app.strategy import Strategy
from app.technical_indicators import simple_moving_average
from app.entry_filter import EntryFilter

class BuyTheDipStrategy(Strategy):
    def __init__(
        self,
        drop_threshold_percent: float = 2.0,
        target_allocation_percent: float = 10.0,
        cooldown_cycles: int = 2,
        sma_period: int | None = None,
        entry_filters: list[EntryFilter] | None = None,
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
        self.sma_period = sma_period
        self.entry_filters = (
            list(entry_filters)
            if entry_filters is not None
            else []
        )

        self.previous_prices: dict[str, float] = {}
        self.cooldowns: dict[str, int] = {}
        self.price_history: dict[str, list[float]] = {}

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

            symbol_price_history = (
                self.price_history.setdefault(
                    symbol,
                    [],
                )
            )

            previous_price = self.previous_prices.get(
                symbol
            )

            if previous_price is None:
                self.previous_prices[symbol] = price
                symbol_price_history.append(price)
                continue

            percentage_change = (
                (price - previous_price)
                / previous_price
            ) * 100

            symbol_is_on_cooldown = (
                self.cooldowns.get(symbol, 0) > 0
            )

            sma_allows_buy = True

            if self.sma_period is not None:
                if len(symbol_price_history) < self.sma_period:
                    sma_allows_buy = False
                else:
                    moving_average = simple_moving_average(
                        values=symbol_price_history,
                        period=self.sma_period,
                    )
                    sma_allows_buy = (
                        price >= moving_average
                    )

            entry_filters_allow_buy = all(
                entry_filter.allows_entry(
                    symbol=symbol,
                    current_price=price,
                    price_history=list(
                        symbol_price_history
                    ),
                )
                for entry_filter in self.entry_filters
            )

            if (
                percentage_change
                <= -self.drop_threshold_percent
                and not symbol_is_on_cooldown
                and sma_allows_buy
                and entry_filters_allow_buy
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
            symbol_price_history.append(price)

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