from typing import Any, Mapping

from app.adaptive_intelligence_models import (
    PerformanceIntelligence,
    PositionSizeRecommendation,
)
from app.performance_intelligence_service import (
    PerformanceIntelligenceService,
)


class PositionSizingService:
    def __init__(
        self,
        *,
        performance_service: (
            PerformanceIntelligenceService
        ),
    ) -> None:
        self._performance_service = (
            performance_service
        )

    def recommend(
        self,
        *,
        theses: tuple[
            Mapping[str, Any],
            ...
        ],
        performance: PerformanceIntelligence,
        maximum_order_value: float,
        maximum_position_value: float,
        available_cash: float,
    ) -> tuple[
        PositionSizeRecommendation,
        ...
    ]:
        results: list[
            PositionSizeRecommendation
        ] = []

        hard_cap = max(
            0.0,
            min(
                maximum_order_value,
                maximum_position_value,
                available_cash,
            ),
        )

        for thesis in theses:
            eligible = bool(
                thesis.get(
                    "eligible_for_execution",
                    False,
                )
            )
            score = max(
                0.0,
                min(
                    float(
                        thesis.get(
                            "score",
                            0.0,
                        )
                    )
                    / 100,
                    1.0,
                ),
            )
            confidence = max(
                0.0,
                min(
                    float(
                        thesis.get(
                            "confidence",
                            0.0,
                        )
                    ),
                    1.0,
                ),
            )
            risk_multiplier = {
                "LOW": 0.75,
                "MEDIUM": 0.50,
                "HIGH": 0.25,
            }.get(
                str(
                    thesis.get(
                        "risk_tier",
                        "HIGH",
                    )
                ),
                0.25,
            )
            calibration = (
                self._performance_service
                .calibration_multiplier(
                    confidence=confidence,
                    performance=performance,
                )
            )

            base = (
                hard_cap
                * score
                * confidence
                * risk_multiplier
                if eligible
                else 0.0
            )
            calibrated = (
                min(
                    base * calibration,
                    hard_cap,
                )
                if eligible
                else 0.0
            )

            reasons = [
                (
                    "Position is bounded by order, position "
                    "and available-cash limits."
                ),
                (
                    f"Historical confidence calibration "
                    f"multiplier is {calibration:.3f}."
                ),
            ]

            if not eligible:
                reasons.append(
                    "The thesis is not execution eligible."
                )

            results.append(
                PositionSizeRecommendation(
                    symbol=str(
                        thesis["symbol"]
                    ),
                    base_value=round(
                        base,
                        2,
                    ),
                    calibrated_value=round(
                        calibrated,
                        2,
                    ),
                    maximum_value=round(
                        hard_cap,
                        2,
                    ),
                    score_multiplier=round(
                        score,
                        4,
                    ),
                    confidence_multiplier=round(
                        confidence,
                        4,
                    ),
                    risk_multiplier=round(
                        risk_multiplier,
                        4,
                    ),
                    calibration_multiplier=(
                        calibration
                    ),
                    eligible=eligible,
                    reasons=tuple(reasons),
                )
            )

        return tuple(results)
