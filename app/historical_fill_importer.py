from dataclasses import dataclass
from typing import Protocol

from app.broker import (
    BrokerOrderResult,
)
from app.portfolio import (
    Portfolio,
)


class HistoricalOrderBroker(Protocol):
    def get_historical_orders(
        self,
    ) -> list[BrokerOrderResult]:
        ...


class PortfolioSaver(Protocol):
    def save(
        self,
        portfolio: Portfolio,
    ) -> None:
        ...


@dataclass(frozen=True)
class HistoricalFillImportResult:
    imported_order_ids: tuple[int, ...]
    skipped_order_ids: tuple[int, ...]


class HistoricalFillImporter:
    def __init__(
        self,
        *,
        broker: HistoricalOrderBroker,
        portfolio: Portfolio,
        portfolio_store: PortfolioSaver,
        symbol_mapping: dict[str, str],
    ) -> None:
        self._broker = broker
        self._portfolio = portfolio
        self._portfolio_store = portfolio_store

        self._broker_to_symbol = {
            broker_ticker.upper().strip(): (
                symbol.upper().strip()
            )
            for symbol, broker_ticker
            in symbol_mapping.items()
        }

    def import_unapplied_fills(
        self,
    ) -> HistoricalFillImportResult:
        imported_order_ids: list[int] = []
        skipped_order_ids: list[int] = []

        for order in (
            self._broker.get_historical_orders()
        ):
            order_id = order.order_id

            if (
                self._portfolio
                .has_applied_broker_order(
                    order_id
                )
            ):
                skipped_order_ids.append(
                    order_id
                )
                continue

            status = order.status.upper().strip()

            if status != "FILLED":
                skipped_order_ids.append(
                    order_id
                )
                continue

            broker_ticker = (
                order.ticker.upper().strip()
            )

            symbol = self._broker_to_symbol.get(
                broker_ticker
            )

            if symbol is None:
                skipped_order_ids.append(
                    order_id
                )
                continue

            filled_quantity = int(
                order.filled_quantity
            )

            if (
                filled_quantity <= 0
                or float(filled_quantity)
                != order.filled_quantity
            ):
                skipped_order_ids.append(
                    order_id
                )
                continue

            if order.filled_value <= 0:
                skipped_order_ids.append(
                    order_id
                )
                continue

            fill_price = (
                order.filled_value
                / order.filled_quantity
            )

            side = order.side.upper().strip()

            if side == "BUY":
                self._portfolio.buy(
                    symbol=symbol,
                    quantity=filled_quantity,
                    price=fill_price,
                )
            elif side == "SELL":
                self._portfolio.sell(
                    symbol=symbol,
                    quantity=filled_quantity,
                    price=fill_price,
                )
            else:
                skipped_order_ids.append(
                    order_id
                )
                continue

            self._portfolio.mark_broker_order_applied(
                order_id
            )

            imported_order_ids.append(
                order_id
            )

        if imported_order_ids:
            self._portfolio_store.save(
                self._portfolio
            )

        return HistoricalFillImportResult(
            imported_order_ids=tuple(
                imported_order_ids
            ),
            skipped_order_ids=tuple(
                skipped_order_ids
            ),
        )