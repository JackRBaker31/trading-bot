from pathlib import Path

from app.demo_recovery_factory import (
    create_demo_recovery_startup_service,
)
from app.order_journal import OrderJournal
from app.portfolio import Portfolio
from app.portfolio_store import PortfolioStore
from app.recovery_startup import (
    RecoveryStartupService,
)
from app.trading212_client import Trading212Client


def test_demo_factory_builds_recovery_stack(
    tmp_path: Path,
) -> None:
    journal = OrderJournal(
        path=tmp_path / "order_journal.jsonl"
    )

    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    portfolio_store = PortfolioStore(
        file_path=str(
            tmp_path / "portfolio.json"
        )
    )

    service = (
        create_demo_recovery_startup_service(
            api_key="demo-key",
            api_secret="demo-secret",
            order_journal=journal,
            portfolio=portfolio,
            portfolio_store=portfolio_store,
            max_poll_attempts=3,
            poll_interval_seconds=0,
        )
    )

    assert isinstance(
        service,
        RecoveryStartupService,
    )

    recovery_service = (
        service
        .recovery_coordinator
        .startup_recovery_service
        .recovery_service
    )

    polling_service = (
        recovery_service.polling_service
    )

    assert isinstance(
        polling_service.broker,
        Trading212Client,
    )

    assert (
        polling_service.broker.environment
        == "DEMO"
    )
    assert polling_service.broker.api_key == (
        "demo-key"
    )
    assert polling_service.broker.api_secret == (
        "demo-secret"
    )
    assert polling_service.max_attempts == 3
    assert (
        polling_service.poll_interval_seconds
        == 0
    )

    assert (
        service
        .recovery_coordinator
        .startup_recovery_service
        .order_journal
        is journal
    )