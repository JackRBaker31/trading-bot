from pathlib import Path

from app.buy_the_dip import (
    BuyTheDipStrategy,
)
from app.execution import (
    ExecutionService,
)
from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.news_analysis_provider import (
    InMemoryNewsAnalysisProvider,
)
from app.news_analysis_refresh_service import (
    NewsAnalysisRefreshService,
)
from app.news_analysis_validator import (
    NewsAnalysisValidator,
)
from app.news_article_source import (
    InMemoryNewsArticleSource,
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


class FakeAnalyser:
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        return NewsAnalysis(
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

class PositiveFakeAnalyser:
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        return NewsAnalysis(
            impact_term=(
                NewsImpactTerm.SHORTTERM
            ),
            impact_scope=(
                NewsImpactScope.STOCK
            ),
            scope_items=("AAPL",),
            highlights=(
                "Apple reported stronger revenue",
            ),
            sentiment=(
                NewsSentiment.POSITIVE
            ),
        )

def test_negative_news_blocks_generated_buy_order(
    tmp_path: Path,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={}
    )

    article_source = InMemoryNewsArticleSource(
        articles={
            "AAPL": (
                "Apple received a regulatory penalty."
            ),
        }
    )

    refresh_service = NewsAnalysisRefreshService(
        analyser=FakeAnalyser(),
        validator=NewsAnalysisValidator(),
        provider=provider,
        article_source=article_source,
    )

    refresh_service.refresh_symbol(
        symbol="AAPL"
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

    trading_loop = TradingLoop(
        symbols=["AAPL"],
        market_data=market_data,
        strategy=BuyTheDipStrategy(),
        execution_service=execution_service,
        interval_seconds=0,
        news_trading_policy=(
            NewsTradingPolicy()
        ),
        news_analysis_provider=provider,
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
    
def test_positive_news_allows_generated_buy_order(
    tmp_path: Path,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={}
    )

    article_source = InMemoryNewsArticleSource(
        articles={
            "AAPL": (
                "Apple reported stronger revenue."
            ),
        }
    )

    refresh_service = NewsAnalysisRefreshService(
        analyser=PositiveFakeAnalyser(),
        validator=NewsAnalysisValidator(),
        provider=provider,
        article_source=article_source,
    )

    refresh_service.refresh_symbol(
        symbol="AAPL"
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

    trading_loop = TradingLoop(
        symbols=["AAPL"],
        market_data=market_data,
        strategy=BuyTheDipStrategy(),
        execution_service=execution_service,
        interval_seconds=0,
        news_trading_policy=(
            NewsTradingPolicy()
        ),
        news_analysis_provider=provider,
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
    assert log_file.exists()
    
def test_missing_news_analysis_does_not_block_order(
    tmp_path: Path,
) -> None:
    log_file = (
        tmp_path
        / "trade_log.jsonl"
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={}
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

    trading_loop = TradingLoop(
        symbols=["AAPL"],
        market_data=market_data,
        strategy=BuyTheDipStrategy(),
        execution_service=execution_service,
        interval_seconds=0,
        news_trading_policy=(
            NewsTradingPolicy()
        ),
        news_analysis_provider=provider,
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
    assert log_file.exists()