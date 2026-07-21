from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from app.application_errors import (
    ApplicationError,
    ConfigurationError,
    DataStoreError,
)
from app.config import AppConfig, load_config
from app.order_journal import (
    OrderJournal,
    OrderJournalEntry,
)
from app.portfolio import Portfolio
from app.portfolio_store import PortfolioStore
from app.run_history import RunHistoryRecord, RunType
from app.run_history_repository import (
    RunHistoryRepository,
)


@dataclass(frozen=True)
class OperationsQueryRequest:
    config_path: str = "config.json"
    portfolio_path: str = "data/portfolio.json"
    order_journal_path: str = "order_journal.jsonl"
    application_database_path: str = "data/application.db"

    def __post_init__(self) -> None:
        for field_name, value in asdict(self).items():
            if not str(value).strip():
                raise ConfigurationError(
                    f"{field_name} is required.",
                    code="OPERATIONS_PATH_REQUIRED",
                    context={"field": field_name},
                )


@dataclass(frozen=True)
class PositionView:
    symbol: str
    quantity: int

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PortfolioView:
    available: bool
    starting_cash: float | None
    cash: float | None
    position_count: int
    positions: tuple[PositionView, ...]
    applied_broker_order_count: int

    def to_dictionary(self) -> dict[str, object]:
        return {
            "available": self.available,
            "starting_cash": self.starting_cash,
            "cash": self.cash,
            "position_count": self.position_count,
            "positions": [
                position.to_dictionary()
                for position in self.positions
            ],
            "applied_broker_order_count": (
                self.applied_broker_order_count
            ),
            "valuation_available": False,
            "valuation_note": (
                "Current market valuation is not "
                "loaded by this offline endpoint."
            ),
        }


@dataclass(frozen=True)
class OrderPage:
    total_count: int
    offset: int
    limit: int
    items: tuple[OrderJournalEntry, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "total_count": self.total_count,
            "offset": self.offset,
            "limit": self.limit,
            "count": len(self.items),
            "items": [
                {
                    "timestamp": entry.timestamp,
                    "reservation_key": (
                        entry.reservation_key
                    ),
                    "event": entry.event,
                    "symbol": entry.symbol,
                    "side": entry.side,
                    "quantity": entry.quantity,
                    "broker_order_id": (
                        entry.broker_order_id
                    ),
                    "reason": entry.reason,
                }
                for entry in self.items
            ],
        }


@dataclass(frozen=True)
class RiskStatusView:
    max_order_value: float
    max_position_value: float
    max_portfolio_exposure_ratio: float
    max_portfolio_exposure_value: float
    max_trades_per_session: int
    approved_symbols: tuple[str, ...]
    paper_trading_enabled: bool
    broker_environment: str
    execution_permission_confirmed: bool
    real_money_trading_enabled: bool

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ReconciliationStatusView:
    available: bool
    latest_run: RunHistoryRecord | None
    unresolved_order_count: int
    safe_to_start: bool

    def to_dictionary(self) -> dict[str, object]:
        return {
            "available": self.available,
            "latest_run": (
                None
                if self.latest_run is None
                else self.latest_run.to_dictionary()
            ),
            "unresolved_order_count": (
                self.unresolved_order_count
            ),
            "safe_to_start": self.safe_to_start,
        }


