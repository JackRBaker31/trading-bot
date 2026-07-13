from app.paper_application_startup import (
    PaperApplicationStartupService,
)
from app.paper_startup_reconciliation import (
    PaperStartupReconciliationResult,
)
from app.reconciliation import ReconciliationReport
from app.recovery_coordinator import (
    RecoveryCoordinatorReport,
)
from app.recovery_startup import (
    RecoveryStartupResult,
)
from app.recovery_startup_gate import (
    RecoveryStartupDecision,
)
from app.startup_recovery import (
    StartupRecoveryReport,
)


def create_recovery_report() -> (
    RecoveryCoordinatorReport
):
    return RecoveryCoordinatorReport(
        startup_report=StartupRecoveryReport(
            items=()
        ),
        plan=(),
        items=(),
        startup_blocked=False,
    )


def create_recovery_result(
    approved: bool,
) -> RecoveryStartupResult:
    return RecoveryStartupResult(
        recovery_report=create_recovery_report(),
        decision=RecoveryStartupDecision(
            approved=approved,
            reason=(
                "Recovery approved."
                if approved
                else "Recovery refused."
            ),
        ),
        trading_started=approved,
    )


def create_reconciliation_result(
    approved: bool,
) -> PaperStartupReconciliationResult:
    return PaperStartupReconciliationResult(
        report=ReconciliationReport(
            is_reconciled=approved,
            local_cash=5_000.00,
            broker_cash=5_000.00,
            local_positions={},
            broker_positions={},
            issues=[],
        ),
        approved=approved,
        reason=(
            "PAPER startup reconciliation "
            "completed safely."
            if approved
            else
            "PAPER startup reconciliation failed."
        ),
    )


class FakeRecoveryStartupService:
    def __init__(
        self,
        approved: bool,
    ) -> None:
        self.approved = approved
        self.start_calls = 0

    def start(
        self,
        start_trading,
    ) -> RecoveryStartupResult:
        self.start_calls += 1

        if self.approved:
            start_trading()

        return create_recovery_result(
            approved=self.approved
        )


class FakeReconciliationService:
    def __init__(
        self,
        approved: bool,
    ) -> None:
        self.approved = approved
        self.calls = 0

    def reconcile(
        self,
    ) -> PaperStartupReconciliationResult:
        self.calls += 1

        return create_reconciliation_result(
            approved=self.approved
        )


def test_recovery_and_reconciliation_start_trading() -> None:
    recovery_service = FakeRecoveryStartupService(
        approved=True
    )
    reconciliation_service = (
        FakeReconciliationService(
            approved=True
        )
    )

    trading_calls = 0

    def start_trading() -> None:
        nonlocal trading_calls
        trading_calls += 1

    service = PaperApplicationStartupService(
        recovery_startup_service=(
            recovery_service
        ),
        reconciliation_service=(
            reconciliation_service
        ),
    )

    result = service.start(
        start_trading=start_trading
    )

    assert recovery_service.start_calls == 1
    assert reconciliation_service.calls == 1
    assert trading_calls == 1
    assert result.trading_started is True


def test_failed_recovery_skips_reconciliation() -> None:
    recovery_service = FakeRecoveryStartupService(
        approved=False
    )
    reconciliation_service = (
        FakeReconciliationService(
            approved=True
        )
    )

    trading_calls = 0

    def start_trading() -> None:
        nonlocal trading_calls
        trading_calls += 1

    service = PaperApplicationStartupService(
        recovery_startup_service=(
            recovery_service
        ),
        reconciliation_service=(
            reconciliation_service
        ),
    )

    result = service.start(
        start_trading=start_trading
    )

    assert reconciliation_service.calls == 0
    assert trading_calls == 0
    assert result.trading_started is False
    assert result.reconciliation_result is None


def test_failed_reconciliation_blocks_trading() -> None:
    recovery_service = FakeRecoveryStartupService(
        approved=True
    )
    reconciliation_service = (
        FakeReconciliationService(
            approved=False
        )
    )

    trading_calls = 0

    def start_trading() -> None:
        nonlocal trading_calls
        trading_calls += 1

    service = PaperApplicationStartupService(
        recovery_startup_service=(
            recovery_service
        ),
        reconciliation_service=(
            reconciliation_service
        ),
    )

    result = service.start(
        start_trading=start_trading
    )

    assert reconciliation_service.calls == 1
    assert trading_calls == 0
    assert result.trading_started is False
    assert (
        result.reconciliation_result
        is not None
    )
    assert (
        result.reconciliation_result.approved
        is False
    )