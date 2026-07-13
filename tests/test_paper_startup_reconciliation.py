from app.broker import (
    BrokerAccountSummary,
    BrokerPosition,
)
from app.paper_startup_reconciliation import (
    PaperStartupReconciliationService,
)
from app.portfolio import Portfolio
from app.reconciliation import BrokerReconciler


class FakeBroker:
    def __init__(
        self,
        account_summary: BrokerAccountSummary,
        positions: list[BrokerPosition],
    ) -> None:
        self.account_summary = account_summary
        self.positions = positions
        self.account_calls = 0
        self.position_calls = 0

    def get_account_summary(
        self,
    ) -> BrokerAccountSummary:
        self.account_calls += 1
        return self.account_summary

    def get_positions(
        self,
    ) -> list[BrokerPosition]:
        self.position_calls += 1
        return self.positions


def create_account_summary(
    available_to_trade: float,
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


def test_matching_account_is_approved() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        account_summary=create_account_summary(
            available_to_trade=5_000.00
        ),
        positions=[],
    )

    service = PaperStartupReconciliationService(
        broker=broker,
        reconciler=create_reconciler(),
        portfolio=portfolio,
    )

    result = service.reconcile()

    assert broker.account_calls == 1
    assert broker.position_calls == 1
    assert result.approved is True
    assert result.report.is_reconciled is True
    assert result.reason == (
        "PAPER startup reconciliation "
        "completed safely."
    )


def test_cash_mismatch_is_refused() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        account_summary=create_account_summary(
            available_to_trade=4_500.00
        ),
        positions=[],
    )

    service = PaperStartupReconciliationService(
        broker=broker,
        reconciler=create_reconciler(),
        portfolio=portfolio,
    )

    result = service.reconcile()

    assert result.approved is False
    assert result.report.is_reconciled is False
    assert result.reason == (
        "PAPER startup reconciliation failed."
    )

    categories = {
        issue.category
        for issue in result.report.issues
    }

    assert "CASH" in categories


def test_position_mismatch_is_refused() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    portfolio.positions = {
        "AAPL": 2,
    }

    broker = FakeBroker(
        account_summary=create_account_summary(
            available_to_trade=5_000.00
        ),
        positions=[
            BrokerPosition(
                ticker="AAPL_US_EQ",
                quantity=1.0,
                average_price_paid=150.0,
                current_price=150.0,
                profit_loss=0.0,
            )
        ],
    )

    service = PaperStartupReconciliationService(
        broker=broker,
        reconciler=create_reconciler(),
        portfolio=portfolio,
    )

    result = service.reconcile()

    assert result.approved is False
    assert result.report.is_reconciled is False

    categories = {
        issue.category
        for issue in result.report.issues
    }

    assert "POSITION" in categories


def test_unmapped_broker_position_is_refused() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeBroker(
        account_summary=create_account_summary(
            available_to_trade=5_000.00
        ),
        positions=[
            BrokerPosition(
                ticker="TSLA_US_EQ",
                quantity=1.0,
                average_price_paid=200.0,
                current_price=200.0,
                profit_loss=0.0,
            )
        ],
    )

    service = PaperStartupReconciliationService(
        broker=broker,
        reconciler=create_reconciler(),
        portfolio=portfolio,
    )

    result = service.reconcile()

    assert result.approved is False

    categories = {
        issue.category
        for issue in result.report.issues
    }

    assert "UNMAPPED_POSITION" in categories