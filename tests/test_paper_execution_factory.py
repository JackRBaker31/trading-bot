from pathlib import Path

from app.market_session import MarketSession
from app.order_journal import OrderJournal
from app.paper_execution_adapter import (
    PaperExecutionAdapter,
)
from app.paper_execution_factory import (
    create_paper_execution_adapter,
)
from app.portfolio import Portfolio
from app.risk import RiskEngine, RiskLimits
from app.trade_log import TradeLog
from app.trading212_client import Trading212Client


def test_factory_builds_demo_paper_execution_stack(
    tmp_path: Path,
) -> None:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    risk_engine = RiskEngine(
        limits=RiskLimits(
            max_order_value=1_000.00,
            max_position_value=2_000.00,
            max_portfolio_exposure=0.5,
            max_trades_per_session=3,
            approved_symbols={"AAPL"},
        )
    )

    trade_log = TradeLog()

    journal = OrderJournal(
        path=tmp_path / "order_journal.jsonl"
    )

    market_session = MarketSession(
        timezone_name="America/New_York",
        opening_time="09:30",
        closing_time="16:00",
        trading_weekdays={
            0,
            1,
            2,
            3,
            4,
        },
    )

    adapter = create_paper_execution_adapter(
        api_key="demo-key",
        api_secret="demo-secret",
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
        },
        portfolio=portfolio,
        risk_engine=risk_engine,
        trade_log=trade_log,
        order_journal=journal,
        paper_trading_enabled=True,
        broker_environment="DEMO",
        order_execution_permission_confirmed=False,
        market_session=market_session,
        enforce_market_hours=False,
        max_poll_attempts=3,
        poll_interval_seconds=0,
    )

    assert isinstance(
        adapter,
        PaperExecutionAdapter,
    )

    assert adapter.portfolio is portfolio
    assert adapter.risk_engine is risk_engine
    assert adapter.trade_log is trade_log

    workflow = adapter.workflow

    assert (
        workflow.order_journal
        is journal
    )

    broker = (
        workflow
        .execution_service
        .broker
    )

    assert isinstance(
        broker,
        Trading212Client,
    )

    assert broker.environment == "DEMO"
    assert broker.api_key == "demo-key"
    assert broker.api_secret == "demo-secret"

    assert (
        workflow
        .polling_service
        .max_attempts
        == 3
    )

    assert (
        workflow
        .polling_service
        .poll_interval_seconds
        == 0
    )

    assert (
        adapter
        .order_execution_permission_confirmed
        is False
    )