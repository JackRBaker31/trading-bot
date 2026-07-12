import os

from dotenv import load_dotenv

from app.config import load_config
from app.logging_config import setup_logging
from app.market_session import MarketSession
from app.orders import Order, OrderSide
from app.paper_trading_gate import PaperTradingGate
from app.portfolio_store import PortfolioStore
from app.reconciliation import BrokerReconciler
from app.risk import RiskEngine, RiskLimits
from app.trading212_client import Trading212Client


def main() -> None:
    setup_logging()
    load_dotenv()

    config = load_config()

    api_key = os.getenv(
        "TRADING212_DEMO_API_KEY",
        "",
    ).strip()

    api_secret = os.getenv(
        "TRADING212_DEMO_API_SECRET",
        "",
    ).strip()

    if not api_key:
        raise RuntimeError(
            "TRADING212_DEMO_API_KEY was not found."
        )

    if not api_secret:
        raise RuntimeError(
            "TRADING212_DEMO_API_SECRET was not found."
        )

    client = Trading212Client(
        api_key=api_key,
        api_secret=api_secret,
        environment=(
            config.paper_trading.broker_environment
        ),
    )

    account_summary = client.get_account_summary()
    broker_positions = client.get_positions()

    portfolio = PortfolioStore().load_or_create(
        starting_cash=config.starting_cash
    )

    reconciler = BrokerReconciler(
        symbol_mapping={
            "AAPL": "AAPL_US_EQ",
            "MSFT": "MSFT_US_EQ",
        }
    )

    reconciliation_report = reconciler.reconcile(
        portfolio=portfolio,
        account_summary=account_summary,
        broker_positions=broker_positions,
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
            config.market_session.trading_weekdays
        ),
    )

    session_status = market_session.get_status()

    risk_limits = RiskLimits(
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

    risk_engine = RiskEngine(
        limits=risk_limits
    )

    proposed_order = Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        price=150.00,
    )

    current_prices = {
        "AAPL": 150.00,
        "MSFT": 320.00,
    }

    risk_decision = risk_engine.evaluate(
        order=proposed_order,
        portfolio=portfolio,
        current_prices=current_prices,
    )

    gate = PaperTradingGate()

    gate_decision = gate.evaluate(
        paper_trading_enabled=(
            config.paper_trading.enabled
        ),
        broker_environment=(
            config.paper_trading.broker_environment
        ),
        reconciliation_passed=(
            reconciliation_report.safe_to_trade
        ),
        market_is_open=session_status.is_open,
        risk_approved=risk_decision.approved,
    )

    print("\n================================")
    print("PAPER TRADING DRY RUN")
    print("================================")
    print(
        f"Paper trading enabled: "
        f"{config.paper_trading.enabled}"
    )
    print(
        f"Broker environment: "
        f"{config.paper_trading.broker_environment}"
    )
    print(
        f"Reconciliation passed: "
        f"{reconciliation_report.safe_to_trade}"
    )
    print(
        f"Market open: "
        f"{session_status.is_open}"
    )
    print(
        f"Market status: "
        f"{session_status.reason}"
    )
    print(
        f"Risk approved: "
        f"{risk_decision.approved}"
    )
    print(
        f"Risk reason: "
        f"{risk_decision.reason}"
    )
    print(
        f"Gate approved: "
        f"{gate_decision.approved}"
    )
    print(
        f"Gate reason: "
        f"{gate_decision.reason}"
    )
    print("================================")
    print("\nNo order was submitted.")


if __name__ == "__main__":
    main()