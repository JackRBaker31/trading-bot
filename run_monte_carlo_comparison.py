import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from app.buy_the_dip import BuyTheDipStrategy
from app.config import load_config
from app.csv_historical_data import (
    load_historical_prices_from_csv,
)
from app.execution_cost import (
    ExecutionCostModel,
)
from app.monte_carlo import (
    MonteCarloSimulator,
)
from app.monte_carlo_summary import (
    MonteCarloSummary,
    summarize_monte_carlo_results,
)
from app.position_exit_manager import (
    PositionExitManager,
)
from app.position_exit_policy import (
    PositionExitPolicy,
)
from app.risk import RiskLimits
from app.rsi_entry_filter import RsiEntryFilter
from app.strategy_comparison_runner import (
    StrategyComparisonRunner,
)
from app.strategy_definition import (
    StrategyDefinition,
)


CaseResult = tuple[
    str,
    ExecutionCostModel,
    Any,
    MonteCarloSummary,
]


def run_case(
    *,
    label: str,
    execution_cost_model: ExecutionCostModel,
    historical_prices,
    starting_cash: float,
    risk_limits: RiskLimits,
    position_exit_manager: PositionExitManager,
    target_allocation_percent: float,
) -> CaseResult:
    runner = StrategyComparisonRunner(
        starting_cash=starting_cash,
        risk_limits=risk_limits,
        position_exit_manager=(
            position_exit_manager
        ),
        execution_cost_model=(
            execution_cost_model
        ),
    )

    rows, results = runner.run(
        historical_prices=historical_prices,
        strategy_definitions=[
            StrategyDefinition(
                name=(
                    "Drop=3 SMA=None "
                    "RSI=3/30 Cooldown=0"
                ),
                factory=lambda: BuyTheDipStrategy(
                    drop_threshold_percent=3.0,
                    target_allocation_percent=(
                        target_allocation_percent
                    ),
                    cooldown_cycles=0,
                    entry_filters=[
                        RsiEntryFilter(
                            period=3,
                            buy_threshold=30.0,
                        )
                    ],
                ),
            )
        ],
    )

    strategy_name = rows[0].name
    backtest_result = results[
        strategy_name
    ]

    trade_profits = (
        backtest_result
        .completed_trade_profits
    )

    if not trade_profits:
        raise RuntimeError(
            f"{label} run produced no completed trades."
        )

    simulations = (
        MonteCarloSimulator()
        .run_from_trade_profits(
            starting_equity=(
                backtest_result.starting_cash
            ),
            trade_profits=trade_profits,
            simulation_count=1_000,
            random_seed=12345,
        )
    )

    summary = summarize_monte_carlo_results(
        simulations
    )

    return (
        label,
        execution_cost_model,
        backtest_result,
        summary,
    )


def save_comparison_csv(
    *,
    cases: list[CaseResult],
    output_path: str,
) -> None:
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_at = (
        datetime.now()
        .astimezone()
        .isoformat()
    )

    with path.open(
        mode="w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "generated_at",
                "case",
                "completed_trades",
                "backtest_return_percent",
                "median_monte_carlo_return_percent",
                "fifth_percentile_return_percent",
                "ninety_fifth_percentile_return_percent",
                "loss_probability_percent",
                "average_drawdown_percent",
                "worst_drawdown_percent",
                "slippage_percent",
                "commission_percent",
                "minimum_fee",
            ]
        )

        for (
            label,
            cost_model,
            backtest_result,
            summary,
        ) in cases:
            writer.writerow(
                [
                    generated_at,
                    label,
                    len(
                        backtest_result
                        .completed_trade_profits
                    ),
                    round(
                        backtest_result
                        .total_return_percent,
                        4,
                    ),
                    round(
                        summary
                        .median_return_percent,
                        4,
                    ),
                    round(
                        summary
                        .fifth_percentile_return_percent,
                        4,
                    ),
                    round(
                        summary
                        .ninety_fifth_percentile_return_percent,
                        4,
                    ),
                    round(
                        summary
                        .loss_probability_percent,
                        4,
                    ),
                    round(
                        summary
                        .average_drawdown_percent,
                        4,
                    ),
                    round(
                        summary
                        .worst_drawdown_percent,
                        4,
                    ),
                    round(
                        cost_model.slippage_percent,
                        4,
                    ),
                    round(
                        cost_model.commission_percent,
                        4,
                    ),
                    round(
                        cost_model.minimum_fee,
                        4,
                    ),
                ]
            )


def main() -> None:
    config = load_config()

    logging.getLogger(
        "app.execution"
    ).setLevel(
        logging.ERROR
    )

    historical_prices = (
        load_historical_prices_from_csv(
            file_path="data/research_prices.csv"
        )
    )

    symbols = set(
        historical_prices[0].prices
    )

    risk_limits = RiskLimits(
        max_order_value=(
            config.risk.max_order_value
        ),
        max_position_value=(
            config.risk.max_position_value
        ),
        max_portfolio_exposure=(
            config.risk.max_portfolio_exposure
        ),
        max_trades_per_session=10_000,
        approved_symbols=symbols,
    )

    position_exit_manager = PositionExitManager(
        policy=PositionExitPolicy(
            stop_loss_percent=5.0,
            take_profit_percent=10.0,
            trailing_stop_percent=4.0,
            trailing_activation_percent=6.0,
        )
    )

    cases = [
        run_case(
            label="Gross",
            execution_cost_model=ExecutionCostModel(),
            historical_prices=historical_prices,
            starting_cash=config.starting_cash,
            risk_limits=risk_limits,
            position_exit_manager=(
                position_exit_manager
            ),
            target_allocation_percent=(
                config.strategy
                .target_allocation_percent
            ),
        ),
        run_case(
            label="Net",
            execution_cost_model=ExecutionCostModel(
                slippage_percent=0.10,
                commission_percent=0.10,
                minimum_fee=0.0,
            ),
            historical_prices=historical_prices,
            starting_cash=config.starting_cash,
            risk_limits=risk_limits,
            position_exit_manager=(
                position_exit_manager
            ),
            target_allocation_percent=(
                config.strategy
                .target_allocation_percent
            ),
        ),
    ]

    print("GROSS VS NET MONTE CARLO")
    print(
        "Case | Trades | Backtest Return % | "
        "Median MC % | 5th % | 95th % | "
        "Loss Prob % | Avg DD % | Worst DD %"
    )
    print("-" * 125)

    for (
        label,
        cost_model,
        backtest_result,
        summary,
    ) in cases:
        print(
            f"{label} | "
            f"{len(backtest_result.completed_trade_profits)} | "
            f"{backtest_result.total_return_percent:.2f} | "
            f"{summary.median_return_percent:.2f} | "
            f"{summary.fifth_percentile_return_percent:.2f} | "
            f"{summary.ninety_fifth_percentile_return_percent:.2f} | "
            f"{summary.loss_probability_percent:.2f} | "
            f"{summary.average_drawdown_percent:.2f} | "
            f"{summary.worst_drawdown_percent:.2f}"
        )

        print(
            f"  Costs: slippage="
            f"{cost_model.slippage_percent:.2f}% "
            f"commission="
            f"{cost_model.commission_percent:.2f}% "
            f"minimum_fee="
            f"£{cost_model.minimum_fee:.2f}"
        )

    output_path = (
        "data/"
        "monte_carlo_comparison.csv"
    )

    save_comparison_csv(
        cases=cases,
        output_path=output_path,
    )

    print()
    print(
        f"Saved comparison to "
        f"{output_path}"
    )


if __name__ == "__main__":
    main()