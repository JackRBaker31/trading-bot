from itertools import product

from app.buy_the_dip import BuyTheDipStrategy
from app.entry_filter import EntryFilter
from app.rsi_entry_filter import RsiEntryFilter
from app.strategy_definition import (
    StrategyDefinition,
)


def create_rsi_filters(
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


def generate_buy_the_dip_definitions(
    *,
    drop_thresholds: list[float],
    sma_periods: list[int | None],
    rsi_settings: list[
        tuple[int | None, float | None]
    ],
    cooldown_cycles: list[int],
    target_allocation_percent: float,
) -> list[StrategyDefinition]:
    if not drop_thresholds:
        raise ValueError(
            "At least one drop threshold is required."
        )

    if not sma_periods:
        raise ValueError(
            "At least one SMA period is required."
        )

    if not rsi_settings:
        raise ValueError(
            "At least one RSI setting is required."
        )

    if not cooldown_cycles:
        raise ValueError(
            "At least one cooldown value is required."
        )

    definitions: list[
        StrategyDefinition
    ] = []

    for (
        drop_threshold,
        sma_period,
        rsi_setting,
        cooldown,
    ) in product(
        drop_thresholds,
        sma_periods,
        rsi_settings,
        cooldown_cycles,
    ):
        rsi_period, rsi_buy_threshold = (
            rsi_setting
        )

        name = (
            f"Drop={drop_threshold:g} "
            f"SMA={sma_period} "
            f"RSI={rsi_period}/{rsi_buy_threshold} "
            f"Cooldown={cooldown}"
        )

        definitions.append(
            StrategyDefinition(
                name=name,
                factory=(
                    lambda
                    drop_threshold=drop_threshold,
                    sma_period=sma_period,
                    rsi_period=rsi_period,
                    rsi_buy_threshold=(
                        rsi_buy_threshold
                    ),
                    cooldown=cooldown:
                    BuyTheDipStrategy(
                        drop_threshold_percent=(
                            drop_threshold
                        ),
                        target_allocation_percent=(
                            target_allocation_percent
                        ),
                        cooldown_cycles=cooldown,
                        sma_period=sma_period,
                        entry_filters=(
                            create_rsi_filters(
                                rsi_period=rsi_period,
                                rsi_buy_threshold=(
                                    rsi_buy_threshold
                                ),
                            )
                        ),
                    )
                ),
            )
        )

    return definitions