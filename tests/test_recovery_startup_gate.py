from app.order_journal import OrderJournalEntry
from app.recovery_coordinator import (
    RecoveryCoordinatorItem,
    RecoveryCoordinatorReport,
)
from app.recovery_plan import (
    RecoveryAction,
    RecoveryPlanItem,
)
from app.recovery_startup_gate import (
    RecoveryStartupGate,
)
from app.startup_recovery import (
    StartupRecoveryItem,
    StartupRecoveryReport,
)


def create_recovery_item() -> StartupRecoveryItem:
    return StartupRecoveryItem(
        journal_entry=OrderJournalEntry(
            timestamp=(
                "2026-07-13T10:00:00+00:00"
            ),
            reservation_key="AAPL:BUY:2",
            event="PENDING",
            symbol="AAPL",
            side="BUY",
            quantity=2,
            broker_order_id=123456,
            reason="Startup gate test.",
        ),
        polling_result=None,
        error=None,
    )


def create_plan_item() -> RecoveryPlanItem:
    return RecoveryPlanItem(
        recovery_item=create_recovery_item(),
        action=RecoveryAction.RECORD_FAILURE,
        reason="Startup gate plan.",
    )


def create_report(
    *,
    completed: bool,
    startup_blocked: bool,
) -> RecoveryCoordinatorReport:
    plan_item = create_plan_item()

    startup_report = StartupRecoveryReport(
        items=(
            plan_item.recovery_item,
        )
    )

    coordinator_item = RecoveryCoordinatorItem(
        plan_item=plan_item,
        completed=completed,
        reason="Startup gate result.",
    )

    return RecoveryCoordinatorReport(
        startup_report=startup_report,
        plan=(plan_item,),
        items=(coordinator_item,),
        startup_blocked=startup_blocked,
    )


def test_completed_recovery_is_approved() -> None:
    gate = RecoveryStartupGate()

    decision = gate.evaluate(
        report=create_report(
            completed=True,
            startup_blocked=False,
        )
    )

    assert decision.approved is True
    assert decision.reason == (
        "Startup recovery completed safely."
    )


def test_blocked_recovery_is_refused() -> None:
    gate = RecoveryStartupGate()

    decision = gate.evaluate(
        report=create_report(
            completed=False,
            startup_blocked=True,
        )
    )

    assert decision.approved is False
    assert "remains blocked" in decision.reason


def test_incomplete_recovery_is_refused() -> None:
    gate = RecoveryStartupGate()

    decision = gate.evaluate(
        report=create_report(
            completed=False,
            startup_blocked=False,
        )
    )

    assert decision.approved is False
    assert "incomplete" in decision.reason


def test_empty_recovery_is_approved() -> None:
    report = RecoveryCoordinatorReport(
        startup_report=StartupRecoveryReport(
            items=()
        ),
        plan=(),
        items=(),
        startup_blocked=False,
    )

    gate = RecoveryStartupGate()

    decision = gate.evaluate(
        report=report
    )

    assert decision.approved is True