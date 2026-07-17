from app.broker import (
    BrokerOrderResult,
)
from app.historical_fill_importer import (
    HistoricalFillImporter,
)
from app.portfolio import (
    Portfolio,
)


class FakeHistoricalOrderBroker:
    def __init__(
        self,
        orders: list[BrokerOrderResult],
    ) -> None:
        self.orders = orders
        self.calls = 0

    def get_historical_orders(
        self,
    ) -> list[BrokerOrderResult]:
        self.calls += 1

        return list(
            self.orders
        )


class RecordingPortfolioStore:
    def __init__(
        self,
    ) -> None:
        self.saved_portfolios: list[
            Portfolio
        ] = []

    def save(
        self,
        portfolio: Portfolio,
    ) -> None:
        self.saved_portfolios.append(
            portfolio
        )


def test_imports_unapplied_filled_buy_order() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker_order = BrokerOrderResult(
        order_id=123456,
        ticker="AAPL_US_EQ",
        quantity=1.0,
        side="BUY",
        status="FILLED",
        order_type="MARKET",
        filled_quantity=1.0,
        filled_value=234.58,
        currency="GBP",
    )

    broker = FakeHistoricalOrderBroker(
        orders=[
            broker_order,
        ]
    )

    portfolio_store = RecordingPortfolioStore()

    importer = HistoricalFillImporter(
        broker=broker,
        portfolio=portfolio,
        portfolio_store=portfolio_store,
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
        },
    )

    result = importer.import_unapplied_fills()

    assert result.imported_order_ids == (
        123456,
    )
    assert result.skipped_order_ids == ()

    assert portfolio.cash == 4_765.42
    assert portfolio.positions == {
        "AAPL": 1,
    }
    assert portfolio.applied_broker_order_ids == {
        123456,
    }

    assert portfolio_store.saved_portfolios == [
        portfolio,
    ]
    assert broker.calls == 1
    
def test_skips_already_applied_order() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )
    portfolio.mark_broker_order_applied(
        123456
    )

    broker_order = BrokerOrderResult(
        order_id=123456,
        ticker="AAPL_US_EQ",
        quantity=1.0,
        side="BUY",
        status="FILLED",
        order_type="MARKET",
        filled_quantity=1.0,
        filled_value=234.58,
        currency="GBP",
    )

    broker = FakeHistoricalOrderBroker(
        orders=[broker_order]
    )
    portfolio_store = RecordingPortfolioStore()

    importer = HistoricalFillImporter(
        broker=broker,
        portfolio=portfolio,
        portfolio_store=portfolio_store,
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
        },
    )

    result = importer.import_unapplied_fills()

    assert result.imported_order_ids == ()
    assert result.skipped_order_ids == (
        123456,
    )
    assert portfolio.cash == 5_000.00
    assert portfolio.positions == {}
    assert portfolio_store.saved_portfolios == []


def test_skips_non_filled_order() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker_order = BrokerOrderResult(
        order_id=123456,
        ticker="AAPL_US_EQ",
        quantity=1.0,
        side="BUY",
        status="CANCELLED",
        order_type="MARKET",
        filled_quantity=0.0,
        filled_value=0.0,
        currency="GBP",
    )

    broker = FakeHistoricalOrderBroker(
        orders=[broker_order]
    )
    portfolio_store = RecordingPortfolioStore()

    importer = HistoricalFillImporter(
        broker=broker,
        portfolio=portfolio,
        portfolio_store=portfolio_store,
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
        },
    )

    result = importer.import_unapplied_fills()

    assert result.imported_order_ids == ()
    assert result.skipped_order_ids == (
        123456,
    )
    assert portfolio.cash == 5_000.00
    assert portfolio.positions == {}
    assert portfolio_store.saved_portfolios == []