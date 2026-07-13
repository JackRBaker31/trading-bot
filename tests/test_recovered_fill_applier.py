import pytest

from app.portfolio import Portfolio
from app.recovered_fill import RecoveredFill
from app.recovered_fill_applier import (
    RecoveredFillApplier,
)


class FakePortfolioStore:
    def __init__(
        self,
        save_error: Exception | None = None,
    ) -> None:
        self.save_error = save_error
        self.save_calls: list[Portfolio] = []

    def save(
        self,
        portfolio: Portfolio,
    ) -> None:
        self.save_calls.append(portfolio)

        if self.save_error is not None:
            raise self.save_error


def create_recovered_fill(
    side: str = "BUY",
    broker_order_id: int = 123456,
    quantity: int = 2,
    filled_value: float = 300.0,
    average_fill_price: float = 150.0,
) -> RecoveredFill:
    return RecoveredFill(
        broker_order_id=broker_order_id,
        reservation_key=(
            f"AAPL:{side}:{quantity}"
        ),
        symbol="AAPL",
        side=side,
        quantity=quantity,
        filled_value=filled_value,
        average_fill_price=average_fill_price,
    )


def test_recovered_buy_is_applied_and_saved() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )
    store = FakePortfolioStore()

    applier = RecoveredFillApplier(
        portfolio=portfolio,
        portfolio_store=store,
    )

    result = applier.apply(
        recovered_fill=create_recovered_fill()
    )

    assert result.applied is True
    assert portfolio.cash == 4_700.00
    assert portfolio.positions == {
        "AAPL": 2,
    }
    assert (
        portfolio.applied_broker_order_ids
        == {123456}
    )
    assert store.save_calls == [portfolio]


def test_recovered_sell_is_applied_and_saved() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    portfolio.buy(
        symbol="AAPL",
        quantity=2,
        price=150.00,
    )

    store = FakePortfolioStore()

    applier = RecoveredFillApplier(
        portfolio=portfolio,
        portfolio_store=store,
    )

    result = applier.apply(
        recovered_fill=create_recovered_fill(
            side="SELL",
            filled_value=320.0,
            average_fill_price=160.0,
        )
    )

    assert result.applied is True
    assert portfolio.cash == 5_020.00
    assert portfolio.positions == {}
    assert (
        portfolio.applied_broker_order_ids
        == {123456}
    )
    assert store.save_calls == [portfolio]


def test_already_applied_fill_is_not_applied_again() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    portfolio.mark_broker_order_applied(
        broker_order_id=123456
    )

    store = FakePortfolioStore()

    applier = RecoveredFillApplier(
        portfolio=portfolio,
        portfolio_store=store,
    )

    result = applier.apply(
        recovered_fill=create_recovered_fill()
    )

    assert result.applied is False
    assert portfolio.cash == 5_000.00
    assert portfolio.positions == {}
    assert (
        portfolio.applied_broker_order_ids
        == {123456}
    )
    assert store.save_calls == []


def test_save_failure_rolls_back_portfolio() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    store = FakePortfolioStore(
        save_error=RuntimeError(
            "Portfolio persistence failed."
        )
    )

    applier = RecoveredFillApplier(
        portfolio=portfolio,
        portfolio_store=store,
    )

    with pytest.raises(
        RuntimeError,
        match="persistence failed",
    ):
        applier.apply(
            recovered_fill=create_recovered_fill()
        )

    assert portfolio.cash == 5_000.00
    assert portfolio.positions == {}
    assert (
        portfolio.applied_broker_order_ids
        == set()
    )


def test_invalid_recovered_side_changes_nothing() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )
    store = FakePortfolioStore()

    applier = RecoveredFillApplier(
        portfolio=portfolio,
        portfolio_store=store,
    )

    with pytest.raises(
        ValueError,
        match="BUY or SELL",
    ):
        applier.apply(
            recovered_fill=create_recovered_fill(
                side="HOLD",
            )
        )

    assert portfolio.cash == 5_000.00
    assert portfolio.positions == {}
    assert (
        portfolio.applied_broker_order_ids
        == set()
    )
    assert store.save_calls == []