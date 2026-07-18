import pytest

from app.buy_the_dip import BuyTheDipStrategy
from app.strategy_definition import (
    StrategyDefinition,
)


def test_creates_strategy_definition() -> None:
    definition = StrategyDefinition(
        name="Baseline",
        factory=lambda: BuyTheDipStrategy(),
    )

    assert definition.name == "Baseline"
    assert isinstance(
        definition.factory(),
        BuyTheDipStrategy,
    )


def test_trims_strategy_name() -> None:
    definition = StrategyDefinition(
        name="  SMA  ",
        factory=lambda: BuyTheDipStrategy(),
    )

    assert definition.name == "SMA"


def test_rejects_empty_strategy_name() -> None:
    with pytest.raises(
        ValueError,
        match="Strategy name is required",
    ):
        StrategyDefinition(
            name="   ",
            factory=lambda: BuyTheDipStrategy(),
        )