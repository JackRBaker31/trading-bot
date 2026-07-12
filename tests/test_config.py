import json
from pathlib import Path

import pytest

from app.config import load_config


def write_config(
    file_path: Path,
    data: dict[str, object],
) -> None:
    file_path.write_text(
        json.dumps(data),
        encoding="utf-8",
    )


def valid_config() -> dict[str, object]:
    return {
        "mode": "SIMULATION",
        "market_data_provider": "SIMULATED",
        "starting_cash": 10_000.00,
        "symbols": ["AAPL", "MSFT"],
        "risk": {
            "max_order_value": 2_000.00,
            "max_position_value": 3_000.00,
            "max_portfolio_exposure": 0.50,
            "max_trades_per_session": 3,
        },
        "strategy": {
            "drop_threshold_percent": 2.0,
            "quantity": 5,
            "cooldown_cycles": 2,
        },
        "trading_loop": {
            "cycles": 5,
            "interval_seconds": 1.0,
        },
    }


def test_load_config(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "config.json"

    write_config(
        file_path,
        valid_config(),
    )

    config = load_config(
        str(file_path)
    )

    assert config.mode == "SIMULATION"
    assert config.market_data_provider == "SIMULATED"
    assert config.starting_cash == 10_000.00
    assert config.symbols == ["AAPL", "MSFT"]
    assert config.risk.max_trades_per_session == 3
    assert config.strategy.quantity == 5
    assert config.trading_loop.cycles == 5


def test_symbols_are_cleaned(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "config.json"

    data = valid_config()
    data["symbols"] = [" aapl ", "msft"]

    write_config(
        file_path,
        data,
    )

    config = load_config(
        str(file_path)
    )

    assert config.symbols == ["AAPL", "MSFT"]


def test_invalid_mode_is_rejected(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "config.json"

    data = valid_config()
    data["mode"] = "LIVE"

    write_config(
        file_path,
        data,
    )

    with pytest.raises(
        ValueError,
        match="SIMULATION or PAPER",
    ):
        load_config(
            str(file_path)
        )


def test_empty_symbols_are_rejected(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "config.json"

    data = valid_config()
    data["symbols"] = []

    write_config(
        file_path,
        data,
    )

    with pytest.raises(
        ValueError,
        match="At least one symbol",
    ):
        load_config(
            str(file_path)
        )


def test_missing_file_raises_error(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "missing.json"

    with pytest.raises(
        FileNotFoundError,
    ):
        load_config(
            str(file_path)
        )