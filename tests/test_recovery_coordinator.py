import pytest

from app.order_journal import OrderJournalEntry
from app.recovery_coordinator import (
    RecoveryCoordinator,
)
from app.recovery_executor import (
    RecoveryExecutionResult,
)
from app.recovery_plan import (
    RecoveryAction,
    RecoveryPlanItem,
)
from app.startup_recovery import (
    StartupRecoveryItem,
    StartupRecoveryReport,
)


class FakeStartupRecoveryService:
    def __init__(
        self,
        report: StartupRecoveryReport,
    ) -> None:
        self.report = report
        self.calls = 0

    def recover_unfinished_orders(
        self,
    ) -> StartupRecoveryReport:
        self.calls += 1
        return self.report


class FakeRecoveryPlanner:
    def __init__(
        self,
        plan: tuple[RecoveryPlanItem, ...],
    ) -> None:
        self.plan = plan
        self.create_plan_calls: list[
            tuple[StartupRecoveryItem, ...]
        ] = []

    def create_plan(
        self,
        recovery_items: tuple[
            StartupRecoveryItem,
            ...
        ],
    ) -> tuple[RecoveryPlanItem, ...]:
        self.create_plan_calls.append(
            recovery_items
        )
        return self.plan


class FakeRecoveryExecutor:
    def __init__(self) -> None:
        self.execute_calls: list[
            RecoveryPlanItem
        ] = []

    def execute(
        self,
        plan_item: RecoveryPlanItem,
    ) -> RecoveryExecutionResult:
        self.execute_calls.append(plan_item)

        return RecoveryExecutionResult(
            plan_item=plan_item,
            completed=True,
            reason=(
                "Recovered failure was recorded."
            ),
        )


class FakeFillRecoveryResult:
    def __init__(
        self,
        completed: bool = True,
        reason: str = (
            "Recovered fill was finalized."
        ),
    ) -> None:
        self.completed = completed
        self.reason = reason


class FakeFillRecoveryService:
    def __init__(self) -> None:
        self.recover_calls: list[
            RecoveryPlanItem
        ] = []

    def recover(
        self,
        plan_item: RecoveryPlanItem,
    ) -> FakeFillRecoveryResult:
        self.recover_calls.append(plan_item)
        return FakeFillRecoveryResult()


def create_journal_entry() -> OrderJournalEntry:
    return OrderJournalEntry(
        timestamp="2026-07-13T10:00:00+00:00",
        reservation_key="AAPL:BUY:2",
        event="PENDING",
        symbol="AAPL",
        side="BUY",
        quantity=2,
        broker_order_id=123456,
        reason="Recovery coordinator test.",
    )


def create_recovery_item() -> StartupRecoveryItem:
    return StartupRecoveryItem(
        journal_entry=create_journal_entry(),
        polling_result=None,
        error=None,
    )


def create_plan_item(
    action: RecoveryAction,
) -> RecoveryPlanItem:
    return RecoveryPlanItem(
        recovery_item=create_recovery_item(),
        action=action,
        reason="Recovery coordinator plan.",
    )


def create_coordinator(
    plan: tuple[RecoveryPlanItem, ...],
) -> tuple[
    RecoveryCoordinator,
    FakeStartupRecoveryService,
    FakeRecoveryPlanner,
    FakeRecoveryExecutor,
    FakeFillRecoveryService,
]:
    recovery_items = tuple(
        plan_item.recovery_item
        for plan_item in plan
    )

    startup_report = StartupRecoveryReport(
        items=recovery_items
    )

    startup_service = (
        FakeStartupRecoveryService(
            report=startup_report
        )
    )

    planner = FakeRecoveryPlanner(
        plan=plan
    )

    executor = FakeRecoveryExecutor()
    fill_service = FakeFillRecoveryService()

    coordinator = RecoveryCoordinator(
        startup_recovery_service=(
            startup_service
        ),
        recovery_planner=planner,
        recovery_executor=executor,
        fill_recovery_service=fill_service,
    )

    return (
        coordinator,
        startup_service,
        planner,
        executor,
        fill_service,
    )


def test_record_failure_is_executed() -> None:
    plan_item = create_plan_item(
        action=RecoveryAction.RECORD_FAILURE
    )

    (
        coordinator,
        startup_service,
        planner,
        executor,
        fill_service,
    ) = create_coordinator(
        plan=(plan_item,)
    )

    report = coordinator.recover()

    assert startup_service.calls == 1
    assert planner.create_plan_calls == [
        (plan_item.recovery_item,)
    ]
    assert executor.execute_calls == [
        plan_item
    ]
    assert fill_service.recover_calls == []

    assert report.completed_items == 1
    assert report.incomplete_items == 0
    assert report.startup_blocked is False


def test_update_portfolio_is_executed() -> None:
    plan_item = create_plan_item(
        action=RecoveryAction.UPDATE_PORTFOLIO
    )

    (
        coordinator,
        _,
        _,
        executor,
        fill_service,
    ) = create_coordinator(
        plan=(plan_item,)
    )

    report = coordinator.recover()

    assert executor.execute_calls == []
    assert fill_service.recover_calls == [
        plan_item
    ]
    assert report.completed_items == 1
    assert report.startup_blocked is False


@pytest.mark.parametrize(
    "action",
    [
        (
            RecoveryAction
            .REQUIRE_MANUAL_INTERVENTION
        ),
        RecoveryAction.ABORT_STARTUP,
    ],
)
def test_blocking_action_blocks_startup(
    action: RecoveryAction,
) -> None:
    plan_item = create_plan_item(
        action=action
    )

    (
        coordinator,
        _,
        _,
        executor,
        fill_service,
    ) = create_coordinator(
        plan=(plan_item,)
    )

    report = coordinator.recover()

    assert executor.execute_calls == []
    assert fill_service.recover_calls == []
    assert report.completed_items == 0
    assert report.incomplete_items == 1
    assert report.startup_blocked is True


def test_resume_polling_is_not_implemented() -> None:
    plan_item = create_plan_item(
        action=RecoveryAction.RESUME_POLLING
    )

    (
        coordinator,
        _,
        _,
        _,
        _,
    ) = create_coordinator(
        plan=(plan_item,)
    )

    with pytest.raises(
        NotImplementedError,
        match="Resume-polling",
    ):
        coordinator.recover()


def test_empty_recovery_returns_empty_report() -> None:
    (
        coordinator,
        startup_service,
        planner,
        executor,
        fill_service,
    ) = create_coordinator(
        plan=()
    )

    report = coordinator.recover()

    assert startup_service.calls == 1
    assert planner.create_plan_calls == [
        ()
    ]
    assert executor.execute_calls == []
    assert fill_service.recover_calls == []
    assert report.items == ()
    assert report.completed_items == 0
    assert report.incomplete_items == 0
    assert report.startup_blocked is False