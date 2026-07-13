from app.duplicate_order_guard import (
    DuplicateOrderGuard,
)
from app.orders import Order, OrderSide


def create_order(
    symbol: str = "AAPL",
    side: OrderSide = OrderSide.BUY,
    quantity: int = 2,
) -> Order:
    return Order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=150.00,
    )


def test_first_order_reservation_is_approved() -> None:
    guard = DuplicateOrderGuard()
    order = create_order()

    result = guard.reserve(order)

    assert result.approved is True
    assert guard.is_reserved(order) is True


def test_identical_order_is_blocked() -> None:
    guard = DuplicateOrderGuard()
    order = create_order()

    first_result = guard.reserve(order)
    second_result = guard.reserve(order)

    assert first_result.approved is True
    assert second_result.approved is False
    assert "already being processed" in (
        second_result.reason
    )


def test_released_order_can_be_reserved_again() -> None:
    guard = DuplicateOrderGuard()
    order = create_order()

    guard.reserve(order)
    guard.release(order)

    result = guard.reserve(order)

    assert result.approved is True


def test_different_symbols_are_not_duplicates() -> None:
    guard = DuplicateOrderGuard()

    apple_order = create_order(
        symbol="AAPL"
    )
    microsoft_order = create_order(
        symbol="MSFT"
    )

    assert guard.reserve(apple_order).approved is True
    assert (
        guard.reserve(microsoft_order).approved
        is True
    )


def test_different_sides_are_not_duplicates() -> None:
    guard = DuplicateOrderGuard()

    buy_order = create_order(
        side=OrderSide.BUY
    )
    sell_order = create_order(
        side=OrderSide.SELL
    )

    assert guard.reserve(buy_order).approved is True
    assert guard.reserve(sell_order).approved is True


def test_different_quantities_are_not_duplicates() -> None:
    guard = DuplicateOrderGuard()

    small_order = create_order(
        quantity=1
    )
    large_order = create_order(
        quantity=2
    )

    assert guard.reserve(small_order).approved is True
    assert guard.reserve(large_order).approved is True


def test_symbol_matching_is_case_insensitive() -> None:
    guard = DuplicateOrderGuard()

    uppercase_order = create_order(
        symbol="AAPL"
    )
    lowercase_order = create_order(
        symbol="aapl"
    )

    assert (
        guard.reserve(uppercase_order).approved
        is True
    )
    assert (
        guard.reserve(lowercase_order).approved
        is False
    )


def test_releasing_missing_reservation_is_safe() -> None:
    guard = DuplicateOrderGuard()
    order = create_order()

    guard.release(order)

    assert guard.is_reserved(order) is False