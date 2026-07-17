import pytest

from app.position_state import (
    PositionState,
)


def test_creates_position_state() -> None:
    position = PositionState(
        symbol=" aapl ",
        quantity=3,
        average_entry_price=150.00,
        highest_price=155.00,
    )

    assert position.symbol == "AAPL"
    assert position.quantity == 3
    assert position.average_entry_price == 150.00
    assert position.highest_price == 155.00


def test_defaults_highest_price_to_entry_price() -> None:
    position = PositionState(
        symbol="MSFT",
        quantity=2,
        average_entry_price=320.00,
    )

    assert position.highest_price == 320.00


def test_updates_highest_price_only_when_price_increases() -> None:
    position = PositionState(
        symbol="AMZN",
        quantity=4,
        average_entry_price=250.00,
    )

    position.observe_price(
        260.00
    )
    position.observe_price(
        255.00
    )

    assert position.highest_price == 260.00


@pytest.mark.parametrize(
    (
        "symbol",
        "quantity",
        "average_entry_price",
    ),
    [
        ("", 1, 100.00),
        ("AAPL", 0, 100.00),
        ("AAPL", -1, 100.00),
        ("AAPL", 1, 0.00),
        ("AAPL", 1, -100.00),
    ],
)
def test_rejects_invalid_position_state(
    symbol: str,
    quantity: int,
    average_entry_price: float,
) -> None:
    with pytest.raises(
        ValueError
    ):
        PositionState(
            symbol=symbol,
            quantity=quantity,
            average_entry_price=(
                average_entry_price
            ),
        )


def test_rejects_highest_price_below_entry_price() -> None:
    with pytest.raises(
        ValueError,
        match="highest price",
    ):
        PositionState(
            symbol="AAPL",
            quantity=1,
            average_entry_price=150.00,
            highest_price=140.00,
        )


def test_rejects_invalid_observed_price() -> None:
    position = PositionState(
        symbol="AAPL",
        quantity=1,
        average_entry_price=150.00,
    )

    with pytest.raises(
        ValueError,
        match="Observed price",
    ):
        position.observe_price(
            0.00
        )
        
def test_adds_to_position_with_weighted_average() -> None:
    position = PositionState(
        symbol="AAPL",
        quantity=2,
        average_entry_price=100.00,
    )

    position.add(
        quantity=1,
        price=130.00,
    )

    assert position.quantity == 3
    assert position.average_entry_price == 110.00
    assert position.highest_price == 130.00


def test_add_rejects_invalid_quantity() -> None:
    position = PositionState(
        symbol="AAPL",
        quantity=1,
        average_entry_price=100.00,
    )

    with pytest.raises(
        ValueError,
        match="quantity",
    ):
        position.add(
            quantity=0,
            price=120.00,
        )


def test_add_rejects_invalid_price() -> None:
    position = PositionState(
        symbol="AAPL",
        quantity=1,
        average_entry_price=100.00,
    )

    with pytest.raises(
        ValueError,
        match="price",
    ):
        position.add(
            quantity=1,
            price=0.00,
        )
        
def test_reduces_position_quantity() -> None:
    position = PositionState(
        symbol="AAPL",
        quantity=5,
        average_entry_price=100.00,
        highest_price=130.00,
    )

    position.reduce(
        quantity=2,
    )

    assert position.quantity == 3
    assert position.average_entry_price == 100.00
    assert position.highest_price == 130.00


def test_reduce_rejects_entire_position() -> None:
    position = PositionState(
        symbol="AAPL",
        quantity=2,
        average_entry_price=100.00,
    )

    with pytest.raises(
        ValueError,
        match="less than",
    ):
        position.reduce(
            quantity=2,
        )


def test_reduce_rejects_invalid_quantity() -> None:
    position = PositionState(
        symbol="AAPL",
        quantity=2,
        average_entry_price=100.00,
    )

    with pytest.raises(
        ValueError,
        match="quantity",
    ):
        position.reduce(
            quantity=0,
        )
        
def test_calculates_return_percent() -> None:
    position = PositionState(
        symbol="AAPL",
        quantity=2,
        average_entry_price=100.00,
    )

    assert position.return_percent(
        current_price=110.00
    ) == pytest.approx(10.00)

    assert position.return_percent(
        current_price=90.00
    ) == pytest.approx(-10.00)


def test_calculates_drawdown_from_high_percent() -> None:
    position = PositionState(
        symbol="AAPL",
        quantity=2,
        average_entry_price=100.00,
        highest_price=125.00,
    )

    assert position.drawdown_from_high_percent(
        current_price=120.00
    ) == pytest.approx(-4.00)


def test_percentage_methods_reject_invalid_price() -> None:
    position = PositionState(
        symbol="AAPL",
        quantity=1,
        average_entry_price=100.00,
    )

    with pytest.raises(
        ValueError,
        match="Current price",
    ):
        position.return_percent(
            current_price=0.00
        )

    with pytest.raises(
        ValueError,
        match="Current price",
    ):
        position.drawdown_from_high_percent(
            current_price=0.00
        )