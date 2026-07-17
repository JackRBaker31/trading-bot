import pytest

from app.risk_position_sizer import (
    RiskPositionSizer,
)


def test_calculates_quantity_from_risk_budget() -> None:
    sizer = RiskPositionSizer(
        risk_percent=1.0,
    )

    quantity = sizer.calculate_quantity(
        portfolio_value=10_000.00,
        entry_price=100.00,
        stop_price=95.00,
        available_cash=10_000.00,
    )

    assert quantity == 20

def test_limits_quantity_to_available_cash() -> None:
    sizer = RiskPositionSizer(
        risk_percent=1.0,
    )

    quantity = sizer.calculate_quantity(
        portfolio_value=10_000.00,
        entry_price=100.00,
        stop_price=95.00,
        available_cash=750.00,
    )

    assert quantity == 7


def test_returns_zero_when_cash_cannot_buy_one_share() -> None:
    sizer = RiskPositionSizer(
        risk_percent=1.0,
    )

    quantity = sizer.calculate_quantity(
        portfolio_value=10_000.00,
        entry_price=100.00,
        stop_price=95.00,
        available_cash=99.00,
    )

    assert quantity == 0


def test_rejects_stop_price_at_or_above_entry() -> None:
    sizer = RiskPositionSizer(
        risk_percent=1.0,
    )

    with pytest.raises(
        ValueError,
        match="Stop price",
    ):
        sizer.calculate_quantity(
            portfolio_value=10_000.00,
            entry_price=100.00,
            stop_price=100.00,
            available_cash=10_000.00,
        )


@pytest.mark.parametrize(
    "risk_percent",
    [
        0.0,
        -1.0,
        100.0,
        101.0,
    ],
)
def test_rejects_invalid_risk_percent(
    risk_percent: float,
) -> None:
    with pytest.raises(
        ValueError,
    ):
        RiskPositionSizer(
            risk_percent=risk_percent,
        )


@pytest.mark.parametrize(
    (
        "portfolio_value",
        "entry_price",
        "stop_price",
        "available_cash",
    ),
    [
        (0.0, 100.0, 95.0, 1_000.0),
        (-1.0, 100.0, 95.0, 1_000.0),
        (10_000.0, 0.0, 95.0, 1_000.0),
        (10_000.0, -1.0, 95.0, 1_000.0),
        (10_000.0, 100.0, 95.0, -1.0),
    ],
)
def test_rejects_invalid_calculation_inputs(
    portfolio_value: float,
    entry_price: float,
    stop_price: float,
    available_cash: float,
) -> None:
    sizer = RiskPositionSizer(
        risk_percent=1.0,
    )

    with pytest.raises(
        ValueError,
    ):
        sizer.calculate_quantity(
            portfolio_value=portfolio_value,
            entry_price=entry_price,
            stop_price=stop_price,
            available_cash=available_cash,
        )