import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RiskConfig:
    max_order_value: float
    max_position_value: float
    max_portfolio_exposure: float
    max_trades_per_session: int


@dataclass(frozen=True)
class StrategyConfig:
    drop_threshold_percent: float
    quantity: int
    cooldown_cycles: int


@dataclass(frozen=True)
class TradingLoopConfig:
    cycles: int
    interval_seconds: float


@dataclass(frozen=True)
class AppConfig:
    mode: str
    starting_cash: float
    symbols: list[str]
    risk: RiskConfig
    strategy: StrategyConfig
    trading_loop: TradingLoopConfig


def load_config(
    file_path: str = "config.json",
) -> AppConfig:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file does not exist: {path}"
        )

    raw_data = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    mode = str(raw_data["mode"]).upper().strip()

    if mode not in {"SIMULATION", "PAPER"}:
        raise ValueError(
            "Mode must be SIMULATION or PAPER."
        )

    starting_cash = float(
        raw_data["starting_cash"]
    )

    if starting_cash <= 0:
        raise ValueError(
            "Starting cash must be positive."
        )

    symbols = [
        str(symbol).upper().strip()
        for symbol in raw_data["symbols"]
    ]

    if not symbols:
        raise ValueError(
            "At least one symbol is required."
        )

    if any(not symbol for symbol in symbols):
        raise ValueError(
            "Symbols cannot be empty."
        )

    risk_data = raw_data["risk"]

    risk = RiskConfig(
        max_order_value=float(
            risk_data["max_order_value"]
        ),
        max_position_value=float(
            risk_data["max_position_value"]
        ),
        max_portfolio_exposure=float(
            risk_data["max_portfolio_exposure"]
        ),
        max_trades_per_session=int(
            risk_data["max_trades_per_session"]
        ),
    )

    strategy_data = raw_data["strategy"]

    strategy = StrategyConfig(
        drop_threshold_percent=float(
            strategy_data["drop_threshold_percent"]
        ),
        quantity=int(
            strategy_data["quantity"]
        ),
        cooldown_cycles=int(
            strategy_data["cooldown_cycles"]
        ),
    )

    trading_loop_data = raw_data["trading_loop"]

    trading_loop = TradingLoopConfig(
        cycles=int(
            trading_loop_data["cycles"]
        ),
        interval_seconds=float(
            trading_loop_data["interval_seconds"]
        ),
    )

    return AppConfig(
        mode=mode,
        starting_cash=starting_cash,
        symbols=symbols,
        risk=risk,
        strategy=strategy,
        trading_loop=trading_loop,
    )