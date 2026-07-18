import logging
from types import SimpleNamespace

from app.config import load_config
from app.csv_historical_data import (
    load_historical_prices_from_csv,
)
from app.monte_carlo import (
    MonteCarloSimulator,
)
from app.monte_carlo_summary import (
    summarize_monte_carlo_results,
)
from app.research_report import (
    save_research_report_csv,
    save_research_report_json,
)
from app.research_report_builder import (
    build_research_report,
)
from app.research_setup import (
    STRATEGY_NAME,
    create_research_cost_models,
    create_research_exit_manager,
    create_research_strategy_definition,
)
from app.risk import RiskLimits
from app.rolling_walk_forward_optimizer import (
    RollingWalkForwardOptimizer,
)
from app.rolling_walk_forward_summary import (
    summarize_rolling_results,
)
from app.strategy_comparison_runner import (
    StrategyComparisonRunner,
)
from app.walk_forward_optimizer import (
    WalkForwardOptimizer,
)
from app.research_charts import (
    save_drawdown_chart,
    save_equity_curve_chart,
    save_monte_carlo_histogram,
    save_rolling_returns_chart,
)


def run_backtest_case(
    *,
    historical_prices,
    starting_cash: float,
    risk_limits: RiskLimits,
    target_allocation_percent: float,
    execution_cost_model,
):
    runner = StrategyComparisonRunner(
        starting_cash=starting_cash,
        risk_limits=risk_limits,
        position_exit_manager=(
            create_research_exit_manager()
        ),
        execution_cost_model=(
            execution_cost_model
        ),
    )

    _, results = runner.run(
        historical_prices=historical_prices,
        strategy_definitions=[
            create_research_strategy_definition(
                target_allocation_percent=(
                    target_allocation_percent
                )
            )
        ],
    )

    return results[STRATEGY_NAME]


