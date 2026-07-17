from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from app.orders import (
    OrderSide,
)
import pytest

from app.active_order_manager import (
    ActiveOrderManager,
)
from app.broker import (
    BrokerOrderResult,
)
from app.buy_the_dip import (
    BuyTheDipStrategy,
)
from app.execution import (
    ExecutionService,
)
from app.market_session import (
    MarketSession,
    MarketSessionStatus,
)
from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.news_trading_policy import (
    NewsTradingPolicy,
)
from app.portfolio import (
    Portfolio,
)
from app.risk import (
    RiskEngine,
    RiskLimits,
)
from app.simulated_market_data import (
    SimulatedMarketDataProvider,
)
from app.trade_log import (
    TradeLog,
)
from app.trading_loop import (
    TradingLoop,
)
from app.news_analysis_provider import (
    InMemoryNewsAnalysisProvider,
)
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.expiring_news_analysis_provider import (
    ExpiringNewsAnalysisProvider,
)
from app.news_policy_observation_log import (
    NewsPolicyObservationLog,
)
from app.stored_news_analysis import (
    StoredNewsAnalysis,
)
from app.position_exit_manager import (
    PositionExitManager,
)
from app.position_exit_policy import (
    PositionExitPolicy,
)
from app.position_state import (
    PositionState,
)

class RecordingMarketDataProvider:
    def __init__(self) -> None:
        self.requested_symbols: (
            list[str] | None
        ) = None

    def get_prices(
        self,
        symbols: list[str],
    ) -> dict[str, float]:
        self.requested_symbols = symbols

        return {
            "AAPL": 150.00,
            "MSFT": 320.00,
        }


class RecordingNewsTradingPolicy:
    def __init__(self) -> None:
        self.calls: list[
            tuple[object, NewsAnalysis]
        ] = []

    def approve_order(
        self,
        *,
        order,
        analysis: NewsAnalysis,
    ) -> bool:
        self.calls.append(
            (
                order,
                analysis,
            )
        )

        return False


def create_trading_loop(
    log_file: Path,
) -> tuple[
    TradingLoop,
    Portfolio,
    SimulatedMarketDataProvider,
]:
    market_data = SimulatedMarketDataProvider(
        prices={
            "AAPL": 150.00,
            "MSFT": 320.00,
        }
    )

    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        max_trades_per_session=3,
        approved_symbols={
            "AAPL",
            "MSFT",
        },
    )

    risk_engine = RiskEngine(
        limits=limits
    )

    trade_log = TradeLog(
        file_path=str(log_file)
    )

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=risk_engine,
        trade_log=trade_log,
    )

    strategy = BuyTheDipStrategy()

    trading_loop = TradingLoop(
        symbols=[
            "AAPL",
            "MSFT",
        ],
        market_data=market_data,
        strategy=strategy,
        execution_service=execution_service,
        interval_seconds=0,
    )

    return (
        trading_loop,
        portfolio,
        market_data,
    )


def test_loop_accepts_news_trading_policy(
    tmp_path: Path,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    market_data = SimulatedMarketDataProvider(
        prices={
            "AAPL": 150.00,
        }
    )

    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        max_trades_per_session=3,
        approved_symbols={
            "AAPL",
        },
    )

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=RiskEngine(
            limits
        ),
        trade_log=TradeLog(
            file_path=str(log_file)
        ),
    )

    policy = NewsTradingPolicy()

    trading_loop = TradingLoop(
        symbols=[
            "AAPL",
        ],
        market_data=market_data,
        strategy=BuyTheDipStrategy(),
        execution_service=execution_service,
        interval_seconds=0,
        news_trading_policy=policy,
    )

    assert (
        trading_loop.news_trading_policy
        is policy
    )


