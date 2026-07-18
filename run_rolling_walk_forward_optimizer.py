import logging

from app.config import load_config
from app.csv_historical_data import (
    load_historical_prices_from_csv,
)
from app.risk import RiskLimits
from app.rolling_walk_forward_optimizer import (
    RollingWalkForwardOptimizer,
)
from app.rolling_walk_forward_summary import (
    summarize_rolling_results,
)
from app.strategy_grid import (
    generate_buy_the_dip_definitions,
)
from app.strategy_robustness import (
    rank_strategy_robustness,
)
from app.strategy_validation_matrix import (
    StrategyValidationMatrix,
)
from app.strategy_validation_summary import (
    summarize_strategy_validation,
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

    optimizer = RollingWalkForwardOptimizer(
        starting_cash=config.starting_cash,
        risk_limits=risk_limits,
    )

    results = optimizer.run(
        historical_prices=historical_prices,
        training_size=250,
        validation_size=50,
        step_size=50,
        drop_thresholds=[
            1.0,
            2.0,
            3.0,
        ],
        sma_periods=[
            None,
            3,
        ],
        rsi_settings=[
            (None, None),
            (3, 30.0),
        ],
        cooldown_cycles=[
            0,
            2,
        ],
        target_allocation_percent=(
            config.strategy
            .target_allocation_percent
        ),
    )

    print(
        "ROLLING WALK-FORWARD RESULTS"
    )
    print(
        "Window | Strategy | Trades | "
        "Return % | Drawdown % | Calmar"
    )
    print("-" * 100)

    for result in results:
        validation = result.validation_result

        print(
            f"{result.window_number} | "
            f"{validation.name} | "
            f"{validation.executed_trades} | "
            f"{validation.total_return_percent:.2f} | "
            f"{validation.maximum_drawdown_percent:.2f} | "
            f"{validation.calmar_ratio:.2f}"
        )

    summary = summarize_rolling_results(
        results
    )

    print()
    print("AGGREGATE VALIDATION")
    print(
        f"Windows: {summary.window_count}"
    )
    print(
        f"Positive windows: "
        f"{summary.positive_window_count} "
        f"({summary.positive_window_percent:.2f}%)"
    )
    print(
        f"Average return: "
        f"{summary.average_return_percent:.2f}%"
    )
    print(
        f"Median return: "
        f"{summary.median_return_percent:.2f}%"
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

    robustness_rows = (
        rank_strategy_robustness(
            results
        )
    )

    print()
    print("STRATEGY ROBUSTNESS")
    print(
        "Strategy | Selected | Positive % | "
        "Average % | Median % | Worst % | "
        "Best % | Avg Drawdown %"
    )
    print("-" * 140)

    for row in robustness_rows:
        print(
            f"{row.name} | "
            f"{row.selected_window_count} | "
            f"{row.positive_window_percent:.2f} | "
            f"{row.average_return_percent:.2f} | "
            f"{row.median_return_percent:.2f} | "
            f"{row.worst_return_percent:.2f} | "
            f"{row.best_return_percent:.2f} | "
            f"{row.average_drawdown_percent:.2f}"
        )

    definitions = (
        generate_buy_the_dip_definitions(
            drop_thresholds=[
                1.0,
                2.0,
                3.0,
            ],
            sma_periods=[
                None,
                3,
            ],
            rsi_settings=[
                (None, None),
                (3, 30.0),
            ],
            cooldown_cycles=[
                0,
                2,
            ],
            target_allocation_percent=(
                config.strategy
                .target_allocation_percent
            ),
        )
    )

    validation_matrix = (
        StrategyValidationMatrix(
            starting_cash=config.starting_cash,
            risk_limits=risk_limits,
        )
    )

    matrix_results = validation_matrix.run(
        historical_prices=historical_prices,
        strategy_definitions=definitions,
        training_size=250,
        validation_size=50,
        step_size=50,
    )

    validation_summary = (
        summarize_strategy_validation(
            matrix_results
        )
    )

    print()
    print("FULL VALIDATION MATRIX")
    print(
        "Strategy | Windows | Positive % | "
        "Average % | Median % | Worst % | "
        "Best % | Avg Drawdown %"
    )
    print("-" * 140)

    for row in validation_summary[:10]:
        print(
            f"{row.name} | "
            f"{row.window_count} | "
            f"{row.positive_window_percent:.2f} | "
            f"{row.average_return_percent:.2f} | "
            f"{row.median_return_percent:.2f} | "
            f"{row.worst_return_percent:.2f} | "
            f"{row.best_return_percent:.2f} | "
            f"{row.average_drawdown_percent:.2f}"
        )


if __name__ == "__main__":
    main()