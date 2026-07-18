import logging
from app.config import load_config
from app.csv_historical_data import (
    load_historical_prices_from_csv,
)
from app.risk import RiskLimits
from app.strategy_comparison_report import (
    format_strategy_comparison,
)
from app.strategy_optimizer import (
    StrategyOptimizer,
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

    optimizer = StrategyOptimizer(
        starting_cash=config.starting_cash,
        risk_limits=risk_limits,
    )

    rows = optimizer.optimize(
        historical_prices=historical_prices,
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

    top_rows = rows[:10]

    print(
        format_strategy_comparison(
            top_rows
        )
    )

    print(
        f"\nEvaluated combinations: "
        f"{len(rows)}"
    )


if __name__ == "__main__":
    main()