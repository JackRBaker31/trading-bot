import json

from app.position_state import (
    PositionState,
)
from app.position_state_store import (
    PositionStateStore,
)


def test_missing_file_returns_empty_dict(
    tmp_path,
) -> None:
    store = PositionStateStore(
        file_path=(
            tmp_path
            / "position_states.json"
        )
    )

    assert store.load() == {}


def test_empty_file_returns_empty_dict(
    tmp_path,
) -> None:
    file_path = (
        tmp_path
        / "position_states.json"
    )

    file_path.write_text(
        "",
        encoding="utf-8",
    )

    store = PositionStateStore(
        file_path=file_path
    )

    assert store.load() == {}


def test_saves_and_loads_position_state(
    tmp_path,
) -> None:
    store = PositionStateStore(
        file_path=(
            tmp_path
            / "position_states.json"
        )
    )

    states = {
        "AAPL": PositionState(
            symbol="AAPL",
            quantity=3,
            average_entry_price=234.58,
            highest_price=333.33,
        ),
    }

    store.save(
        states
    )

    loaded = store.load()

    assert loaded == states


def test_saves_and_loads_multiple_positions(
    tmp_path,
) -> None:
    file_path = (
        tmp_path
        / "position_states.json"
    )

    store = PositionStateStore(
        file_path=file_path
    )

    states = {
        "AAPL": PositionState(
            symbol="AAPL",
            quantity=3,
            average_entry_price=234.58,
            highest_price=333.33,
        ),
        "MSFT": PositionState(
            symbol="MSFT",
            quantity=2,
            average_entry_price=391.10,
            highest_price=407.20,
        ),
        "AMZN": PositionState(
            symbol="AMZN",
            quantity=1,
            average_entry_price=248.90,
            highest_price=255.00,
        ),
    }

    store.save(
        states
    )

    loaded = store.load()

    assert loaded == states

    raw_data = json.loads(
        file_path.read_text(
            encoding="utf-8"
        )
    )

    assert set(raw_data) == {
        "AAPL",
        "MSFT",
        "AMZN",
    }