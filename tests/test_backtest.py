from datetime import date
from pathlib import Path

import pytest

from app.backtest import BacktestEngine
from app.buy_the_dip import BuyTheDipStrategy
from app.execution import ExecutionService
from app.historical_data import HistoricalPrice
from app.portfolio import Portfolio
from app.risk import RiskEngine, RiskLimits
from app.trade_log import TradeLog
from app.backtest_result import EquityPoint
from app.backtest_models import HistoricalPriceBar
from app.orders import Order, OrderSide
from app.strategy import Strategy
from app.execution_cost import (
    ExecutionCostModel,
)
from app.position_exit_manager import (
    PositionExitManager,
)
from app.position_exit_policy import (
    PositionExitPolicy,
)

class BuyThenSellStrategy(Strategy):
    def __init__(self) -> None:
        self.call_count = 0

    def generate_orders(
        self,
        prices: dict[str, float],
        portfolio: Portfolio,
    ) -> list[Order]:
        self.call_count += 1

        if self.call_count == 1:
            return [
                Order(
                    symbol="AAPL",
                    side=OrderSide.BUY,
                    quantity=2,
                    price=100.0,
                )
            ]

        if self.call_count == 2:
            return [
                Order(
                    symbol="AAPL",
                    side=OrderSide.SELL,
                    quantity=2,
                    price=110.0,
                )
            ]

        return []

def create_backtest_engine(
    log_file: Path,
) -> tuple[
    BacktestEngine,
    Portfolio,
    TradeLog,
]:
    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        max_trades_per_session=10,
        approved_symbols={"AAPL"},
    )

    trade_log = TradeLog(
        file_path=str(log_file)
    )

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=RiskEngine(limits),
        trade_log=trade_log,
    )

    strategy = BuyTheDipStrategy(
        drop_threshold_percent=2.0,
        target_allocation_percent=10.0,
        cooldown_cycles=2,
    )

    engine = BacktestEngine(
        portfolio=portfolio,
        strategy=strategy,
        execution_service=execution_service,
    )

    return engine, portfolio, trade_log


def test_backtest_executes_strategy_order(
    tmp_path: Path,
) -> None:
    engine, portfolio, trade_log = (
        create_backtest_engine(
            tmp_path / "trade_log.jsonl"
        )
    )

    prices = [
        HistoricalPrice(
            trading_date=date(2026, 1, 2),
            prices={"AAPL": 150.00},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 3),
            prices={"AAPL": 146.00},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 4),
            prices={"AAPL": 150.00},
        ),
    ]

    result = engine.run(
        historical_prices=prices
    )

    assert portfolio.positions["AAPL"] == 6
    assert result.executed_trades == 1
    assert result.rejected_orders == 0
    assert result.profit_factor == 0.0
    assert len(result.equity_curve) == 3
    assert len(trade_log.entries) == 1
    assert result.average_winning_trade == 0.0
    assert result.average_losing_trade == 0.0
    assert result.largest_winning_trade == 0.0
    assert result.largest_losing_trade == 0.0
    assert result.expectancy == 0.0
    assert result.win_rate_percent == 0.0
    assert result.maximum_consecutive_wins == 0
    assert result.maximum_consecutive_losses == 0
    assert (
        result.completed_trade_returns_percent
        == []
    )


def test_backtest_exposes_completed_trade_returns(
    tmp_path: Path,
) -> None:
    portfolio = Portfolio(
        starting_cash=10_000.0
    )

    trade_log = TradeLog(
        file_path=str(
            tmp_path / "trade_log.jsonl"
        )
    )

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=RiskEngine(
            RiskLimits(
                max_order_value=2_000.0,
                max_position_value=3_000.0,
                max_portfolio_exposure=0.5,
                max_trades_per_session=10,
                approved_symbols={"AAPL"},
            )
        ),
        trade_log=trade_log,
    )

    engine = BacktestEngine(
        portfolio=portfolio,
        strategy=BuyThenSellStrategy(),
        execution_service=execution_service,
    )

    result = engine.run(
        historical_prices=[
            HistoricalPrice(
                trading_date=date(2026, 1, 2),
                prices={"AAPL": 100.0},
            ),
            HistoricalPrice(
                trading_date=date(2026, 1, 3),
                prices={"AAPL": 110.0},
            ),
        ]
    )

    assert result.executed_trades == 2
    assert (
        result.completed_trade_returns_percent
        == pytest.approx(
            [
                10.0,
            ]
        )
    )

