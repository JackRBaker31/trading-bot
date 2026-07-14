from app.active_order_manager import (
    ActiveOrderManager,
)
from app.broker import BrokerOrderResult


def create_order(
    *,
    ticker: str,
    side: str = "BUY",
    status: str = "NEW",
    quantity: float = 1.0,
) -> BrokerOrderResult:
    return BrokerOrderResult(
        order_id=123456,
        ticker=ticker,
        quantity=quantity,
        side=side,
        status=status,
        order_type="MARKET",
        filled_quantity=0.0,
        filled_value=0.0,
        currency="GBP",
    )


def test_symbol_with_active_order_is_blocked() -> None:
    manager = ActiveOrderManager(
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
            "MSFT": "MSFT_US_EQ",
        },
        active_orders=[
            create_order(
                ticker="AAPL_US_EQ",
            )
        ],
    )

    assert manager.is_symbol_blocked("AAPL") is True
    assert manager.is_symbol_blocked("MSFT") is False


def test_symbol_lookup_is_cleaned() -> None:
    manager = ActiveOrderManager(
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
        },
        active_orders=[
            create_order(
                ticker="AAPL_US_EQ",
            )
        ],
    )

    assert manager.is_symbol_blocked(
        " aapl "
    ) is True


def test_unknown_symbol_is_rejected() -> None:
    manager = ActiveOrderManager(
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
        },
        active_orders=[],
    )

    try:
        manager.is_symbol_blocked("MSFT")
    except ValueError as error:
        assert "MSFT" in str(error)
    else:
        raise AssertionError(
            "Expected unknown symbol to be rejected."
        )

class FakeProvider:
    def __init__(
        self,
        orders,
    ):
        self.orders = orders

    def get_active_orders(
        self,
    ):
        return list(self.orders)

def test_refresh_updates_blocked_symbols() -> None:
    provider = FakeProvider(
        [
            create_order(
                ticker="MSFT_US_EQ",
            )
        ]
    )

    manager = ActiveOrderManager(
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
            "MSFT": "MSFT_US_EQ",
        },
        active_orders=[],
        order_provider=provider,
    )

    assert (
        manager.is_symbol_blocked("AAPL")
        is False
    )

    assert (
        manager.is_symbol_blocked("MSFT")
        is False
    )

    manager.refresh()

    assert (
        manager.is_symbol_blocked("AAPL")
        is False
    )

    assert (
        manager.is_symbol_blocked("MSFT")
        is True
    )

def test_refresh_unblocks_removed_orders() -> None:
    provider = FakeProvider([])

    manager = ActiveOrderManager(
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
        },
        active_orders=[
            create_order(
                ticker="AAPL_US_EQ",
            )
        ],
        order_provider=provider,
    )

    assert (
        manager.is_symbol_blocked("AAPL")
        is True
    )

    manager.refresh()

    assert (
        manager.is_symbol_blocked("AAPL")
        is False
    )
