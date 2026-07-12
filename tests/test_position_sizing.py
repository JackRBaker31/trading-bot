import pytest

from app.position_sizing import (
    PercentagePositionSizer,
)


def test_calculates_quantity_from_percentage() -> None:
    sizer = PercentagePositionSizer(
        target_allocation_percent=10.0
    )

    result = sizer.calculate(
        portfolio_value=10_000.00,
        price=146.00,
        available_cash=10_000.00,
    )

    assert result.target_order_value == 1_000.00
    assert result.quantity == 6
    assert result.actual_order_value == 876.00


def test_position_size_is_limited_by_cash() -> None:
    sizer = PercentagePositionSizer(
        target_allocation_percent=50.0
    )

    result = sizer.calculate(
        portfolio_value=10_000.00,
        price=150.00,
        available_cash=500.00,
    )

    assert result.quantity == 3
    assert result.actual_order_value == 450.00


def test_returns_zero_when_one_share_is_unaffordable() -> None:
    sizer = PercentagePositionSizer(
        target_allocation_percent=10.0
    )

    result = sizer.calculate(
        portfolio_value=1_000.00,
        price=500.00,
        available_cash=100.00,
    )

    assert result.quantity == 0
    assert result.actual_order_value == 0.00


def test_rejects_invalid_allocation() -> None:
    with pytest.raises(
        ValueError,
        match="allocation",
    ):
        PercentagePositionSizer(
            target_allocation_percent=0
        )

    with pytest.raises(
        ValueError,
        match="allocation",
    ):
        PercentagePositionSizer(
            target_allocation_percent=101
        )


def test_rejects_invalid_inputs() -> None:
    sizer = PercentagePositionSizer(
        target_allocation_percent=10.0
    )

    with pytest.raises(
        ValueError,
        match="Portfolio value",
    ):
        sizer.calculate(
            portfolio_value=0,
            price=100.00,
            available_cash=1_000.00,
        )

    with pytest.raises(
        ValueError,
        match="Price",
    ):
        sizer.calculate(
            portfolio_value=10_000.00,
            price=0,
            available_cash=1_000.00,
        )

    with pytest.raises(
        ValueError,
        match="cash",
    ):
        sizer.calculate(
            portfolio_value=10_000.00,
            price=100.00,
            available_cash=-1.00,
        )