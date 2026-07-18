import pytest

from app.buy_the_dip import BuyTheDipStrategy
from app.strategy_grid import (
    generate_buy_the_dip_definitions,
)


def test_generates_all_parameter_combinations() -> None:
    definitions = generate_buy_the_dip_definitions(
        drop_thresholds=[
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
        target_allocation_percent=10.0,
    )

    assert len(definitions) == 16
    assert len(
        {
            definition.name
            for definition in definitions
        }
    ) == 16


def test_factories_keep_their_own_parameters() -> None:
    definitions = generate_buy_the_dip_definitions(
        drop_thresholds=[
            2.0,
            5.0,
        ],
        sma_periods=[
            None,
        ],
        rsi_settings=[
            (None, None),
        ],
        cooldown_cycles=[
            0,
        ],
        target_allocation_percent=10.0,
    )

    first = definitions[0].factory()
    second = definitions[1].factory()

    assert isinstance(
        first,
        BuyTheDipStrategy,
    )
    assert isinstance(
        second,
        BuyTheDipStrategy,
    )
    assert first.drop_threshold_percent == 2.0
    assert second.drop_threshold_percent == 5.0


@pytest.mark.parametrize(
    ("argument_name", "kwargs"),
    [
        (
            "drop threshold",
            {
                "drop_thresholds": [],
                "sma_periods": [None],
                "rsi_settings": [(None, None)],
                "cooldown_cycles": [0],
            },
        ),
        (
            "SMA period",
            {
                "drop_thresholds": [2.0],
                "sma_periods": [],
                "rsi_settings": [(None, None)],
                "cooldown_cycles": [0],
            },
        ),
        (
            "RSI setting",
            {
                "drop_thresholds": [2.0],
                "sma_periods": [None],
                "rsi_settings": [],
                "cooldown_cycles": [0],
            },
        ),
        (
            "cooldown value",
            {
                "drop_thresholds": [2.0],
                "sma_periods": [None],
                "rsi_settings": [(None, None)],
                "cooldown_cycles": [],
            },
        ),
    ],
)
def test_rejects_empty_parameter_dimension(
    argument_name: str,
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(
        ValueError,
        match=argument_name,
    ):
        generate_buy_the_dip_definitions(
            **kwargs,
            target_allocation_percent=10.0,
        )