class OperationsQueryService:
    def __init__(
        self,
        *,
        config_loader: Callable[[str], AppConfig] = (
            load_config
        ),
    ) -> None:
        self._config_loader = config_loader

    def get_portfolio(
        self,
        *,
        request: OperationsQueryRequest = (
            OperationsQueryRequest()
        ),
    ) -> PortfolioView:
        portfolio = self._load_optional_portfolio(
            request.portfolio_path
        )

        if portfolio is None:
            return PortfolioView(
                available=False,
                starting_cash=None,
                cash=None,
                position_count=0,
                positions=(),
                applied_broker_order_count=0,
            )

        positions = tuple(
            PositionView(
                symbol=symbol,
                quantity=quantity,
            )
            for symbol, quantity in sorted(
                portfolio.positions.items()
            )
        )

        return PortfolioView(
            available=True,
            starting_cash=portfolio.starting_cash,
            cash=portfolio.cash,
            position_count=len(positions),
            positions=positions,
            applied_broker_order_count=len(
                portfolio.applied_broker_order_ids
            ),
        )

    def list_positions(
        self,
        *,
        request: OperationsQueryRequest = (
            OperationsQueryRequest()
        ),
    ) -> tuple[PositionView, ...]:
        return self.get_portfolio(
            request=request
        ).positions

    def list_orders(
        self,
        *,
        request: OperationsQueryRequest = (
            OperationsQueryRequest()
        ),
        symbol: str | None = None,
        event: str | None = None,
        active_only: bool = False,
        unresolved_only: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> OrderPage:
        if offset < 0:
            raise ConfigurationError(
                "Order offset cannot be negative.",
                code="ORDER_OFFSET_INVALID",
            )

        if limit <= 0:
            raise ConfigurationError(
                "Order limit must be positive.",
                code="ORDER_LIMIT_INVALID",
            )

        journal = OrderJournal(
            path=request.order_journal_path
        )
        entries = list(
            self._load_latest_order_entries(
                journal
            )
        )

        cleaned_symbol = (
            None
            if symbol is None
            else symbol.upper().strip()
        )
        cleaned_event = (
            None
            if event is None
            else event.upper().strip()
        )

        if cleaned_symbol:
            entries = [
                entry
                for entry in entries
                if entry.symbol.upper().strip()
                == cleaned_symbol
            ]

        if cleaned_event:
            entries = [
                entry
                for entry in entries
                if entry.event.upper().strip()
                == cleaned_event
            ]

        if active_only:
            entries = [
                entry
                for entry in entries
                if entry.event
                in OrderJournal.ACTIVE_EVENTS
            ]

        if unresolved_only:
            entries = [
                entry
                for entry in entries
                if entry.event
                in OrderJournal.RECOVERABLE_EVENTS
            ]

        entries.sort(
            key=lambda entry: entry.timestamp,
            reverse=True,
        )
        total_count = len(entries)
        selected = tuple(
            entries[offset : offset + limit]
        )

        return OrderPage(
            total_count=total_count,
            offset=offset,
            limit=limit,
            items=selected,
        )

    def get_risk_status(
        self,
        *,
        request: OperationsQueryRequest = (
            OperationsQueryRequest()
        ),
    ) -> RiskStatusView:
        config = self._load_configuration(
            request.config_path
        )

        return RiskStatusView(
            max_order_value=(
                config.risk.max_order_value
            ),
            max_position_value=(
                config.risk.max_position_value
            ),
            max_portfolio_exposure_ratio=(
                config.risk.max_portfolio_exposure
            ),
            max_portfolio_exposure_value=(
                config.starting_cash
                * config.risk.max_portfolio_exposure
            ),
            max_trades_per_session=(
                config.risk.max_trades_per_session
            ),
            approved_symbols=tuple(
                config.symbols
            ),
            paper_trading_enabled=(
                config.paper_trading.enabled
            ),
            broker_environment=(
                config.paper_trading
                .broker_environment
            ),
            execution_permission_confirmed=(
                config.paper_trading
                .order_execution_permission_confirmed
            ),
            real_money_trading_enabled=False,
        )

    def get_latest_reconciliation(
        self,
        *,
        request: OperationsQueryRequest = (
            OperationsQueryRequest()
        ),
    ) -> ReconciliationStatusView:
        unfinished = self.list_orders(
            request=request,
            unresolved_only=True,
            limit=10_000,
        )
        latest_run = self._load_latest_reconciliation(
            request.application_database_path
        )

        safe_statuses = {
            "SUCCEEDED",
            "SUCCEEDED_WITH_WARNINGS",
        }
        safe_to_start = (
            latest_run is not None
            and latest_run.status.value
            in safe_statuses
            and unfinished.total_count == 0
        )

        return ReconciliationStatusView(
            available=latest_run is not None,
            latest_run=latest_run,
            unresolved_order_count=(
                unfinished.total_count
            ),
            safe_to_start=safe_to_start,
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
                "Operations configuration could not "
                "be loaded.",
                code="OPERATIONS_CONFIG_FAILED",
                context={"path": file_path},
            ) from error

    @staticmethod
    def _load_optional_portfolio(
        file_path: str,
    ) -> Portfolio | None:
        path = Path(file_path)

        if not path.exists():
            return None

        try:
            return PortfolioStore(
                file_path=file_path
            ).load()
        except ApplicationError:
            raise
        except Exception as error:
            raise DataStoreError(
                "Portfolio data could not be loaded.",
                code="OPERATIONS_PORTFOLIO_FAILED",
                context={"path": file_path},
            ) from error

    @staticmethod
    def _load_latest_order_entries(
        journal: OrderJournal,
    ) -> tuple[OrderJournalEntry, ...]:
        try:
            return tuple(
                journal.latest_entries().values()
            )
        except ApplicationError:
            raise
        except Exception as error:
            raise DataStoreError(
                "Order journal could not be loaded.",
                code="OPERATIONS_JOURNAL_FAILED",
                context={
                    "path": str(journal.path)
                },
            ) from error

    @staticmethod
    def _load_latest_reconciliation(
        database_path: str,
    ) -> RunHistoryRecord | None:
        try:
            repository = RunHistoryRepository(
                database_path=database_path
            )
            repository.initialize()
            records = repository.list_recent(
                limit=1,
                run_type=RunType.RECONCILIATION,
            )
        except ApplicationError:
            raise
        except Exception as error:
            raise DataStoreError(
                "Reconciliation history could not "
                "be loaded.",
                code=(
                    "OPERATIONS_RECONCILIATION_FAILED"
                ),
                context={
                    "database_path": database_path
                },
            ) from error

        return records[0] if records else None
