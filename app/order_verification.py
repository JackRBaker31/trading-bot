from dataclasses import dataclass
from enum import Enum

from app.broker import BrokerOrderResult


class OrderVerificationStatus(str, Enum):
    PENDING = "PENDING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class OrderVerificationResult:
    status: OrderVerificationStatus
    reason: str
    broker_order: BrokerOrderResult

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            OrderVerificationStatus.FILLED,
            OrderVerificationStatus.FAILED,
        }

    @property
    def portfolio_update_allowed(self) -> bool:
        return (
            self.status
            == OrderVerificationStatus.FILLED
        )


class OrderVerificationService:
    PENDING_STATUSES = {
        "NEW",
        "PENDING",
        "PENDING_NEW",
        "ACCEPTED",
    }

    PARTIALLY_FILLED_STATUSES = {
        "PARTIALLY_FILLED",
        "PARTIAL",
    }

    FILLED_STATUSES = {
        "FILLED",
        "COMPLETED",
    }

    FAILED_STATUSES = {
        "CANCELLED",
        "CANCELED",
        "REJECTED",
        "EXPIRED",
    }

    def verify(
        self,
        broker_order: BrokerOrderResult,
    ) -> OrderVerificationResult:
        cleaned_status = (
            broker_order.status.upper().strip()
        )

        if cleaned_status in self.PENDING_STATUSES:
            return OrderVerificationResult(
                status=OrderVerificationStatus.PENDING,
                reason=(
                    "The broker order is still pending."
                ),
                broker_order=broker_order,
            )

        if (
            cleaned_status
            in self.PARTIALLY_FILLED_STATUSES
        ):
            return OrderVerificationResult(
                status=(
                    OrderVerificationStatus
                    .PARTIALLY_FILLED
                ),
                reason=(
                    "The broker order is only "
                    "partially filled."
                ),
                broker_order=broker_order,
            )

        if cleaned_status in self.FILLED_STATUSES:
            if broker_order.filled_quantity <= 0:
                return OrderVerificationResult(
                    status=(
                        OrderVerificationStatus.UNKNOWN
                    ),
                    reason=(
                        "The broker reports FILLED, "
                        "but filled quantity is not "
                        "positive."
                    ),
                    broker_order=broker_order,
                )

            return OrderVerificationResult(
                status=OrderVerificationStatus.FILLED,
                reason=(
                    "The broker order is fully filled."
                ),
                broker_order=broker_order,
            )

        if cleaned_status in self.FAILED_STATUSES:
            return OrderVerificationResult(
                status=OrderVerificationStatus.FAILED,
                reason=(
                    "The broker order did not complete."
                ),
                broker_order=broker_order,
            )

        return OrderVerificationResult(
            status=OrderVerificationStatus.UNKNOWN,
            reason=(
                "The broker returned an unknown "
                f"order status: {cleaned_status}."
            ),
            broker_order=broker_order,
        )