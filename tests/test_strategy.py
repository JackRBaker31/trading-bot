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

def test_strategy_does_not_repeat_order_during_cooldown() -> None:
    strategy = BuyTheDipStrategy(
        cooldown_cycles=2,
    )

    strategy.generate_orders(
        {"AAPL": 150.00}
    )

    first_orders = strategy.generate_orders(
        {"AAPL": 146.00}
    )

    second_orders = strategy.generate_orders(
        {"AAPL": 142.00}
    )

    assert len(first_orders) == 1
    assert second_orders == []


def test_strategy_can_trade_again_after_cooldown() -> None:
    strategy = BuyTheDipStrategy(
        cooldown_cycles=2,
    )

    strategy.generate_orders(
        {"AAPL": 150.00}
    )

    first_orders = strategy.generate_orders(
        {"AAPL": 146.00}
    )

    cooldown_orders = strategy.generate_orders(
        {"AAPL": 142.00}
    )

    later_orders = strategy.generate_orders(
        {"AAPL": 138.00}
    )

    assert len(first_orders) == 1
    assert cooldown_orders == []
    assert len(later_orders) == 1


def test_strategy_uses_configured_quantity() -> None:
    strategy = BuyTheDipStrategy(
        quantity=3,
    )

    strategy.generate_orders(
        {"AAPL": 150.00}
    )

    orders = strategy.generate_orders(
        {"AAPL": 146.00}
    )

    assert len(orders) == 1
    assert orders[0].quantity == 3


def test_strategy_rejects_invalid_configuration() -> None:
    import pytest

    with pytest.raises(
        ValueError,
        match="Drop threshold",
    ):
        BuyTheDipStrategy(
            drop_threshold_percent=0,
        )

    with pytest.raises(
        ValueError,
        match="Quantity",
    ):
        BuyTheDipStrategy(
            quantity=0,
        )

    with pytest.raises(
        ValueError,
        match="Cooldown",
    ):
        BuyTheDipStrategy(
            cooldown_cycles=-1,
        )