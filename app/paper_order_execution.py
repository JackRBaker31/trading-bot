from dataclasses import dataclass
from typing import Protocol

from app.broker import BrokerOrderResult
from app.orders import Order, OrderSide
from app.paper_trading_gate import GateDecision


class MarketOrderBroker(Protocol):
    def place_market_order(
        self,
        ticker: str,
        quantity: float,
        extended_hours: bool = False,
    ) -> BrokerOrderResult:
        """Submit a broker market order."""


@dataclass(frozen=True)
class PaperOrderExecutionResult:
    submitted: bool
    reason: str
    broker_order: BrokerOrderResult | None = None


class PaperOrderExecutionService:
    def __init__(
        self,
        broker: MarketOrderBroker,
        symbol_mapping: dict[str, str],
    ) -> None:
        self.broker = broker

        self.symbol_mapping = {
            local_symbol.upper().strip(): (
                broker_ticker.upper().strip()
            )
            for local_symbol, broker_ticker
            in symbol_mapping.items()
        }

        if any(
            not local_symbol or not broker_ticker
            for local_symbol, broker_ticker
            in self.symbol_mapping.items()
        ):
            raise ValueError(
                "Symbol mappings cannot contain "
                "empty symbols or tickers."
            )

    def submit(
        self,
        order: Order,
        gate_decision: GateDecision,
    ) -> PaperOrderExecutionResult:
        if not gate_decision.approved:
            return PaperOrderExecutionResult(
                submitted=False,
                reason=(
                    "Order blocked by paper-trading "
                    f"gate: {gate_decision.reason}"
                ),
            )

        local_symbol = order.symbol.upper().strip()

        broker_ticker = self.symbol_mapping.get(
            local_symbol
        )

        if broker_ticker is None:
            return PaperOrderExecutionResult(
                submitted=False,
                reason=(
                    f"No broker ticker mapping exists "
                    f"for {local_symbol}."
                ),
            )

        broker_quantity = float(
            order.quantity
        )

        if order.side == OrderSide.SELL:
            broker_quantity = -broker_quantity

        broker_order = (
            self.broker.place_market_order(
                ticker=broker_ticker,
                quantity=broker_quantity,
                extended_hours=False,
            )
        )

        return PaperOrderExecutionResult(
            submitted=True,
            reason=(
                "Order submitted to the Trading 212 "
                "demo environment."
            ),
            broker_order=broker_order,
        )