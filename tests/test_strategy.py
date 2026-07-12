from app.buy_the_dip import BuyTheDipStrategy
from app.orders import OrderSide


def test_first_price_read_generates_no_orders() -> None:
    strategy = BuyTheDipStrategy()

    orders = strategy.generate_orders(
        {
            "AAPL": 150.00,
            "MSFT": 320.00,
        }
    )

    assert orders == []


def test_drop_greater_than_two_percent_generates_buy_order() -> None:
    strategy = BuyTheDipStrategy()

    strategy.generate_orders(
        {
            "AAPL": 150.00,
        }
    )

    orders = strategy.generate_orders(
        {
            "AAPL": 146.00,
        }
    )

    assert len(orders) == 1
    assert orders[0].symbol == "AAPL"
    assert orders[0].side == OrderSide.BUY
    assert orders[0].quantity == 5
    assert orders[0].price == 146.00


def test_small_drop_generates_no_order() -> None:
    strategy = BuyTheDipStrategy()

    strategy.generate_orders(
        {
            "AAPL": 150.00,
        }
    )

    orders = strategy.generate_orders(
        {
            "AAPL": 148.00,
        }
    )

    assert orders == []


def test_price_increase_generates_no_order() -> None:
    strategy = BuyTheDipStrategy()

    strategy.generate_orders(
        {
            "AAPL": 150.00,
        }
    )

    orders = strategy.generate_orders(
        {
            "AAPL": 155.00,
        }
    )

    assert orders == []


def test_strategy_tracks_each_symbol_separately() -> None:
    strategy = BuyTheDipStrategy()

    strategy.generate_orders(
        {
            "AAPL": 150.00,
            "MSFT": 320.00,
        }
    )

    orders = strategy.generate_orders(
        {
            "AAPL": 146.00,
            "MSFT": 318.00,
        }
    )

    assert len(orders) == 1
    assert orders[0].symbol == "AAPL"