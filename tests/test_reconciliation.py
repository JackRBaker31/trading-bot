import pytest

from app.broker import (
    BrokerAccountSummary,
    BrokerPosition,
)
from app.portfolio import Portfolio
from app.reconciliation import BrokerReconciler


def create_account_summary(
    available_to_trade: float = 5_000.00,
) -> BrokerAccountSummary:
    return BrokerAccountSummary(
        account_id=123,
        currency="GBP",
        available_to_trade=available_to_trade,
        reserved_for_orders=0.0,
        cash_in_pies=0.0,
        investments_current_value=0.0,
        investments_total_cost=0.0,
        realized_profit_loss=0.0,
        unrealized_profit_loss=0.0,
        total_value=available_to_trade,
    )


def create_reconciler() -> BrokerReconciler:
    return BrokerReconciler(
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
            "MSFT": "MSFT_US_EQ",
        }
    )


def test_empty_matching_accounts_reconcile() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    report = create_reconciler().reconcile(
        portfolio=portfolio,
        account_summary=create_account_summary(),
        broker_positions=[],
    )

    assert report.is_reconciled is True
    assert report.safe_to_trade is True
    assert report.issues == []


def test_cash_mismatch_blocks_trading() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    portfolio.cash = 4_500.00

    report = create_reconciler().reconcile(
        portfolio=portfolio,
        account_summary=create_account_summary(
            available_to_trade=5_000.00
        ),
        broker_positions=[],
    )

    assert report.is_reconciled is False
    assert report.safe_to_trade is False
    assert any(
        issue.category == "CASH"
        for issue in report.issues
    )


def test_matching_position_reconciles() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    portfolio.positions = {
        "AAPL": 5,
    }

    broker_positions = [
        BrokerPosition(
            ticker="AAPL_US_EQ",
            quantity=5,
            average_price_paid=150.00,
            current_price=155.00,
            profit_loss=25.00,
        )
    ]

    report = create_reconciler().reconcile(
        portfolio=portfolio,
        account_summary=create_account_summary(),
        broker_positions=broker_positions,
    )

    assert report.is_reconciled is True
    assert report.broker_positions == {
        "AAPL": 5.0,
    }


def test_position_quantity_mismatch_blocks_trading() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    portfolio.positions = {
        "AAPL": 5,
    }

    broker_positions = [
        BrokerPosition(
            ticker="AAPL_US_EQ",
            quantity=7,
            average_price_paid=150.00,
            current_price=155.00,
            profit_loss=35.00,
        )
    ]

    report = create_reconciler().reconcile(
        portfolio=portfolio,
        account_summary=create_account_summary(),
        broker_positions=broker_positions,
    )

    assert report.is_reconciled is False
    assert any(
        issue.category == "POSITION"
        for issue in report.issues
    )


def test_unmapped_broker_position_blocks_trading() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker_positions = [
        BrokerPosition(
            ticker="NVDA_US_EQ",
            quantity=2,
            average_price_paid=100.00,
            current_price=110.00,
            profit_loss=20.00,
        )
    ]

    report = create_reconciler().reconcile(
        portfolio=portfolio,
        account_summary=create_account_summary(),
        broker_positions=broker_positions,
    )

    assert report.is_reconciled is False
    assert any(
        issue.category == "UNMAPPED_POSITION"
        for issue in report.issues
    )


def test_cash_tolerance_is_respected() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    portfolio.cash = 4_999.995

    reconciler = BrokerReconciler(
        symbol_mapping={},
        cash_tolerance=0.01,
    )

    report = reconciler.reconcile(
        portfolio=portfolio,
        account_summary=create_account_summary(),
        broker_positions=[],
    )

    assert report.is_reconciled is True


def test_invalid_tolerances_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Cash tolerance",
    ):
        BrokerReconciler(
            symbol_mapping={},
            cash_tolerance=-1,
        )

    with pytest.raises(
        ValueError,
        match="Quantity tolerance",
    ):
        BrokerReconciler(
            symbol_mapping={},
            quantity_tolerance=-1,
        )