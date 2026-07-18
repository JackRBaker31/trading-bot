import pytest

from app.research_setup import (
    STRATEGY_NAME,
    create_research_cost_models,
    create_research_exit_manager,
    create_research_strategy_definition,
)


def test_creates_named_strategy_definition() -> None:
    definition = (
        create_research_strategy_definition(
            target_allocation_percent=25.0,
        )
    )

    assert definition.name == STRATEGY_NAME

    strategy = definition.factory()

    assert strategy is not None


def test_rejects_non_positive_allocation() -> None:
    with pytest.raises(
        ValueError,
        match="Target allocation",
    ):
        create_research_strategy_definition(
            target_allocation_percent=0.0,
        )


def test_creates_gross_and_net_cost_models() -> None:
    models = create_research_cost_models()

    assert models.gross.slippage_percent == 0.0
    assert models.gross.commission_percent == 0.0
    assert models.net.slippage_percent == 0.10
    assert models.net.commission_percent == 0.10


def test_creates_exit_manager() -> None:
    manager = create_research_exit_manager()

    assert manager is not None