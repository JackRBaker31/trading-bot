import logging
import os
from pathlib import Path

from app.active_order_manager import ActiveOrderManager
from app.buy_the_dip import BuyTheDipStrategy
from app.config import load_config
from app.demo_recovery_factory import (
    create_demo_recovery_startup_service,
)
from app.execution import ExecutionService
from app.historical_fill_importer import HistoricalFillImporter
from app.market_data_factory import create_market_data_provider
from app.market_session import MarketSession
from app.news_policy_runtime_factory import (
    create_news_policy_runtime,
)
from app.news_refresh_coordinator import NewsRefreshCoordinator
from app.news_runtime_factory import create_news_runtime_pipeline
from app.order_journal import OrderJournal
from app.paper_application_startup import PaperApplicationStartupService
from app.paper_execution_factory import create_paper_execution_adapter
from app.paper_startup_reconciliation import (
    PaperStartupReconciliationService,
)
from app.portfolio_store import PortfolioStore
from app.position_state_store import PositionStateStore
from app.reconciliation import BrokerReconciler
from app.risk import RiskEngine, RiskLimits
from app.rsi_entry_filter import RsiEntryFilter
from app.simulated_market_data import SimulatedMarketDataProvider
from app.simulated_price_scenario import SimulatedPriceScenario
from app.startup_order_discovery import StartupOrderDiscoveryService
from app.startup_summary import StartupSummaryBuilder
from app.symbol_mapping_service import SymbolMappingService
from app.trade_log import TradeLog
from app.trading212_client import Trading212Client
from app.trading_application import TradingApplicationRuntime
from app.trading_loop import TradingLoop


logger = logging.getLogger(__name__)


