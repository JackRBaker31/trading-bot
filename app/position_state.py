from dataclasses import dataclass


@dataclass
class PositionState:
    symbol: str
    quantity: int
    average_entry_price: float
    highest_price: float | None = None

    def __post_init__(
        self,
    ) -> None:
        self.symbol = (
            self.symbol.upper().strip()
        )

        if not self.symbol:
            raise ValueError(
                "Position symbol is required."
            )

        if self.quantity <= 0:
            raise ValueError(
                "Position quantity must be positive."
            )

        if self.average_entry_price <= 0:
            raise ValueError(
                "Average entry price must be positive."
            )

        if self.highest_price is None:
            self.highest_price = (
                self.average_entry_price
            )

        if (
            self.highest_price
            < self.average_entry_price
        ):
            raise ValueError(
                "Position highest price cannot be "
                "below the average entry price."
            )

    def observe_price(
        self,
        price: float,
    ) -> None:
        if price <= 0:
            raise ValueError(
                "Observed price must be positive."
            )

        if price > self.highest_price:
            self.highest_price = price

    def add(
        self,
        *,
        quantity: int,
        price: float,
    ) -> None:
        if quantity <= 0:
            raise ValueError(
                "Added quantity must be positive."
            )

        if price <= 0:
            raise ValueError(
                "Added price must be positive."
            )

        total_cost = (
            self.quantity
            * self.average_entry_price
            + quantity
            * price
        )

        self.quantity += quantity

        self.average_entry_price = (
            total_cost
            / self.quantity
        )

        self.observe_price(
            price
        )
        
    def reduce(
        self,
        *,
        quantity: int,
    ) -> None:
        if quantity <= 0:
            raise ValueError(
                "Reduced quantity must be positive."
            )

        if quantity >= self.quantity:
            raise ValueError(
                "Reduced quantity must be less than "
                "the current position quantity."
            )

        self.quantity -= quantity
        
    def return_percent(
        self,
        *,
        current_price: float,
    ) -> float:
        if current_price <= 0:
            raise ValueError(
                "Current price must be positive."
            )

        return (
            (
                current_price
                - self.average_entry_price
            )
            / self.average_entry_price
            * 100.0
        )


    def drawdown_from_high_percent(
        self,
        *,
        current_price: float,
    ) -> float:
        if current_price <= 0:
            raise ValueError(
                "Current price must be positive."
            )

        return (
            (
                current_price
                - self.highest_price
            )
            / self.highest_price
            * 100.0
        )