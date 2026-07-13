from dataclasses import dataclass

from app.recovery_plan import (
    RecoveryAction,
    RecoveryPlanItem,
)
from app.order_verification import (
    OrderVerificationStatus,
)


@dataclass(frozen=True)
class RecoveredFill:
    broker_order_id: int
    reservation_key: str
    symbol: str
    side: str
    quantity: int
    filled_value: float
    average_fill_price: float


class RecoveredFillValidator:
    def __init__(
        self,
        quantity_tolerance: float = 0.000001,
    ) -> None:
        if quantity_tolerance < 0:
            raise ValueError(
                "Quantity tolerance cannot be negative."
            )

        self.quantity_tolerance = quantity_tolerance

    def validate(
        self,
        plan_item: RecoveryPlanItem,
    ) -> RecoveredFill:
        if (
            plan_item.action
            != RecoveryAction.UPDATE_PORTFOLIO
        ):
            raise ValueError(
                "Recovery plan does not require a "
                "portfolio update."
            )

        recovery_item = plan_item.recovery_item
        polling_result = recovery_item.polling_result

        if polling_result is None:
            raise ValueError(
                "Recovered fill requires a broker "
                "polling result."
            )

        if (
            polling_result.status
            != OrderVerificationStatus.FILLED
        ):
            raise ValueError(
                "Recovered fill requires FILLED "
                "broker status."
            )

        broker_order = polling_result.order

        if broker_order is None:
            raise ValueError(
                "Recovered fill requires broker "
                "order information."
            )

        journal_entry = recovery_item.journal_entry

        if broker_order.order_id <= 0:
            raise ValueError(
                "Recovered fill requires a valid "
                "broker order ID."
            )

        if (
            journal_entry.broker_order_id is not None
            and broker_order.order_id
            != journal_entry.broker_order_id
        ):
            raise ValueError(
                "Recovered broker order ID does not "
                "match the journal."
            )

        journal_side = journal_entry.side.strip().upper()
        broker_side = broker_order.side.strip().upper()

        if broker_side != journal_side:
            raise ValueError(
                "Recovered broker side does not "
                "match the journal."
            )

        expected_quantity = float(
            journal_entry.quantity
        )
        filled_quantity = abs(
            float(broker_order.filled_quantity)
        )

        if (
            abs(
                filled_quantity
                - expected_quantity
            )
            > self.quantity_tolerance
        ):
            raise ValueError(
                "Recovered filled quantity does not "
                "match the journal."
            )

        filled_value = float(
            broker_order.filled_value
        )

        if filled_value <= 0:
            raise ValueError(
                "Recovered fill has an invalid "
                "filled value."
            )

        average_fill_price = (
            filled_value / filled_quantity
        )

        return RecoveredFill(
            broker_order_id=broker_order.order_id,
            reservation_key=(
                journal_entry.reservation_key
            ),
            symbol=journal_entry.symbol,
            side=journal_side,
            quantity=journal_entry.quantity,
            filled_value=filled_value,
            average_fill_price=average_fill_price,
        )