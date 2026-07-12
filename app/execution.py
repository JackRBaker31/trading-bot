import logging
from datetime import datetime

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
    ) -> None:
        self.portfolio = portfolio
        self.risk_engine = risk_engine
        self.trade_log = trade_log

    def submit_order(
        self,
        order: Order,
        current_prices: dict[str, float],
    ) -> bool:
        logger.info(
            "order_received symbol=%s side=%s quantity=%s price=%.2f value=%.2f",
            order.symbol,
            order.side.value,
            order.quantity,
            order.price,
            order.value,
        )

        decision = self.risk_engine.evaluate(
            order=order,
            portfolio=self.portfolio,
            current_prices=current_prices,
        )

        executed = False

        if decision.approved:
            if order.side == OrderSide.BUY:
                self.portfolio.buy(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    price=order.price,
                )
            else:
                self.portfolio.sell(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    price=order.price,
                )

            self.risk_engine.record_executed_trade()
            executed = True

            logger.info(
                "order_executed symbol=%s side=%s quantity=%s "
                "price=%.2f session_trade_count=%s",
                order.symbol,
                order.side.value,
                order.quantity,
                order.price,
                self.risk_engine.executed_trade_count,
            )
        else:
            logger.warning(
                "order_rejected symbol=%s side=%s reason=%s",
                order.symbol,
                order.side.value,
                decision.reason,
            )

        entry = TradeLogEntry(
            timestamp=datetime.now(),
            symbol=order.symbol,
            side=order.side.value,
            quantity=order.quantity,
            price=order.price,
            order_value=order.value,
            approved=decision.approved,
            reason=decision.reason,
            executed=executed,
        )

        self.trade_log.add(entry)

        return executed