def test_execution_costs_do_not_change_exit_signal_path(
    tmp_path: Path,
) -> None:
    historical_prices = [
        HistoricalPrice(
            trading_date=date(2026, 1, 1),
            prices={
                "AAPL": 100.0,
            },
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 2),
            prices={
                "AAPL": 110.0,
            },
        ),
    ]

    exit_manager = PositionExitManager(
        policy=PositionExitPolicy(
            stop_loss_percent=5.0,
            take_profit_percent=10.0,
            trailing_stop_percent=4.0,
            trailing_activation_percent=6.0,
        )
    )

    gross_portfolio = Portfolio(
        starting_cash=10_000.0
    )

    gross_service = ExecutionService(
        portfolio=gross_portfolio,
        risk_engine=RiskEngine(
            RiskLimits(
                max_order_value=5_000.0,
                max_position_value=5_000.0,
                max_portfolio_exposure=1.0,
                max_trades_per_session=10,
                approved_symbols={"AAPL"},
            )
        ),
        trade_log=TradeLog(
            file_path=str(
                tmp_path / "gross.jsonl"
            )
        ),
        execution_cost_model=ExecutionCostModel(),
    )

    gross_engine = BacktestEngine(
        portfolio=gross_portfolio,
        strategy=BuyThenSellStrategy(),
        execution_service=gross_service,
        position_exit_manager=exit_manager,
    )

    net_portfolio = Portfolio(
        starting_cash=10_000.0
    )

    net_service = ExecutionService(
        portfolio=net_portfolio,
        risk_engine=RiskEngine(
            RiskLimits(
                max_order_value=5_000.0,
                max_position_value=5_000.0,
                max_portfolio_exposure=1.0,
                max_trades_per_session=10,
                approved_symbols={"AAPL"},
            )
        ),
        trade_log=TradeLog(
            file_path=str(
                tmp_path / "net.jsonl"
            )
        ),
        execution_cost_model=ExecutionCostModel(
            slippage_percent=0.10,
            commission_percent=0.10,
        ),
    )

    net_engine = BacktestEngine(
        portfolio=net_portfolio,
        strategy=BuyThenSellStrategy(),
        execution_service=net_service,
        position_exit_manager=exit_manager,
    )

    gross_result = gross_engine.run(
        historical_prices=historical_prices
    )

    net_result = net_engine.run(
        historical_prices=historical_prices
    )

    assert (
        gross_result.executed_trades
        == net_result.executed_trades
    )

    assert (
        len(
            gross_result
            .completed_trade_profits
        )
        == len(
            net_result
            .completed_trade_profits
        )
    )

    assert (
        net_result.completed_trade_profits[0]
        < gross_result.completed_trade_profits[0]
    )

def test_backtest_calculates_return(
    tmp_path: Path,
) -> None:
    engine, _, _ = create_backtest_engine(
        tmp_path / "trade_log.jsonl"
    )

    prices = [
        HistoricalPrice(
            trading_date=date(2026, 1, 2),
            prices={"AAPL": 150.00},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 3),
            prices={"AAPL": 146.00},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 4),
            prices={"AAPL": 156.00},
        ),
    ]

    result = engine.run(
        historical_prices=prices
    )

    assert result.starting_cash == 10_000.00
    assert result.ending_value == 10_060.00
    assert result.total_return_percent == pytest.approx(
        0.60
    )
    assert result.maximum_drawdown_percent >= 0
    assert result.benchmark_return_percent == pytest.approx(
        4.0
    )
    assert result.excess_return_percent == pytest.approx(
        -3.4
    )
    assert result.average_exposure_percent > 0

def test_backtest_rejects_empty_history(
    tmp_path: Path,
) -> None:
    engine, _, _ = create_backtest_engine(
        tmp_path / "trade_log.jsonl"
    )

    with pytest.raises(
        ValueError,
        match="At least one historical price point",
    ):
        engine.run(
            historical_prices=[]
        )


def test_backtest_records_rejected_orders(
    tmp_path: Path,
) -> None:
    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    limits = RiskLimits(
        max_order_value=100.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        max_trades_per_session=10,
        approved_symbols={"AAPL"},
    )

    trade_log = TradeLog(
        file_path=str(
            tmp_path / "trade_log.jsonl"
        )
    )

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=RiskEngine(limits),
        trade_log=trade_log,
    )

    strategy = BuyTheDipStrategy(
        drop_threshold_percent=2.0,
        target_allocation_percent=10.0,
        cooldown_cycles=2,
    )

    engine = BacktestEngine(
        portfolio=portfolio,
        strategy=strategy,
        execution_service=execution_service,
    )

    prices = [
        HistoricalPrice(
            trading_date=date(2026, 1, 2),
            prices={"AAPL": 150.00},
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 3),
            prices={"AAPL": 146.00},
        ),
    ]

    result = engine.run(
        historical_prices=prices
    )

    assert result.executed_trades == 0
    assert result.rejected_orders == 1

