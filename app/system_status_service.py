import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from app.application_errors import (
    ApplicationError,
    ConfigurationError,
    DataStoreError,
)
from app.config import AppConfig, load_config
from app.news_policy_runtime_factory import (
    NewsPolicyRuntime,
    create_news_policy_runtime,
)
from app.order_journal import OrderJournal
from app.portfolio import Portfolio
from app.portfolio_store import PortfolioStore


@dataclass(frozen=True)
class SystemStatusRequest:
    config_path: str = "config.json"
    portfolio_path: str = "data/portfolio.json"
    order_journal_path: str = "order_journal.jsonl"
    research_report_path: str = "data/research_report.json"
    news_signals_path: str = "data/news_signals.jsonl"
    news_outcomes_path: str = "data/news_signal_outcomes.jsonl"

    def __post_init__(self) -> None:
        for field_name, value in asdict(self).items():
            if not str(value).strip():
                raise ConfigurationError(
                    f"{field_name} is required.",
                    code="SYSTEM_STATUS_PATH_REQUIRED",
                    context={"field": field_name},
                )


@dataclass(frozen=True)
class SystemStatusResult:
    generated_at: str
    application_mode: str
    market_data_provider: str
    configured_symbols: tuple[str, ...]
    real_money_trading_enabled: bool
    paper_trading_enabled: bool
    broker_environment: str
    execution_permission_confirmed: bool
    market_hours_enforced: bool
    news_policy_mode: str
    news_policy_shadow_mode: bool
    news_policy_enforce_mode: bool
    portfolio_exists: bool
    portfolio_starting_cash: float | None
    portfolio_cash: float | None
    position_count: int
    positions: dict[str, int]
    unresolved_order_count: int
    unresolved_order_symbols: tuple[str, ...]
    research_report_exists: bool
    latest_research_report_at: str | None
    news_signal_count: int
    news_outcome_count: int

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


class SystemStatusService:
    def __init__(
        self,
        *,
        config_loader: Callable[[str], AppConfig] = load_config,
        news_policy_runtime_factory: Callable[[], NewsPolicyRuntime] = (
            create_news_policy_runtime
        ),
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._config_loader = config_loader
        self._news_policy_runtime_factory = (
            news_policy_runtime_factory
        )
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )

    def get_status(
        self,
        *,
        request: SystemStatusRequest,
    ) -> SystemStatusResult:
        config = self._load_configuration(request.config_path)
        news_policy_runtime = self._load_news_policy_runtime()
        portfolio = self._load_optional_portfolio(
            request.portfolio_path
        )
        unfinished_orders = self._load_unfinished_orders(
            request.order_journal_path
        )
        latest_research_report_at = (
            self._load_research_report_timestamp(
                request.research_report_path
            )
        )

        return SystemStatusResult(
            generated_at=(
                self._now_provider()
                .astimezone(timezone.utc)
                .isoformat()
            ),
            application_mode=config.mode,
            market_data_provider=(
                config.market_data_provider
            ),
            configured_symbols=tuple(config.symbols),
            real_money_trading_enabled=False,
            paper_trading_enabled=(
                config.paper_trading.enabled
            ),
            broker_environment=(
                config.paper_trading.broker_environment
            ),
            execution_permission_confirmed=(
                config.paper_trading
                .order_execution_permission_confirmed
            ),
            market_hours_enforced=(
                config.market_session
                .enforce_market_hours
            ),
            news_policy_mode=(
                news_policy_runtime.config.mode
            ),
            news_policy_shadow_mode=(
                news_policy_runtime.config.shadow_mode
            ),
            news_policy_enforce_mode=(
                news_policy_runtime.config.enforce_mode
            ),
            portfolio_exists=portfolio is not None,
            portfolio_starting_cash=(
                None
                if portfolio is None
                else portfolio.starting_cash
            ),
            portfolio_cash=(
                None
                if portfolio is None
                else portfolio.cash
            ),
            position_count=(
                0
                if portfolio is None
                else len(portfolio.positions)
            ),
            positions=(
                {}
                if portfolio is None
                else dict(portfolio.positions)
            ),
            unresolved_order_count=len(unfinished_orders),
            unresolved_order_symbols=tuple(
                sorted(
                    {
                        entry.symbol
                        for entry in unfinished_orders
                    }
                )
            ),
            research_report_exists=(
                latest_research_report_at is not None
            ),
            latest_research_report_at=(
                latest_research_report_at
            ),
            news_signal_count=self._count_jsonl_records(
                request.news_signals_path
            ),
            news_outcome_count=self._count_jsonl_records(
                request.news_outcomes_path
            ),
        )

    def _load_configuration(
        self,
        file_path: str,
    ) -> AppConfig:
        try:
            return self._config_loader(file_path)
        except ApplicationError:
            raise
        except Exception as error:
            raise ConfigurationError(
                "System configuration could not be loaded.",
                code="SYSTEM_STATUS_CONFIG_FAILED",
                context={"path": file_path},
            ) from error

    def _load_news_policy_runtime(
        self,
    ) -> NewsPolicyRuntime:
        try:
            return self._news_policy_runtime_factory()
        except ApplicationError:
            raise
        except Exception as error:
            raise ConfigurationError(
                "News policy configuration could not be loaded.",
                code="SYSTEM_STATUS_NEWS_POLICY_FAILED",
            ) from error

    @staticmethod
    def _load_optional_portfolio(
        file_path: str,
    ) -> Portfolio | None:
        path = Path(file_path)

        if not path.exists():
            return None

        try:
            return PortfolioStore(file_path=file_path).load()
        except ApplicationError:
            raise
        except Exception as error:
            raise DataStoreError(
                "Portfolio status could not be loaded.",
                code="SYSTEM_STATUS_PORTFOLIO_FAILED",
                context={"path": file_path},
            ) from error

    @staticmethod
    def _load_unfinished_orders(
        file_path: str,
    ) -> list:
        try:
            return OrderJournal(
                path=file_path
            ).load_unfinished_orders()
        except ApplicationError:
            raise
        except Exception as error:
            raise DataStoreError(
                "Order-journal status could not be loaded.",
                code="SYSTEM_STATUS_JOURNAL_FAILED",
                context={"path": file_path},
            ) from error

    @staticmethod
    def _load_research_report_timestamp(
        file_path: str,
    ) -> str | None:
        path = Path(file_path)

        if not path.exists():
            return None

        try:
            payload = json.loads(
                path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as error:
            raise DataStoreError(
                "Research report status could not be loaded.",
                code="SYSTEM_STATUS_REPORT_FAILED",
                context={"path": file_path},
            ) from error

        if not isinstance(payload, dict):
            raise DataStoreError(
                "Research report must contain a JSON object.",
                code="SYSTEM_STATUS_REPORT_INVALID",
                context={"path": file_path},
            )

        generated_at = payload.get("generated_at")

        if generated_at is None:
            return datetime.fromtimestamp(
                path.stat().st_mtime,
                tz=timezone.utc,
            ).isoformat()

        return str(generated_at)

    @staticmethod
    def _count_jsonl_records(
        file_path: str,
    ) -> int:
        path = Path(file_path)

        if not path.exists():
            return 0

        try:
            with path.open("r", encoding="utf-8") as file:
                return sum(
                    1
                    for line in file
                    if line.strip()
                )
        except OSError as error:
            raise DataStoreError(
                "JSONL status data could not be read.",
                code="SYSTEM_STATUS_JSONL_FAILED",
                context={"path": file_path},
            ) from error