from dataclasses import dataclass
from typing import Protocol

from app.broker import BrokerOrderResult
from app.order_verification import (
    OrderVerificationResult,
    OrderVerificationService,
    OrderVerificationStatus,
)
from app.orders import Order, OrderSide
from app.paper_order_execution import (
    PaperOrderExecutionResult,
    PaperOrderExecutionService,
)
from app.paper_trading_gate import GateDecision
from app.portfolio import Portfolio


class OrderStatusBroker(Protocol):
    def get_pending_order(
        self,
        order_id: int,
    ) -> BrokerOrderResult:
        """Retrieve the latest broker order state."""


@dataclass(frozen=True)
class PaperOrderWorkflowResult:
    submitted: bool
    portfolio_updated: bool
    reason: str
    execution_result: (
        PaperOrderExecutionResult | None
    ) = None
    verification_result: (
        OrderVerificationResult | None
    ) = None


class PaperOrderWorkflow:
    def __init__(
        self,
        execution_service: PaperOrderExecutionService,
        status_broker: OrderStatusBroker,
        verification_service: OrderVerificationService,
        portfolio: Portfolio,
        quantity_tolerance: float = 0.000001,
    ) -> None:
        if quantity_tolerance < 0:
            raise ValueError(
                "Quantity tolerance cannot be negative."
            )

        self.execution_service = execution_service
        self.status_broker = status_broker
        self.verification_service = (
            verification_service
        )
        self.portfolio = portfolio
        self.quantity_tolerance = (
            quantity_tolerance
        )

    def execute(
        self,
        order: Order,
        gate_decision: GateDecision,
    ) -> PaperOrderWorkflowResult:
        execution_result = (
            self.execution_service.submit(
                order=order,
                gate_decision=gate_decision,
            )
        )

        if not execution_result.submitted:
            return PaperOrderWorkflowResult(
                submitted=False,
                portfolio_updated=False,
                reason=execution_result.reason,
                execution_result=execution_result,
            )

        submitted_order = (
            execution_result.broker_order
        )

        if submitted_order is None:
            return PaperOrderWorkflowResult(
                submitted=True,
                portfolio_updated=False,
                reason=(
                    "Broker submission returned no "
                    "order information."
                ),
                execution_result=execution_result,
            )

        current_order = (
            self.status_broker.get_pending_order(
                order_id=submitted_order.order_id
            )
        )

        verification_result = (
            self.verification_service.verify(
                current_order
            )
        )

        if (
            verification_result.status
            != OrderVerificationStatus.FILLED
        ):
            return PaperOrderWorkflowResult(
                submitted=True,
                portfolio_updated=False,
                reason=verification_result.reason,
                execution_result=execution_result,
                verification_result=(
                    verification_result
                ),
            )

        filled_quantity = abs(
            current_order.filled_quantity
        )

        if (
            abs(filled_quantity - order.quantity)
            > self.quantity_tolerance
        ):
            return PaperOrderWorkflowResult(
                submitted=True,
                portfolio_updated=False,
                reason=(
                    "Broker reported FILLED, but the "
                    "filled quantity does not match "
                    "the submitted order."
                ),
                execution_result=execution_result,
                verification_result=(
                    verification_result
                ),
            )

        if not filled_quantity.is_integer():
            return PaperOrderWorkflowResult(
                submitted=True,
                portfolio_updated=False,
                reason=(
                    "Fractional broker fills are not "
                    "supported by the local portfolio."
                ),
                execution_result=execution_result,
                verification_result=(
                    verification_result
                ),
            )

        if current_order.filled_value <= 0:
            return PaperOrderWorkflowResult(
                submitted=True,
                portfolio_updated=False,
                reason=(
                    "Broker reported an invalid "
                    "filled value."
                ),
                execution_result=execution_result,
                verification_result=(
                    verification_result
                ),
            )

        fill_price = (
            current_order.filled_value
            / filled_quantity
        )

        whole_quantity = int(
            filled_quantity
        )

        if order.side == OrderSide.BUY:
            self.portfolio.buy(
                symbol=order.symbol,
                quantity=whole_quantity,
                price=fill_price,
            )
        else:
            self.portfolio.sell(
                symbol=order.symbol,
                quantity=whole_quantity,
                price=fill_price,
            )

        return PaperOrderWorkflowResult(
            submitted=True,
            portfolio_updated=True,
            reason=(
                "Broker order was fully filled and "
                "the local portfolio was updated."
            ),
            execution_result=execution_result,
            verification_result=(
                verification_result
            ),
        )