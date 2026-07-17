from app.orders import (
    Order,
    OrderSide,
)
from app.position_exit_manager import (
    PositionExitManager,
)
from app.position_exit_policy import (
    PositionExitPolicy,
)
from app.position_state import (
    PositionState,
)
from app.position_exit_manager import (
    PositionExitManager,
)
from app.position_exit_policy import (
    PositionExitPolicy,
)
from app.position_state import (
    PositionState,
)


def test_generates_sell_order_for_exit_signal() -> None:
    manager = PositionExitManager(
        policy=PositionExitPolicy(
            stop_loss_percent=5.0,
            take_profit_percent=10.0,
            trailing_stop_percent=4.0,
            trailing_activation_percent=8.0,
        )
    )

    positions = {
        "AAPL": PositionState(
            symbol="AAPL",
            quantity=3,
            average_entry_price=100.00,
        ),
    }

    orders = manager.generate_exit_orders(
        positions=positions,
        current_prices={
            "AAPL": 94.00,
        },
    )

    assert orders == [
        Order(
            symbol="AAPL",
            side=OrderSide.SELL,
            quantity=3,
            price=94.00,
        ),
    ]


def test_does_not_generate_order_when_policy_holds() -> None:
    manager = PositionExitManager(
        policy=PositionExitPolicy(
            stop_loss_percent=5.0,
            take_profit_percent=10.0,
            trailing_stop_percent=4.0,
            trailing_activation_percent=8.0,
        )
    )

    positions = {
        "AAPL": PositionState(
            symbol="AAPL",
            quantity=3,
            average_entry_price=100.00,
            highest_price=105.00,
        ),
    }

    orders = manager.generate_exit_orders(
        positions=positions,
        current_prices={
            "AAPL": 103.00,
        },
    )

    assert orders == []


def test_skips_position_when_price_is_missing() -> None:
    manager = PositionExitManager(
        policy=PositionExitPolicy(
            stop_loss_percent=5.0,
            take_profit_percent=10.0,
            trailing_stop_percent=4.0,
            trailing_activation_percent=8.0,
        )
    )

    positions = {
        "AAPL": PositionState(
            symbol="AAPL",
            quantity=3,
            average_entry_price=100.00,
        ),
    }

    orders = manager.generate_exit_orders(
        positions=positions,
        current_prices={},
    )

    assert orders == []


def test_observes_price_before_evaluating() -> None:
    manager = PositionExitManager(
        policy=PositionExitPolicy(
            stop_loss_percent=5.0,
            take_profit_percent=20.0,
            trailing_stop_percent=4.0,
            trailing_activation_percent=8.0,
        )
    )

    position = PositionState(
        symbol="AAPL",
        quantity=3,
        average_entry_price=100.00,
    )

    orders = manager.generate_exit_orders(
        positions={
            "AAPL": position,
        },
        current_prices={
            "AAPL": 112.00,
        },
    )

    assert orders == []
    assert position.highest_price == 112.00