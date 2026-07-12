import json
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RiskConfig:
    max_order_value: float
    max_position_value: float
    max_portfolio_exposure: float
    max_trades_per_session: int


@dataclass(frozen=True)
class StrategyConfig:
    drop_threshold_percent: float
    target_allocation_percent: float
    cooldown_cycles: int


@dataclass(frozen=True)
class TradingLoopConfig:
    cycles: int
    interval_seconds: float

@dataclass(frozen=True)
class MarketSessionConfig:
    enforce_market_hours: bool
    timezone: str
    opening_time: str
    closing_time: str
    trading_weekdays: list[int]

@dataclass(frozen=True)
class AppConfig:
    mode: str
    market_data_provider: str
    starting_cash: float
    symbols: list[str]
    risk: RiskConfig
    strategy: StrategyConfig
    trading_loop: TradingLoopConfig
    market_session: MarketSessionConfig


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
    
    market_data_provider = str(
        raw_data["market_data_provider"]
    ).upper().strip()

    if market_data_provider not in {
        "SIMULATED",
        "TWELVE_DATA",
    }:
        raise ValueError(
            "Market-data provider must be "
            "SIMULATED or TWELVE_DATA."
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
        target_allocation_percent=float(
            strategy_data[
                "target_allocation_percent"
            ]
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

    market_session_data = raw_data[
    "market_session"
]

    market_session = MarketSessionConfig(
        enforce_market_hours=bool(
            market_session_data[
                "enforce_market_hours"
            ]
        ),
        timezone=str(
            market_session_data["timezone"]
        ).strip(),
        opening_time=str(
            market_session_data["opening_time"]
        ).strip(),
        closing_time=str(
            market_session_data["closing_time"]
        ).strip(),
        trading_weekdays=[
            int(weekday)
            for weekday in market_session_data[
                "trading_weekdays"
            ]
        ],
    )

    config = AppConfig(
        mode=mode,
        market_data_provider=market_data_provider,
        starting_cash=starting_cash,
        symbols=symbols,
        risk=risk,
        strategy=strategy,
        trading_loop=trading_loop,
        market_session=market_session,
    )

    logger.info(
        "configuration_loaded file=%s mode=%s "
        "market_data_provider=%s symbols=%s "
        "starting_cash=%.2f",
        path,
        config.mode,
        config.market_data_provider,
        ",".join(config.symbols),
        config.starting_cash,
    )

    return config