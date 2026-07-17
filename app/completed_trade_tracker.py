from dataclasses import dataclass


@dataclass(frozen=True)
class CompletedTrade:
    symbol: str
    quantity: int
    average_entry_price: float
    exit_price: float
    realised_profit: float


@dataclass
class _OpenPosition:
    quantity: int
    average_entry_price: float


class CompletedTradeTracker:
    def __init__(
        self,
    ) -> None:
        self._positions: dict[
            str,
            _OpenPosition,
        ] = {}

        self.completed_trades: list[
            CompletedTrade
        ] = []

    @property
    def winning_trade_count(
        self,
    ) -> int:
        return sum(
            1
            for trade in self.completed_trades
            if trade.realised_profit > 0
        )

    @property
    def losing_trade_count(
        self,
    ) -> int:
        return sum(
            1
            for trade in self.completed_trades
            if trade.realised_profit < 0
        )

    def record_buy(
        self,
        *,
        symbol: str,
        quantity: int,
        price: float,
    ) -> None:
        normalised_symbol = (
            symbol.upper().strip()
        )

        if not normalised_symbol:
            raise ValueError(
                "Symbol is required."
            )

        if quantity <= 0:
            raise ValueError(
                "Buy quantity must be positive."
            )

        if price <= 0:
            raise ValueError(
                "Buy price must be positive."
            )

        existing = self._positions.get(
            normalised_symbol
        )

        if existing is None:
            self._positions[
                normalised_symbol
            ] = _OpenPosition(
                quantity=quantity,
                average_entry_price=price,
            )
            return

        total_cost = (
            existing.quantity
            * existing.average_entry_price
            + quantity
            * price
        )

        existing.quantity += quantity
        existing.average_entry_price = (
            total_cost
            / existing.quantity
        )

    def record_sell(
        self,
        *,
        symbol: str,
        quantity: int,
        price: float,
    ) -> CompletedTrade:
        normalised_symbol = (
            symbol.upper().strip()
        )

        if not normalised_symbol:
            raise ValueError(
                "Symbol is required."
            )

        if quantity <= 0:
            raise ValueError(
                "Sell quantity must be positive."
            )

        if price <= 0:
            raise ValueError(
                "Sell price must be positive."
            )

        position = self._positions.get(
            normalised_symbol
        )

        if position is None:
            raise ValueError(
                "No open position exists for symbol."
            )

        if quantity > position.quantity:
            raise ValueError(
                "Sell quantity exceeds open position."
            )

        realised_profit = (
            (
                price
                - position.average_entry_price
            )
            * quantity
        )

        completed = CompletedTrade(
            symbol=normalised_symbol,
            quantity=quantity,
            average_entry_price=(
                position.average_entry_price
            ),
            exit_price=price,
            realised_profit=realised_profit,
        )

        self.completed_trades.append(
            completed
        )

        position.quantity -= quantity

        if position.quantity == 0:
            del self._positions[
                normalised_symbol
            ]

        return completed