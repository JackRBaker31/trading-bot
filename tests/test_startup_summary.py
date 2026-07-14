from app.startup_summary import StartupSummaryBuilder
from app.startup_order_discovery import (
    StartupOrderDiscoveryResult,
)
from app.startup_summary import (
    StartupOutcome,
    StartupSummaryBuilder,
)

def test_summary_includes_order_discovery_counts() -> None:
    discovery_result = StartupOrderDiscoveryResult(
        approved=True,
        known_order_ids=(123456,),
        unknown_order_ids=(),
        reason=(
            "PAPER startup order discovery "
            "completed safely."
        ),
    )

    builder = StartupSummaryBuilder()

    from app.paper_application_startup import (
        PaperApplicationStartupResult,
    )

    summary = builder.build(
        startup_result=PaperApplicationStartupResult(
            recovery_result=None,          # temporary for this test
            discovery_result=discovery_result,
            reconciliation_result=None,
            trading_started=True,
            reason="OK",
        ),
    )

    assert (
    summary.discovery.known_order_count
    == 1
    )
    assert (
        summary.discovery.unknown_order_count
        == 0
    )
    assert summary.discovery.approved is True
    assert summary.discovery.reason == (
            "PAPER startup order discovery "
            "completed safely."
    )
    assert summary.startup_approved is True
    assert summary.outcome == StartupOutcome.APPROVED

def test_summary_classifies_discovery_block() -> None:
    discovery_result = StartupOrderDiscoveryResult(
        approved=False,
        known_order_ids=(),
        unknown_order_ids=(987654,),
        reason=(
            "PAPER startup blocked by unknown "
            "active broker orders."
        ),
    )

    from app.paper_application_startup import (
        PaperApplicationStartupResult,
    )

    summary = StartupSummaryBuilder().build(
        startup_result=PaperApplicationStartupResult(
            recovery_result=None,
            discovery_result=discovery_result,
            reconciliation_result=None,
            trading_started=False,
            reason=discovery_result.reason,
        ),
    )

    assert (
        summary.outcome
        == StartupOutcome.BLOCKED_BY_DISCOVERY
    )

def test_summary_classifies_recovery_block() -> None:
    from app.paper_application_startup import (
        PaperApplicationStartupResult,
    )

    startup_result = PaperApplicationStartupResult(
        recovery_result=None,
        discovery_result=None,
        reconciliation_result=None,
        trading_started=False,
        reason="Recovery refused.",
    )

    summary = StartupSummaryBuilder().build(
        startup_result=startup_result,
    )

    assert (
        summary.outcome
        == StartupOutcome.BLOCKED_BY_RECOVERY
    )

def test_summary_classifies_reconciliation_block() -> None:
    from app.paper_application_startup import (
        PaperApplicationStartupResult,
    )
    from app.paper_startup_reconciliation import (
        PaperStartupReconciliationResult,
    )
    from app.reconciliation import (
        ReconciliationReport,
    )

    discovery_result = StartupOrderDiscoveryResult(
        approved=True,
        known_order_ids=(),
        unknown_order_ids=(),
        reason=(
            "PAPER startup order discovery "
            "completed safely."
        ),
    )

    reconciliation_result = (
        PaperStartupReconciliationResult(
            report=ReconciliationReport(
                is_reconciled=False,
                local_cash=5_000.00,
                broker_cash=4_500.00,
                local_positions={},
                broker_positions={},
                issues=[],
            ),
            approved=False,
            reason=(
                "PAPER startup reconciliation "
                "failed."
            ),
        )
    )

    summary = StartupSummaryBuilder().build(
        startup_result=PaperApplicationStartupResult(
            recovery_result=None,
            discovery_result=discovery_result,
            reconciliation_result=(
                reconciliation_result
            ),
            trading_started=False,
            reason=reconciliation_result.reason,
        ),
    )

    assert (
        summary.outcome
        == StartupOutcome
        .BLOCKED_BY_RECONCILIATION
    )