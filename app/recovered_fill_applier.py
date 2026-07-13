from dataclasses import dataclass

from app.portfolio import Portfolio
from app.portfolio_store import PortfolioStore
from app.recovered_fill import RecoveredFill


@dataclass(frozen=True)
class RecoveredFillApplicationResult:
    recovered_fill: RecoveredFill
    applied: bool
    reason: str


class RecoveredFillApplier:
    def __init__(
        self,
        portfolio: Portfolio,
        portfolio_store: PortfolioStore,
    ) -> None:
        self.portfolio = portfolio
        self.portfolio_store = portfolio_store

    def apply(
        self,
        recovered_fill: RecoveredFill,
    ) -> RecoveredFillApplicationResult:
        broker_order_id = (
            recovered_fill.broker_order_id
        )

        if self.portfolio.has_applied_broker_order(
            broker_order_id
        ):
            return RecoveredFillApplicationResult(
                recovered_fill=recovered_fill,
                applied=False,
                reason=(
                    "Recovered broker order was "
                    "already applied."
                ),
            )

        original_cash = self.portfolio.cash
        original_positions = (
            self.portfolio.positions.copy()
        )
        original_applied_ids = (
            self.portfolio
            .applied_broker_order_ids
            .copy()
        )

        try:
            if recovered_fill.side == "BUY":
                self.portfolio.buy(
                    symbol=recovered_fill.symbol,
                    quantity=recovered_fill.quantity,
                    price=(
                        recovered_fill
                        .average_fill_price
                    ),
                )
            elif recovered_fill.side == "SELL":
                self.portfolio.sell(
                    symbol=recovered_fill.symbol,
                    quantity=recovered_fill.quantity,
                    price=(
                        recovered_fill
                        .average_fill_price
                    ),
                )
            else:
                raise ValueError(
                    "Recovered fill side must be "
                    "BUY or SELL."
                )

            self.portfolio.mark_broker_order_applied(
                broker_order_id=broker_order_id
            )

            self.portfolio_store.save(
                self.portfolio
            )
        except Exception:
            self.portfolio.cash = original_cash
            self.portfolio.positions = (
                original_positions
            )
            self.portfolio.applied_broker_order_ids = (
                original_applied_ids
            )
            raise

        return RecoveredFillApplicationResult(
            recovered_fill=recovered_fill,
            applied=True,
            reason=(
                "Recovered fill was applied and "
                "persisted."
            ),
        )