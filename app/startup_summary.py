from dataclasses import dataclass

from app.paper_application_startup import (
    PaperApplicationStartupResult,
)
from enum import Enum

@dataclass(frozen=True)
class StartupOutcome(str, Enum):
    APPROVED = "APPROVED"
    BLOCKED_BY_RECOVERY = (
        "BLOCKED_BY_RECOVERY"
    )
    BLOCKED_BY_DISCOVERY = (
        "BLOCKED_BY_DISCOVERY"
    )
    BLOCKED_BY_RECONCILIATION = (
        "BLOCKED_BY_RECONCILIATION"
    )

@dataclass(frozen=True)
class StartupDiscoverySummary:
    approved: bool | None
    reason: str
    known_order_count: int
    unknown_order_count: int

@dataclass(frozen=True)
class StartupSummary:
    outcome: StartupOutcome
    startup_approved: bool
    discovery: StartupDiscoverySummary


class StartupSummaryBuilder:
       def build(
        self,
        startup_result: PaperApplicationStartupResult,
    ) -> StartupSummary:
        discovery_result = (
            startup_result.discovery_result
        )

        if discovery_result is None:
            return StartupSummary(
                outcome=(
                    StartupOutcome
                    .BLOCKED_BY_RECOVERY
                ),
                startup_approved=False,
                discovery=StartupDiscoverySummary(
                    approved=None,
                    reason="",
                    known_order_count=0,
                    unknown_order_count=0,
                ),
            )

        outcome = StartupOutcome.APPROVED

        if not discovery_result.approved:
            outcome = (
                StartupOutcome
                .BLOCKED_BY_DISCOVERY
            )
        else:
            reconciliation_result = (
                startup_result.reconciliation_result
            )

            if (
                reconciliation_result is not None
                and not reconciliation_result.approved
            ):
                outcome = (
                    StartupOutcome
                    .BLOCKED_BY_RECONCILIATION
                )

        return StartupSummary(
            outcome=outcome,
            startup_approved=(
                startup_result.trading_started
            ),
            discovery=StartupDiscoverySummary(
                approved=discovery_result.approved,
                reason=discovery_result.reason,
                known_order_count=(
                    discovery_result.known_order_count
                ),
                unknown_order_count=(
                    discovery_result.unknown_order_count
                ),
            ),
        )