import logging

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

    execution_cost_model = ExecutionCostModel(
        slippage_percent=0.10,
        commission_percent=0.10,
        minimum_fee=0.0,
    )

    runner = StrategyComparisonRunner(
        starting_cash=config.starting_cash,
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
                        config.strategy
                        .target_allocation_percent
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
            "The selected strategy produced no "
            "completed trades, so Monte Carlo "
            "simulation cannot run."
        )

    simulator = MonteCarloSimulator()

    simulations = (
        simulator.run_from_trade_profits(
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

    print("MONTE CARLO RESULTS")
    print(
        f"Strategy: {strategy_name}"
    )
    print(
        f"Completed trades: "
        f"{len(trade_profits)}"
    )
    print(
        f"Simulations: "
        f"{summary.simulation_count}"
    )
    print()
    print(
        f"Average return: "
        f"{summary.average_return_percent:.2f}%"
    )
    print(
        f"Median return: "
        f"{summary.median_return_percent:.2f}%"
    )
    print(
        f"5th percentile return: "
        f"{summary.fifth_percentile_return_percent:.2f}%"
    )
    print(
        f"95th percentile return: "
        f"{summary.ninety_fifth_percentile_return_percent:.2f}%"
    )
    print(
        f"Worst return: "
        f"{summary.worst_return_percent:.2f}%"
    )
    print(
        f"Best return: "
        f"{summary.best_return_percent:.2f}%"
    )
    print(
        f"Average drawdown: "
        f"{summary.average_drawdown_percent:.2f}%"
    )
    print(
        f"Worst drawdown: "
        f"{summary.worst_drawdown_percent:.2f}%"
    )
    print(
        f"Probability of loss: "
        f"{summary.loss_probability_percent:.2f}%"
    )
    print(
        f"Slippage: "
        f"{execution_cost_model.slippage_percent:.2f}%"
    )
    print(
        f"Commission: "
        f"{execution_cost_model.commission_percent:.2f}%"
    )
    print(
        f"Minimum fee: "
        f"£{execution_cost_model.minimum_fee:.2f}"
    )


if __name__ == "__main__":
    main()