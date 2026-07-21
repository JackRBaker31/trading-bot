from datetime import datetime, timezone

import pytest

from app.application_errors import DataStoreError
from app.config import (
    AppConfig,
    MarketSessionConfig,
    PaperTradingConfig,
    RiskConfig,
    StrategyConfig,
    TradingLoopConfig,
)
from app.operations_query_service import (
    OperationsQueryRequest,
    OperationsQueryService,
)
from app.order_journal import OrderJournal
from app.orders import Order, OrderSide
from app.portfolio import Portfolio
from app.portfolio_store import PortfolioStore
from app.run_history import (
    RunHistoryRecord,
    RunStatus,
    RunType,
)
from app.run_history_repository import (
    RunHistoryRepository,
)


def create_config(_: str) -> AppConfig:
    return AppConfig(
        mode="PAPER",
        market_data_provider="TWELVE_DATA",
        starting_cash=10_000.0,
        symbols=["AAPL", "MSFT"],
        risk=RiskConfig(
            max_order_value=2_000.0,
            max_position_value=3_000.0,
            max_portfolio_exposure=0.5,
            max_trades_per_session=3,
        ),
        strategy=StrategyConfig(
            drop_threshold_percent=3.0,
            target_allocation_percent=20.0,
            cooldown_cycles=0,
        ),
        trading_loop=TradingLoopConfig(
            cycles=5,
            interval_seconds=1.0,
        ),
        market_session=MarketSessionConfig(
            enforce_market_hours=True,
            timezone="America/New_York",
            opening_time="09:30",
            closing_time="16:00",
            trading_weekdays=[0, 1, 2, 3, 4],
        ),
        paper_trading=PaperTradingConfig(
            enabled=True,
            broker_environment="DEMO",
            order_execution_permission_confirmed=True,
        ),
    )


def test_returns_missing_portfolio() -> None:
    service = OperationsQueryService(
        config_loader=create_config
    )

    result = service.get_portfolio(
        request=OperationsQueryRequest(
            portfolio_path="missing.json"
        )
    )

    assert result.available is False
    assert result.positions == ()


def test_returns_portfolio_and_positions(
    tmp_path,
) -> None:
    path = tmp_path / "portfolio.json"
    portfolio = Portfolio(
        starting_cash=10_000.0
    )
    portfolio.buy(
        symbol="MSFT",
        quantity=2,
        price=100.0,
    )
    portfolio.buy(
        symbol="AAPL",
        quantity=3,
        price=100.0,
    )
    portfolio.mark_broker_order_applied(10)
    PortfolioStore(file_path=str(path)).save(
        portfolio
    )

    result = OperationsQueryService(
        config_loader=create_config
    ).get_portfolio(
        request=OperationsQueryRequest(
            portfolio_path=str(path)
        )
    )

    assert result.available is True
    assert result.cash == 9_500.0
    assert [
        position.symbol
        for position in result.positions
    ] == ["AAPL", "MSFT"]
    assert result.applied_broker_order_count == 1


def test_lists_latest_unresolved_orders(
    tmp_path,
) -> None:
    path = tmp_path / "orders.jsonl"
    journal = OrderJournal(
        path=path,
        clock=lambda: datetime(
            2026, 7, 19, 12, 0,
            tzinfo=timezone.utc,
        ),
    )
    order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        price=100.0,
    )
    journal.record(order, "RESERVED")
    journal.record(order, "PENDING", 123)

    result = OperationsQueryService(
        config_loader=create_config
    ).list_orders(
        request=OperationsQueryRequest(
            order_journal_path=str(path)
        ),
        unresolved_only=True,
    )

    assert result.total_count == 1
    assert result.items[0].event == "PENDING"
    assert result.items[0].broker_order_id == 123


def test_returns_risk_status() -> None:
    result = OperationsQueryService(
        config_loader=create_config
    ).get_risk_status()

    assert result.max_order_value == 2_000.0
    assert (
        result.max_portfolio_exposure_value
        == 5_000.0
    )
    assert result.real_money_trading_enabled is False


def test_returns_latest_reconciliation(
    tmp_path,
) -> None:
    database = tmp_path / "application.db"
    repository = RunHistoryRepository(
        database_path=str(database)
    )
    repository.initialize()
    repository.add(
        record=RunHistoryRecord(
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
        )
    )

    result = OperationsQueryService(
        config_loader=create_config
    ).get_latest_reconciliation(
        request=OperationsQueryRequest(
            application_database_path=str(
                database
            ),
            order_journal_path=str(
                tmp_path / "missing.jsonl"
            ),
        )
    )

    assert result.available is True
    assert result.latest_run is not None
    assert result.latest_run.run_id == "recon-1"
    assert result.safe_to_start is True


def test_corrupt_portfolio_is_safe_error(
    tmp_path,
) -> None:
    path = tmp_path / "portfolio.json"
    path.write_text("not-json", encoding="utf-8")

    with pytest.raises(
        DataStoreError,
    ) as captured:
        OperationsQueryService(
            config_loader=create_config
        ).get_portfolio(
            request=OperationsQueryRequest(
                portfolio_path=str(path)
            )
        )

    assert captured.value.code == (
        "OPERATIONS_PORTFOLIO_FAILED"
    )