class TradingApplicationRuntimeFactory:
    def build(
        self,
        *,
        config_path: str,
    ) -> TradingApplicationRuntime:
        config = load_config(config_path)

        news_policy_runtime = create_news_policy_runtime()
        news_runtime_pipeline = None

        if news_policy_runtime.config.enabled:
            news_runtime_pipeline = create_news_runtime_pipeline(
                source_name="alpha_vantage",
            )

        news_refresh_coordinator = None
        if news_runtime_pipeline is not None:
            news_refresh_coordinator = NewsRefreshCoordinator(
                provider=news_runtime_pipeline.provider,
                refresh_service=(
                    news_runtime_pipeline.refresh_service
                ),
            )

        market_data = create_market_data_provider(
            provider_name=config.market_data_provider,
            symbols=config.symbols,
        )

        portfolio_store = PortfolioStore()
        portfolio = portfolio_store.load_or_create(
            starting_cash=config.starting_cash
        )

        position_state_store = PositionStateStore(
            file_path=Path("data/position_states.json")
        )
        position_states = position_state_store.load()

        risk_engine = RiskEngine(
            limits=RiskLimits(
                max_order_value=config.risk.max_order_value,
                max_position_value=config.risk.max_position_value,
                max_portfolio_exposure=(
                    config.risk.max_portfolio_exposure
                ),
                max_trades_per_session=(
                    config.risk.max_trades_per_session
                ),
                approved_symbols=set(config.symbols),
            )
        )
        trade_log = TradeLog()

        entry_filters = []
        if (
            config.strategy.rsi_period is not None
            and config.strategy.rsi_buy_threshold is not None
        ):
            entry_filters.append(
                RsiEntryFilter(
                    period=config.strategy.rsi_period,
                    buy_threshold=(
                        config.strategy.rsi_buy_threshold
                    ),
                )
            )

        strategy = BuyTheDipStrategy(
            drop_threshold_percent=(
                config.strategy.drop_threshold_percent
            ),
            target_allocation_percent=(
                config.strategy.target_allocation_percent
            ),
            cooldown_cycles=config.strategy.cooldown_cycles,
            sma_period=config.strategy.sma_period,
            entry_filters=entry_filters,
        )

        simulation_scenario = SimulatedPriceScenario(
            prices_by_cycle={
                2: {"AAPL": 95.0, "MSFT": 195.0},
                3: {"AAPL": 92.0, "MSFT": 188.0},
                4: {"AAPL": 105.0, "MSFT": 205.0},
                5: {"AAPL": 110.0, "MSFT": 215.0},
            }
        )

        def prepare_cycle(cycle_number: int) -> None:
            if news_refresh_coordinator is not None:
                refresh_result = (
                    news_refresh_coordinator
                    .refresh_missing_or_expired(
                        symbols=config.symbols,
                    )
                )
                logger.info(
                    "news_refresh_cycle_completed "
                    "cycle=%s refreshed_symbols=%s "
                    "skipped_symbols=%s failed_symbols=%s",
                    cycle_number,
                    refresh_result.refreshed_symbols,
                    refresh_result.skipped_symbols,
                    refresh_result.failed_symbols,
                )

            if config.market_data_provider != "SIMULATED":
                return
            if not isinstance(
                market_data,
                SimulatedMarketDataProvider,
            ):
                return
            simulation_scenario.apply(
                cycle_number=cycle_number,
                market_data=market_data,
            )

        market_session = MarketSession(
            timezone_name=config.market_session.timezone,
            opening_time=config.market_session.opening_time,
            closing_time=config.market_session.closing_time,
            trading_weekdays=set(
                config.market_session.trading_weekdays
            ),
        )

        active_order_manager = None
        paper_startup_service = None
        historical_fill_importer = None

        if config.mode == "PAPER":
            self._validate_paper_config(config)
            api_key, api_secret = self._load_broker_credentials()

            broker = Trading212Client(
                api_key=api_key,
                api_secret=api_secret,
                environment=(
                    config.paper_trading.broker_environment
                ),
            )
            symbol_mapping = SymbolMappingService().resolve(
                broker=broker,
                configured_symbols=config.symbols,
            )
            startup_active_orders = broker.get_active_orders()
            active_order_manager = ActiveOrderManager(
                symbol_mapping=symbol_mapping,
                active_orders=startup_active_orders,
                order_provider=broker,
            )
            historical_fill_importer = HistoricalFillImporter(
                broker=broker,
                portfolio=portfolio,
                portfolio_store=portfolio_store,
                symbol_mapping=symbol_mapping,
            )
            order_journal = OrderJournal(
                path=Path("order_journal.jsonl")
            )
            execution_service = create_paper_execution_adapter(
                api_key=api_key,
                api_secret=api_secret,
                symbol_mapping=symbol_mapping,
                portfolio=portfolio,
                risk_engine=risk_engine,
                trade_log=trade_log,
                order_journal=order_journal,
                paper_trading_enabled=(
                    config.paper_trading.enabled
                ),
                broker_environment=(
                    config.paper_trading.broker_environment
                ),
                order_execution_permission_confirmed=(
                    config.paper_trading
                    .order_execution_permission_confirmed
                ),
                market_session=market_session,
                enforce_market_hours=(
                    config.market_session.enforce_market_hours
                ),
            )

            recovery_startup_service = (
                create_demo_recovery_startup_service(
                    api_key=api_key,
                    api_secret=api_secret,
                    order_journal=order_journal,
                    portfolio=portfolio,
                    portfolio_store=portfolio_store,
                )
            )
            reconciliation_service = (
                PaperStartupReconciliationService(
                    broker=broker,
                    reconciler=BrokerReconciler(
                        symbol_mapping=symbol_mapping
                    ),
                    portfolio=portfolio,
                    initial_active_orders=startup_active_orders,
                )
            )
            order_discovery_service = StartupOrderDiscoveryService(
                broker=broker,
                journal=order_journal,
                initial_active_orders=startup_active_orders,
            )
            paper_startup_service = PaperApplicationStartupService(
                recovery_startup_service=(
                    recovery_startup_service
                ),
                order_discovery_service=order_discovery_service,
                reconciliation_service=reconciliation_service,
            )
        else:
            execution_service = ExecutionService(
                portfolio=portfolio,
                risk_engine=risk_engine,
                trade_log=trade_log,
            )

        trading_loop = TradingLoop(
            symbols=config.symbols,
            market_data=market_data,
            strategy=strategy,
            execution_service=execution_service,
            interval_seconds=(
                config.trading_loop.interval_seconds
            ),
            market_session=market_session,
            enforce_market_hours=(
                config.market_session.enforce_market_hours
            ),
            active_order_manager=(
                active_order_manager
                if config.mode == "PAPER"
                else None
            ),
            refresh_active_orders_on_first_cycle=(
                config.mode != "PAPER"
            ),
            news_analysis_provider=(
                news_runtime_pipeline.provider
                if news_runtime_pipeline is not None
                else None
            ),
            news_policy_observation_log=(
                news_policy_runtime.observation_log
            ),
            news_policy_shadow_mode=(
                news_policy_runtime.config.shadow_mode
            ),
            position_states=position_states,
        )

        return TradingApplicationRuntime(
            config=config,
            market_data=market_data,
            portfolio=portfolio,
            portfolio_store=portfolio_store,
            position_state_store=position_state_store,
            risk_engine=risk_engine,
            trade_log=trade_log,
            trading_loop=trading_loop,
            prepare_cycle=prepare_cycle,
            paper_startup_service=paper_startup_service,
            historical_fill_importer=historical_fill_importer,
            startup_summary_builder=StartupSummaryBuilder(),
        )

    @staticmethod
    def _validate_paper_config(config) -> None:
        if not config.paper_trading.enabled:
            raise ValueError(
                "PAPER mode requires paper trading to be enabled."
            )
        if config.paper_trading.broker_environment != "DEMO":
            raise ValueError(
                "PAPER mode requires the Trading 212 DEMO environment."
            )

    @staticmethod
    def _load_broker_credentials() -> tuple[str, str]:
        api_key = os.getenv("TRADING212_API_KEY", "").strip()
        api_secret = os.getenv(
            "TRADING212_API_SECRET",
            "",
        ).strip()
        if not api_key or not api_secret:
            raise ValueError(
                "Trading 212 Demo credentials are required "
                "for PAPER mode."
            )
        return api_key, api_secret
