import math


class RiskPositionSizer:
    def __init__(
        self,
        *,
        risk_percent: float,
    ) -> None:
        if (
            risk_percent <= 0
            or risk_percent >= 100
        ):
            raise ValueError(
                "Risk percent must be "
                "between 0 and 100."
            )

        self._risk_percent = (
            risk_percent
        )

    def calculate_quantity(
        self,
        *,
        portfolio_value: float,
        entry_price: float,
        stop_price: float,
        available_cash: float,
    ) -> int:
        if portfolio_value <= 0:
            raise ValueError(
                "Portfolio value must "
                "be positive."
            )

        if entry_price <= 0:
            raise ValueError(
                "Entry price must "
                "be positive."
            )

        if available_cash < 0:
            raise ValueError(
                "Available cash cannot "
                "be negative."
            )

        if stop_price >= entry_price:
            raise ValueError(
                "Stop price must be "
                "below entry price."
            )

        risk_budget = (
            portfolio_value
            * self._risk_percent
            / 100.0
        )

        risk_per_share = (
            entry_price
            - stop_price
        )

        risk_quantity = math.floor(
            risk_budget
            / risk_per_share
        )

        cash_quantity = math.floor(
            available_cash
            / entry_price
        )

        return max(
            0,
            min(
                risk_quantity,
                cash_quantity,
            ),
        )