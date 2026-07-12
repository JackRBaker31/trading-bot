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
        symbol = symbol.upper().strip()

        if not symbol:
            raise ValueError("A stock symbol is required.")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        if price <= 0:
            raise ValueError("Price must be greater than zero.")

        total_cost = quantity * price

        if total_cost > self.cash:
            raise ValueError(
                f"Insufficient cash. Required £{total_cost:.2f}, "
                f"but only £{self.cash:.2f} is available."
            )

        self.cash -= total_cost
        self.positions[symbol] = self.positions.get(symbol, 0) + quantity

    def portfolio_value(self, current_prices: dict[str, float]) -> float:
        positions_value = 0.0

        for symbol, quantity in self.positions.items():
            if symbol not in current_prices:
                raise ValueError(f"No current price was supplied for {symbol}.")

            positions_value += quantity * current_prices[symbol]

        return self.cash + positions_value

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
                else:
                    value = quantity * current_price
                    print(
                        f"  {symbol}: {quantity} shares "
                        f"at £{current_price:.2f} = £{value:.2f}"
                    )

        total_value = self.portfolio_value(current_prices)
        print(f"Total portfolio value: £{total_value:.2f}")
        print("---------------------------")