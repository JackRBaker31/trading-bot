from dataclasses import dataclass

from app.startup_order_discovery import (
    StartupOrderDiscoveryResult,
)


@dataclass(frozen=True)
class StartupSummary:
    startup_approved: bool
    discovery_approved: bool
    discovery_reason: str
    known_active_order_count: int
    unknown_active_order_count: int


class StartupSummaryBuilder:
    def build(
        self,
        discovery_result: (
            StartupOrderDiscoveryResult
        ),
        startup_approved: bool,
    ) -> StartupSummary:
        return StartupSummary(
            startup_approved=startup_approved,
            discovery_approved=(
                discovery_result.approved
            ),
            discovery_reason=(
                discovery_result.reason
            ),
            known_active_order_count=(
                discovery_result
                .known_order_count
            ),
            unknown_active_order_count=(
                discovery_result
                .unknown_order_count
            ),
        )