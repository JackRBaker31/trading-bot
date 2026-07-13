from app.startup_summary import StartupSummaryBuilder
from app.startup_order_discovery import (
    StartupOrderDiscoveryResult,
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

    summary = builder.build(
        discovery_result=discovery_result,
        startup_approved=True,
    )

    assert summary.known_active_order_count == 1
    assert summary.unknown_active_order_count == 0
    assert summary.discovery_approved is True
    assert summary.discovery_reason == (
            "PAPER startup order discovery "
            "completed safely."
    )
    assert summary.startup_approved is True