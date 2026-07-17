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
        self._orders = orders

    def get_historical_orders(
        self,
    ) -> list[BrokerOrderResult]:
        return list(
            self._orders
        )


class RecordingPortfolioStore:
    def __init__(
        self,
    ) -> None:
        self.save_count = 0

    def save(
        self,
        portfolio: Portfolio,
    ) -> None:
        self.save_count += 1


class RecordingReconciliationService:
    def __init__(
        self,
        portfolio: Portfolio,
    ) -> None:
        self._portfolio = portfolio
        self.called = False

    def reconcile(
        self,
    ) -> None:
        self.called = True

        assert self._portfolio.cash == 4_765.42
        assert self._portfolio.positions == {
            "AAPL": 1,
        }
        assert (
            self._portfolio
            .applied_broker_order_ids
            == {
                123456,
            }
        )


def test_imports_historical_fill_before_reconciliation() -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    broker = FakeHistoricalOrderBroker(
        orders=[
            BrokerOrderResult(
                order_id=123456,
                ticker="AAPL_US_EQ",
                quantity=1.0,
                side="BUY",
                status="FILLED",
                order_type="MARKET",
                filled_quantity=1.0,
                filled_value=234.58,
                currency="GBP",
            ),
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

    reconciliation_service = (
        RecordingReconciliationService(
            portfolio=portfolio
        )
    )

    import_result = (
        importer.import_unapplied_fills()
    )

    reconciliation_service.reconcile()

    assert import_result.imported_order_ids == (
        123456,
    )
    assert import_result.skipped_order_ids == ()
    assert portfolio_store.save_count == 1
    assert reconciliation_service.called