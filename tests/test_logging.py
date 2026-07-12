import logging
from pathlib import Path

from app.execution import ExecutionService
from app.logging_config import setup_logging
from app.orders import Order, OrderSide
from app.portfolio import Portfolio
from app.portfolio_store import PortfolioStore
from app.risk import RiskEngine, RiskLimits
from app.trade_log import TradeLog


def flush_logging_handlers() -> None:
    for handler in logging.getLogger().handlers:
        handler.flush()


def test_setup_logging_writes_message_to_file(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "application.log"

    setup_logging(
        log_file=str(log_file),
        level=logging.INFO,
    )

    logger = logging.getLogger("tests.logging")
    logger.info("test_event symbol=AAPL")

    flush_logging_handlers()

    contents = log_file.read_text(
        encoding="utf-8"
    )

    assert "test_event symbol=AAPL" in contents
    assert "INFO" in contents


def test_setup_logging_does_not_duplicate_its_handlers(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "application.log"

    setup_logging(
        log_file=str(log_file),
    )

    setup_logging(
        log_file=str(log_file),
    )

    managed_handlers = [
        handler
        for handler in logging.getLogger().handlers
        if getattr(
            handler,
            "_trading_bot_handler",
            False,
        )
    ]

    assert len(managed_handlers) == 2


def test_rejected_order_is_logged(
    tmp_path: Path,
    caplog,
) -> None:
    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    limits = RiskLimits(
        max_order_value=2_000.00,
        max_position_value=3_000.00,
        max_portfolio_exposure=0.50,
        max_trades_per_session=3,
        approved_symbols={"AAPL"},
    )

    service = ExecutionService(
        portfolio=portfolio,
        risk_engine=RiskEngine(limits),
        trade_log=TradeLog(
            file_path=str(
                tmp_path / "trade_log.jsonl"
            )
        ),
    )

    order = Order(
        symbol="TSLA",
        side=OrderSide.BUY,
        quantity=1,
        price=250.00,
    )

    with caplog.at_level(
        logging.WARNING,
        logger="app.execution",
    ):
        service.submit_order(
            order=order,
            current_prices={"TSLA": 250.00},
        )

    assert "order_rejected" in caplog.text
    assert "TSLA" in caplog.text


def test_portfolio_save_is_logged(
    tmp_path: Path,
    caplog,
) -> None:
    store = PortfolioStore(
        file_path=str(
            tmp_path / "portfolio.json"
        )
    )

    portfolio = Portfolio(
        starting_cash=10_000.00
    )

    with caplog.at_level(
        logging.INFO,
        logger="app.portfolio_store",
    ):
        store.save(portfolio)

    assert "portfolio_saved" in caplog.text