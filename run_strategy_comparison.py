from app.buy_the_dip import BuyTheDipStrategy
from app.config import load_config
from app.csv_historical_data import (
    load_historical_prices_from_csv,
)
from app.entry_filter import EntryFilter
from app.risk import RiskLimits
from app.rsi_entry_filter import RsiEntryFilter
from app.strategy_comparison_report import (
    format_strategy_comparison,
)
from app.strategy_comparison_runner import (
    StrategyComparisonRunner,
)
from app.strategy_definition import (
    StrategyDefinition,
)


def create_entry_filters(
    *,
    rsi_period: int | None,
    rsi_buy_threshold: float | None,
) -> list[EntryFilter]:
    if (
        rsi_period is None
        or rsi_buy_threshold is None
    ):
        return []

    return [
        RsiEntryFilter(
            period=rsi_period,
            buy_threshold=rsi_buy_threshold,
        )
    ]


def main() -> None:
    config = load_config()

    historical_prices = (
        load_historical_prices_from_csv(
            file_path="data/sample_prices.csv"
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

    runner = StrategyComparisonRunner(
        starting_cash=config.starting_cash,
        risk_limits=risk_limits,
    )

    rows, _ = runner.run(
        historical_prices=historical_prices,
        strategy_definitions=[
            StrategyDefinition(
                name="Baseline",
                factory=(
                    lambda: BuyTheDipStrategy(
                        drop_threshold_percent=(
                            config.strategy
                            .drop_threshold_percent
                        ),
                        target_allocation_percent=(
                            config.strategy
                            .target_allocation_percent
                        ),
                        cooldown_cycles=(
                            config.strategy
                            .cooldown_cycles
                        ),
                    )
                ),
            ),
            StrategyDefinition(
                name="SMA 3",
                factory=(
                    lambda: BuyTheDipStrategy(
                        drop_threshold_percent=(
                            config.strategy
                            .drop_threshold_percent
                        ),
                        target_allocation_percent=(
                            config.strategy
                            .target_allocation_percent
                        ),
                        cooldown_cycles=(
                            config.strategy
                            .cooldown_cycles
                        ),
                        sma_period=3,
                    )
                ),
            ),
            StrategyDefinition(
                name="RSI 3",
                factory=(
                    lambda: BuyTheDipStrategy(
                        drop_threshold_percent=(
                            config.strategy
                            .drop_threshold_percent
                        ),
                        target_allocation_percent=(
                            config.strategy
                            .target_allocation_percent
                        ),
                        cooldown_cycles=(
                            config.strategy
                            .cooldown_cycles
                        ),
                        entry_filters=(
                            create_entry_filters(
                                rsi_period=3,
                                rsi_buy_threshold=30.0,
                            )
                        ),
                    )
                ),
            ),
            StrategyDefinition(
                name="SMA 3 + RSI 3",
                factory=(
                    lambda: BuyTheDipStrategy(
                        drop_threshold_percent=(
                            config.strategy
                            .drop_threshold_percent
                        ),
                        target_allocation_percent=(
                            config.strategy
                            .target_allocation_percent
                        ),
                        cooldown_cycles=(
                            config.strategy
                            .cooldown_cycles
                        ),
                        sma_period=3,
                        entry_filters=(
                            create_entry_filters(
                                rsi_period=3,
                                rsi_buy_threshold=30.0,
                            )
                        ),
                    )
                ),
            ),
        ],
    )
    print(
        format_strategy_comparison(
            rows
        )
    )


if __name__ == "__main__":
    main()