def test_loop_consults_policy_when_analysis_is_provided(
    tmp_path: Path,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, portfolio, market_data = (
        create_trading_loop(
            log_file
        )
    )

    policy = RecordingNewsTradingPolicy()

    trading_loop.news_trading_policy = (
        policy
    )

    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=(
            "AAPL",
        ),
        highlights=(
            "Apple received a regulatory penalty",
        ),
        sentiment=(
            NewsSentiment.NEGATIVE
        ),
    )

    def change_price(
        cycle_number: int,
    ) -> None:
        if cycle_number == 2:
            market_data.set_price(
                "AAPL",
                146.00,
            )

    trading_loop.run(
        cycles=2,
        before_cycle=change_price,
        news_analysis_by_symbol={
            "AAPL": analysis,
        },
    )

    assert len(policy.calls) == 1

    order, received_analysis = (
        policy.calls[0]
    )

    assert order.symbol == "AAPL"
    assert received_analysis is analysis
    assert portfolio.positions == {}
    assert portfolio.cash == 10_000.00
    assert not log_file.exists()


def test_loop_uses_news_analysis_provider(
    tmp_path: Path,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, portfolio, market_data = (
        create_trading_loop(
            log_file
        )
    )

    policy = RecordingNewsTradingPolicy()
    trading_loop.news_trading_policy = policy

    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("AAPL",),
        highlights=(
            "Apple received a regulatory penalty",
        ),
        sentiment=(
            NewsSentiment.NEGATIVE
        ),
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={
            "AAPL": analysis,
        }
    )

    trading_loop.news_analysis_provider = (
        provider
    )

    def change_price(
        cycle_number: int,
    ) -> None:
        if cycle_number == 2:
            market_data.set_price(
                "AAPL",
                146.00,
            )

    trading_loop.run(
        cycles=2,
        before_cycle=change_price,
    )

    assert len(policy.calls) == 1
    assert portfolio.positions == {}
    assert portfolio.cash == 10_000.00
    assert not log_file.exists()

