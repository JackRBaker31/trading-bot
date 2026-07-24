from collections import defaultdict
from typing import Any, Mapping

from app.adaptive_intelligence_models import (
    ConfidenceBandPerformance,
    PerformanceIntelligence,
)


class PerformanceIntelligenceService:
    def analyse(
        self,
        *,
        decisions: tuple[
            Mapping[str, Any],
            ...
        ],
        outcomes: tuple[
            Mapping[str, Any],
            ...
        ],
    ) -> PerformanceIntelligence:
        by_decision = {
            str(item["decision_id"]): item
            for item in decisions
        }

        joined = [
            (
                by_decision[
                    str(outcome["decision_id"])
                ],
                outcome,
            )
            for outcome in outcomes
            if str(outcome["decision_id"])
            in by_decision
        ]

        positive_rate = (
            sum(
                1
                for _, outcome in joined
                if float(
                    outcome["absolute_return"]
                ) > 0
            )
            / len(joined)
            if joined
            else None
        )

        average_return = self._average(
            float(outcome["absolute_return"])
            for _, outcome in joined
        )
        average_alpha = self._average(
            float(outcome["alpha"])
            for _, outcome in joined
        )

        horizon_returns: dict[
            int,
            list[float],
        ] = defaultdict(list)

        for _, outcome in joined:
            horizon_returns[
                int(outcome["horizon_days"])
            ].append(
                float(
                    outcome["absolute_return"]
                )
            )

        best_horizon = (
            max(
                horizon_returns,
                key=lambda horizon: (
                    sum(
                        horizon_returns[horizon]
                    )
                    / len(
                        horizon_returns[horizon]
                    )
                ),
            )
            if horizon_returns
            else None
        )

        bands = tuple(
            self._band(
                lower=lower,
                upper=upper,
                joined=joined,
            )
            for lower, upper
            in (
                (0.50, 0.60),
                (0.60, 0.70),
                (0.70, 0.80),
                (0.80, 0.90),
                (0.90, 1.01),
            )
        )

        sample_count = len(joined)
        learning_confidence = round(
            min(
                sample_count / 250,
                1.0,
            ),
            4,
        )

        findings: list[str] = []

        if sample_count == 0:
            findings.append(
                "No linked decision outcomes are available yet."
            )
        else:
            findings.append(
                f"{sample_count} decision-outcome observation(s) "
                "were analysed."
            )

        if best_horizon is not None:
            findings.append(
                f"The strongest average observed horizon is "
                f"{best_horizon} day(s)."
            )

        calibrated = [
            item
            for item in bands
            if (
                item.sample_count >= 10
                and item.calibration_gap
                is not None
            )
        ]

        if calibrated:
            weakest = max(
                calibrated,
                key=lambda item: abs(
                    float(item.calibration_gap)
                ),
            )
            findings.append(
                f"The largest confidence calibration gap is "
                f"{weakest.band}."
            )

        return PerformanceIntelligence(
            observation_count=sample_count,
            tracked_decision_count=len(
                {
                    str(outcome["decision_id"])
                    for _, outcome in joined
                }
            ),
            positive_rate=(
                round(positive_rate, 6)
                if positive_rate is not None
                else None
            ),
            average_return=average_return,
            average_alpha=average_alpha,
            best_horizon_days=best_horizon,
            confidence_bands=bands,
            learning_confidence=learning_confidence,
            findings=tuple(findings),
        )

    def calibration_multiplier(
        self,
        *,
        confidence: float,
        performance: PerformanceIntelligence,
    ) -> float:
        for band in performance.confidence_bands:
            lower, upper = self._parse_band(
                band.band
            )
            if (
                lower <= confidence < upper
                and band.sample_count >= 10
                and band.positive_rate is not None
            ):
                predicted = max(
                    band.predicted_midpoint,
                    0.01,
                )
                observed = float(
                    band.positive_rate
                )
                return round(
                    max(
                        0.75,
                        min(
                            observed / predicted,
                            1.15,
                        ),
                    ),
                    4,
                )

        return 1.0

    def _band(
        self,
        *,
        lower: float,
        upper: float,
        joined: list[
            tuple[
                Mapping[str, Any],
                Mapping[str, Any],
            ]
        ],
    ) -> ConfidenceBandPerformance:
        matches = [
            (decision, outcome)
            for decision, outcome in joined
            if (
                lower
                <= float(
                    decision["confidence"]
                )
                < upper
            )
        ]

        midpoint = round(
            min(
                (lower + min(upper, 1.0))
                / 2,
                1.0,
            ),
            4,
        )

        positive_rate = (
            sum(
                1
                for _, outcome in matches
                if float(
                    outcome["absolute_return"]
                ) > 0
            )
            / len(matches)
            if matches
            else None
        )

        return ConfidenceBandPerformance(
            band=(
                f"{int(lower * 100)}-"
                f"{int(min(upper, 1.0) * 100)}%"
            ),
            sample_count=len(matches),
            predicted_midpoint=midpoint,
            positive_rate=(
                round(positive_rate, 6)
                if positive_rate is not None
                else None
            ),
            average_return=self._average(
                float(outcome["absolute_return"])
                for _, outcome in matches
            ),
            average_alpha=self._average(
                float(outcome["alpha"])
                for _, outcome in matches
            ),
            calibration_gap=(
                round(
                    positive_rate - midpoint,
                    6,
                )
                if positive_rate is not None
                else None
            ),
        )

    @staticmethod
    def _average(
        values,
    ) -> float | None:
        items = list(values)
        if not items:
            return None
        return round(
            sum(items) / len(items),
            6,
        )

    @staticmethod
    def _parse_band(
        band: str,
    ) -> tuple[float, float]:
        left, right = (
            band.replace("%", "")
            .split("-")
        )
        return (
            int(left) / 100,
            int(right) / 100
            + (
                0.01
                if right == "100"
                else 0.0
            ),
        )
