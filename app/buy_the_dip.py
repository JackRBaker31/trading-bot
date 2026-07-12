from app.orders import Order
from app.orders import OrderSide
from app.strategy import Strategy


class BuyTheDipStrategy(Strategy):

    def __init__(self):
        self.previous_prices: dict[str, float] = {}

    def generate_orders(
        self,
        prices: dict[str, float],
    ) -> list[Order]:

        orders: list[Order] = []

        for symbol, price in prices.items():

            previous_price = self.previous_prices.get(symbol)

            if previous_price is None:
                self.previous_prices[symbol] = price
                continue

            percentage_change = (
                (price - previous_price)
                / previous_price
            ) * 100

            if percentage_change <= -2:

                orders.append(
                    Order(
                        symbol=symbol,
                        side=OrderSide.BUY,
                        quantity=5,
                        price=price,
                    )
                )

            self.previous_prices[symbol] = price

        return orders