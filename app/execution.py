import logging
from datetime import datetime

from app.execution_cost import (
    ExecutionCostModel,
)
from app.orders import Order, OrderSide
from app.portfolio import Portfolio
from app.risk import RiskEngine
from app.trade_log import TradeLog, TradeLogEntry


logger = logging.getLogger(__name__)


class ExecutionService:
    def __init__(
        self,
        portfolio: Portfolio,
        risk_engine: RiskEngine,
        trade_log: TradeLog,
        execution_cost_model: (
            ExecutionCostModel | None
        ) = None,
    ) -> None:
        self.portfolio = portfolio
        self.risk_engine = risk_engine
        self.trade_log = trade_log
        self.execution_cost_model = (
            execution_cost_model
            or ExecutionCostModel()
        )

    def submit_order(
        self,
        order: Order,
        current_prices: dict[str, float],
    ) -> bool:
        logger.info(
            "order_received symbol=%s side=%s "
            "quantity=%s price=%.2f value=%.2f",
            order.symbol,
            order.side.value,
            order.quantity,
            order.price,
            order.value,
        )

        cost_result = (
            self.execution_cost_model.calculate(
                order=order
            )
        )

        fee_per_share = (
            cost_result.fee
            / order.quantity
        )

        if order.side is OrderSide.BUY:
            effective_price = (
                cost_result.fill_price
                + fee_per_share
            )
        else:
            effective_price = (
                cost_result.fill_price
                - fee_per_share
            )

        if effective_price <= 0:
            raise ValueError(
                "Execution costs produced a "
                "non-positive effective price."
            )

        execution_order = Order(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=effective_price,
        )

        decision = self.risk_engine.evaluate(
            order=execution_order,
            portfolio=self.portfolio,
            current_prices=current_prices,
        )

        executed = False

        if decision.approved:
            if execution_order.side is OrderSide.BUY:
                self.portfolio.buy(
                    symbol=execution_order.symbol,
                    quantity=execution_order.quantity,
                    price=execution_order.price,
                )
            else:
                self.portfolio.sell(
                    symbol=execution_order.symbol,
                    quantity=execution_order.quantity,
                    price=execution_order.price,
                )

            self.risk_engine.record_executed_trade()
            executed = True

            logger.info(
                "order_executed symbol=%s side=%s "
                "quantity=%s requested_price=%.2f "
                "fill_price=%.4f fee=%.4f "
                "effective_price=%.4f "
                "session_trade_count=%s",
                execution_order.symbol,
                execution_order.side.value,
                execution_order.quantity,
                order.price,
                cost_result.fill_price,
                cost_result.fee,
                execution_order.price,
                self.risk_engine.executed_trade_count,
            )
        else:
            logger.warning(
                "order_rejected symbol=%s side=%s "
                "reason=%s",
                execution_order.symbol,
                execution_order.side.value,
                decision.reason,
            )

        entry = TradeLogEntry(
            timestamp=datetime.now(),
            symbol=execution_order.symbol,
            side=execution_order.side.value,
            quantity=execution_order.quantity,
            price=execution_order.price,
            order_value=execution_order.value,
            approved=decision.approved,
            reason=decision.reason,
            executed=executed,
        )

        self.trade_log.add(entry)

        return executed