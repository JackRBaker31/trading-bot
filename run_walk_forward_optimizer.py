import logging

from app.config import load_config
from app.csv_historical_data import (
    load_historical_prices_from_csv,
)
from app.risk import RiskLimits
from app.walk_forward_optimizer import (
    WalkForwardOptimizer,
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

    optimizer = WalkForwardOptimizer(
        starting_cash=config.starting_cash,
        risk_limits=risk_limits,
    )

    training_row, validation_row = (
        optimizer.run(
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
                config.strategy
                .target_allocation_percent
            ),
        )
    )

    print("TRAINING WINNER")
    print(
        f"{training_row.name} | "
        f"Trades={training_row.executed_trades} | "
        f"Return={training_row.total_return_percent:.2f}% | "
        f"Drawdown={training_row.maximum_drawdown_percent:.2f}% | "
        f"Calmar={training_row.calmar_ratio:.2f}"
    )

    print()

    print("VALIDATION RESULT")
    print(
        f"{validation_row.name} | "
        f"Trades={validation_row.executed_trades} | "
        f"Return={validation_row.total_return_percent:.2f}% | "
        f"Drawdown={validation_row.maximum_drawdown_percent:.2f}% | "
        f"Calmar={validation_row.calmar_ratio:.2f}"
    )


if __name__ == "__main__":
    main()