from app.broker import BrokerOrderResult
from typing import Protocol

from app.broker import BrokerOrderResult


class ActiveOrderProvider(Protocol):
    def get_active_orders(
        self,
    ) -> list[BrokerOrderResult]:
        ...

class ActiveOrderManager:
    def __init__(
        self,
        *,
        symbol_mapping: dict[str, str],
        active_orders: list[BrokerOrderResult],
        order_provider: ActiveOrderProvider | None = None,
    ) -> None:
        self.symbol_mapping = {
            symbol.upper().strip(): ticker.upper().strip()
            for symbol, ticker in symbol_mapping.items()
        }

        self.active_orders = list(
            active_orders
        )

        self._blocked_tickers = {
            order.ticker.upper().strip()
            for order in self.active_orders
        }
        self.order_provider = order_provider

    def is_symbol_blocked(
        self,
        symbol: str,
    ) -> bool:
        cleaned_symbol = (
            symbol.upper().strip()
        )

        broker_ticker = (
            self.symbol_mapping.get(
                cleaned_symbol
            )
        )

        if broker_ticker is None:
            raise ValueError(
                f"No broker ticker is available "
                f"for {cleaned_symbol}."
            )

        return (
            broker_ticker
            in self._blocked_tickers
        )

    def _rebuild_blocked_tickers(
        self,
    ) -> None:
        self._blocked_tickers = {
            order.ticker.upper().strip()
            for order in self.active_orders
        }

    def refresh(self) -> None:
        if self.order_provider is None:
            return

        active_orders = (
            self.order_provider.get_active_orders()
        )

        self.active_orders = list(active_orders)

        self._rebuild_blocked_tickers()