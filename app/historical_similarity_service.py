from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from statistics import mean, median
from typing import Protocol

from app.decision_memory_models import (
    DecisionMemoryCapability,
    DecisionMemoryRecord,
)
from app.decision_outcome_models import DecisionOutcomeObservation
from app.historical_similarity_models import (
    HistoricalSimilarityCase,
    HistoricalSimilarityReport,
    SimilarityFeatureComparison,
    SimilarityOutcome,
)
from app.investment_thesis_models import (
    InvestmentThesis,
    ThesisCapabilityAssessment,
)


class CapabilityLike(Protocol):
    capability: str
    status: str
    score: float | None
    maximum: float
    confidence: float | None
    stance: str


ThesisProvider = Callable[[str], InvestmentThesis | None]
DecisionProvider = Callable[[int], tuple[DecisionMemoryRecord, ...]]
OutcomeProvider = Callable[[str], tuple[DecisionOutcomeObservation, ...]]
NowProvider = Callable[[], datetime]


class HistoricalSimilarityService:
    """Match the current thesis against measured decision-memory feature vectors."""

    METHODOLOGY_VERSION = "KAIRO-HSIM-1.0"
    METHODOLOGY_SUMMARY = (
        "Weighted feature-vector comparison across capability scores, capability "
        "stances, data availability, overall score, confidence, coverage, event "
        "type, recommendation, risk tier, time horizon, primary driver and symbol."
    )

    def __init__(
        self,
        *,
        thesis_provider: ThesisProvider,
        decisions_provider: DecisionProvider,
        outcomes_provider: OutcomeProvider,
        now_provider: NowProvider | None = None,
    ) -> None:
        self._thesis_provider = thesis_provider
        self._decisions_provider = decisions_provider
        self._outcomes_provider = outcomes_provider
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )

    def analyse(
        self,
        *,
        symbol: str,
        minimum_similarity_percent: float = 65.0,
        limit: int = 12,
        candidate_limit: int = 1000,
    ) -> HistoricalSimilarityReport:
        normalised_symbol = symbol.upper().strip()
        if not normalised_symbol:
            raise ValueError("Symbol is required.")
        if not 0 <= minimum_similarity_percent <= 100:
            raise ValueError("Minimum similarity must be between 0 and 100.")
        if limit <= 0:
            raise ValueError("Limit must be positive.")
        if candidate_limit <= 0:
            raise ValueError("Candidate limit must be positive.")

        current = self._thesis_provider(
            normalised_symbol
        )
        if current is None:
            raise LookupError(
                f"No current investment thesis is available for {normalised_symbol}."
            )

        candidates = tuple(
            item
            for item in self._decisions_provider(candidate_limit)
            if item.thesis_generated_at < current.generated_at
        )
        target_horizon = self._target_horizon(current.time_horizon)

        matched: list[HistoricalSimilarityCase] = []
        measured_for_summary: list[HistoricalSimilarityCase] = []

        for historical in candidates:
            comparisons = self._comparisons(current=current, historical=historical)
            similarity = round(
                sum(item.contribution_points for item in comparisons),
                2,
            )
            if similarity < minimum_similarity_percent:
                continue

            outcome = self._selected_outcome(
                historical=historical,
                target_horizon=target_horizon,
            )
            matching, differing = self._factor_summaries(comparisons)
            case = HistoricalSimilarityCase(
                decision_id=historical.decision_id,
                symbol=historical.symbol,
                captured_at=historical.captured_at,
                thesis_generated_at=historical.thesis_generated_at,
                recommendation=historical.recommendation,
                score=historical.score,
                confidence=historical.confidence,
                risk_tier=historical.risk_tier,
                time_horizon=historical.time_horizon,
                headline=historical.headline,
                primary_driver=historical.primary_driver,
                similarity_percent=similarity,
                same_symbol=historical.symbol == current.symbol,
                matching_factors=matching,
                differing_factors=differing,
                feature_comparisons=comparisons,
                outcome=outcome,
            )
            matched.append(case)
            if outcome is not None:
                measured_for_summary.append(case)

        matched.sort(
            key=lambda item: (
                item.similarity_percent,
                item.outcome is not None,
                item.thesis_generated_at,
            ),
            reverse=True,
        )

        measured_outcomes = [
            item.outcome
            for item in measured_for_summary
            if item.outcome is not None
        ]
        directional_returns = [
            item.directional_return_percent for item in measured_outcomes
        ]
        raw_returns = [item.raw_return_percent for item in measured_outcomes]
        alpha_values = [item.alpha_percent for item in measured_outcomes]
        horizons = [item.horizon_days for item in measured_outcomes]
        warnings = self._warnings(
            current=current,
            candidates=candidates,
            matched=matched,
            measured_count=len(measured_outcomes),
            target_horizon=target_horizon,
            measured_horizons=horizons,
        )

        return HistoricalSimilarityReport(
            generated_at=self._utc_now(),
            symbol=current.symbol,
            current_thesis_id=current.thesis_id,
            current_recommendation=current.recommendation,
            current_score=current.score,
            current_confidence=current.confidence,
            current_risk_tier=current.risk_tier,
            current_time_horizon=current.time_horizon,
            current_primary_driver=current.primary_driver,
            methodology_version=self.METHODOLOGY_VERSION,
            methodology_summary=self.METHODOLOGY_SUMMARY,
            minimum_similarity_percent=round(minimum_similarity_percent, 2),
            target_horizon_days=target_horizon,
            candidate_count=len(candidates),
            matched_case_count=len(matched),
            measured_case_count=len(measured_outcomes),
            sample_quality=self._sample_quality(len(measured_outcomes)),
            average_similarity_percent=(
                round(mean(item.similarity_percent for item in matched), 2)
                if matched
                else None
            ),
            win_rate_percent=(
                round(
                    sum(item.directional_success for item in measured_outcomes)
                    / len(measured_outcomes)
                    * 100,
                    1,
                )
                if measured_outcomes
                else None
            ),
            average_return_percent=(
                round(mean(raw_returns), 3) if raw_returns else None
            ),
            median_return_percent=(
                round(median(raw_returns), 3) if raw_returns else None
            ),
            average_directional_return_percent=(
                round(mean(directional_returns), 3)
                if directional_returns
                else None
            ),
            average_alpha_percent=(
                round(mean(alpha_values), 3) if alpha_values else None
            ),
            best_directional_return_percent=(
                round(max(directional_returns), 3)
                if directional_returns
                else None
            ),
            worst_directional_return_percent=(
                round(min(directional_returns), 3)
                if directional_returns
                else None
            ),
            average_holding_days=(
                round(mean(horizons), 1) if horizons else None
            ),
            cases=tuple(matched[:limit]),
            warnings=warnings,
        )

    def _comparisons(
        self,
        *,
        current: InvestmentThesis,
        historical: DecisionMemoryRecord,
    ) -> tuple[SimilarityFeatureComparison, ...]:
        current_capabilities = self._capability_index(current.capabilities)
        historical_capabilities = self._capability_index(
            historical.capabilities
        )

        values: list[tuple[str, str, str, str, float, float]] = [
            (
                "CAPABILITY_PROFILE",
                "Capability score profile",
                self._capability_summary(current_capabilities),
                self._capability_summary(historical_capabilities),
                self._capability_score_similarity(
                    current_capabilities,
                    historical_capabilities,
                ),
                36.0,
            ),
            (
                "CAPABILITY_STANCE",
                "Capability stance alignment",
                self._stance_summary(current_capabilities),
                self._stance_summary(historical_capabilities),
                self._capability_stance_similarity(
                    current_capabilities,
                    historical_capabilities,
                ),
                8.0,
            ),
            (
                "CAPABILITY_STATUS",
                "Capability availability",
                self._status_summary(current_capabilities),
                self._status_summary(historical_capabilities),
                self._capability_status_similarity(
                    current_capabilities,
                    historical_capabilities,
                ),
                4.0,
            ),
            (
                "SCORE",
                "Overall score",
                f"{current.score:.2f}",
                f"{historical.score:.2f}",
                self._distance_similarity(current.score, historical.score, 100.0),
                8.0,
            ),
            (
                "CONFIDENCE",
                "Confidence",
                f"{current.confidence * 100:.1f}%",
                f"{historical.confidence * 100:.1f}%",
                self._distance_similarity(
                    current.confidence,
                    historical.confidence,
                    1.0,
                ),
                8.0,
            ),
            (
                "COVERAGE",
                "Capability coverage",
                f"{current.confidence_coverage * 100:.1f}%",
                f"{historical.confidence_coverage * 100:.1f}%",
                self._distance_similarity(
                    current.confidence_coverage,
                    historical.confidence_coverage,
                    1.0,
                ),
                5.0,
            ),
            self._categorical(
                "RECOMMENDATION",
                "Recommendation",
                current.recommendation,
                historical.recommendation,
                5.0,
            ),
            self._categorical(
                "RISK_TIER",
                "Risk tier",
                current.risk_tier,
                historical.risk_tier,
                4.0,
                ordered=("LOW", "MEDIUM", "HIGH"),
            ),
            self._categorical(
                "TIME_HORIZON",
                "Time horizon",
                current.time_horizon,
                historical.time_horizon,
                4.0,
            ),
            self._categorical(
                "PRIMARY_DRIVER",
                "Primary driver",
                current.primary_driver,
                historical.primary_driver,
                4.0,
            ),
            self._categorical(
                "EVENT_TYPE",
                "News event type",
                self._event_type(current.capabilities),
                self._event_type(historical.capabilities),
                8.0,
            ),
            self._categorical(
                "SYMBOL",
                "Symbol",
                current.symbol,
                historical.symbol,
                6.0,
            ),
        ]

        return tuple(
            SimilarityFeatureComparison(
                code=code,
                label=label,
                current_value=current_value,
                historical_value=historical_value,
                similarity_percent=round(similarity * 100, 1),
                weight=weight,
                contribution_points=round(similarity * weight, 3),
            )
            for (
                code,
                label,
                current_value,
                historical_value,
                similarity,
                weight,
            ) in values
        )

    def _selected_outcome(
        self,
        *,
        historical: DecisionMemoryRecord,
        target_horizon: int,
    ) -> SimilarityOutcome | None:
        outcomes = self._outcomes_provider(historical.decision_id)
        if not outcomes:
            return None

        selected = min(
            outcomes,
            key=lambda item: (
                abs(item.horizon_days - target_horizon),
                item.horizon_days < target_horizon,
                item.horizon_days,
            ),
        )
        multiplier = self._direction_multiplier(historical)
        raw_return = selected.absolute_return * 100
        directional_return = raw_return * multiplier

        return SimilarityOutcome(
            horizon_days=selected.horizon_days,
            observed_at=selected.observed_at,
            raw_return_percent=round(raw_return, 3),
            directional_return_percent=round(directional_return, 3),
            alpha_percent=round(selected.alpha * 100 * multiplier, 3),
            maximum_favourable_excursion_percent=round(
                selected.maximum_favourable_excursion * 100,
                3,
            ),
            maximum_drawdown_percent=round(
                selected.maximum_drawdown * 100,
                3,
            ),
            directional_success=directional_return > 0,
            status=selected.status,
        )

    @staticmethod
    def _capability_index(
        capabilities: Iterable[CapabilityLike],
    ) -> dict[str, CapabilityLike]:
        return {
            item.capability.upper().strip(): item
            for item in capabilities
        }

    def _capability_score_similarity(
        self,
        current: dict[str, CapabilityLike],
        historical: dict[str, CapabilityLike],
    ) -> float:
        codes = sorted(set(current) | set(historical))
        if not codes:
            return 0.0
        weighted = 0.0
        total = 0.0
        for code in codes:
            left = current.get(code)
            right = historical.get(code)
            maximum = max(
                left.maximum if left else 0.0,
                right.maximum if right else 0.0,
                1.0,
            )
            total += maximum
            if left is None or right is None:
                similarity = 0.0
            elif left.score is None and right.score is None:
                similarity = 1.0 if left.status == right.status else 0.5
            elif left.score is None or right.score is None:
                similarity = 0.0
            else:
                left_normalised = left.score / max(left.maximum, 1.0)
                right_normalised = right.score / max(right.maximum, 1.0)
                similarity = max(0.0, 1.0 - abs(left_normalised - right_normalised))
            weighted += similarity * maximum
        return weighted / total if total else 0.0

    def _capability_stance_similarity(
        self,
        current: dict[str, CapabilityLike],
        historical: dict[str, CapabilityLike],
    ) -> float:
        codes = sorted(set(current) | set(historical))
        if not codes:
            return 0.0
        values = []
        for code in codes:
            left = current.get(code)
            right = historical.get(code)
            if left is None or right is None:
                values.append(0.0)
                continue
            left_stance = left.stance.upper().strip()
            right_stance = right.stance.upper().strip()
            if left_stance == right_stance:
                values.append(1.0)
            elif self._stance_group(left_stance) == self._stance_group(right_stance):
                values.append(0.75)
            elif "UNKNOWN" in {left_stance, right_stance}:
                values.append(0.5)
            else:
                values.append(0.0)
        return mean(values)

    @staticmethod
    def _capability_status_similarity(
        current: dict[str, CapabilityLike],
        historical: dict[str, CapabilityLike],
    ) -> float:
        codes = sorted(set(current) | set(historical))
        if not codes:
            return 0.0
        values = []
        for code in codes:
            left = current.get(code)
            right = historical.get(code)
            if left is None or right is None:
                values.append(0.0)
            elif left.status == right.status:
                values.append(1.0)
            elif left.status != "AVAILABLE" and right.status != "AVAILABLE":
                values.append(0.75)
            else:
                values.append(0.0)
        return mean(values)

    @staticmethod
    def _categorical(
        code: str,
        label: str,
        current: str,
        historical: str,
        weight: float,
        ordered: tuple[str, ...] | None = None,
    ) -> tuple[str, str, str, str, float, float]:
        left = current.upper().strip() or "UNKNOWN"
        right = historical.upper().strip() or "UNKNOWN"
        if left == right:
            similarity = 1.0
        elif ordered and left in ordered and right in ordered:
            distance = abs(ordered.index(left) - ordered.index(right))
            similarity = max(0.0, 1.0 - distance / max(1, len(ordered) - 1))
        elif "UNKNOWN" in {left, right}:
            similarity = 0.5
        else:
            similarity = 0.0
        return code, label, left, right, similarity, weight

    @staticmethod
    def _distance_similarity(left: float, right: float, scale: float) -> float:
        return max(0.0, min(1.0, 1.0 - abs(left - right) / scale))

    @staticmethod
    def _event_type(
        capabilities: Iterable[ThesisCapabilityAssessment | DecisionMemoryCapability],
    ) -> str:
        news = next(
            (
                item
                for item in capabilities
                if item.capability.upper().strip() == "NEWS"
            ),
            None,
        )
        if news is None:
            return "UNKNOWN"
        for evidence in news.evidence:
            prefix, separator, value = evidence.partition(":")
            if separator and prefix.strip().upper() == "EVENT TYPE":
                return value.strip().upper() or "UNKNOWN"
        return "UNKNOWN"

    @staticmethod
    def _direction_multiplier(historical: DecisionMemoryRecord) -> float:
        news = next(
            (
                item
                for item in historical.capabilities
                if item.capability.upper().strip() == "NEWS"
            ),
            None,
        )
        if news is not None:
            stance = news.stance.upper().strip()
            if stance == "BEARISH":
                return -1.0
            if stance == "BULLISH":
                return 1.0
        return -1.0 if historical.recommendation.upper() == "AVOID" else 1.0

    @staticmethod
    def _target_horizon(time_horizon: str) -> int:
        return {
            "SWING": 7,
            "POSITION": 90,
            "UNSPECIFIED": 30,
        }.get(time_horizon.upper().strip(), 30)

    @staticmethod
    def _sample_quality(measured_count: int) -> str:
        if measured_count == 0:
            return "NO_MEASURED_SAMPLE"
        if measured_count < 3:
            return "INSUFFICIENT"
        if measured_count < 10:
            return "EARLY"
        if measured_count < 30:
            return "DEVELOPING"
        return "MEANINGFUL"

    @staticmethod
    def _factor_summaries(
        comparisons: tuple[SimilarityFeatureComparison, ...],
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        matching = tuple(
            f"{item.label}: {item.current_value} aligns with {item.historical_value}."
            for item in sorted(
                (value for value in comparisons if value.similarity_percent >= 85),
                key=lambda value: value.contribution_points,
                reverse=True,
            )[:5]
        )
        differing = tuple(
            f"{item.label}: current {item.current_value}; historical {item.historical_value}."
            for item in sorted(
                (value for value in comparisons if value.similarity_percent < 60),
                key=lambda value: value.weight,
                reverse=True,
            )[:4]
        )
        return matching, differing

    def _warnings(
        self,
        *,
        current: InvestmentThesis,
        candidates: tuple[DecisionMemoryRecord, ...],
        matched: list[HistoricalSimilarityCase],
        measured_count: int,
        target_horizon: int,
        measured_horizons: list[int],
    ) -> tuple[str, ...]:
        warnings: list[str] = []
        if not candidates:
            warnings.append(
                "Decision memory does not yet contain an older feature vector for comparison."
            )
        elif not matched:
            warnings.append(
                "No historical decision met the selected similarity threshold."
            )
        if measured_count < 3:
            warnings.append(
                "The measured sample is too small for decision-making; treat the result as descriptive only."
            )
        elif measured_count < 10:
            warnings.append(
                "The measured sample is still early and should not override KAIRO's risk gates."
            )
        if measured_horizons and any(
            value != target_horizon for value in measured_horizons
        ):
            warnings.append(
                "Some cases use the nearest available measured horizon rather than the exact target horizon."
            )
        unavailable = [
            item.capability
            for item in current.capabilities
            if item.status != "AVAILABLE"
        ]
        if unavailable:
            warnings.append(
                "Current feature coverage is incomplete for: "
                + ", ".join(unavailable)
                + "."
            )
        return tuple(dict.fromkeys(warnings))

    @staticmethod
    def _capability_summary(capabilities: dict[str, CapabilityLike]) -> str:
        parts = []
        for code, item in sorted(capabilities.items()):
            if item.score is None:
                parts.append(f"{code}=NA")
            else:
                parts.append(
                    f"{code}={item.score / max(item.maximum, 1.0) * 100:.0f}%"
                )
        return ", ".join(parts) or "No capabilities"

    @staticmethod
    def _stance_summary(capabilities: dict[str, CapabilityLike]) -> str:
        return ", ".join(
            f"{code}={item.stance}" for code, item in sorted(capabilities.items())
        ) or "No stances"

    @staticmethod
    def _status_summary(capabilities: dict[str, CapabilityLike]) -> str:
        return ", ".join(
            f"{code}={item.status}" for code, item in sorted(capabilities.items())
        ) or "No statuses"

    @staticmethod
    def _stance_group(value: str) -> str:
        if value in {"BULLISH", "SUPPORTIVE", "PASS", "POSITIVE"}:
            return "POSITIVE"
        if value in {"BEARISH", "CONSTRAINED", "BLOCKED", "NEGATIVE"}:
            return "NEGATIVE"
        return "NEUTRAL"

    def _utc_now(self) -> datetime:
        value = self._now_provider()
        if value.tzinfo is None:
            raise ValueError("Current time must be timezone-aware.")
        return value.astimezone(timezone.utc)
