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
            "target_allocation_percent": 10.0,
            "cooldown_cycles": 2,
        },
        "trading_loop": {
            "cycles": 5,
            "interval_seconds": 1.0,
        },
        "market_session": {
            "enforce_market_hours": False,
            "timezone": "America/New_York",
            "opening_time": "09:30",
            "closing_time": "16:00",
            "trading_weekdays": [
                0,
                1,
                2,
                3,
                4,
            ],
        },
        "paper_trading": {
            "enabled": False,
            "broker_environment": "DEMO",
            "order_execution_permission_confirmed": False,
        }
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
    assert (
    config.strategy.target_allocation_percent
    == 10.0
)
    assert config.trading_loop.cycles == 5
    assert (
    config.market_session.enforce_market_hours
    is False
    )

    assert (
        config.market_session.timezone
        == "America/New_York"
    )

    assert (
        config.market_session.opening_time
        == "09:30"
    )

    assert config.paper_trading.enabled is False
    assert (
        config.paper_trading.broker_environment
        == "DEMO"
    )

    assert (
        config.paper_trading
        .order_execution_permission_confirmed
        is False
    )

    assert config.strategy.sma_period is None
    assert config.strategy.rsi_period is None
    assert (
        config.strategy.rsi_buy_threshold
        is None
    )


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

def test_invalid_paper_trading_environment_is_rejected(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "config.json"

    data = valid_config()
    data["paper_trading"] = {
        "enabled": False,
        "broker_environment": "UNKNOWN",
        "order_execution_permission_confirmed": False,
    }

    write_config(
        file_path,
        data,
    )

    with pytest.raises(
        ValueError,
        match="DEMO or LIVE",
    ):
        load_config(
            str(file_path)
        )
def test_enabled_paper_trading_rejects_live_environment(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "config.json"

    data = valid_config()
    data["paper_trading"] = {
        "enabled": True,
        "broker_environment": "LIVE",
        "order_execution_permission_confirmed": False,
    }

    write_config(
        file_path,
        data,
    )

    with pytest.raises(
        ValueError,
        match="only be enabled",
    ):
        load_config(
            str(file_path)
    )
def test_config_allows_continuous_trading_loop(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "config.json"

    data = valid_config()
    data["trading_loop"] = {
        "cycles": None,
        "interval_seconds": 60.0,
    }

    write_config(
        file_path,
        data,
    )

    config = load_config(
        str(file_path)
    )

    assert config.trading_loop.cycles is None

def test_config_rejects_non_positive_cycles(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "config.json"

    data = valid_config()
    data["trading_loop"] = {
        "cycles": 0,
        "interval_seconds": 60.0,
    }

    write_config(
        file_path,
        data,
    )

    with pytest.raises(
        ValueError,
        match="cycles",
    ):
        load_config(
            str(file_path)
        )

def test_loads_optional_indicator_strategy_config(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "config.json"

    data = valid_config()
    strategy_data = data["strategy"]

    assert isinstance(
        strategy_data,
        dict,
    )

    strategy_data["sma_period"] = 20
    strategy_data["rsi_period"] = 14
    strategy_data["rsi_buy_threshold"] = 30.0

    write_config(
        file_path,
        data,
    )

    config = load_config(
        str(file_path)
    )

    assert config.strategy.sma_period == 20
    assert config.strategy.rsi_period == 14
    assert (
        config.strategy.rsi_buy_threshold
        == 30.0
    )