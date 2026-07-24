from typing import Any, Mapping

from app.advanced_intelligence_models import (
    BayesianCalibrationResult,
    ExplainableDecision,
    ExplanationContribution,
    MarketRegimeAssessment,
    MultiTimeframeAssessment,
)
from app.bayesian_confidence_service import (
    BayesianConfidenceService,
)


class ExplainableDecisionService:
    def explain(
        self,
        *,
        theses: tuple[
            Mapping[str, Any],
            ...
        ],
        regime: MarketRegimeAssessment,
        timeframe_by_symbol: Mapping[
            str,
            MultiTimeframeAssessment,
        ],
        calibration: BayesianCalibrationResult,
    ) -> tuple[
        ExplainableDecision,
        ...
    ]:
        results = []

        for thesis in theses:
            symbol = str(thesis["symbol"])
            raw_score = float(thesis["score"])
            raw_confidence = float(
                thesis["confidence"]
            )

            timeframe = timeframe_by_symbol.get(
                symbol
            )

            contributions = []

            for capability in thesis.get(
                "capabilities",
                (),
            ):
                score = capability.get("score")
                maximum = float(
                    capability.get(
                        "maximum",
                        1.0,
                    )
                )
                if score is None or maximum <= 0:
                    continue

                normalised = (
                    float(score) / maximum
                )
                contribution = (
                    normalised - 0.5
                ) * maximum

                contributions.append(
                    ExplanationContribution(
                        code=str(
                            capability.get(
                                "capability",
                                "UNKNOWN",
                            )
                        ),
                        label=str(
                            capability.get(
                                "capability",
                                "Unknown",
                            )
                        ).title(),
                        contribution=round(
                            contribution,
                            2,
                        ),
                        direction=(
                            "POSITIVE"
                            if contribution >= 0
                            else "NEGATIVE"
                        ),
                        source="CAPABILITY",
                        detail=str(
                            capability.get(
                                "summary",
                                "",
                            )
                        ),
                    )
                )

            regime_adjustment = (
                regime.position_multiplier
                - 1.0
            ) * 20.0

            contributions.append(
                ExplanationContribution(
                    code="MARKET_REGIME",
                    label="Market regime",
                    contribution=round(
                        regime_adjustment,
                        2,
                    ),
                    direction=(
                        "POSITIVE"
                        if regime_adjustment >= 0
                        else "NEGATIVE"
                    ),
                    source="REGIME",
                    detail=(
                        f"{regime.regime} regime with "
                        f"{regime.volatility_state} volatility."
                    ),
                )
            )

            timeframe_adjustment = 0.0

            if timeframe is not None:
                timeframe_adjustment = (
                    timeframe.composite_score
                    - 50.0
                ) / 5.0

                if (
                    timeframe.alignment
                    == "CONFLICTED"
                ):
                    timeframe_adjustment -= 5.0

                contributions.append(
                    ExplanationContribution(
                        code="MULTI_TIMEFRAME",
                        label="Multi-timeframe alignment",
                        contribution=round(
                            timeframe_adjustment,
                            2,
                        ),
                        direction=(
                            "POSITIVE"
                            if timeframe_adjustment >= 0
                            else "NEGATIVE"
                        ),
                        source="MULTI_TIMEFRAME",
                        detail=(
                            f"{timeframe.alignment}; "
                            f"score {timeframe.composite_score:.1f}."
                        ),
                    )
                )

            adjusted_score = max(
                0.0,
                min(
                    raw_score
                    + regime_adjustment
                    + timeframe_adjustment,
                    100.0,
                ),
            )

            calibrated_confidence = (
                BayesianConfidenceService.apply(
                    raw_confidence=raw_confidence,
                    calibration=calibration,
                )
            )

            blockers = tuple(
                str(value)
                for value in thesis.get(
                    "blockers",
                    (),
                )
            )

            if timeframe is not None:
                blockers = tuple(
                    dict.fromkeys(
                        (
                            *blockers,
                            *timeframe.blockers,
                        )
                    )
                )

            recommendation = (
                "BLOCKED"
                if blockers
                else "BUY"
                if (
                    adjusted_score
                    >= regime.buy_threshold
                    and calibrated_confidence
                    >= 0.75
                )
                else "WATCH"
                if adjusted_score >= 65
                else "HOLD"
                if adjusted_score >= 50
                else "AVOID"
            )

            sorted_contributions = tuple(
                sorted(
                    contributions,
                    key=lambda item: abs(
                        item.contribution
                    ),
                    reverse=True,
                )
            )

            results.append(
                ExplainableDecision(
                    symbol=symbol,
                    recommendation=recommendation,
                    raw_score=raw_score,
                    adjusted_score=round(
                        adjusted_score,
                        2,
                    ),
                    raw_confidence=raw_confidence,
                    calibrated_confidence=(
                        calibrated_confidence
                    ),
                    regime=regime.regime,
                    timeframe_alignment=(
                        timeframe.alignment
                        if timeframe is not None
                        else "UNAVAILABLE"
                    ),
                    contributions=(
                        sorted_contributions
                    ),
                    blockers=blockers,
                    summary=(
                        f"{symbol} is {recommendation} after "
                        "regime, timeframe and Bayesian "
                        "confidence adjustments."
                    ),
                )
            )

        return tuple(results)