def test_maximum_drawdown_is_calculated() -> None:
    equity_curve = [
        EquityPoint(
            label="2026-01-01",
            portfolio_value=10_000.00,
        ),
        EquityPoint(
            label="2026-01-02",
            portfolio_value=11_000.00,
        ),
        EquityPoint(
            label="2026-01-03",
            portfolio_value=9_900.00,
        ),
        EquityPoint(
            label="2026-01-04",
            portfolio_value=10_500.00,
        ),
    ]

    drawdown = (
        BacktestEngine._calculate_maximum_drawdown(
            equity_curve
        )
    )

    assert drawdown == pytest.approx(
        10.0
    )


def test_equal_weight_benchmark_is_calculated() -> None:
    historical_prices = [
        HistoricalPrice(
            trading_date=date(2026, 1, 2),
            prices={
                "AAPL": 100.00,
                "MSFT": 200.00,
            },
        ),
        HistoricalPrice(
            trading_date=date(2026, 1, 3),
            prices={
                "AAPL": 110.00,
                "MSFT": 180.00,
            },
        ),
    ]

    benchmark_return = (
        BacktestEngine
        ._calculate_equal_weight_benchmark_return(
            historical_prices
        )
    )

    assert benchmark_return == pytest.approx(
        0.0
    )

def test_backtest_can_run_historical_price_bars(
    tmp_path: Path,
) -> None:
    engine, portfolio, trade_log = (
        create_backtest_engine(
            tmp_path / "trade_log.jsonl"
        )
    )

    bars = [
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 1, 2),
            open_price=149.0,
            high_price=152.0,
            low_price=148.0,
            close_price=150.0,
            volume=1_000,
        ),
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 1, 3),
            open_price=149.0,
            high_price=150.0,
            low_price=145.0,
            close_price=146.0,
            volume=1_100,
        ),
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 1, 4),
            open_price=147.0,
            high_price=151.0,
            low_price=146.0,
            close_price=150.0,
            volume=1_200,
        ),
    ]

    result = engine.run_bars(
        bars=bars
    )

    assert portfolio.positions["AAPL"] == 6
    assert result.executed_trades == 1
    assert result.rejected_orders == 0
    assert len(result.equity_curve) == 3
    assert len(trade_log.entries) == 1


def test_backtest_rejects_empty_price_bars(
    tmp_path: Path,
) -> None:
    engine, _, _ = create_backtest_engine(
        tmp_path / "trade_log.jsonl"
    )

    with pytest.raises(
        ValueError,
        match="At least one historical price bar",
    ):
        engine.run_bars(
            bars=[]
        )


def test_backtest_rejects_duplicate_symbol_bar_for_date(
    tmp_path: Path,
) -> None:
    engine, _, _ = create_backtest_engine(
        tmp_path / "trade_log.jsonl"
    )

    bars = [
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 1, 2),
            open_price=149.0,
            high_price=152.0,
            low_price=148.0,
            close_price=150.0,
            volume=1_000,
        ),
        HistoricalPriceBar(
            symbol="AAPL",
            trading_date=date(2026, 1, 2),
            open_price=150.0,
            high_price=153.0,
            low_price=149.0,
            close_price=151.0,
            volume=1_100,
        ),
    ]

    with pytest.raises(
        ValueError,
        match=(
            "Duplicate historical price bar "
            "for AAPL on 2026-01-02"
        ),
    ):
        engine.run_bars(
            bars=bars
        )

def test_backtest_completed_profit_includes_execution_costs(
    tmp_path: Path,
) -> None:
    portfolio = Portfolio(
        starting_cash=10_000.0
    )

    trade_log = TradeLog(
        file_path=str(
            tmp_path / "trade_log.jsonl"
        )
    )

    execution_service = ExecutionService(
        portfolio=portfolio,
        risk_engine=RiskEngine(
            RiskLimits(
                max_order_value=5_000.0,
                max_position_value=5_000.0,
                max_portfolio_exposure=1.0,
                max_trades_per_session=10,
                approved_symbols={"AAPL"},
            )
        ),
        trade_log=trade_log,
        execution_cost_model=ExecutionCostModel(
            slippage_percent=1.0,
            commission_percent=0.5,
        ),
    )

    engine = BacktestEngine(
        portfolio=portfolio,
        strategy=BuyThenSellStrategy(),
        execution_service=execution_service,
    )

    result = engine.run(
        historical_prices=[
            HistoricalPrice(
                trading_date=date(
                    2026,
                    1,
                    2,
                ),
                prices={
                    "AAPL": 100.0,
                },
            ),
            HistoricalPrice(
                trading_date=date(
                    2026,
                    1,
                    3,
                ),
                prices={
                    "AAPL": 110.0,
                },
            ),
        ]
    )

    assert result.completed_trade_profits == pytest.approx(
        [
            13.701,
        ]
    )