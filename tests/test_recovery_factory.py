from pathlib import Path

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


class FakeBroker:
    def get_pending_order(
        self,
        order_id: int,
    ):
        raise AssertionError(
            "Broker must not be called while "
            "constructing recovery services."
        )

    def find_historical_order(
        self,
        order_id: int,
        max_pages: int = 5,
    ):
        raise AssertionError(
            "Broker must not be called while "
            "constructing recovery services."
        )


def test_factory_creates_recovery_startup_service(
    tmp_path: Path,
) -> None:
    journal = OrderJournal(
        path=tmp_path / "order_journal.jsonl"
    )

    portfolio_store = PortfolioStore(
        file_path=str(
            tmp_path / "portfolio.json"
        )
    )

    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    polling_service = OrderPollingService(
        broker=FakeBroker(),
        verification_service=(
            OrderVerificationService()
        ),
        max_attempts=1,
        poll_interval_seconds=0,
        sleep_function=lambda _: None,
    )

    service = create_recovery_startup_service(
        order_journal=journal,
        polling_service=polling_service,
        portfolio=portfolio,
        portfolio_store=portfolio_store,
    )

    assert isinstance(
        service,
        RecoveryStartupService,
    )

    coordinator = service.recovery_coordinator

    assert (
        coordinator
        .startup_recovery_service
        .order_journal
        is journal
    )

    assert (
        coordinator
        .startup_recovery_service
        .recovery_service
        .polling_service
        is polling_service
    )

    assert (
        coordinator
        .recovery_executor
        .order_journal
        is journal
    )

    fill_service = (
        coordinator.fill_recovery_service
    )

    assert (
        fill_service.order_journal
        is journal
    )

    assert (
        fill_service.applier.portfolio
        is portfolio
    )

    assert (
        fill_service.applier.portfolio_store
        is portfolio_store
    )

    assert (
        coordinator
        .active_order_recovery_service
        .order_journal
        is journal
    )