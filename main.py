import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from app.buy_the_dip import BuyTheDipStrategy
from app.config import load_config
from app.demo_recovery_factory import (
    create_demo_recovery_startup_service,
)
from app.execution import ExecutionService
from app.logging_config import setup_logging
from app.market_data_factory import (
    create_market_data_provider,
)
from app.market_session import MarketSession
from app.order_journal import OrderJournal
from app.paper_application_startup import (
    PaperApplicationStartupService,
)
from app.paper_execution_factory import (
    create_paper_execution_adapter,
)
from app.paper_startup_reconciliation import (
    PaperStartupReconciliationService,
)
from app.portfolio_store import PortfolioStore
from app.reconciliation import BrokerReconciler
from app.risk import RiskEngine, RiskLimits
from app.simulated_market_data import (
    SimulatedMarketDataProvider,
)
from app.trade_log import TradeLog
from app.trading212_client import Trading212Client
from app.trading_loop import TradingLoop
from app.startup_order_discovery import (
    StartupOrderDiscoveryService,
)
from app.startup_summary import (
    StartupSummaryBuilder,
)
from app.symbol_mapping_service import (
    SymbolMappingService,
)
from app.active_order_manager import (
    ActiveOrderManager,
)
from app.news_policy_runtime_factory import (
    create_news_policy_runtime,
)
from app.news_runtime_factory import (
    create_news_runtime_pipeline,
)
from app.historical_fill_importer import (
    HistoricalFillImporter,
)
from app.news_refresh_coordinator import (
    NewsRefreshCoordinator,
)
from app.position_state_store import (
    PositionStateStore,
)
logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()
    load_dotenv()

    logger.info("application_starting")

    config = load_config()
    
    news_policy_runtime = (
    create_news_policy_runtime()
)

    news_runtime_pipeline = None

    if news_policy_runtime.config.enabled:
        news_runtime_pipeline = (
            create_news_runtime_pipeline(
                source_name="alpha_vantage",
            )
        )

    news_refresh_coordinator = None

    if news_runtime_pipeline is not None:
        news_refresh_coordinator = (
            NewsRefreshCoordinator(
                provider=(
                    news_runtime_pipeline.provider
                ),
                refresh_service=(
                    news_runtime_pipeline
                    .refresh_service
                ),
            )
        )

    print("Trading system starting...")
    print(f"Current time: {datetime.now()}")
    print(f"Mode: {config.mode}")
    print(
        "Market data: "
        f"{config.market_data_provider}"
    )
    print("Real-money trading: DISABLED")
    print(
        "News policy: "
        f"{news_policy_runtime.config.mode}"
    )

    if news_runtime_pipeline is None:
        print("News runtime: disabled")
    else:
        print("News runtime: enabled")


    logger.info(
        "safe_mode_confirmed mode=%s "
        "market_data_provider=%s "
        "real_money_trading=false",
        config.mode,
        config.market_data_provider,
    )

    market_data = create_market_data_provider(
        provider_name=(
            config.market_data_provider
        ),
        symbols=config.symbols,
    )

    portfolio_store = PortfolioStore()

    portfolio = portfolio_store.load_or_create(
        starting_cash=config.starting_cash
    )

    position_state_store = PositionStateStore(
        file_path=Path(
            "data/position_states.json"
        )
    )

    position_states = (
        position_state_store.load()
    )

    risk_limits = RiskLimits(
        max_order_value=(
            config.risk.max_order_value
        ),
        max_position_value=(
            config.risk.max_position_value
        ),
        max_portfolio_exposure=(
            config.risk.max_portfolio_exposure
        ),
        max_trades_per_session=(
            config.risk.max_trades_per_session
        ),
        approved_symbols=set(
            config.symbols
        ),
    )

    risk_engine = RiskEngine(
        limits=risk_limits
    )

    trade_log = TradeLog()

    strategy = BuyTheDipStrategy(
        drop_threshold_percent=(
            config.strategy
            .drop_threshold_percent
        ),
        target_allocation_percent=(
            config.strategy
            .target_allocation_percent
        ),
        cooldown_cycles=(
            config.strategy.cooldown_cycles
        ),
    )

    def prepare_cycle(
        cycle_number: int,
    ) -> None:
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
                "skipped_symbols=%s "
                "failed_symbols=%s",
                cycle_number,
                refresh_result.refreshed_symbols,
                refresh_result.skipped_symbols,
                refresh_result.failed_symbols,
            )
                
        
        if (
            config.market_data_provider
            != "SIMULATED"
        ):
            return

        if not isinstance(
            market_data,
            SimulatedMarketDataProvider,
        ):
            return

        if cycle_number == 2:
            if "AAPL" in config.symbols:
                market_data.set_price(
                    "AAPL",
                    146.00,
                )

            if "MSFT" in config.symbols:
                market_data.set_price(
                    "MSFT",
                    318.00,
                )

        elif cycle_number == 3:
            if "AAPL" in config.symbols:
                market_data.set_price(
                    "AAPL",
                    142.00,
                )

            if "MSFT" in config.symbols:
                market_data.set_price(
                    "MSFT",
                    310.00,
                )

        elif cycle_number == 4:
            if "AAPL" in config.symbols:
                market_data.set_price(
                    "AAPL",
                    138.00,
                )

            if "MSFT" in config.symbols:
                market_data.set_price(
                    "MSFT",
                    308.00,
                )

        elif cycle_number == 5:
            if "AAPL" in config.symbols:
                market_data.set_price(
                    "AAPL",
                    134.00,
                )

            if "MSFT" in config.symbols:
                market_data.set_price(
                    "MSFT",
                    305.00,
                )

    market_session = MarketSession(
        timezone_name=(
            config.market_session.timezone
        ),
        opening_time=(
            config.market_session.opening_time
        ),
        closing_time=(
            config.market_session.closing_time
        ),
        trading_weekdays=set(
            config.market_session
            .trading_weekdays
        ),
    )

    order_journal: OrderJournal | None = None
    active_order_manager: ActiveOrderManager | None = None
    api_key = ""
    api_secret = ""

    if config.mode == "PAPER":
        if not config.paper_trading.enabled:
            raise ValueError(
                "PAPER mode requires paper "
                "trading to be enabled."
            )

        if (
            config.paper_trading
            .broker_environment
            != "DEMO"
        ):
            raise ValueError(
                "PAPER mode requires the "
                "Trading 212 DEMO environment."
            )

        api_key = os.getenv(
            "TRADING212_API_KEY",
            "",
        ).strip()

        api_secret = os.getenv(
            "TRADING212_API_SECRET",
            "",
        ).strip()

        if not api_key or not api_secret:
            raise ValueError(
                "Trading 212 Demo credentials "
                "are required for PAPER mode."
            )
        broker = Trading212Client(
                api_key=api_key,
                api_secret=api_secret,
                environment=(
                    config.paper_trading
                    .broker_environment
            ),
        )

        symbol_mapping = (
            SymbolMappingService().resolve(
                broker=broker,
                configured_symbols=config.symbols,
            )
        )
        
        logger.info(
            "broker_symbol_mapping_resolved "
            "symbol_count=%s",
            len(symbol_mapping),
        )

        startup_active_orders = (
            broker.get_active_orders()
        )

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
            path=Path(
                "order_journal.jsonl"
            )
        )

        execution_service = (
            create_paper_execution_adapter(
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
                    config.paper_trading
                    .broker_environment
                ),
                order_execution_permission_confirmed=(
                    config.paper_trading
                    .order_execution_permission_confirmed
                ),
                market_session=market_session,
                enforce_market_hours=(
                    config.market_session
                    .enforce_market_hours
                ),
            )
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
            config.market_session
            .enforce_market_hours
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
            if news_runtime_pipeline
            is not None
            else None
        ),
        news_policy_observation_log=(
            news_policy_runtime.observation_log
        ),
        news_policy_shadow_mode=(
            news_policy_runtime
            .config
            .shadow_mode
        ),
        position_states=position_states,
    )

    def start_trading() -> None:
        trading_loop.run(
            cycles=(
                config.trading_loop.cycles
            ),
            before_cycle=(
                prepare_cycle
            ),
        )
    if config.mode == "PAPER":
        if order_journal is None:
            raise RuntimeError(
                "PAPER mode order journal "
                "was not initialized."
            )

        recovery_startup_service = (
            create_demo_recovery_startup_service(
                api_key=api_key,
                api_secret=api_secret,
                order_journal=order_journal,
                portfolio=portfolio,
                portfolio_store=(
                    portfolio_store
                ),
            )
        )

        reconciler = BrokerReconciler(
            symbol_mapping=symbol_mapping
        )

        reconciliation_service = (
            PaperStartupReconciliationService(
                broker=broker,
                reconciler=reconciler,
                portfolio=portfolio,
                initial_active_orders=(
                    startup_active_orders
                ),
            )
        )

        order_discovery_service = (
            StartupOrderDiscoveryService(
                broker=broker,
                journal=order_journal,
                initial_active_orders=(
                    startup_active_orders
                ),
            )
        )

        paper_startup_service = (
            PaperApplicationStartupService(
                recovery_startup_service=(
                    recovery_startup_service
                ),
                order_discovery_service=(
                    order_discovery_service
                ),
                reconciliation_service=(
                    reconciliation_service
                ),
            )
        )

        historical_fill_result = (
            historical_fill_importer
            .import_unapplied_fills()
        )

        logger.info(
            "historical_fill_import_completed "
            "imported_order_ids=%s "
            "skipped_order_ids=%s",
            historical_fill_result.imported_order_ids,
            historical_fill_result.skipped_order_ids,
        )

        startup_result = (
            paper_startup_service.start(
                start_trading=start_trading
            )
        )

        startup_summary = (
            StartupSummaryBuilder().build(
                startup_result=startup_result,
            )
        )
        logger.info(
            "paper_startup_summary "
            "outcome=%s "
            "startup_approved=%s "
            "discovery_approved=%s "
            "discovery_reason=%s "
            "known_order_count=%s "
            "unknown_order_count=%s",
            startup_summary.outcome.value,
            startup_summary.startup_approved,
            startup_summary.discovery.approved,
            startup_summary.discovery.reason,
            (
                startup_summary
                .discovery
                .known_order_count
            ),
            (
                startup_summary
                .discovery
                .unknown_order_count
            ),
        )

        if not startup_result.trading_started:
            logger.error(
                "paper_trading_refused "
                "reason=%s",
                startup_result.reason,
            )

            print(
                "Trading refused: "
                f"{startup_result.reason}"
            )

            if (
                startup_result
                .reconciliation_result
                is not None
            ):
                reconciliation_report = (
                    startup_result
                    .reconciliation_result
                    .report
                )

                reconciliation_report.display()

            return
    else:
        start_trading()

    portfolio_store.save(
        portfolio
    )

    position_state_store.save(
        trading_loop.position_states
    )
    print("\nPortfolio saved.")

    final_prices = market_data.get_prices(
        config.symbols
    )

    portfolio.display(
        final_prices
    )

    trade_log.display()

    logger.info(
        "application_finished "
        "cash=%.2f positions=%s "
        "session_trade_count=%s",
        portfolio.cash,
        portfolio.positions,
        risk_engine.executed_trade_count,
    )


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        logger.info(
            "application_shutdown_requested"
        )

        print(
            "\nShutdown requested."
        )

        print(
            "Application stopped cleanly."
        )

    except Exception:
        logger.exception(
            "application_stopped_due_to_"
            "unhandled_error"
        )
        raise