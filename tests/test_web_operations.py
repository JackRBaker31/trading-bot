from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.operations_query_service import (
    OrderPage,
    PortfolioView,
    PositionView,
    ReconciliationStatusView,
    RiskStatusView,
)
from app.order_journal import OrderJournalEntry
from app.run_history import (
    RunHistoryRecord,
    RunStatus,
    RunType,
)
from web.app import create_app
from tests.web_test_auth import (
    FakeAuthenticatedService,
    authenticated_client,
)


class FakeOperationsQueryService:
    def get_portfolio(self, *, request):
        del request
        return PortfolioView(
            available=True,
            starting_cash=10_000.0,
            cash=9_500.0,
            position_count=1,
            positions=(
                PositionView(
                    symbol="AAPL",
                    quantity=5,
                ),
            ),
            applied_broker_order_count=1,
        )

    def list_positions(self, *, request):
        del request
        return (
            PositionView(
                symbol="AAPL",
                quantity=5,
            ),
        )

    def list_orders(self, **kwargs):
        unresolved = kwargs.get(
            "unresolved_only",
            False,
        )
        return OrderPage(
            total_count=1,
            offset=kwargs.get("offset", 0),
            limit=kwargs.get("limit", 50),
            items=(
                OrderJournalEntry(
                    timestamp=(
                        "2026-07-19T12:00:00+00:00"
                    ),
                    reservation_key=(
                        "AAPL:BUY:1"
                    ),
                    event=(
                        "PENDING"
                        if unresolved
                        else "FILLED"
                    ),
                    symbol="AAPL",
                    side="BUY",
                    quantity=1,
                    broker_order_id=123,
                ),
            ),
        )

    def get_risk_status(self, *, request):
        del request
        return RiskStatusView(
            max_order_value=2_000.0,
            max_position_value=3_000.0,
            max_portfolio_exposure_ratio=0.5,
            max_portfolio_exposure_value=5_000.0,
            max_trades_per_session=3,
            approved_symbols=("AAPL",),
            paper_trading_enabled=True,
            broker_environment="DEMO",
            execution_permission_confirmed=True,
            real_money_trading_enabled=False,
        )

    def get_latest_reconciliation(
        self,
        *,
        request,
    ):
        del request
        return ReconciliationStatusView(
            available=True,
            latest_run=RunHistoryRecord(
                run_id="recon-1",
                run_type=RunType.RECONCILIATION,
                status=RunStatus.SUCCEEDED,
                started_at=datetime(
                    2026, 7, 19, 12, 0,
                    tzinfo=timezone.utc,
                ),
                finished_at=datetime(
                    2026, 7, 19, 12, 0, 1,
                    tzinfo=timezone.utc,
                ),
            ),
            unresolved_order_count=0,
            safe_to_start=True,
        )


def create_client() -> TestClient:
    return authenticated_client(
        create_app(
            authentication_service_factory=(
                lambda: FakeAuthenticatedService()
            ),
            operations_query_service_factory=(
                lambda: (
                    FakeOperationsQueryService()
                )
            )
        )
    )


def test_returns_portfolio() -> None:
    response = create_client().get(
        "/api/portfolio"
    )

    assert response.status_code == 200
    assert response.json()["cash"] == 9_500.0
    assert response.json()[
        "positions"
    ][0]["symbol"] == "AAPL"


def test_returns_positions() -> None:
    response = create_client().get(
        "/api/positions"
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_returns_orders() -> None:
    response = create_client().get(
        "/api/orders?limit=10"
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_returns_unresolved_orders() -> None:
    response = create_client().get(
        "/api/orders/unresolved"
    )

    assert response.status_code == 200
    assert response.json()[
        "items"
    ][0]["event"] == "PENDING"


def test_returns_risk_status() -> None:
    response = create_client().get(
        "/api/risk/status"
    )

    assert response.status_code == 200
    assert response.json()[
        "real_money_trading_enabled"
    ] is False


def test_returns_reconciliation_status() -> None:
    response = create_client().get(
        "/api/reconciliation/latest"
    )

    assert response.status_code == 200
    assert response.json()[
        "safe_to_start"
    ] is True
