import logging
from datetime import datetime

from app.market_session import MarketSession
from app.orders import Order
from app.paper_order_workflow import (
    PaperOrderWorkflow,
)
from app.paper_trading_gate import (
    PaperTradingGate,
)
from app.portfolio import Portfolio
from app.risk import RiskEngine
from app.trade_log import TradeLog, TradeLogEntry


logger = logging.getLogger(__name__)


class PaperExecutionAdapter:
    def __init__(
        self,
        workflow: PaperOrderWorkflow,
        gate: PaperTradingGate,
        portfolio: Portfolio,
        risk_engine: RiskEngine,
        trade_log: TradeLog,
        paper_trading_enabled: bool,
        broker_environment: str,
        order_execution_permission_confirmed: bool,
        reconciliation_passed: bool,
        market_session: MarketSession | None = None,
        enforce_market_hours: bool = False,
    ) -> None:
        self.workflow = workflow
        self.gate = gate
        self.portfolio = portfolio
        self.risk_engine = risk_engine
        self.trade_log = trade_log
        self.paper_trading_enabled = (
            paper_trading_enabled
        )
        self.broker_environment = (
            broker_environment
        )
        self.order_execution_permission_confirmed = (
            order_execution_permission_confirmed
        )
        self.reconciliation_passed = (
            reconciliation_passed
        )
        self.market_session = market_session
        self.enforce_market_hours = (
            enforce_market_hours
        )

    def submit_order(
        self,
        order: Order,
        current_prices: dict[str, float],
    ) -> bool:
        logger.info(
            "paper_order_received "
            "symbol=%s side=%s quantity=%s "
            "price=%.2f value=%.2f",
            order.symbol,
            order.side.value,
            order.quantity,
            order.price,
            order.value,
        )

        risk_decision = self.risk_engine.evaluate(
            order=order,
            portfolio=self.portfolio,
            current_prices=current_prices,
        )

        market_is_open = True

        if self.enforce_market_hours:
            if self.market_session is None:
                raise RuntimeError(
                    "Market-hours enforcement is "
                    "enabled but no market session "
                    "was supplied."
                )

            market_is_open = (
                self.market_session
                .get_status()
                .is_open
            )

        gate_decision = self.gate.evaluate(
            paper_trading_enabled=(
                self.paper_trading_enabled
            ),
            broker_environment=(
                self.broker_environment
            ),
            reconciliation_passed=(
                self.reconciliation_passed
            ),
            market_is_open=market_is_open,
            risk_approved=risk_decision.approved,
            order_execution_permission_confirmed=(
                self
                .order_execution_permission_confirmed
            ),
        )

        result = self.workflow.execute(
            order=order,
            gate_decision=gate_decision,
        )

        executed = result.portfolio_updated

        if executed:
            self.risk_engine.record_executed_trade()

        reason = result.reason

        if not gate_decision.approved:
            reason = gate_decision.reason

        self.trade_log.add(
            TradeLogEntry(
                timestamp=datetime.now(),
                symbol=order.symbol,
                side=order.side.value,
                quantity=order.quantity,
                price=order.price,
                order_value=order.value,
                approved=gate_decision.approved,
                reason=reason,
                executed=executed,
            )
        )

        if executed:
            logger.info(
                "paper_order_completed "
                "symbol=%s side=%s quantity=%s",
                order.symbol,
                order.side.value,
                order.quantity,
            )
        else:
            logger.warning(
                "paper_order_not_completed "
                "symbol=%s side=%s reason=%s",
                order.symbol,
                order.side.value,
                reason,
            )

        return executed