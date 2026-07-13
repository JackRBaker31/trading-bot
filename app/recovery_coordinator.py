from dataclasses import dataclass

from app.recovered_fill_recovery import (
    RecoveredFillRecoveryResult,
    RecoveredFillRecoveryService,
)
from app.recovery_executor import (
    RecoveryExecutionResult,
    RecoveryExecutor,
)
from app.recovery_plan import (
    RecoveryAction,
    RecoveryPlanItem,
    RecoveryPlanner,
)
from app.startup_recovery import (
    StartupRecoveryReport,
    StartupRecoveryService,
)


@dataclass(frozen=True)
class RecoveryCoordinatorItem:
    plan_item: RecoveryPlanItem
    completed: bool
    reason: str
    execution_result: (
        RecoveryExecutionResult | None
    ) = None
    fill_recovery_result: (
        RecoveredFillRecoveryResult | None
    ) = None


@dataclass(frozen=True)
class RecoveryCoordinatorReport:
    startup_report: StartupRecoveryReport
    plan: tuple[RecoveryPlanItem, ...]
    items: tuple[RecoveryCoordinatorItem, ...]
    startup_blocked: bool

    @property
    def completed_items(self) -> int:
        return sum(
            item.completed
            for item in self.items
        )

    @property
    def incomplete_items(self) -> int:
        return (
            len(self.items)
            - self.completed_items
        )


class RecoveryCoordinator:
    def __init__(
        self,
        startup_recovery_service: (
            StartupRecoveryService
        ),
        recovery_planner: RecoveryPlanner,
        recovery_executor: RecoveryExecutor,
        fill_recovery_service: (
            RecoveredFillRecoveryService
        ),
    ) -> None:
        self.startup_recovery_service = (
            startup_recovery_service
        )
        self.recovery_planner = recovery_planner
        self.recovery_executor = recovery_executor
        self.fill_recovery_service = (
            fill_recovery_service
        )

    def recover(self) -> RecoveryCoordinatorReport:
        startup_report = (
            self.startup_recovery_service
            .recover_unfinished_orders()
        )

        plan = self.recovery_planner.create_plan(
            recovery_items=startup_report.items
        )

        items: list[RecoveryCoordinatorItem] = []
        startup_blocked = False

        for plan_item in plan:
            if (
                plan_item.action
                == RecoveryAction.RECORD_FAILURE
            ):
                execution_result = (
                    self.recovery_executor.execute(
                        plan_item=plan_item
                    )
                )

                items.append(
                    RecoveryCoordinatorItem(
                        plan_item=plan_item,
                        completed=(
                            execution_result.completed
                        ),
                        reason=execution_result.reason,
                        execution_result=(
                            execution_result
                        ),
                    )
                )
                continue

            if (
                plan_item.action
                == RecoveryAction.UPDATE_PORTFOLIO
            ):
                fill_recovery_result = (
                    self.fill_recovery_service
                    .recover(
                        plan_item=plan_item
                    )
                )

                items.append(
                    RecoveryCoordinatorItem(
                        plan_item=plan_item,
                        completed=(
                            fill_recovery_result
                            .completed
                        ),
                        reason=(
                            fill_recovery_result.reason
                        ),
                        fill_recovery_result=(
                            fill_recovery_result
                        ),
                    )
                )
                continue

            if (
                plan_item.action
                == RecoveryAction
                .REQUIRE_MANUAL_INTERVENTION
            ):
                startup_blocked = True

                items.append(
                    RecoveryCoordinatorItem(
                        plan_item=plan_item,
                        completed=False,
                        reason=plan_item.reason,
                    )
                )
                continue

            if (
                plan_item.action
                == RecoveryAction.ABORT_STARTUP
            ):
                startup_blocked = True

                items.append(
                    RecoveryCoordinatorItem(
                        plan_item=plan_item,
                        completed=False,
                        reason=plan_item.reason,
                    )
                )
                continue

            if (
                plan_item.action
                == RecoveryAction.RESUME_POLLING
            ):
                raise NotImplementedError(
                    "Resume-polling recovery is not "
                    "implemented."
                )

            raise ValueError(
                "Unknown recovery action."
            )

        return RecoveryCoordinatorReport(
            startup_report=startup_report,
            plan=plan,
            items=tuple(items),
            startup_blocked=startup_blocked,
        )