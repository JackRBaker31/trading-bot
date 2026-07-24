from collections.abc import Callable
from datetime import datetime, timezone
from uuid import uuid4

from app.copilot_history_models import (
    CopilotChangeSummary, CopilotDecisionSnapshot, CopilotMetricChange,
)
from app.copilot_history_repository import CopilotHistoryRepository
from app.copilot_overview_models import CopilotOverview


class CopilotChangeService:
    def __init__(
        self,
        *,
        repository: CopilotHistoryRepository,
        overview_provider: Callable[[], CopilotOverview],
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._overview_provider = overview_provider
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def initialize(self) -> None:
        self._repository.initialize()

    def capture(self) -> CopilotDecisionSnapshot:
        snapshot = self._from_overview(self._overview_provider())
        self._repository.save(snapshot=snapshot)
        return snapshot

    def list_history(
        self, *, limit: int = 100, capture_current: bool = True,
    ) -> tuple[CopilotDecisionSnapshot, ...]:
        if capture_current:
            self.capture()
        return self._repository.list_recent(limit=limit)

    def change_summary(self) -> CopilotChangeSummary:
        current = self.capture()
        previous = self._repository.latest_before(captured_at=current.captured_at)
        if previous is None:
            return CopilotChangeSummary(
                generated_at=self._now(), comparison_available=False,
                current=current, previous=None, confidence_change=None,
                signal_count_change=None, actionable_signal_change=None,
                graduation_passed_change=None,
                summary=(
                    "This is the first recorded Copilot decision snapshot. "
                    "Change analysis will become available after the next capture."
                ),
            )

        confidence = self._change("confidence", previous.confidence, current.confidence)
        signals = self._change("signal_count", previous.signal_count, current.signal_count)
        actionable = self._change(
            "actionable_signal_count",
            previous.actionable_signal_count,
            current.actionable_signal_count,
        )
        graduation = self._change(
            "graduation_passed_checks",
            previous.graduation_passed_checks,
            current.graduation_passed_checks,
        )
        new_blockers = tuple(sorted(set(current.blockers) - set(previous.blockers)))
        cleared = tuple(sorted(set(previous.blockers) - set(current.blockers)))

        parts: list[str] = []
        if current.decision != previous.decision:
            parts.append(
                f"The trading decision changed from {previous.decision} "
                f"to {current.decision}."
            )
        if confidence.change:
            parts.append(
                f"Confidence {'increased' if confidence.change > 0 else 'decreased'} "
                f"by {abs(confidence.change):.1f}."
            )
        if actionable.change:
            parts.append(
                f"Actionable signals "
                f"{'increased' if actionable.change > 0 else 'decreased'} "
                f"by {abs(actionable.change):.0f}."
            )
        if new_blockers:
            parts.append(f"{len(new_blockers)} new blocker(s) appeared.")
        if cleared:
            parts.append(f"{len(cleared)} blocker(s) cleared.")
        if not parts:
            parts.append(
                "No material Copilot decision changes were detected "
                "since the previous snapshot."
            )

        return CopilotChangeSummary(
            generated_at=self._now(), comparison_available=True,
            current=current, previous=previous,
            confidence_change=confidence, signal_count_change=signals,
            actionable_signal_change=actionable,
            graduation_passed_change=graduation,
            new_blockers=new_blockers, cleared_blockers=cleared,
            summary=" ".join(parts),
        )

    def _from_overview(self, overview: CopilotOverview) -> CopilotDecisionSnapshot:
        intelligence = overview.trading_intelligence
        graduation = overview.graduation
        blockers: list[str] = []

        if intelligence.trading_readiness != "READY":
            blockers.append("Trading readiness has not reached READY.")

        confidence = float(intelligence.confidence)
        confidence_percent = confidence * 100 if confidence <= 1 else confidence
        if confidence_percent < 80:
            blockers.append("Intelligence confidence is below 80%.")

        if intelligence.actionable_signal_count <= 0:
            blockers.append("No actionable signals are currently available.")

        if intelligence.evidence_quality.upper() in {
            "LOW", "VERY_LOW", "INSUFFICIENT", "UNKNOWN",
        }:
            blockers.append("Evidence quality is not strong enough.")

        blockers.extend(
            check.reason or f"{check.name} has not passed."
            for check in graduation.failed_checks
        )
        unique_blockers = tuple(dict.fromkeys(blockers))
        decision = (
            "TRADE_READY"
            if intelligence.trading_readiness == "READY"
            and graduation.ready and not unique_blockers
            else "NO_TRADE"
        )

        return CopilotDecisionSnapshot(
            snapshot_id=str(uuid4()), captured_at=self._now(),
            overall_status=overview.overall_status,
            platform_status=overview.platform.overall_status,
            trading_readiness=intelligence.trading_readiness,
            market_outlook=intelligence.market_outlook,
            confidence=confidence, signal_count=intelligence.signal_count,
            actionable_signal_count=intelligence.actionable_signal_count,
            evidence_quality=intelligence.evidence_quality,
            graduation_ready=graduation.ready,
            graduation_passed_checks=graduation.passed_checks,
            graduation_total_checks=graduation.total_checks,
            graduation_failed_checks=len(graduation.failed_checks),
            decision=decision, blockers=unique_blockers,
        )

    @staticmethod
    def _change(metric: str, previous: float, current: float) -> CopilotMetricChange:
        change = float(current) - float(previous)
        direction = "UP" if change > 0 else "DOWN" if change < 0 else "UNCHANGED"
        return CopilotMetricChange(
            metric=metric, previous=float(previous), current=float(current),
            change=change, direction=direction,
        )

    def _now(self) -> datetime:
        value = self._now_provider()
        if value.tzinfo is None:
            raise ValueError("Copilot change clock must be timezone-aware.")
        return value.astimezone(timezone.utc)
