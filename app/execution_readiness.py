from dataclasses import dataclass

from app.startup_summary import StartupOutcome


@dataclass(frozen=True)
class ExecutionReadinessResult:
    approved: bool
    reason: str


class ExecutionReadinessService:
    def evaluate(
        self,
        startup_outcome: StartupOutcome,
        paper_trading_enabled: bool,
        broker_environment: str,
        execution_permission_confirmed: bool,
    ) -> ExecutionReadinessResult:
        if startup_outcome != StartupOutcome.APPROVED:
            return ExecutionReadinessResult(
                approved=False,
                reason=(
                    "Execution readiness failed "
                    "because startup was not approved."
                ),
            )

        if not paper_trading_enabled:
            return ExecutionReadinessResult(
                approved=False,
                reason="Paper trading is disabled.",
            )

        cleaned_environment = (
            broker_environment.upper().strip()
        )

        if cleaned_environment != "DEMO":
            return ExecutionReadinessResult(
                approved=False,
                reason=(
                    "Execution readiness requires "
                    "the DEMO broker environment."
                ),
            )

        if not execution_permission_confirmed:
            return ExecutionReadinessResult(
                approved=False,
                reason=(
                    "Order-execution permission has "
                    "not been confirmed."
                ),
            )

        return ExecutionReadinessResult(
            approved=True,
            reason="Execution readiness passed.",
        )