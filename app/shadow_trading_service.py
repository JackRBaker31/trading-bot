from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from app.intelligence_snapshot import OpportunityClassification
from app.news_signal_outcome_store import NewsSignalOutcomeStore
from app.news_signal_price_snapshot_store import (
    NewsSignalPriceSnapshotStore,
)
from app.shadow_decision import ShadowAction, ShadowDecision
from app.shadow_decision_repository import ShadowDecisionRepository


@dataclass(frozen=True)
class ShadowAnalysisResult:
    opportunities_seen: int
    decisions_created: int
    decisions_skipped: int

    def to_dictionary(self) -> dict[str, int]:
        return {
            "opportunities_seen": self.opportunities_seen,
            "decisions_created": self.decisions_created,
            "decisions_skipped": self.decisions_skipped,
        }


class ShadowTradingService:
    MODEL_VERSION = "KAIRO_SHADOW_V1"

    def __init__(
        self,
        *,
        intelligence_service,
        repository: ShadowDecisionRepository,
        snapshot_store: NewsSignalPriceSnapshotStore | None = None,
        outcome_store: NewsSignalOutcomeStore | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._intelligence_service = intelligence_service
        self._repository = repository
        self._snapshot_store = snapshot_store or (
            NewsSignalPriceSnapshotStore()
        )
        self._outcome_store = outcome_store or NewsSignalOutcomeStore()
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )

    def initialize(self) -> None:
        self._repository.initialize()

    def run_analysis(self) -> ShadowAnalysisResult:
        snapshot = self._intelligence_service.get_snapshot()
        created = 0
        skipped = 0

        for opportunity in snapshot.top_opportunities:
            price_snapshot = self._snapshot_store.get_by_article_id(
                opportunity.article_id
            )
            decision = ShadowDecision(
                decision_id=str(uuid4()),
                article_id=opportunity.article_id,
                symbol=opportunity.symbol,
                created_at=self._utc_now(),
                model_version=self.MODEL_VERSION,
                action=self._action_for(opportunity.classification),
                score=opportunity.score,
                confidence=opportunity.confidence,
                sentiment=opportunity.sentiment,
                event_type=opportunity.event_type,
                is_material=opportunity.is_material,
                headline=opportunity.headline,
                eligible_for_trade=opportunity.eligible_for_trade,
                reasons=opportunity.reasons,
                blocking_reasons=opportunity.blocking_reasons,
                reference_price=(
                    None if price_snapshot is None else price_snapshot.price
                ),
                reference_captured_at=(
                    None
                    if price_snapshot is None
                    else price_snapshot.captured_at
                ),
            )
            if self._repository.add_if_missing(decision=decision):
                created += 1
            else:
                skipped += 1

        return ShadowAnalysisResult(
            opportunities_seen=len(snapshot.top_opportunities),
            decisions_created=created,
            decisions_skipped=skipped,
        )

    def list_decisions(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        symbol: str | None = None,
        action: ShadowAction | None = None,
    ) -> dict[str, object]:
        decisions = self._repository.list_recent(
            limit=limit,
            offset=offset,
            symbol=symbol,
            action=action,
        )
        return {
            "total_count": self._repository.count(),
            "offset": offset,
            "limit": limit,
            "count": len(decisions),
            "items": [item.to_dictionary() for item in decisions],
        }

    def get_summary(self) -> dict[str, object]:
        decisions = self._repository.list_recent(limit=10_000)
        outcomes = self._outcome_store.load_all()
        outcome_map = {
            (outcome.article_id, outcome.horizon_name): outcome
            for outcome in outcomes
        }

        by_horizon: list[dict[str, object]] = []
        for horizon in ("1H", "1D", "5D"):
            measured = []
            for decision in decisions:
                outcome = outcome_map.get((decision.article_id, horizon))
                if outcome is not None:
                    measured.append((decision, outcome))

            consider_long = [
                pair
                for pair in measured
                if pair[0].action is ShadowAction.CONSIDER_LONG
            ]
            profitable = sum(
                1 for _, outcome in consider_long
                if outcome.return_percent > 0
            )
            returns = [
                outcome.return_percent
                for _, outcome in consider_long
            ]
            by_horizon.append(
                {
                    "horizon": horizon,
                    "measured_count": len(consider_long),
                    "profitable_count": profitable,
                    "directional_success_percent": (
                        0.0
                        if not consider_long
                        else round(
                            profitable / len(consider_long) * 100,
                            2,
                        )
                    ),
                    "average_return_percent": (
                        0.0
                        if not returns
                        else round(sum(returns) / len(returns), 4)
                    ),
                }
            )

        action_counts = {
            action.value: sum(1 for item in decisions if item.action is action)
            for action in ShadowAction
        }
        one_day_measured = sum(
            1
            for decision in decisions
            if (decision.article_id, "1D") in outcome_map
        )
        eligible_decisions = sum(
            1
            for decision in decisions
            if decision.eligible_for_trade
        )
        latest_decision_at = (
            None
            if not decisions
            else max(
                decision.created_at
                for decision in decisions
            ).isoformat()
        )
        return {
            "decision_count": len(decisions),
            "total_decisions": len(decisions),
            "measured_decisions": one_day_measured,
            "eligible_decisions": eligible_decisions,
            "blocked_decisions": (
                len(decisions) - eligible_decisions
            ),
            "latest_decision_at": latest_decision_at,
            "model_version": self.MODEL_VERSION,
            "action_counts": action_counts,
            "performance_by_horizon": by_horizon,
            "trading_impact": "NONE",
        }

    @staticmethod
    def _action_for(
        classification: OpportunityClassification,
    ) -> ShadowAction:
        mapping = {
            OpportunityClassification.MONITOR: ShadowAction.MONITOR,
            OpportunityClassification.WATCH: ShadowAction.WATCH,
            OpportunityClassification.CANDIDATE: (
                ShadowAction.CONSIDER_LONG
            ),
            OpportunityClassification.BLOCKED: ShadowAction.BLOCKED,
        }
        return mapping[classification]

    def _utc_now(self) -> datetime:
        value = self._now_provider()
        if value.tzinfo is None:
            raise ValueError(
                "Shadow-analysis clock must be timezone-aware."
            )
        return value.astimezone(timezone.utc)
