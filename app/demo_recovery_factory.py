from app.order_journal import OrderJournal
from app.order_polling import OrderPollingService
from app.order_verification import (
    OrderVerificationService,
)
from app.portfolio import Portfolio
from app.portfolio_store import PortfolioStore
from app.recovery_factory import (
    create_recovery_startup_service,
)
from app.recovery_startup import (
    RecoveryStartupService,
)
from app.trading212_client import Trading212Client


def create_demo_recovery_startup_service(
    *,
    api_key: str,
    api_secret: str,
    order_journal: OrderJournal,
    portfolio: Portfolio,
    portfolio_store: PortfolioStore,
    max_poll_attempts: int = 5,
    poll_interval_seconds: float = 1.0,
    quantity_tolerance: float = 0.000001,
) -> RecoveryStartupService:
    broker = Trading212Client(
        api_key=api_key,
        api_secret=api_secret,
        environment="DEMO",
    )

    verification_service = (
        OrderVerificationService()
    )

    polling_service = OrderPollingService(
        broker=broker,
        verification_service=verification_service,
        max_attempts=max_poll_attempts,
        poll_interval_seconds=(
            poll_interval_seconds
        ),
    )

    return create_recovery_startup_service(
        order_journal=order_journal,
        polling_service=polling_service,
        portfolio=portfolio,
        portfolio_store=portfolio_store,
        quantity_tolerance=quantity_tolerance,
    )