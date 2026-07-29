from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Callable

from app.opportunity_ranking_history_models import (
    OpportunityHistoryOverviewItem,
    OpportunityHistoryOverviewReport,
    OpportunityRankingChange,
    OpportunitySymbolHistoryReport,
)
from app.opportunity_ranking_history_repository import (
    OpportunityRankingHistoryRepository,
)
from app.opportunity_ranking_models import OpportunityRankingReport


class OpportunityRankingHistoryService:
    VALID_WINDOWS = (1, 7, 30)

    def __init__(
        self,
        *,
        repository: OpportunityRankingHistoryRepository,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )

    def initialize(self) -> None:
        self._repository.initialize()

    def capture(
        self,
        *,
        report: OpportunityRankingReport,
        source: str,
    ):
        return self._repository.record_report(
            report=report,
            source=source,
        )

    def get_symbol_history(
        self,
        *,
        symbol: str,
        window_days: int = 7,
    ) -> OpportunitySymbolHistoryReport:
        window = self._validated_window(window_days)
        generated_at = self._utc_now()
        all_snapshots = self._repository.list_for_symbol(
            symbol=symbol,
            limit=5000,
        )
        if not all_snapshots:
            return OpportunitySymbolHistoryReport(
                generated_at=generated_at,
                symbol=symbol.upper().strip(),
                window_days=window,
                first_seen_at=None,
                last_observed_at=None,
                snapshot_count=0,
                current_rank=None,
                current_score=None,
                score_change=0.0,
                rank_change=0,
                streak_direction="UNCHANGED",
                snapshots=(),
                changes=(),
            )

        cutoff = generated_at - timedelta(days=window)
        visible = [
            snapshot
            for snapshot in all_snapshots
            if snapshot.captured_at >= cutoff
        ]
        previous = [
            snapshot
            for snapshot in all_snapshots
            if snapshot.captured_at < cutoff
        ]
        if previous:
            visible.insert(0, previous[-1])
        if not visible:
            visible = [all_snapshots[-1]]

        changes = tuple(
            self._change(previous_snapshot, current_snapshot)
            for previous_snapshot, current_snapshot in zip(
                visible,
                visible[1:],
            )
        )
        current = visible[-1]
        baseline = visible[0]

        universe_versions = self._universe_versions(visible)
        return OpportunitySymbolHistoryReport(
            generated_at=generated_at,
            symbol=current.symbol,
            window_days=window,
            first_seen_at=all_snapshots[0].captured_at,
            last_observed_at=all_snapshots[-1].last_observed_at,
            snapshot_count=len(all_snapshots),
            current_rank=current.rank,
            current_score=current.opportunity_score,
            score_change=round(
                current.opportunity_score - baseline.opportunity_score,
                2,
            ),
            rank_change=baseline.rank - current.rank,
            streak_direction=self._streak_direction(visible),
            snapshots=tuple(visible),
            changes=changes,
            universe_versions=universe_versions,
            rank_comparability_warning=self._comparability_warning(
                snapshots=visible,
            ),
        )

    def get_overview(
        self,
        *,
        window_days: int = 1,
    ) -> OpportunityHistoryOverviewReport:
        window = self._validated_window(window_days)
        generated_at = self._utc_now()
        cutoff = generated_at - timedelta(days=window)
        grouped: dict[str, list] = defaultdict(list)
        all_snapshots = self._repository.list_all(limit=10000)
        for snapshot in all_snapshots:
            grouped[snapshot.symbol].append(snapshot)

        items: list[OpportunityHistoryOverviewItem] = []
        for symbol, snapshots in grouped.items():
            current = snapshots[-1]
            baseline_candidates = [
                snapshot for snapshot in snapshots if snapshot.captured_at <= cutoff
            ]
            if baseline_candidates:
                baseline = baseline_candidates[-1]
            else:
                baseline = snapshots[0]
            items.append(
                OpportunityHistoryOverviewItem(
                    symbol=symbol,
                    current_rank=current.rank,
                    current_score=current.opportunity_score,
                    score_change=round(
                        current.opportunity_score - baseline.opportunity_score,
                        2,
                    ),
                    rank_change=baseline.rank - current.rank,
                    eligible_for_execution=current.eligible_for_execution,
                    category=current.category,
                    last_observed_at=current.last_observed_at,
                )
            )

        ordered = tuple(
            sorted(
                items,
                key=lambda item: (item.current_rank, item.symbol),
            )
        )
        risers = tuple(
            sorted(
                (item for item in items if item.score_change > 0),
                key=lambda item: (item.score_change, item.rank_change),
                reverse=True,
            )[:5]
        )
        fallers = tuple(
            sorted(
                (item for item in items if item.score_change < 0),
                key=lambda item: (item.score_change, -item.rank_change),
            )[:5]
        )
        latest = max(
            (snapshot.last_observed_at for snapshot in all_snapshots),
            default=None,
        )
        return OpportunityHistoryOverviewReport(
            generated_at=generated_at,
            window_days=window,
            tracked_symbol_count=len(grouped),
            snapshot_count=len(all_snapshots),
            latest_observed_at=latest,
            largest_risers=risers,
            largest_fallers=fallers,
            items=ordered,
            universe_versions=self._universe_versions(all_snapshots),
            rank_comparability_warning=self._comparability_warning(
                snapshots=all_snapshots,
            ),
        )

    def _change(self, previous, current) -> OpportunityRankingChange:
        score_change = round(
            current.opportunity_score - previous.opportunity_score,
            2,
        )
        rank_change = previous.rank - current.rank
        codes = set(previous.component_values) | set(current.component_values)
        component_changes = []
        for code in codes:
            delta = round(
                current.component_values.get(code, 0.0)
                - previous.component_values.get(code, 0.0),
                2,
            )
            if abs(delta) < 0.01:
                continue
            component_changes.append(
                {
                    "code": code,
                    "label": current.component_labels.get(
                        code,
                        previous.component_labels.get(code, code),
                    ),
                    "change": delta,
                }
            )
        component_changes.sort(
            key=lambda item: abs(float(item["change"])),
            reverse=True,
        )

        previous_blockers = set(previous.blockers)
        current_blockers = set(current.blockers)
        blockers_added = tuple(sorted(current_blockers - previous_blockers))
        blockers_resolved = tuple(sorted(previous_blockers - current_blockers))
        readiness_changed = (
            previous.eligible_for_execution != current.eligible_for_execution
        )
        direction = (
            "IMPROVING"
            if score_change > 0.01
            else "WEAKENING"
            if score_change < -0.01
            else "RANK_ONLY"
            if rank_change != 0
            else "UNCHANGED"
        )

        fragments = []
        if score_change:
            fragments.append(f"score {score_change:+.2f}")
        if rank_change:
            fragments.append(
                f"rank {'up' if rank_change > 0 else 'down'} "
                f"{abs(rank_change)}"
            )
        if readiness_changed:
            fragments.append(
                "execution became ready"
                if current.eligible_for_execution
                else "execution became blocked"
            )
        if blockers_added:
            fragments.append(f"{len(blockers_added)} blocker(s) added")
        if blockers_resolved:
            fragments.append(f"{len(blockers_resolved)} blocker(s) resolved")
        summary = "; ".join(fragments) or "No material movement."

        return OpportunityRankingChange(
            captured_at=current.captured_at,
            previous_captured_at=previous.captured_at,
            score_change=score_change,
            rank_change=rank_change,
            direction=direction,
            summary=summary,
            component_changes=tuple(component_changes[:5]),
            blockers_added=blockers_added,
            blockers_resolved=blockers_resolved,
            readiness_changed=readiness_changed,
            previous_eligible_for_execution=previous.eligible_for_execution,
            eligible_for_execution=current.eligible_for_execution,
        )

    @staticmethod
    def _universe_versions(snapshots) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                snapshot.universe_version_id
                for snapshot in snapshots
                if snapshot.universe_version_id
            )
        )

    @classmethod
    def _comparability_warning(cls, *, snapshots) -> str | None:
        versions = cls._universe_versions(snapshots)
        sizes = {
            snapshot.universe_size
            for snapshot in snapshots
            if snapshot.universe_size is not None
        }
        if len(versions) <= 1 and len(sizes) <= 1:
            return None
        ordered_sizes = sorted(sizes)
        size_text = (
            "different universe sizes"
            if not ordered_sizes
            else " and ".join(str(value) for value in ordered_sizes)
        )
        return (
            "Absolute rank movement spans multiple universe versions "
            f"({size_text} symbols). Compare score movement directly; rank "
            "movement may also reflect added or removed competitors."
        )

    @staticmethod
    def _streak_direction(snapshots) -> str:
        if len(snapshots) < 2:
            return "NEW"
        signs: list[int] = []
        for previous, current in zip(snapshots, snapshots[1:]):
            delta = current.opportunity_score - previous.opportunity_score
            if abs(delta) < 0.01:
                continue
            signs.append(1 if delta > 0 else -1)
        if not signs:
            return "UNCHANGED"
        latest = signs[-1]
        streak = 0
        for sign in reversed(signs):
            if sign != latest:
                break
            streak += 1
        label = "IMPROVING" if latest > 0 else "WEAKENING"
        return f"{label}_{streak}"

    @classmethod
    def _validated_window(cls, value: int) -> int:
        if value not in cls.VALID_WINDOWS:
            raise ValueError("History window must be 1, 7 or 30 days.")
        return value

    def _utc_now(self) -> datetime:
        value = self._now_provider()
        if value.tzinfo is None:
            raise ValueError("Opportunity-history clock must be timezone-aware.")
        return value.astimezone(timezone.utc)
