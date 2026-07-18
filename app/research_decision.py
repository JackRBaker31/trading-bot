from dataclasses import dataclass
from enum import Enum


class ResearchVerdict(str, Enum):
    PROMISING = "PROMISING"
    BORDERLINE = "BORDERLINE"
    REJECT = "REJECT"


@dataclass(frozen=True)
class ResearchDecisionThresholds:
    minimum_net_return_percent: float = 0.0
    minimum_walk_forward_validation_percent: float = 0.0
    minimum_positive_rolling_windows_percent: float = 60.0
    maximum_monte_carlo_loss_probability_percent: float = 15.0
    maximum_monte_carlo_worst_drawdown_percent: float = 15.0


@dataclass(frozen=True)
class ResearchDecision:
    verdict: ResearchVerdict
    passed_check_count: int
    total_check_count: int
    reasons: tuple[str, ...]


def evaluate_research_decision(
    *,
    net_return_percent: float,
    walk_forward_validation_percent: float,
    positive_rolling_windows_percent: float,
    monte_carlo_loss_probability_percent: float,
    monte_carlo_worst_drawdown_percent: float,
    thresholds: ResearchDecisionThresholds | None = None,
) -> ResearchDecision:
    active_thresholds = (
        thresholds
        or ResearchDecisionThresholds()
    )

    checks = [
        (
            net_return_percent
            > active_thresholds
            .minimum_net_return_percent,
            (
                "Net return is positive."
                if net_return_percent
                > active_thresholds
                .minimum_net_return_percent
                else "Net return is not positive."
            ),
        ),
        (
            walk_forward_validation_percent
            > active_thresholds
            .minimum_walk_forward_validation_percent,
            (
                "Walk-forward validation return is positive."
                if walk_forward_validation_percent
                > active_thresholds
                .minimum_walk_forward_validation_percent
                else (
                    "Walk-forward validation return "
                    "is not positive."
                )
            ),
        ),
        (
            positive_rolling_windows_percent
            >= active_thresholds
            .minimum_positive_rolling_windows_percent,
            (
                "Rolling positive-window rate meets "
                "the minimum."
                if positive_rolling_windows_percent
                >= active_thresholds
                .minimum_positive_rolling_windows_percent
                else (
                    "Rolling positive-window rate is "
                    "below the minimum."
                )
            ),
        ),
        (
            monte_carlo_loss_probability_percent
            <= active_thresholds
            .maximum_monte_carlo_loss_probability_percent,
            (
                "Monte Carlo loss probability is "
                "within the limit."
                if monte_carlo_loss_probability_percent
                <= active_thresholds
                .maximum_monte_carlo_loss_probability_percent
                else (
                    "Monte Carlo loss probability "
                    "exceeds the limit."
                )
            ),
        ),
        (
            monte_carlo_worst_drawdown_percent
            <= active_thresholds
            .maximum_monte_carlo_worst_drawdown_percent,
            (
                "Monte Carlo worst drawdown is "
                "within the limit."
                if monte_carlo_worst_drawdown_percent
                <= active_thresholds
                .maximum_monte_carlo_worst_drawdown_percent
                else (
                    "Monte Carlo worst drawdown "
                    "exceeds the limit."
                )
            ),
        ),
    ]

    passed_check_count = sum(
        1
        for passed, _ in checks
        if passed
    )
    total_check_count = len(checks)

    if passed_check_count == total_check_count:
        verdict = ResearchVerdict.PROMISING
    elif passed_check_count >= 3:
        verdict = ResearchVerdict.BORDERLINE
    else:
        verdict = ResearchVerdict.REJECT

    return ResearchDecision(
        verdict=verdict,
        passed_check_count=passed_check_count,
        total_check_count=total_check_count,
        reasons=tuple(
            reason
            for _, reason in checks
        ),
    )