import pytest

from app.position_exit_policy import (
    PositionExitDecision,
    PositionExitPolicy,
)
from app.position_state import (
    PositionState,
)


def test_triggers_stop_loss() -> None:
    policy = PositionExitPolicy(
        stop_loss_percent=5.0,
        take_profit_percent=10.0,
        trailing_stop_percent=4.0,
        trailing_activation_percent=8.0,
    )

    position = PositionState(
        symbol="AAPL",
        quantity=3,
        average_entry_price=100.00,
    )

    decision = policy.evaluate(
        position=position,
        current_price=94.00,
    )

    assert decision.should_exit
    assert decision.reason == "STOP_LOSS"


def test_triggers_take_profit() -> None:
    policy = PositionExitPolicy(
        stop_loss_percent=5.0,
        take_profit_percent=10.0,
        trailing_stop_percent=4.0,
        trailing_activation_percent=8.0,
    )

    position = PositionState(
        symbol="AAPL",
        quantity=3,
        average_entry_price=100.00,
    )

    decision = policy.evaluate(
        position=position,
        current_price=111.00,
    )

    assert decision.should_exit
    assert decision.reason == "TAKE_PROFIT"


def test_triggers_trailing_stop() -> None:
    policy = PositionExitPolicy(
        stop_loss_percent=5.0,
        take_profit_percent=20.0,
        trailing_stop_percent=4.0,
        trailing_activation_percent=8.0,
    )

    position = PositionState(
        symbol="AAPL",
        quantity=3,
        average_entry_price=100.00,
        highest_price=120.00,
    )

    decision = policy.evaluate(
        position=position,
        current_price=114.00,
    )

    assert decision.should_exit
    assert decision.reason == "TRAILING_STOP"


def test_holds_when_no_exit_rule_matches() -> None:
    policy = PositionExitPolicy(
        stop_loss_percent=5.0,
        take_profit_percent=10.0,
        trailing_stop_percent=4.0,
        trailing_activation_percent=8.0,
    )

    position = PositionState(
        symbol="AAPL",
        quantity=3,
        average_entry_price=100.00,
        highest_price=105.00,
    )

    decision = policy.evaluate(
        position=position,
        current_price=103.00,
    )

    assert not decision.should_exit
    assert decision.reason == "HOLD"


@pytest.mark.parametrize(
    (
        "stop_loss_percent",
        "take_profit_percent",
        "trailing_stop_percent",
    ),
    [
        (0.0, 10.0, 4.0),
        (-1.0, 10.0, 4.0),
        (5.0, 0.0, 4.0),
        (5.0, -1.0, 4.0),
        (5.0, 10.0, 0.0),
        (5.0, 10.0, -1.0),
    ],
)
def test_rejects_invalid_thresholds(
    stop_loss_percent: float,
    take_profit_percent: float,
    trailing_stop_percent: float,
) -> None:
    with pytest.raises(
        ValueError
    ):
        PositionExitPolicy(
            stop_loss_percent=(
                stop_loss_percent
            ),
            take_profit_percent=(
                take_profit_percent
            ),
            trailing_stop_percent=(
                trailing_stop_percent
            ),
            trailing_activation_percent=8.0,
        )

def test_rejects_invalid_current_price() -> None:
    policy = PositionExitPolicy(
        stop_loss_percent=5.0,
        take_profit_percent=10.0,
        trailing_stop_percent=4.0,
        trailing_activation_percent=8.0,
    )

    position = PositionState(
        symbol="AAPL",
        quantity=1,
        average_entry_price=100.00,
    )

    with pytest.raises(
        ValueError,
        match="Current price",
    ):
        policy.evaluate(
            position=position,
            current_price=0.00,
        )
        
def test_trailing_stop_waits_for_activation_gain() -> None:
    policy = PositionExitPolicy(
        stop_loss_percent=5.0,
        take_profit_percent=20.0,
        trailing_stop_percent=4.0,
        trailing_activation_percent=8.0,
    )

    position = PositionState(
        symbol="AAPL",
        quantity=3,
        average_entry_price=100.00,
        highest_price=105.00,
    )

    decision = policy.evaluate(
        position=position,
        current_price=100.50,
    )

    assert not decision.should_exit
    assert decision.reason == "HOLD"