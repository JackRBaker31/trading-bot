from dataclasses import dataclass

from app.buy_the_dip import BuyTheDipStrategy
from app.execution_cost import ExecutionCostModel
from app.position_exit_manager import (
    PositionExitManager,
)
from app.position_exit_policy import (
    PositionExitPolicy,
)
from app.rsi_entry_filter import RsiEntryFilter
from app.strategy_definition import (
    StrategyDefinition,
)


STRATEGY_NAME = (
    "Drop=3 SMA=None "
    "RSI=3/30 Cooldown=0"
)


@dataclass(frozen=True)
class ResearchCostModels:
    gross: ExecutionCostModel
    net: ExecutionCostModel


def create_research_strategy_definition(
    *,
    target_allocation_percent: float,
) -> StrategyDefinition:
    if target_allocation_percent <= 0:
        raise ValueError(
            "Target allocation percentage "
            "must be positive."
        )

    return StrategyDefinition(
        name=STRATEGY_NAME,
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


def create_research_exit_manager(
) -> PositionExitManager:
    return PositionExitManager(
        policy=PositionExitPolicy(
            stop_loss_percent=5.0,
            take_profit_percent=10.0,
            trailing_stop_percent=4.0,
            trailing_activation_percent=6.0,
        )
    )


def create_research_cost_models(
) -> ResearchCostModels:
    return ResearchCostModels(
        gross=ExecutionCostModel(),
        net=ExecutionCostModel(
            slippage_percent=0.10,
            commission_percent=0.10,
            minimum_fee=0.0,
        ),
    )