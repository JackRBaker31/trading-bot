import pytest

from app.recovery_coordinator import (
    RecoveryCoordinatorReport,
)
from app.recovery_startup import (
    RecoveryStartupService,
)
from app.recovery_startup_gate import (
    RecoveryStartupDecision,
)
from app.startup_recovery import (
    StartupRecoveryReport,
)


class FakeRecoveryCoordinator:
    def __init__(
        self,
        report: RecoveryCoordinatorReport,
    ) -> None:
        self.report = report
        self.recover_calls = 0

    def recover(
        self,
    ) -> RecoveryCoordinatorReport:
        self.recover_calls += 1
        return self.report


class FakeRecoveryStartupGate:
    def __init__(
        self,
        decision: RecoveryStartupDecision,
    ) -> None:
        self.decision = decision
        self.evaluate_calls: list[
            RecoveryCoordinatorReport
        ] = []

    def evaluate(
        self,
        report: RecoveryCoordinatorReport,
    ) -> RecoveryStartupDecision:
        self.evaluate_calls.append(report)
        return self.decision


def create_report() -> RecoveryCoordinatorReport:
    return RecoveryCoordinatorReport(
        startup_report=StartupRecoveryReport(
            items=()
        ),
        plan=(),
        items=(),
        startup_blocked=False,
    )


def test_approved_recovery_starts_trading() -> None:
    report = create_report()

    coordinator = FakeRecoveryCoordinator(
        report=report
    )

    gate = FakeRecoveryStartupGate(
        decision=RecoveryStartupDecision(
            approved=True,
            reason=(
                "Startup recovery completed safely."
            ),
        )
    )

    trading_calls = 0

    def start_trading() -> None:
        nonlocal trading_calls
        trading_calls += 1

    service = RecoveryStartupService(
        recovery_coordinator=coordinator,
        recovery_gate=gate,
    )

    result = service.start(
        start_trading=start_trading
    )

    assert coordinator.recover_calls == 1
    assert gate.evaluate_calls == [report]
    assert trading_calls == 1
    assert result.trading_started is True
    assert result.decision.approved is True


def test_refused_recovery_does_not_start_trading() -> None:
    report = create_report()

    coordinator = FakeRecoveryCoordinator(
        report=report
    )

    gate = FakeRecoveryStartupGate(
        decision=RecoveryStartupDecision(
            approved=False,
            reason=(
                "Trading refused because startup "
                "recovery remains blocked."
            ),
        )
    )

    trading_calls = 0

    def start_trading() -> None:
        nonlocal trading_calls
        trading_calls += 1

    service = RecoveryStartupService(
        recovery_coordinator=coordinator,
        recovery_gate=gate,
    )

    result = service.start(
        start_trading=start_trading
    )

    assert trading_calls == 0
    assert result.trading_started is False
    assert result.decision.approved is False


def test_trading_exception_is_not_hidden() -> None:
    report = create_report()

    coordinator = FakeRecoveryCoordinator(
        report=report
    )

    gate = FakeRecoveryStartupGate(
        decision=RecoveryStartupDecision(
            approved=True,
            reason=(
                "Startup recovery completed safely."
            ),
        )
    )

    service = RecoveryStartupService(
        recovery_coordinator=coordinator,
        recovery_gate=gate,
    )

    def start_trading() -> None:
        raise RuntimeError(
            "Trading loop failed."
        )

    with pytest.raises(
        RuntimeError,
        match="Trading loop failed",
    ):
        service.start(
            start_trading=start_trading
        )


def test_recovery_runs_before_trading() -> None:
    report = create_report()
    call_order: list[str] = []

    class OrderedCoordinator:
        def recover(
            self,
        ) -> RecoveryCoordinatorReport:
            call_order.append("recovery")
            return report

    gate = FakeRecoveryStartupGate(
        decision=RecoveryStartupDecision(
            approved=True,
            reason=(
                "Startup recovery completed safely."
            ),
        )
    )

    def start_trading() -> None:
        call_order.append("trading")

    service = RecoveryStartupService(
        recovery_coordinator=(
            OrderedCoordinator()
        ),
        recovery_gate=gate,
    )

    service.start(
        start_trading=start_trading
    )

    assert call_order == [
        "recovery",
        "trading",
    ]

def test_approved_recovery_is_logged(
    caplog,
) -> None:
    report = create_report()

    coordinator = FakeRecoveryCoordinator(
        report=report
    )

    gate = FakeRecoveryStartupGate(
        decision=RecoveryStartupDecision(
            approved=True,
            reason=(
                "Startup recovery completed safely."
            ),
        )
    )

    service = RecoveryStartupService(
        recovery_coordinator=coordinator,
        recovery_gate=gate,
    )

    with caplog.at_level("INFO"):
        service.start(
            start_trading=lambda: None
        )

    messages = [
        record.getMessage()
        for record in caplog.records
    ]

    assert "startup_recovery_started" in messages

    assert any(
        message.startswith(
            "startup_recovery_report"
        )
        for message in messages
    )

    assert any(
        message.startswith(
            "startup_recovery_approved"
        )
        for message in messages
    )

    assert (
        "trading_started_after_recovery"
        in messages
    )

def test_refused_recovery_is_logged(
    caplog,
) -> None:
    report = create_report()

    coordinator = FakeRecoveryCoordinator(
        report=report
    )

    gate = FakeRecoveryStartupGate(
        decision=RecoveryStartupDecision(
            approved=False,
            reason=(
                "Trading refused because startup "
                "recovery remains blocked."
            ),
        )
    )

    service = RecoveryStartupService(
        recovery_coordinator=coordinator,
        recovery_gate=gate,
    )

    with caplog.at_level("INFO"):
        service.start(
            start_trading=lambda: None
        )

    messages = [
        record.getMessage()
        for record in caplog.records
    ]

    assert any(
        message.startswith(
            "startup_recovery_refused"
        )
        for message in messages
    )

    assert (
        "trading_started_after_recovery"
        not in messages
    )