def summarize_trade_profits(
    *,
    starting_equity: float,
    trade_profits: list[float],
):
    if not trade_profits:
        raise RuntimeError(
            "The research strategy produced no "
            "completed trades."
        )

    simulations = (
        MonteCarloSimulator()
        .run_from_trade_profits(
            starting_equity=starting_equity,
            trade_profits=trade_profits,
            simulation_count=1_000,
            random_seed=12345,
        )
    )

    return (
        simulations,
        summarize_monte_carlo_results(
            simulations
        ),
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

    if not historical_prices:
        raise RuntimeError(
            "No research prices were loaded."
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

    target_allocation_percent = (
        config.strategy
        .target_allocation_percent
    )

    cost_models = (
        create_research_cost_models()
    )

    gross_backtest_result = run_backtest_case(
        historical_prices=historical_prices,
        starting_cash=config.starting_cash,
        risk_limits=risk_limits,
        target_allocation_percent=(
            target_allocation_percent
        ),
        execution_cost_model=(
            cost_models.gross
        ),
    )

    net_backtest_result = run_backtest_case(
        historical_prices=historical_prices,
        starting_cash=config.starting_cash,
        risk_limits=risk_limits,
        target_allocation_percent=(
            target_allocation_percent
        ),
        execution_cost_model=(
            cost_models.net
        ),
    )

    (
        gross_monte_carlo_simulations,
        gross_monte_carlo_summary,
    ) = summarize_trade_profits(
        starting_equity=(
            gross_backtest_result
            .starting_cash
        ),
        trade_profits=(
            gross_backtest_result
            .completed_trade_profits
        ),
    )

    (
        net_monte_carlo_simulations,
        net_monte_carlo_summary,
    ) = summarize_trade_profits(
        starting_equity=(
            net_backtest_result
            .starting_cash
        ),
        trade_profits=(
            net_backtest_result
            .completed_trade_profits
        ),
    )

    walk_forward_optimizer = (
        WalkForwardOptimizer(
            starting_cash=config.starting_cash,
            risk_limits=risk_limits,
        )
    )

    (
        walk_forward_training_result,
        walk_forward_validation_result,
    ) = walk_forward_optimizer.run(
        historical_prices=historical_prices,
        training_fraction=0.8,
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
            target_allocation_percent
        ),
    )

    rolling_optimizer = (
        RollingWalkForwardOptimizer(
            starting_cash=config.starting_cash,
            risk_limits=risk_limits,
        )
    )

    rolling_results = rolling_optimizer.run(
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
            target_allocation_percent
        ),
    )

    rolling_summary = (
        summarize_rolling_results(
            rolling_results
        )
    )

    report = build_research_report(
        strategy_name=STRATEGY_NAME,
        gross_backtest_result=(
            gross_backtest_result
        ),
        net_backtest_result=(
            net_backtest_result
        ),
        gross_monte_carlo_summary=(
            gross_monte_carlo_summary
        ),
        net_monte_carlo_summary=(
            net_monte_carlo_summary
        ),
        net_cost_model=cost_models.net,
        walk_forward_result=SimpleNamespace(
            training_result=(
                walk_forward_training_result
            ),
            validation_result=(
                walk_forward_validation_result
            ),
        ),
        rolling_summary=rolling_summary,
    )

    json_path = (
        "data/research_report.json"
    )
    csv_path = (
        "data/research_report.csv"
    )

    save_research_report_json(
        report=report,
        output_path=json_path,
    )

    save_research_report_csv(
        report=report,
        output_path=csv_path,
    )

    equity_curve_path = (
        "data/equity_curve.png"
    )
    drawdown_path = (
        "data/drawdown.png"
    )
    monte_carlo_path = (
        "data/monte_carlo_histogram.png"
    )
    rolling_returns_path = (
        "data/rolling_returns.png"
    )

    save_equity_curve_chart(
        equity_curve=(
            net_backtest_result.equity_curve
        ),
        output_path=equity_curve_path,
    )

    save_drawdown_chart(
        equity_curve=(
            net_backtest_result.equity_curve
        ),
        output_path=drawdown_path,
    )

    save_monte_carlo_histogram(
        simulations=(
            net_monte_carlo_simulations
        ),
        output_path=monte_carlo_path,
    )

    save_rolling_returns_chart(
        results=rolling_results,
        output_path=rolling_returns_path,
    )

    print("RESEARCH REPORT")
    print(
        f"Strategy: {report.strategy_name}"
    )
    print()

    print("DECISION")
    print(
        f"Verdict: {report.verdict}"
    )
    print(
        f"Checks passed: "
        f"{report.passed_check_count}/"
        f"{report.total_check_count}"
    )

    for reason in report.decision_reasons:
        print(
            f"- {reason}"
        )

    print()

    print("BACKTEST")
    print(
        f"Gross return: "
        f"{report.gross_backtest_return_percent:.2f}%"
    )
    print(
        f"Net return: "
        f"{report.net_backtest_return_percent:.2f}%"
    )
    print(
        f"Completed trades: "
        f"{report.net_completed_trades}"
    )
    print()
    print("MONTE CARLO")
    print(
        f"Net median return: "
        f"{report.net_monte_carlo_median_percent:.2f}%"
    )
    print(
        f"Net 5th percentile: "
        f"{report.net_fifth_percentile_percent:.2f}%"
    )
    print(
        f"Net loss probability: "
        f"{report.net_loss_probability_percent:.2f}%"
    )
    print(
        f"Net worst drawdown: "
        f"{report.net_worst_drawdown_percent:.2f}%"
    )
    print()
    print("WALK FORWARD")
    print(
        f"Training return: "
        f"{report.walk_forward_training_return_percent:.2f}%"
    )
    print(
        f"Validation return: "
        f"{report.walk_forward_validation_return_percent:.2f}%"
    )
    print()
    print("ROLLING VALIDATION")
    print(
        f"Windows: "
        f"{report.rolling_window_count}"
    )
    print(
        f"Positive windows: "
        f"{report.rolling_positive_window_percent:.2f}%"
    )
    print(
        f"Average return: "
        f"{report.rolling_average_return_percent:.2f}%"
    )
    print(
        f"Worst return: "
        f"{report.rolling_worst_return_percent:.2f}%"
    )
    print()
    print(
        f"Saved JSON report to {json_path}"
    )
    print(
        f"Saved CSV report to {csv_path}"
    )
    print(
        f"Saved equity chart to "
        f"{equity_curve_path}"
    )
    print(
        f"Saved drawdown chart to "
        f"{drawdown_path}"
    )
    print(
        f"Saved Monte Carlo chart to "
        f"{monte_carlo_path}"
    )
    print(
        f"Saved rolling returns chart to "
        f"{rolling_returns_path}"
    )


if __name__ == "__main__":
    main()