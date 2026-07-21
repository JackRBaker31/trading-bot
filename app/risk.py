from dataclasses import dataclass, field

from app.orders import Order, OrderSide
from app.portfolio import Portfolio


@dataclass
class RiskLimits:
    max_order_value: float
    max_position_value: float
    max_portfolio_exposure: float
    max_trades_per_session: int
    approved_symbols: set[str] = field(
        default_factory=set
    )

    def __post_init__(self) -> None:
        if self.max_order_value <= 0:
            raise ValueError(
                "Maximum order value must be positive."
            )

        if self.max_position_value <= 0:
            raise ValueError(
                "Maximum position value must be positive."
            )

        if (
            self.max_order_value
            > self.max_position_value
        ):
            raise ValueError(
                "Maximum order value cannot exceed "
                "maximum position value."
            )

        if not (
            0
            < self.max_portfolio_exposure
            <= 1
        ):
            raise ValueError(
                "Maximum portfolio exposure must be "
                "between 0 and 1."
            )

        if self.max_trades_per_session <= 0:
            raise ValueError(
                "Maximum trades per session must be "
                "positive."
            )

        self.approved_symbols = {
            symbol.upper().strip()
            for symbol
            in self.approved_symbols
            if symbol.strip()
        }


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str


class RiskEngine:
    def __init__(
        self,
        limits: RiskLimits,
    ) -> None:
        self.limits = limits
        self.kill_switch_enabled = False
        self.executed_trade_count = 0

    def enable_kill_switch(
        self,
    ) -> None:
        self.kill_switch_enabled = True

    def disable_kill_switch(
        self,
    ) -> None:
        self.kill_switch_enabled = False

    def record_executed_trade(
        self,
    ) -> None:
        self.executed_trade_count += 1

    def reset_session(
        self,
    ) -> None:
        self.executed_trade_count = 0

    def evaluate(
        self,
        order: Order,
        portfolio: Portfolio,
        current_prices: dict[str, float],
    ) -> RiskDecision:
        if self.kill_switch_enabled:
            return RiskDecision(
                approved=False,
                reason=(
                    "Emergency kill switch is enabled."
                ),
            )

        if (
            self.executed_trade_count
            >= self.limits
            .max_trades_per_session
        ):
            return RiskDecision(
                approved=False,
                reason=(
                    "Maximum number of trades for "
                    "this session has been reached."
                ),
            )

        if (
            order.symbol
            not in self.limits.approved_symbols
        ):
            return RiskDecision(
                approved=False,
                reason=(
                    f"{order.symbol} is not on the "
                    "approved-symbol list."
                ),
            )

        if order.value > self.limits.max_order_value:
            return RiskDecision(
                approved=False,
                reason=(
                    f"Order value £{order.value:.2f} "
                    "exceeds the "
                    f"£{self.limits.max_order_value:.2f} "
                    "order limit."
                ),
            )

        if order.side == OrderSide.BUY:
            return self._evaluate_buy(
                order=order,
                portfolio=portfolio,
                current_prices=current_prices,
            )

        return self._evaluate_sell(
            order=order,
            portfolio=portfolio,
        )

    def _evaluate_buy(
        self,
        order: Order,
        portfolio: Portfolio,
        current_prices: dict[str, float],
    ) -> RiskDecision:
        if order.value > portfolio.cash:
            return RiskDecision(
                approved=False,
                reason=(
                    f"Order value £{order.value:.2f} "
                    "exceeds available cash of "
                    f"£{portfolio.cash:.2f}."
                ),
            )

        existing_quantity = (
            portfolio.positions.get(
                order.symbol,
                0,
            )
        )

        proposed_position_value = (
            existing_quantity
            + order.quantity
        ) * order.price

        if (
            proposed_position_value
            > self.limits.max_position_value
        ):
            return RiskDecision(
                approved=False,
                reason=(
                    "Proposed position value "
                    f"£{proposed_position_value:.2f} "
                    "exceeds the "
                    f"£{self.limits.max_position_value:.2f} "
                    "position limit."
                ),
            )

        missing_symbols = sorted(
            symbol
            for symbol in portfolio.positions
            if symbol not in current_prices
        )

        if missing_symbols:
            return RiskDecision(
                approved=False,
                reason=(
                    "Portfolio exposure cannot be "
                    "calculated because current prices "
                    "are unavailable for: "
                    + ", ".join(missing_symbols)
                    + "."
                ),
            )

        invalid_price_symbols = sorted(
            symbol
            for symbol, price
            in current_prices.items()
            if price <= 0
        )

        if invalid_price_symbols:
            return RiskDecision(
                approved=False,
                reason=(
                    "Portfolio exposure cannot be "
                    "calculated because prices are "
                    "not positive for: "
                    + ", ".join(
                        invalid_price_symbols
                    )
                    + "."
                ),
            )

        current_exposure = (
            self._calculate_exposure(
                portfolio=portfolio,
                current_prices=current_prices,
            )
        )

        proposed_exposure = (
            current_exposure
            + order.value
        )

        maximum_exposure = (
            portfolio.starting_cash
            * self.limits
            .max_portfolio_exposure
        )

        if (
            proposed_exposure
            > maximum_exposure
        ):
            return RiskDecision(
                approved=False,
                reason=(
                    "Proposed exposure "
                    f"£{proposed_exposure:.2f} "
                    "exceeds the "
                    f"£{maximum_exposure:.2f} "
                    "portfolio exposure limit."
                ),
            )

        return RiskDecision(
            approved=True,
            reason=(
                "Order passed all risk checks."
            ),
        )

    @staticmethod
    def _evaluate_sell(
        order: Order,
        portfolio: Portfolio,
    ) -> RiskDecision:
        owned_quantity = (
            portfolio.positions.get(
                order.symbol,
                0,
            )
        )

        if order.quantity > owned_quantity:
            return RiskDecision(
                approved=False,
                reason=(
                    f"Cannot sell {order.quantity} "
                    "shares because only "
                    f"{owned_quantity} are owned."
                ),
            )

        return RiskDecision(
            approved=True,
            reason=(
                "Sell order passed all risk checks."
            ),
        )

    @staticmethod
    def _calculate_exposure(
        portfolio: Portfolio,
        current_prices: dict[str, float],
    ) -> float:
        return sum(
            quantity
            * current_prices[symbol]
            for symbol, quantity
            in portfolio.positions.items()
        )