from app.duplicate_order_guard import (
    DuplicateOrderGuard,
)
from app.market_session import MarketSession
from app.order_journal import OrderJournal
from app.order_polling import OrderPollingService
from app.order_verification import (
    OrderVerificationService,
)
from app.paper_execution_adapter import (
    PaperExecutionAdapter,
)
from app.paper_order_execution import (
    PaperOrderExecutionService,
)
from app.paper_order_workflow import (
    PaperOrderWorkflow,
)
from app.paper_trading_gate import (
    PaperTradingGate,
)
from app.portfolio import Portfolio
from app.risk import RiskEngine
from app.trade_log import TradeLog
from app.trading212_client import Trading212Client


def create_paper_execution_adapter(
    *,
    api_key: str,
    api_secret: str,
    symbol_mapping: dict[str, str],
    portfolio: Portfolio,
    risk_engine: RiskEngine,
    trade_log: TradeLog,
    order_journal: OrderJournal,
    paper_trading_enabled: bool,
    broker_environment: str,
    order_execution_permission_confirmed: bool,
    market_session: MarketSession | None = None,
    enforce_market_hours: bool = False,
    max_poll_attempts: int = 5,
    poll_interval_seconds: float = 1.0,
    quantity_tolerance: float = 0.000001,
) -> PaperExecutionAdapter:
    broker = Trading212Client(
        api_key=api_key,
        api_secret=api_secret,
        environment=broker_environment,
    )

    verification_service = (
        OrderVerificationService()
    )

    execution_service = (
        PaperOrderExecutionService(
            broker=broker,
            symbol_mapping=symbol_mapping,
        )
    )

    polling_service = OrderPollingService(
        broker=broker,
        verification_service=verification_service,
        max_attempts=max_poll_attempts,
        poll_interval_seconds=(
            poll_interval_seconds
        ),
    )

    workflow = PaperOrderWorkflow(
        execution_service=execution_service,
        polling_service=polling_service,
        verification_service=verification_service,
        duplicate_order_guard=(
            DuplicateOrderGuard()
        ),
        order_journal=order_journal,
        portfolio=portfolio,
        quantity_tolerance=quantity_tolerance,
    )

    return PaperExecutionAdapter(
        workflow=workflow,
        gate=PaperTradingGate(),
        portfolio=portfolio,
        risk_engine=risk_engine,
        trade_log=trade_log,
        paper_trading_enabled=(
            paper_trading_enabled
        ),
        broker_environment=broker_environment,
        order_execution_permission_confirmed=(
            order_execution_permission_confirmed
        ),
        market_session=market_session,
        enforce_market_hours=(
            enforce_market_hours
        ),
    )