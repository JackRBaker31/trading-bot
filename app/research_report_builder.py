from datetime import datetime
from typing import Protocol

from app.backtest_result import BacktestResult
from app.execution_cost import ExecutionCostModel
from app.monte_carlo_summary import (
    MonteCarloSummary,
)
from app.research_report import ResearchReport
from app.research_decision import (
    evaluate_research_decision,
)


class StrategyResultLike(Protocol):
    total_return_percent: float


class WalkForwardResultLike(Protocol):
    training_result: StrategyResultLike
    validation_result: StrategyResultLike


class RollingSummaryLike(Protocol):
    window_count: int
    positive_window_percent: float
    average_return_percent: float
    worst_return_percent: float


def build_research_report(
    *,
    strategy_name: str,
    gross_backtest_result: BacktestResult,
    net_backtest_result: BacktestResult,
    gross_monte_carlo_summary: MonteCarloSummary,
    net_monte_carlo_summary: MonteCarloSummary,
    net_cost_model: ExecutionCostModel,
    walk_forward_result: WalkForwardResultLike,
    rolling_summary: RollingSummaryLike,
    generated_at: str | None = None,
) -> ResearchReport:
    cleaned_strategy_name = (
        strategy_name.strip()
    )

    if not cleaned_strategy_name:
        raise ValueError(
            "Strategy name is required."
        )

    timestamp = (
        generated_at
        or datetime.now()
        .astimezone()
        .isoformat()
    )

    decision = evaluate_research_decision(
        net_return_percent=(
            net_backtest_result
            .total_return_percent
        ),
        walk_forward_validation_percent=(
            walk_forward_result
            .validation_result
            .total_return_percent
        ),
        positive_rolling_windows_percent=(
            rolling_summary
            .positive_window_percent
        ),
        monte_carlo_loss_probability_percent=(
            net_monte_carlo_summary
            .loss_probability_percent
        ),
        monte_carlo_worst_drawdown_percent=(
            net_monte_carlo_summary
            .worst_drawdown_percent
        ),
    )

    return ResearchReport(
        strategy_name=cleaned_strategy_name,
        generated_at=timestamp,
        gross_completed_trades=len(
            gross_backtest_result
            .completed_trade_profits
        ),
        net_completed_trades=len(
            net_backtest_result
            .completed_trade_profits
        ),
        gross_backtest_return_percent=(
            gross_backtest_result
            .total_return_percent
        ),
        net_backtest_return_percent=(
            net_backtest_result
            .total_return_percent
        ),
        gross_monte_carlo_median_percent=(
            gross_monte_carlo_summary
            .median_return_percent
        ),
        net_monte_carlo_median_percent=(
            net_monte_carlo_summary
            .median_return_percent
        ),
        gross_fifth_percentile_percent=(
            gross_monte_carlo_summary
            .fifth_percentile_return_percent
        ),
        net_fifth_percentile_percent=(
            net_monte_carlo_summary
            .fifth_percentile_return_percent
        ),
        gross_ninety_fifth_percentile_percent=(
            gross_monte_carlo_summary
            .ninety_fifth_percentile_return_percent
        ),
        net_ninety_fifth_percentile_percent=(
            net_monte_carlo_summary
            .ninety_fifth_percentile_return_percent
        ),
        gross_loss_probability_percent=(
            gross_monte_carlo_summary
            .loss_probability_percent
        ),
        net_loss_probability_percent=(
            net_monte_carlo_summary
            .loss_probability_percent
        ),
        gross_average_drawdown_percent=(
            gross_monte_carlo_summary
            .average_drawdown_percent
        ),
        net_average_drawdown_percent=(
            net_monte_carlo_summary
            .average_drawdown_percent
        ),
        gross_worst_drawdown_percent=(
            gross_monte_carlo_summary
            .worst_drawdown_percent
        ),
        net_worst_drawdown_percent=(
            net_monte_carlo_summary
            .worst_drawdown_percent
        ),
        verdict=decision.verdict.value,
        passed_check_count=(
            decision.passed_check_count
        ),
        total_check_count=(
            decision.total_check_count
        ),
        decision_reasons=decision.reasons,
        slippage_percent=(
            net_cost_model.slippage_percent
        ),
        commission_percent=(
            net_cost_model.commission_percent
        ),
        minimum_fee=(
            net_cost_model.minimum_fee
        ),
        walk_forward_training_return_percent=(
            walk_forward_result
            .training_result
            .total_return_percent
        ),
        walk_forward_validation_return_percent=(
            walk_forward_result
            .validation_result
            .total_return_percent
        ),
        rolling_window_count=(
            rolling_summary.window_count
        ),
        rolling_positive_window_percent=(
            rolling_summary
            .positive_window_percent
        ),
        rolling_average_return_percent=(
            rolling_summary
            .average_return_percent
        ),
        rolling_worst_return_percent=(
            rolling_summary
            .worst_return_percent
        ),
    )