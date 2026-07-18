from dataclasses import dataclass


@dataclass(frozen=True)
class CompletedTrade:
    symbol: str
    quantity: int
    average_entry_price: float
    exit_price: float
    realised_profit: float

    @property
    def return_percent(
        self,
    ) -> float:
        return (
            (
                self.exit_price
                - self.average_entry_price
            )
            / self.average_entry_price
            * 100.0
        )


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
    
    @property
    def win_rate_percent(
        self,
    ) -> float:
        completed_trade_count = (
            self.winning_trade_count
            + self.losing_trade_count
        )

        if completed_trade_count == 0:
            return 0.0

        return (
            self.winning_trade_count
            / completed_trade_count
            * 100.0
        )

    @property
    def gross_profit(
        self,
    ) -> float:
        return sum(
            trade.realised_profit
            for trade in self.completed_trades
            if trade.realised_profit > 0
        )

    @property
    def gross_loss(
        self,
    ) -> float:
        return abs(
            sum(
                trade.realised_profit
                for trade in self.completed_trades
                if trade.realised_profit < 0
            )
        )

    @property
    def profit_factor(
        self,
    ) -> float:
        if self.gross_loss == 0:
            if self.gross_profit > 0:
                return float("inf")

            return 0.0

        return (
            self.gross_profit
            / self.gross_loss
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
    
    @property
    def average_winning_trade(
        self,
    ) -> float:
        winning_profits = [
            trade.realised_profit
            for trade in self.completed_trades
            if trade.realised_profit > 0
        ]

        if not winning_profits:
            return 0.0

        return (
            sum(winning_profits)
            / len(winning_profits)
        )

    @property
    def average_losing_trade(
        self,
    ) -> float:
        losing_profits = [
            trade.realised_profit
            for trade in self.completed_trades
            if trade.realised_profit < 0
        ]

        if not losing_profits:
            return 0.0

        return (
            sum(losing_profits)
            / len(losing_profits)
        )

    @property
    def largest_winning_trade(
        self,
    ) -> float:
        winning_profits = [
            trade.realised_profit
            for trade in self.completed_trades
            if trade.realised_profit > 0
        ]

        if not winning_profits:
            return 0.0

        return max(winning_profits)

    @property
    def largest_losing_trade(
        self,
    ) -> float:
        losing_profits = [
            trade.realised_profit
            for trade in self.completed_trades
            if trade.realised_profit < 0
        ]

        if not losing_profits:
            return 0.0

        return min(losing_profits)

    @property
    def expectancy(
        self,
    ) -> float:
        if not self.completed_trades:
            return 0.0

        return (
            sum(
                trade.realised_profit
                for trade in self.completed_trades
            )
            / len(self.completed_trades)
        )
    
    @property
    def maximum_consecutive_wins(
        self,
    ) -> int:
        maximum_streak = 0
        current_streak = 0

        for trade in self.completed_trades:
            if trade.realised_profit > 0:
                current_streak += 1
                maximum_streak = max(
                    maximum_streak,
                    current_streak,
                )
            else:
                current_streak = 0

        return maximum_streak

    @property
    def maximum_consecutive_losses(
        self,
    ) -> int:
        maximum_streak = 0
        current_streak = 0

        for trade in self.completed_trades:
            if trade.realised_profit < 0:
                current_streak += 1
                maximum_streak = max(
                    maximum_streak,
                    current_streak,
                )
            else:
                current_streak = 0

        return maximum_streak