from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.config import AppConfig


@dataclass(frozen=True)
class TradingApplicationRequest:
    config_path: str = "config.json"
    require_paper_mode: bool = False

    def __post_init__(self) -> None:
        if not self.config_path.strip():
            raise ValueError(
                "Trading application config path is required."
            )


@dataclass(frozen=True)
class TradingApplicationResult:
    mode: str
    trading_started: bool
    reason: str
    stopped_by_request: bool
    cash: float
    positions: dict[str, int]
    executed_trade_count: int


@dataclass
class TradingApplicationRuntime:
    config: AppConfig
    market_data: Any
    portfolio: Any
    portfolio_store: Any
    position_state_store: Any
    risk_engine: Any
    trade_log: Any
    trading_loop: Any
    prepare_cycle: Callable[[int], None]
    paper_startup_service: Any | None = None
    historical_fill_importer: Any | None = None
    startup_summary_builder: Any | None = None
