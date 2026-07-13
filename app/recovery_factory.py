from app.active_order_recovery import (
    ActiveOrderRecoveryService,
)
from app.order_journal import OrderJournal
from app.order_polling import OrderPollingService
from app.order_recovery import OrderRecoveryService
from app.portfolio import Portfolio
from app.portfolio_store import PortfolioStore
from app.recovered_fill import (
    RecoveredFillValidator,
)
from app.recovered_fill_applier import (
    RecoveredFillApplier,
)
from app.recovered_fill_recovery import (
    RecoveredFillRecoveryService,
)
from app.recovery_coordinator import (
    RecoveryCoordinator,
)
from app.recovery_executor import RecoveryExecutor
from app.recovery_plan import RecoveryPlanner
from app.recovery_startup import (
    RecoveryStartupService,
)
from app.recovery_startup_gate import (
    RecoveryStartupGate,
)
from app.startup_recovery import (
    StartupRecoveryService,
)


def create_recovery_startup_service(
    *,
    order_journal: OrderJournal,
    polling_service: OrderPollingService,
    portfolio: Portfolio,
    portfolio_store: PortfolioStore,
    quantity_tolerance: float = 0.000001,
) -> RecoveryStartupService:
    order_recovery_service = OrderRecoveryService(
        polling_service=polling_service
    )

    startup_recovery_service = (
        StartupRecoveryService(
            order_journal=order_journal,
            recovery_service=(
                order_recovery_service
            ),
        )
    )

    recovery_planner = RecoveryPlanner()

    recovery_executor = RecoveryExecutor(
        order_journal=order_journal
    )

    recovered_fill_validator = (
        RecoveredFillValidator(
            quantity_tolerance=(
                quantity_tolerance
            )
        )
    )

    recovered_fill_applier = (
        RecoveredFillApplier(
            portfolio=portfolio,
            portfolio_store=portfolio_store,
        )
    )

    recovered_fill_recovery_service = (
        RecoveredFillRecoveryService(
            validator=(
                recovered_fill_validator
            ),
            applier=recovered_fill_applier,
            order_journal=order_journal,
        )
    )

    active_order_recovery_service = (
        ActiveOrderRecoveryService(
            order_journal=order_journal
        )
    )

    recovery_coordinator = RecoveryCoordinator(
        startup_recovery_service=(
            startup_recovery_service
        ),
        recovery_planner=recovery_planner,
        recovery_executor=recovery_executor,
        fill_recovery_service=(
            recovered_fill_recovery_service
        ),
        active_order_recovery_service=(
            active_order_recovery_service
        ),
    )

    return RecoveryStartupService(
        recovery_coordinator=(
            recovery_coordinator
        ),
        recovery_gate=RecoveryStartupGate(),
    )