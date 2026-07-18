import pytest

from app.execution_cost import (
    ExecutionCostModel,
)
from app.orders import (
    Order,
    OrderSide,
)


def test_applies_buy_slippage_upwards() -> None:
    model = ExecutionCostModel(
        slippage_percent=1.0,
    )

    result = model.calculate(
        order=Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=2,
            price=100.0,
        )
    )

    assert result.fill_price == pytest.approx(
        101.0
    )


def test_applies_sell_slippage_downwards() -> None:
    model = ExecutionCostModel(
        slippage_percent=1.0,
    )

    result = model.calculate(
        order=Order(
            symbol="AAPL",
            side=OrderSide.SELL,
            quantity=2,
            price=100.0,
        )
    )

    assert result.fill_price == pytest.approx(
        99.0
    )


def test_calculates_percentage_commission() -> None:
    model = ExecutionCostModel(
        commission_percent=0.5,
    )

    result = model.calculate(
        order=Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10,
            price=100.0,
        )
    )

    assert result.fee == pytest.approx(
        5.0
    )


def test_applies_minimum_fee() -> None:
    model = ExecutionCostModel(
        commission_percent=0.01,
        minimum_fee=1.0,
    )

    result = model.calculate(
        order=Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=1,
            price=100.0,
        )
    )

    assert result.fee == pytest.approx(
        1.0
    )


@pytest.mark.parametrize(
    (
        "slippage_percent",
        "commission_percent",
        "minimum_fee",
    ),
    [
        (-1.0, 0.0, 0.0),
        (0.0, -1.0, 0.0),
        (0.0, 0.0, -1.0),
    ],
)
def test_rejects_negative_cost_inputs(
    slippage_percent: float,
    commission_percent: float,
    minimum_fee: float,
) -> None:
    with pytest.raises(ValueError):
        ExecutionCostModel(
            slippage_percent=slippage_percent,
            commission_percent=(
                commission_percent
            ),
            minimum_fee=minimum_fee,
        )