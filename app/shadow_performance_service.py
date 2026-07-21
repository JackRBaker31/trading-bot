from collections import defaultdict
from statistics import median
from typing import Iterable

from app.news_signal_outcome import NewsSignalOutcome
from app.news_signal_outcome_store import NewsSignalOutcomeStore
from app.shadow_decision import ShadowDecision
from app.shadow_decision_repository import ShadowDecisionRepository
from app.shadow_performance import (
    ShadowHorizonPerformance,
    ShadowPerformanceGroup,
    ShadowPerformanceReport,
)


class ShadowPerformanceService:
    MODEL_VERSION = "KAIRO_SHADOW_V1"
    HORIZONS = ("1H", "1D", "5D")

    def __init__(
        self,
        *,
        repository: ShadowDecisionRepository,
        outcome_store: NewsSignalOutcomeStore | None = None,
        execution_cost_percent: float = 0.20,
        rolling_window_size: int = 20,
    ) -> None:
        if execution_cost_percent < 0:
            raise ValueError(
                "Execution cost cannot be negative."
            )
        if rolling_window_size <= 0:
            raise ValueError(
                "Rolling window size must be positive."
            )

        self._repository = repository
        self._outcome_store = (
            outcome_store or NewsSignalOutcomeStore()
        )
        self._execution_cost_percent = (
            execution_cost_percent
        )
        self._rolling_window_size = (
            rolling_window_size
        )

    def get_report(self) -> ShadowPerformanceReport:
        decisions = self._repository.list_recent(
            limit=100_000
        )
        outcomes = self._outcome_store.load_all()
        outcome_map = {
            (
                outcome.article_id,
                outcome.horizon_name,
            ): outcome
            for outcome in outcomes
        }

        horizons = tuple(
            self._build_horizon(
                horizon=horizon,
                decisions=decisions,
                outcome_map=outcome_map,
            )
            for horizon in self.HORIZONS
        )

        return ShadowPerformanceReport(
            model_version=self.MODEL_VERSION,
            total_decision_count=len(decisions),
            execution_cost_percent=(
                self._execution_cost_percent
            ),
            horizons=horizons,
        )

    def _build_horizon(
        self,
        *,
        horizon: str,
        decisions: tuple[ShadowDecision, ...],
        outcome_map: dict[
            tuple[str, str],
            NewsSignalOutcome,
        ],
    ) -> ShadowHorizonPerformance:
        measured = [
            (
                decision,
                outcome_map[
                    (decision.article_id, horizon)
                ],
            )
            for decision in decisions
            if (
                decision.article_id,
                horizon,
            ) in outcome_map
        ]
        returns = [
            outcome.return_percent
            for _, outcome in measured
        ]
        net_returns = [
            value - self._execution_cost_percent
            for value in returns
        ]
        profitable_count = sum(
            value > 0
            for value in returns
        )
        profitable_after_cost_count = sum(
            value > 0
            for value in net_returns
        )

        ordered_returns = [
            outcome.return_percent
            for _, outcome in sorted(
                measured,
                key=lambda pair: (
                    pair[1].observed_at
                ),
            )
        ]
        rolling_returns = self._rolling_returns(
            ordered_returns
        )

        return ShadowHorizonPerformance(
            horizon=horizon,
            decision_count=len(decisions),
            measured_count=len(measured),
            coverage_percent=self._percent(
                len(measured),
                len(decisions),
            ),
            profitable_count=profitable_count,
            directional_success_percent=self._percent(
                profitable_count,
                len(measured),
            ),
            profitable_after_cost_count=(
                profitable_after_cost_count
            ),
            profitable_after_cost_percent=self._percent(
                profitable_after_cost_count,
                len(measured),
            ),
            average_return_percent=self._average(
                returns
            ),
            median_return_percent=self._median(
                returns
            ),
            average_net_return_percent=self._average(
                net_returns
            ),
            best_return_percent=(
                0.0 if not returns else max(returns)
            ),
            worst_return_percent=(
                0.0 if not returns else min(returns)
            ),
            maximum_drawdown_percent=(
                self._maximum_drawdown(
                    ordered_returns
                )
            ),
            rolling_window_count=len(
                rolling_returns
            ),
            positive_rolling_window_percent=(
                self._percent(
                    sum(
                        value > 0
                        for value in rolling_returns
                    ),
                    len(rolling_returns),
                )
            ),
            by_action=self._groups(
                measured,
                lambda decision: (
                    decision.action.value
                ),
            ),
            by_score_band=self._groups(
                measured,
                lambda decision: (
                    self._score_band(
                        decision.score
                    )
                ),
            ),
            by_confidence_band=self._groups(
                measured,
                lambda decision: (
                    self._confidence_band(
                        decision.confidence
                    )
                ),
            ),
            by_event_type=self._groups(
                measured,
                lambda decision: (
                    decision.event_type
                ),
            ),
            by_materiality=self._groups(
                measured,
                lambda decision: (
                    "MATERIAL"
                    if decision.is_material
                    else "NON_MATERIAL"
                ),
            ),
        )

    def _groups(
        self,
        measured: list[
            tuple[
                ShadowDecision,
                NewsSignalOutcome,
            ]
        ],
        name_provider,
    ) -> tuple[ShadowPerformanceGroup, ...]:
        grouped: dict[
            str,
            list[float],
        ] = defaultdict(list)

        for decision, outcome in measured:
            grouped[
                name_provider(decision)
            ].append(
                outcome.return_percent
            )

        return tuple(
            self._group(
                name=name,
                returns=returns,
            )
            for name, returns in sorted(
                grouped.items()
            )
        )

    def _group(
        self,
        *,
        name: str,
        returns: list[float],
    ) -> ShadowPerformanceGroup:
        profitable = sum(
            value > 0
            for value in returns
        )
        return ShadowPerformanceGroup(
            name=name,
            sample_count=len(returns),
            profitable_count=profitable,
            directional_success_percent=(
                self._percent(
                    profitable,
                    len(returns),
                )
            ),
            average_return_percent=(
                self._average(returns)
            ),
            median_return_percent=(
                self._median(returns)
            ),
            average_net_return_percent=(
                self._average(
                    [
                        value
                        - self._execution_cost_percent
                        for value in returns
                    ]
                )
            ),
        )

    def _rolling_returns(
        self,
        returns: list[float],
    ) -> list[float]:
        if (
            len(returns)
            < self._rolling_window_size
        ):
            return []

        return [
            self._average(
                returns[
                    index:
                    index + self._rolling_window_size
                ]
            )
            for index in range(
                0,
                len(returns)
                - self._rolling_window_size
                + 1,
            )
        ]

    @staticmethod
    def _maximum_drawdown(
        returns: Iterable[float],
    ) -> float:
        equity = 1.0
        peak = 1.0
        maximum = 0.0

        for value in returns:
            equity *= 1 + value / 100
            peak = max(peak, equity)
            drawdown = (
                0.0
                if peak <= 0
                else (peak - equity) / peak * 100
            )
            maximum = max(maximum, drawdown)

        return round(maximum, 4)

    @staticmethod
    def _score_band(
        score: float,
    ) -> str:
        if score >= 80:
            return "80_TO_100"
        if score >= 70:
            return "70_TO_79"
        if score >= 60:
            return "60_TO_69"
        return "BELOW_60"

    @staticmethod
    def _confidence_band(
        confidence: float,
    ) -> str:
        if confidence >= 0.90:
            return "VERY_HIGH_0.90_PLUS"
        if confidence >= 0.80:
            return "HIGH_0.80_TO_0.89"
        if confidence >= 0.70:
            return "MEDIUM_0.70_TO_0.79"
        return "LOW_BELOW_0.70"

    @staticmethod
    def _average(
        values: list[float],
    ) -> float:
        return (
            0.0
            if not values
            else round(
                sum(values) / len(values),
                4,
            )
        )

    @staticmethod
    def _median(
        values: list[float],
    ) -> float:
        return (
            0.0
            if not values
            else round(median(values), 4)
        )

    @staticmethod
    def _percent(
        numerator: int,
        denominator: int,
    ) -> float:
        return (
            0.0
            if denominator == 0
            else round(
                numerator / denominator * 100,
                2,
            )
        )
