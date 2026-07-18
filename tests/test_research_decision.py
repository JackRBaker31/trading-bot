from app.research_decision import (
    ResearchDecisionThresholds,
    ResearchVerdict,
    evaluate_research_decision,
)


def test_returns_promising_when_all_checks_pass() -> None:
    decision = evaluate_research_decision(
        net_return_percent=5.0,
        walk_forward_validation_percent=3.0,
        positive_rolling_windows_percent=60.0,
        monte_carlo_loss_probability_percent=10.0,
        monte_carlo_worst_drawdown_percent=12.0,
    )

    assert decision.verdict is ResearchVerdict.PROMISING
    assert decision.passed_check_count == 5
    assert decision.total_check_count == 5


def test_returns_borderline_when_three_checks_pass() -> None:
    decision = evaluate_research_decision(
        net_return_percent=5.0,
        walk_forward_validation_percent=-1.0,
        positive_rolling_windows_percent=60.0,
        monte_carlo_loss_probability_percent=10.0,
        monte_carlo_worst_drawdown_percent=20.0,
    )

    assert decision.verdict is ResearchVerdict.BORDERLINE
    assert decision.passed_check_count == 3


def test_returns_reject_when_fewer_than_three_checks_pass() -> None:
    decision = evaluate_research_decision(
        net_return_percent=-1.0,
        walk_forward_validation_percent=-1.0,
        positive_rolling_windows_percent=40.0,
        monte_carlo_loss_probability_percent=10.0,
        monte_carlo_worst_drawdown_percent=20.0,
    )

    assert decision.verdict is ResearchVerdict.REJECT
    assert decision.passed_check_count == 1


def test_supports_custom_thresholds() -> None:
    decision = evaluate_research_decision(
        net_return_percent=5.0,
        walk_forward_validation_percent=3.0,
        positive_rolling_windows_percent=60.0,
        monte_carlo_loss_probability_percent=10.0,
        monte_carlo_worst_drawdown_percent=12.0,
        thresholds=ResearchDecisionThresholds(
            minimum_net_return_percent=6.0,
            minimum_walk_forward_validation_percent=4.0,
            minimum_positive_rolling_windows_percent=70.0,
            maximum_monte_carlo_loss_probability_percent=5.0,
            maximum_monte_carlo_worst_drawdown_percent=10.0,
        ),
    )

    assert decision.verdict is ResearchVerdict.REJECT
    assert decision.passed_check_count == 0