def test_loop_executes_strategy_order(
    tmp_path: Path,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, portfolio, market_data = (
        create_trading_loop(
            log_file
        )
    )

    def change_price(
        cycle_number: int,
    ) -> None:
        if cycle_number == 2:
            market_data.set_price(
                "AAPL",
                146.00,
            )

    trading_loop.run(
        cycles=2,
        before_cycle=change_price,
    )

    assert (
        portfolio.positions["AAPL"]
        == 6
    )
    assert portfolio.cash == 9_124.00
    assert log_file.exists()


def test_loop_with_no_price_drop_executes_nothing(
    tmp_path: Path,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, portfolio, _ = (
        create_trading_loop(
            log_file
        )
    )

    trading_loop.run(
        cycles=2
    )

    assert portfolio.positions == {}
    assert portfolio.cash == 10_000.00
    assert not log_file.exists()


def test_loop_rejects_invalid_cycle_count(
    tmp_path: Path,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, _, _ = (
        create_trading_loop(
            log_file
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "Cycles must be greater "
            "than zero"
        ),
    ):
        trading_loop.run(
            cycles=0
        )


def test_loop_rejects_empty_symbol_list(
    tmp_path: Path,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    market_data = SimulatedMarketDataProvider(
        prices={
            "AAPL": 150.00,
        }
    )

    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        max_trades_per_session=3,
        approved_symbols={
            "AAPL",
        },
    )

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=RiskEngine(
            limits
        ),
        trade_log=TradeLog(
            file_path=str(log_file)
        ),
    )

    with pytest.raises(
        ValueError,
        match="At least one symbol",
    ):
        TradingLoop(
            symbols=[],
            market_data=market_data,
            strategy=BuyTheDipStrategy(),
            execution_service=(
                execution_service
            ),
            interval_seconds=0,
        )


def test_loop_skips_trading_when_market_is_closed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, portfolio, market_data = (
        create_trading_loop(
            log_file
        )
    )

    market_session = MarketSession(
        timezone_name=(
            "America/New_York"
        ),
        opening_time="09:30",
        closing_time="16:00",
    )

    closed_status = MarketSessionStatus(
        is_open=False,
        reason="Market has closed.",
        local_time=datetime(
            2026,
            7,
            13,
            17,
            0,
            tzinfo=ZoneInfo(
                "America/New_York"
            ),
        ),
    )

    monkeypatch.setattr(
        market_session,
        "get_status",
        lambda: closed_status,
    )

    trading_loop.market_session = (
        market_session
    )

    trading_loop.enforce_market_hours = (
        True
    )

    def change_price(
        cycle_number: int,
    ) -> None:
        if cycle_number == 2:
            market_data.set_price(
                "AAPL",
                146.00,
            )

    trading_loop.run(
        cycles=2,
        before_cycle=change_price,
    )

    assert portfolio.positions == {}
    assert portfolio.cash == 10_000.00
    assert not log_file.exists()


def test_loop_uses_provider_through_market_data_interface(
    tmp_path: Path,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    provider = (
        RecordingMarketDataProvider()
    )

    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        max_trades_per_session=3,
        approved_symbols={
            "AAPL",
            "MSFT",
        },
    )

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=RiskEngine(
            limits
        ),
        trade_log=TradeLog(
            file_path=str(log_file)
        ),
    )

    trading_loop = TradingLoop(
        symbols=[
            "aapl",
            "msft",
        ],
        market_data=provider,  # type: ignore[arg-type]
        strategy=BuyTheDipStrategy(),
        execution_service=execution_service,
        interval_seconds=0,
    )

    trading_loop.run(
        cycles=1
    )

    assert provider.requested_symbols == [
        "AAPL",
        "MSFT",
    ]
    assert portfolio.positions == {}


def test_loop_logs_session_summary(
    tmp_path: Path,
    caplog,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, _, _ = (
        create_trading_loop(
            log_file
        )
    )

    with caplog.at_level(
        "INFO",
        logger="app.trading_loop",
    ):
        trading_loop.run(
            cycles=2
        )

    assert (
        "trading_session_finished "
        "cycles_completed=2 "
        "symbol_count=2"
        in caplog.text
    )


def test_continuous_loop_stops_when_requested(
    tmp_path: Path,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, _, _ = (
        create_trading_loop(
            log_file
        )
    )

    completed_cycles: list[int] = []

    def before_cycle(
        cycle_number: int,
    ) -> None:
        completed_cycles.append(
            cycle_number
        )

    def stop_requested() -> bool:
        return (
            len(completed_cycles)
            >= 3
        )

    trading_loop.run(
        cycles=None,
        before_cycle=before_cycle,
        stop_requested=stop_requested,
    )

    assert completed_cycles == [
        1,
        2,
        3,
    ]


def test_loop_skips_symbol_with_active_order(
    tmp_path: Path,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, portfolio, market_data = (
        create_trading_loop(
            log_file
        )
    )

    trading_loop.active_order_manager = (
        ActiveOrderManager(
            symbol_mapping={
                "AAPL": "AAPL_US_EQ",
                "MSFT": "MSFT_US_EQ",
            },
            active_orders=[
                BrokerOrderResult(
                    order_id=123456,
                    ticker="AAPL_US_EQ",
                    quantity=1.0,
                    side="BUY",
                    status="NEW",
                    order_type="MARKET",
                    filled_quantity=0.0,
                    filled_value=0.0,
                    currency="GBP",
                )
            ],
        )
    )

    def change_price(
        cycle_number: int,
    ) -> None:
        if cycle_number == 2:
            market_data.set_price(
                "AAPL",
                146.00,
            )

    trading_loop.run(
        cycles=2,
        before_cycle=change_price,
    )

    assert portfolio.positions == {}
    assert portfolio.cash == 10_000.00


def test_loop_refreshes_active_orders_each_cycle(
    tmp_path: Path,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, _, _ = (
        create_trading_loop(
            log_file
        )
    )

    class RecordingManager:
        def __init__(self) -> None:
            self.refresh_calls = 0
            self.active_orders = []

        def refresh(self) -> None:
            self.refresh_calls += 1

        def is_symbol_blocked(
            self,
            symbol: str,
        ) -> bool:
            return False

    manager = RecordingManager()

    trading_loop.active_order_manager = (
        manager  # type: ignore[assignment]
    )

    trading_loop.run(
        cycles=3
    )

    assert manager.refresh_calls == 3
    
def test_shadow_news_policy_records_block_but_executes_order(
    tmp_path: Path,
) -> None:
    trade_log_path = (
        tmp_path
        / "trade_log.jsonl"
    )
    observation_log_path = (
        tmp_path
        / "news-policy-observations.jsonl"
    )

    trading_loop, portfolio, market_data = (
        create_trading_loop(
            trade_log_path
        )
    )

    now = datetime(
        2026,
        7,
        17,
        12,
        0,
        tzinfo=timezone.utc,
    )

    analysis = NewsAnalysis(
        impact_term=NewsImpactTerm.SHORTTERM,
        impact_scope=NewsImpactScope.STOCK,
        scope_items=("AAPL",),
        highlights=(
            "Apple received negative news",
        ),
        sentiment=NewsSentiment.NEGATIVE,
    )

    provider = ExpiringNewsAnalysisProvider(
        time_to_live_seconds=1_800,
        now_provider=lambda: now,
    )

    provider.set_stored_analysis(
        symbol="AAPL",
        stored_analysis=StoredNewsAnalysis(
            analysis=analysis,
            analysed_at=now,
            expires_at=(
                now + timedelta(
                    minutes=30
                )
            ),
            article_title=(
                "Apple received negative news"
            ),
            article_url=(
                "https://example.test/apple"
            ),
            published_at=(
                now - timedelta(
                    minutes=10
                )
            ),
            relevance_score=0.92,
            source_sentiment_label=(
                "Somewhat-Bearish"
            ),
            source_sentiment_score=-0.35,
            model_name="fake-model",
            prompt_version="v3",
        ),
    )

    trading_loop.news_trading_policy = (
        NewsTradingPolicy()
    )
    trading_loop.news_analysis_provider = (
        provider
    )
    trading_loop.news_policy_observation_log = (
        NewsPolicyObservationLog(
            file_path=observation_log_path,
        )
    )
    trading_loop.news_policy_shadow_mode = True
    trading_loop.now_provider = (
        lambda: now
    )

    def change_price(
        cycle_number: int,
    ) -> None:
        if cycle_number == 2:
            market_data.set_price(
                "AAPL",
                146.00,
            )

    trading_loop.run(
        cycles=2,
        before_cycle=change_price,
    )

    assert portfolio.positions["AAPL"] == 6
    assert portfolio.cash == 9_124.00

    observations = (
        trading_loop
        .news_policy_observation_log
        .read_all()
    )

    assert len(observations) == 1

    observation = observations[0]

    assert observation.symbol == "AAPL"
    assert observation.side is OrderSide.BUY
    assert observation.quantity == 6
    assert observation.analysis_available
    assert (
        observation.analysis_sentiment
        is NewsSentiment.NEGATIVE
    )
    assert not observation.would_approve
    assert observation.observed_at == now
    
def test_shadow_mode_records_missing_news_analysis(
    tmp_path: Path,
) -> None:
    trade_log_path = (
        tmp_path
        / "trade_log.jsonl"
    )
    observation_log_path = (
        tmp_path
        / "news-policy-observations.jsonl"
    )

    trading_loop, portfolio, market_data = (
        create_trading_loop(
            trade_log_path
        )
    )

    now = datetime(
        2026,
        7,
        17,
        12,
        0,
        tzinfo=timezone.utc,
    )

    trading_loop.news_analysis_provider = (
        InMemoryNewsAnalysisProvider(
            analyses={}
        )
    )
    trading_loop.news_policy_observation_log = (
        NewsPolicyObservationLog(
            file_path=observation_log_path,
        )
    )
    trading_loop.news_policy_shadow_mode = True
    trading_loop.now_provider = (
        lambda: now
    )

    def change_price(
        cycle_number: int,
    ) -> None:
        if cycle_number == 2:
            market_data.set_price(
                "AAPL",
                146.00,
            )

    trading_loop.run(
        cycles=2,
        before_cycle=change_price,
    )

    assert portfolio.positions["AAPL"] == 6
    assert portfolio.cash == 9_124.00

    observations = (
        trading_loop
        .news_policy_observation_log
        .read_all()
    )

    assert len(observations) == 1

    observation = observations[0]

    assert observation.symbol == "AAPL"
    assert observation.side is OrderSide.BUY
    assert observation.quantity == 6
    assert not observation.analysis_available
    assert observation.analysis_sentiment is None
    assert observation.analysis_expires_at is None
    assert observation.would_approve
    assert observation.reason == (
        "No current news analysis was available."
    )
    assert observation.observed_at == now
    
def test_shadow_mode_records_approved_positive_analysis(
    tmp_path: Path,
) -> None:
    trade_log_path = (
        tmp_path
        / "trade_log.jsonl"
    )
    observation_log_path = (
        tmp_path
        / "news-policy-observations.jsonl"
    )

    trading_loop, portfolio, market_data = (
        create_trading_loop(
            trade_log_path
        )
    )

    now = datetime(
        2026,
        7,
        17,
        12,
        0,
        tzinfo=timezone.utc,
    )

    expires_at = (
        now + timedelta(
            minutes=30
        )
    )

    analysis = NewsAnalysis(
        impact_term=NewsImpactTerm.SHORTTERM,
        impact_scope=NewsImpactScope.STOCK,
        scope_items=("AAPL",),
        highlights=(
            "Apple reported stronger revenue",
        ),
        sentiment=NewsSentiment.POSITIVE,
    )

    provider = ExpiringNewsAnalysisProvider(
        time_to_live_seconds=1_800,
        now_provider=lambda: now,
    )

    provider.set_stored_analysis(
        symbol="AAPL",
        stored_analysis=StoredNewsAnalysis(
            analysis=analysis,
            analysed_at=now,
            expires_at=expires_at,
            article_title=(
                "Apple reports stronger revenue"
            ),
            article_url=(
                "https://example.test/apple"
            ),
            published_at=(
                now - timedelta(
                    minutes=10
                )
            ),
            relevance_score=0.92,
            source_sentiment_label=(
                "Somewhat-Bullish"
            ),
            source_sentiment_score=0.35,
            model_name="fake-model",
            prompt_version="v3",
        ),
    )

    trading_loop.news_analysis_provider = (
        provider
    )
    trading_loop.news_policy_observation_log = (
        NewsPolicyObservationLog(
            file_path=observation_log_path,
        )
    )
    trading_loop.news_policy_shadow_mode = True
    trading_loop.now_provider = (
        lambda: now
    )

    def change_price(
        cycle_number: int,
    ) -> None:
        if cycle_number == 2:
            market_data.set_price(
                "AAPL",
                146.00,
            )

    trading_loop.run(
        cycles=2,
        before_cycle=change_price,
    )

    assert portfolio.positions["AAPL"] == 6
    assert portfolio.cash == 9_124.00

    observations = (
        trading_loop
        .news_policy_observation_log
        .read_all()
    )

    assert len(observations) == 1

    observation = observations[0]

    assert observation.symbol == "AAPL"
    assert observation.side is OrderSide.BUY
    assert observation.quantity == 6
    assert observation.analysis_available
    assert (
        observation.analysis_sentiment
        is NewsSentiment.POSITIVE
    )
    assert (
        observation.analysis_expires_at
        == expires_at
    )
    assert observation.would_approve
    assert observation.reason == (
        "News policy approved the order."
    )
    assert observation.observed_at == now

def test_loop_generates_exit_order_for_stop_loss(
    tmp_path: Path,
) -> None:
    trade_log_path = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, portfolio, market_data = (
        create_trading_loop(
            trade_log_path
        )
    )

    portfolio.cash = 9_700.00
    portfolio.positions["AAPL"] = 3

    trading_loop.position_states = {
        "AAPL": PositionState(
            symbol="AAPL",
            quantity=3,
            average_entry_price=100.00,
        ),
    }

    trading_loop.position_exit_manager = (
        PositionExitManager(
            policy=PositionExitPolicy(
                stop_loss_percent=5.0,
                take_profit_percent=10.0,
                trailing_stop_percent=4.0,
                trailing_activation_percent=8.0,
            )
        )
    )

    market_data.set_price(
        "AAPL",
        94.00,
    )

    trading_loop.run(
        cycles=1,
    )

    assert "AAPL" not in portfolio.positions

    assert "AAPL" not in (
        trading_loop.position_states
    )

    assert portfolio.cash == 9_982.00

def test_successful_buy_creates_position_state(
    tmp_path: Path,
) -> None:
    trade_log_path = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, portfolio, market_data = (
        create_trading_loop(
            trade_log_path
        )
    )

    market_data.set_price(
        "AAPL",
        146.00,
    )

    trading_loop.run(
        cycles=1,
    )

    assert portfolio.positions["AAPL"] == 6

    state = (
        trading_loop.position_states[
            "AAPL"
        ]
    )

    assert state.symbol == "AAPL"
    assert state.quantity == 6
    assert state.average_entry_price == 146.00
    assert state.highest_price == 146.00

def test_successful_buy_creates_position_state(
    tmp_path: Path,
) -> None:
    trade_log_path = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, portfolio, market_data = (
        create_trading_loop(
            trade_log_path
        )
    )

    def change_price(
        cycle_number: int,
    ) -> None:
        if cycle_number == 2:
            market_data.set_price(
                "AAPL",
                146.00,
            )

    trading_loop.run(
        cycles=2,
        before_cycle=change_price,
    )

    assert portfolio.positions["AAPL"] == 6

    state = (
        trading_loop.position_states[
            "AAPL"
        ]
    )

    assert state.symbol == "AAPL"
    assert state.quantity == 6
    assert state.average_entry_price == 146.00
    assert state.highest_price == 146.00

def test_successful_buy_updates_existing_position_state(
    tmp_path: Path,
) -> None:
    trade_log_path = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, portfolio, market_data = (
        create_trading_loop(
            trade_log_path
        )
    )

    portfolio.cash = 9_800.00
    portfolio.positions["AAPL"] = 2

    trading_loop.position_states = {
        "AAPL": PositionState(
            symbol="AAPL",
            quantity=2,
            average_entry_price=100.00,
            highest_price=120.00,
        ),
    }

    def change_price(
        cycle_number: int,
    ) -> None:
        if cycle_number == 2:
            market_data.set_price(
                "AAPL",
                146.00,
            )

    trading_loop.run(
        cycles=2,
        before_cycle=change_price,
    )

    state = (
        trading_loop.position_states[
            "AAPL"
        ]
    )

    assert portfolio.positions["AAPL"] == 8
    assert state.quantity == 8
    assert state.average_entry_price == 134.50
    assert state.highest_price == 146.00

class RecordingPositionStateStore:
    def __init__(
        self,
    ) -> None:
        self.saved_states: list[
            dict[str, PositionState]
        ] = []

    def save(
        self,
        states: dict[
            str,
            PositionState,
        ],
    ) -> None:
        self.saved_states.append(
            dict(states)
        )


def test_successful_buy_saves_position_state(
    tmp_path: Path,
) -> None:
    trade_log_path = (
        tmp_path
        / "trade_log.jsonl"
    )

    trading_loop, portfolio, market_data = (
        create_trading_loop(
            trade_log_path
        )
    )

    store = RecordingPositionStateStore()

    trading_loop.position_state_store = (
        store
    )

    def change_price(
        cycle_number: int,
    ) -> None:
        if cycle_number == 2:
            market_data.set_price(
                "AAPL",
                146.00,
            )

    trading_loop.run(
        cycles=2,
        before_cycle=change_price,
    )

    assert portfolio.positions["AAPL"] == 6
    assert len(store.saved_states) == 1

    saved_state = (
        store.saved_states[0]["AAPL"]
    )

    assert saved_state.symbol == "AAPL"
    assert saved_state.quantity == 6
    assert (
        saved_state.average_entry_price
        == 146.00
    )
    assert saved_state.highest_price == 146.00