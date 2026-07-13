from dataclasses import dataclass

from app.order_journal import OrderJournal
from app.order_polling import OrderPollingService
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
from app.duplicate_order_guard import (
    DuplicateOrderGuard,
)


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
        polling_service: OrderPollingService,
        verification_service: OrderVerificationService,
        duplicate_order_guard: DuplicateOrderGuard,
        order_journal: OrderJournal,
        portfolio: Portfolio,
        quantity_tolerance: float = 0.000001,
    ) -> None:
        if quantity_tolerance < 0:
            raise ValueError(
                "Quantity tolerance cannot be negative."
            )

        self.execution_service = execution_service
        self.polling_service = polling_service
        self.verification_service = verification_service
        self.duplicate_order_guard = duplicate_order_guard
        self.order_journal = order_journal
        self.portfolio = portfolio
        self.quantity_tolerance = quantity_tolerance

    def _record_non_terminal_verification_event(
        self,
        order: Order,
        verification_result: OrderVerificationResult,
    ) -> None:
        event_by_status = {
            OrderVerificationStatus.PENDING: "PENDING",
            OrderVerificationStatus.PARTIALLY_FILLED: (
                "PARTIALLY_FILLED"
            ),
        }

        event = event_by_status.get(
            verification_result.status
        )

        if event is None:
            return

        self.order_journal.record(
            order=order,
            event=event,
            broker_order_id=(
                verification_result.broker_order.order_id
            ),
            reason=verification_result.reason,
        )

    def execute(
        self,
        order: Order,
        gate_decision: GateDecision,
    ) -> PaperOrderWorkflowResult:
        reservation_result = (
            self.duplicate_order_guard.reserve(order)
        )

        if not reservation_result.approved:
            return PaperOrderWorkflowResult(
                submitted=False,
                portfolio_updated=False,
                reason=reservation_result.reason,
            )
        
        self.order_journal.record(
            order=order,
            event="RESERVED",
            reason=reservation_result.reason,
        )

        try:
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

            submitted_order = execution_result.broker_order

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

            self.order_journal.record(
                order=order,
                event="SUBMITTED",
                broker_order_id=submitted_order.order_id,
                reason=execution_result.reason,
            )

            polling_result = self.polling_service.poll(
                order_id=submitted_order.order_id
            )

            current_order = polling_result.order

            if current_order is None:
                return PaperOrderWorkflowResult(
                    submitted=True,
                    portfolio_updated=False,
                    reason=polling_result.reason,
                    execution_result=execution_result,
                )

            verification_result = OrderVerificationResult(
                broker_order=current_order,
                status=polling_result.status,
                reason=polling_result.reason,
            )

            self._record_non_terminal_verification_event(
                order=order,
                verification_result=verification_result,
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
                    verification_result=verification_result,
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
                    verification_result=verification_result,
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
                    verification_result=verification_result,
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
                    verification_result=verification_result,
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

            self.order_journal.record(
                order=order,
                event="FILLED",
                broker_order_id=current_order.order_id,
                reason=verification_result.reason,
            )

            return PaperOrderWorkflowResult(
                submitted=True,
                portfolio_updated=True,
                reason=(
                    "Broker order was fully filled and "
                    "the local portfolio was updated."
                ),
                execution_result=execution_result,
                verification_result=verification_result,
            )

        finally:
            self.duplicate_order_guard.release(order)