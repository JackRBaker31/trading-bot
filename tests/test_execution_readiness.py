from app.execution_readiness import (
    ExecutionReadinessResult,
    ExecutionReadinessService,
)
from app.startup_summary import StartupOutcome


def test_execution_readiness_result_can_be_created() -> None:
    result = ExecutionReadinessResult(
        approved=True,
        reason="Execution readiness passed.",
    )

    assert result.approved is True
    assert result.reason == (
        "Execution readiness passed."
    )


def test_readiness_approves_safe_configuration() -> None:
    result = ExecutionReadinessService().evaluate(
        startup_outcome=StartupOutcome.APPROVED,
        paper_trading_enabled=True,
        broker_environment="DEMO",
        execution_permission_confirmed=True,
    )

    assert result.approved is True
    assert result.reason == (
        "Execution readiness passed."
    )


def test_readiness_blocks_unapproved_startup() -> None:
    result = ExecutionReadinessService().evaluate(
        startup_outcome=(
            StartupOutcome.BLOCKED_BY_DISCOVERY
        ),
        paper_trading_enabled=True,
        broker_environment="DEMO",
        execution_permission_confirmed=True,
    )

    assert result.approved is False
    assert result.reason == (
        "Execution readiness failed "
        "because startup was not approved."
    )


def test_readiness_blocks_disabled_paper_trading() -> None:
    result = ExecutionReadinessService().evaluate(
        startup_outcome=StartupOutcome.APPROVED,
        paper_trading_enabled=False,
        broker_environment="DEMO",
        execution_permission_confirmed=True,
    )

    assert result.approved is False
    assert result.reason == (
        "Paper trading is disabled."
    )


def test_readiness_blocks_non_demo_environment() -> None:
    result = ExecutionReadinessService().evaluate(
        startup_outcome=StartupOutcome.APPROVED,
        paper_trading_enabled=True,
        broker_environment="LIVE",
        execution_permission_confirmed=True,
    )

    assert result.approved is False
    assert "DEMO" in result.reason


def test_readiness_cleans_environment_value() -> None:
    result = ExecutionReadinessService().evaluate(
        startup_outcome=StartupOutcome.APPROVED,
        paper_trading_enabled=True,
        broker_environment=" demo ",
        execution_permission_confirmed=True,
    )

    assert result.approved is True


def test_readiness_blocks_unconfirmed_permission() -> None:
    result = ExecutionReadinessService().evaluate(
        startup_outcome=StartupOutcome.APPROVED,
        paper_trading_enabled=True,
        broker_environment="DEMO",
        execution_permission_confirmed=False,
    )

    assert result.approved is False
    assert result.reason == (
        "Order-execution permission has "
        "not been confirmed."
    )