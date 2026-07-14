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
class StartupSummary:
    outcome: StartupOutcome
    startup_approved: bool
    discovery_approved: bool | None
    discovery_reason: str
    known_active_order_count: int
    unknown_active_order_count: int


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
                discovery_approved=None,
                discovery_reason="",
                known_active_order_count=0,
                unknown_active_order_count=0,
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
            discovery_approved=(
                discovery_result.approved
            ),
            discovery_reason=(
                discovery_result.reason
            ),
            known_active_order_count=(
                discovery_result.known_order_count
            ),
            unknown_active_order_count=(
                discovery_result.unknown_order_count
            ),
        )