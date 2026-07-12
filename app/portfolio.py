from dataclasses import dataclass, field


@dataclass
class Portfolio:
    starting_cash: float
    cash: float = field(init=False)
    positions: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.starting_cash < 0:
            raise ValueError("Starting cash cannot be negative.")

        self.cash = self.starting_cash

    def buy(self, symbol: str, quantity: int, price: float) -> None:
        symbol = self._clean_symbol(symbol)
        self._validate_order(quantity, price)

        total_cost = quantity * price

        if total_cost > self.cash:
            raise ValueError(
                f"Insufficient cash. Required £{total_cost:.2f}, "
                f"but only £{self.cash:.2f} is available."
            )

        self.cash -= total_cost
        self.positions[symbol] = self.positions.get(symbol, 0) + quantity

    def sell(self, symbol: str, quantity: int, price: float) -> None:
        symbol = self._clean_symbol(symbol)
        self._validate_order(quantity, price)

        owned_quantity = self.positions.get(symbol, 0)

        if quantity > owned_quantity:
            raise ValueError(
                f"Insufficient shares. Attempted to sell {quantity} "
                f"{symbol} shares, but only {owned_quantity} are owned."
            )

        self.cash += quantity * price
        remaining_quantity = owned_quantity - quantity

        if remaining_quantity == 0:
            del self.positions[symbol]
        else:
            self.positions[symbol] = remaining_quantity

    def portfolio_value(self, current_prices: dict[str, float]) -> float:
        positions_value = 0.0

        for symbol, quantity in self.positions.items():
            if symbol not in current_prices:
                raise ValueError(f"No current price was supplied for {symbol}.")

            price = current_prices[symbol]

            if price <= 0:
                raise ValueError(f"Current price for {symbol} must be positive.")

            positions_value += quantity * price

        return self.cash + positions_value

    def profit_and_loss(self, current_prices: dict[str, float]) -> float:
        return self.portfolio_value(current_prices) - self.starting_cash

    def display(self, current_prices: dict[str, float]) -> None:
        print("\n--- SIMULATED PORTFOLIO ---")
        print(f"Cash: £{self.cash:.2f}")

        if not self.positions:
            print("Positions: None")
        else:
            print("Positions:")

            for symbol, quantity in self.positions.items():
                current_price = current_prices.get(symbol)

                if current_price is None:
                    print(f"  {symbol}: {quantity} shares — price unavailable")
                    continue

                value = quantity * current_price
                print(
                    f"  {symbol}: {quantity} shares "
                    f"at £{current_price:.2f} = £{value:.2f}"
                )

        total_value = self.portfolio_value(current_prices)
        pnl = self.profit_and_loss(current_prices)

        print(f"Total portfolio value: £{total_value:.2f}")
        print(f"Profit/loss: £{pnl:.2f}")
        print("---------------------------")

    @staticmethod
    def _clean_symbol(symbol: str) -> str:
        cleaned_symbol = symbol.upper().strip()

        if not cleaned_symbol:
            raise ValueError("A stock symbol is required.")

        return cleaned_symbol

    @staticmethod
    def _validate_order(quantity: int, price: float) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        if price <= 0:
            raise ValueError("Price must be greater than zero.")