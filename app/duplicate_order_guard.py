from dataclasses import dataclass

from app.orders import Order


@dataclass(frozen=True)
class OrderReservationResult:
    approved: bool
    reason: str
    reservation_key: str


class DuplicateOrderGuard:
    def __init__(self) -> None:
        self._active_reservations: set[str] = set()

    def create_reservation_key(
        self,
        order: Order,
    ) -> str:
        symbol = order.symbol.strip().upper()

        return (
            f"{symbol}:"
            f"{order.side.value}:"
            f"{order.quantity}"
        )

    def reserve(
        self,
        order: Order,
    ) -> OrderReservationResult:
        reservation_key = self.create_reservation_key(
            order
        )

        if reservation_key in self._active_reservations:
            return OrderReservationResult(
                approved=False,
                reason=(
                    "An identical order is already being "
                    "processed."
                ),
                reservation_key=reservation_key,
            )

        self._active_reservations.add(
            reservation_key
        )

        return OrderReservationResult(
            approved=True,
            reason="Order reservation created.",
            reservation_key=reservation_key,
        )

    def release(
        self,
        order: Order,
    ) -> None:
        reservation_key = self.create_reservation_key(
            order
        )

        self._active_reservations.discard(
            reservation_key
        )

    def is_reserved(
        self,
        order: Order,
    ) -> bool:
        reservation_key = self.create_reservation_key(
            order
        )

        return (
            reservation_key
            in self._active_reservations
        )