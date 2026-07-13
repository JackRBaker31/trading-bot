from collections.abc import Callable
from dataclasses import dataclass
from time import sleep
from typing import Protocol

from app.broker import (
    BrokerOrderResult,
    BrokerResourceNotFoundError,
)
from app.order_verification import (
    OrderVerificationService,
    OrderVerificationStatus,
)


class OrderPollingBroker(Protocol):
    def get_pending_order(
        self,
        order_id: int,
    ) -> BrokerOrderResult:
        """Retrieve the current pending order."""

    def find_historical_order(
        self,
        order_id: int,
        max_pages: int = 5,
    ) -> BrokerOrderResult | None:
        """Find an order in broker history."""


@dataclass(frozen=True)
class OrderPollingResult:
    order: BrokerOrderResult | None
    status: OrderVerificationStatus
    reason: str
    attempts: int
    timed_out: bool


class OrderPollingService:
    def __init__(
        self,
        broker: OrderPollingBroker,
        verification_service: OrderVerificationService,
        max_attempts: int = 5,
        poll_interval_seconds: float = 1.0,
        sleep_function: Callable[[float], None] = sleep,
    ) -> None:
        if max_attempts <= 0:
            raise ValueError(
                "Maximum polling attempts must be positive."
            )

        if poll_interval_seconds < 0:
            raise ValueError(
                "Polling interval cannot be negative."
            )

        self.broker = broker
        self.verification_service = verification_service
        self.max_attempts = max_attempts
        self.poll_interval_seconds = poll_interval_seconds
        self.sleep_function = sleep_function

    def poll(
        self,
        order_id: int,
    ) -> OrderPollingResult:
        if order_id <= 0:
            raise ValueError(
                "Order ID must be positive."
            )

        for attempt in range(1, self.max_attempts + 1):
            try:
                current_order = (
                    self.broker.get_pending_order(
                        order_id=order_id
                    )
                )
            except BrokerResourceNotFoundError:
                historical_order = (
                    self.broker.find_historical_order(
                        order_id=order_id
                    )
                )

                if historical_order is None:
                    return OrderPollingResult(
                        order=None,
                        status=OrderVerificationStatus.UNKNOWN,
                        reason=(
                            "The order was not found in "
                            "pending orders or historical "
                            "orders."
                        ),
                        attempts=attempt,
                        timed_out=False,
                    )

                current_order = historical_order

            verification_result = (
                self.verification_service.verify(
                    current_order
                )
            )

            if verification_result.status in {
                OrderVerificationStatus.FILLED,
                OrderVerificationStatus.FAILED,
                OrderVerificationStatus.UNKNOWN,
            }:
                return OrderPollingResult(
                    order=current_order,
                    status=verification_result.status,
                    reason=verification_result.reason,
                    attempts=attempt,
                    timed_out=False,
                )

            if attempt < self.max_attempts:
                self.sleep_function(
                    self.poll_interval_seconds
                )

        return OrderPollingResult(
            order=current_order,
            status=verification_result.status,
            reason=(
                "The broker order did not reach a terminal "
                "state before polling timed out."
            ),
            attempts=self.max_attempts,
            timed_out=True,
        )