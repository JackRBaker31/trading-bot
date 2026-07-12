import pytest

from app.buy_the_dip import BuyTheDipStrategy
from app.orders import OrderSide
from app.portfolio import Portfolio


def create_portfolio() -> Portfolio:
    return Portfolio(
        starting_cash=10_000.00
    )


def test_first_price_read_generates_no_orders() -> None:
    strategy = BuyTheDipStrategy()
    portfolio = create_portfolio()

    orders = strategy.generate_orders(
        prices={
            "AAPL": 150.00,
            "MSFT": 320.00,
        },
        portfolio=portfolio,
    )

    assert orders == []


def test_drop_generates_percentage_sized_order() -> None:
    strategy = BuyTheDipStrategy(
        target_allocation_percent=10.0,
    )

    portfolio = create_portfolio()

    strategy.generate_orders(
        prices={"AAPL": 150.00},
        portfolio=portfolio,
    )

    orders = strategy.generate_orders(
        prices={"AAPL": 146.00},
        portfolio=portfolio,
    )

    assert len(orders) == 1
    assert orders[0].symbol == "AAPL"
    assert orders[0].side == OrderSide.BUY

    # 10% of £10,000 is £1,000.
    # floor(£1,000 / £146) = 6 shares.
    assert orders[0].quantity == 6
    assert orders[0].price == 146.00


def test_small_drop_generates_no_order() -> None:
    strategy = BuyTheDipStrategy()
    portfolio = create_portfolio()

    strategy.generate_orders(
        prices={"AAPL": 150.00},
        portfolio=portfolio,
    )

    orders = strategy.generate_orders(
        prices={"AAPL": 148.00},
        portfolio=portfolio,
    )

    assert orders == []


def test_price_increase_generates_no_order() -> None:
    strategy = BuyTheDipStrategy()
    portfolio = create_portfolio()

    strategy.generate_orders(
        prices={"AAPL": 150.00},
        portfolio=portfolio,
    )

    orders = strategy.generate_orders(
        prices={"AAPL": 155.00},
        portfolio=portfolio,
    )

    assert orders == []


def test_strategy_tracks_symbols_separately() -> None:
    strategy = BuyTheDipStrategy()
    portfolio = create_portfolio()

    strategy.generate_orders(
        prices={
            "AAPL": 150.00,
            "MSFT": 320.00,
        },
        portfolio=portfolio,
    )

    orders = strategy.generate_orders(
        prices={
            "AAPL": 146.00,
            "MSFT": 318.00,
        },
        portfolio=portfolio,
    )

    assert len(orders) == 1
    assert orders[0].symbol == "AAPL"


def test_strategy_does_not_repeat_during_cooldown() -> None:
    strategy = BuyTheDipStrategy(
        cooldown_cycles=2,
    )

    portfolio = create_portfolio()

    strategy.generate_orders(
        prices={"AAPL": 150.00},
        portfolio=portfolio,
    )

    first_orders = strategy.generate_orders(
        prices={"AAPL": 146.00},
        portfolio=portfolio,
    )

    second_orders = strategy.generate_orders(
        prices={"AAPL": 142.00},
        portfolio=portfolio,
    )

    assert len(first_orders) == 1
    assert second_orders == []


def test_strategy_can_trade_after_cooldown() -> None:
    strategy = BuyTheDipStrategy(
        cooldown_cycles=2,
    )

    portfolio = create_portfolio()

    strategy.generate_orders(
        prices={"AAPL": 150.00},
        portfolio=portfolio,
    )

    first_orders = strategy.generate_orders(
        prices={"AAPL": 146.00},
        portfolio=portfolio,
    )

    cooldown_orders = strategy.generate_orders(
        prices={"AAPL": 142.00},
        portfolio=portfolio,
    )

    later_orders = strategy.generate_orders(
        prices={"AAPL": 138.00},
        portfolio=portfolio,
    )

    assert len(first_orders) == 1
    assert cooldown_orders == []
    assert len(later_orders) == 1


def test_strategy_generates_no_order_when_cash_is_too_low() -> None:
    strategy = BuyTheDipStrategy(
        target_allocation_percent=10.0,
    )

    portfolio = Portfolio(
        starting_cash=100.00
    )

    strategy.generate_orders(
        prices={"AAPL": 150.00},
        portfolio=portfolio,
    )

    orders = strategy.generate_orders(
        prices={"AAPL": 146.00},
        portfolio=portfolio,
    )

    assert orders == []


def test_strategy_rejects_invalid_configuration() -> None:
    with pytest.raises(
        ValueError,
        match="Drop threshold",
    ):
        BuyTheDipStrategy(
            drop_threshold_percent=0,
        )

    with pytest.raises(
        ValueError,
        match="allocation",
    ):
        BuyTheDipStrategy(
            target_allocation_percent=0,
        )

    with pytest.raises(
        ValueError,
        match="Cooldown",
    ):
        BuyTheDipStrategy(
            cooldown_cycles=-1,
        )