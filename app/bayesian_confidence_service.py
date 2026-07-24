from math import sqrt
from typing import Any, Mapping

from app.advanced_intelligence_models import (
    BayesianCalibrationResult,
)


class BayesianConfidenceService:
    def calibrate(
        self,
        *,
        outcomes: tuple[
            Mapping[str, Any],
            ...
        ],
        prior_alpha: float = 2.0,
        prior_beta: float = 2.0,
    ) -> BayesianCalibrationResult:
        successes = sum(
            1
            for outcome in outcomes
            if float(
                outcome.get(
                    "absolute_return",
                    0.0,
                )
            ) > 0
        )
        failures = sum(
            1
            for outcome in outcomes
            if float(
                outcome.get(
                    "absolute_return",
                    0.0,
                )
            ) <= 0
        )

        posterior_alpha = prior_alpha + successes
        posterior_beta = prior_beta + failures
        total = posterior_alpha + posterior_beta
        mean = posterior_alpha / total

        variance = (
            posterior_alpha
            * posterior_beta
            / (
                total
                * total
                * (total + 1)
            )
        )
        standard_error = sqrt(variance)

        lower = max(
            mean - 1.96 * standard_error,
            0.0,
        )
        upper = min(
            mean + 1.96 * standard_error,
            1.0,
        )

        sample_count = successes + failures
        confidence_weight = min(
            sample_count / 100,
            1.0,
        )

        return BayesianCalibrationResult(
            prior_alpha=prior_alpha,
            prior_beta=prior_beta,
            successes=successes,
            failures=failures,
            posterior_alpha=posterior_alpha,
            posterior_beta=posterior_beta,
            posterior_mean=round(mean, 6),
            credible_lower=round(lower, 6),
            credible_upper=round(upper, 6),
            sample_count=sample_count,
            confidence_weight=round(
                confidence_weight,
                4,
            ),
        )

    @staticmethod
    def apply(
        *,
        raw_confidence: float,
        calibration: BayesianCalibrationResult,
    ) -> float:
        weight = calibration.confidence_weight

        return round(
            (
                raw_confidence * (1.0 - weight)
                + calibration.posterior_mean * weight
            ),
            6,
        )
