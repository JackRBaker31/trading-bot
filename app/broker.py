from abc import ABC, abstractmethod
from dataclasses import dataclass


class BrokerError(Exception):
    """Raised when broker communication fails."""


@dataclass(frozen=True)
class BrokerAccountSummary:
    account_id: int
    currency: str
    available_to_trade: float
    reserved_for_orders: float
    cash_in_pies: float
    investments_current_value: float
    investments_total_cost: float
    realized_profit_loss: float
    unrealized_profit_loss: float
    total_value: float


@dataclass(frozen=True)
class BrokerPosition:
    ticker: str
    quantity: float
    average_price_paid: float
    current_price: float
    profit_loss: float


class BrokerClient(ABC):
    @abstractmethod
    def get_account_summary(
        self,
    ) -> BrokerAccountSummary:
        """Return read-only account information."""

    @abstractmethod
    def get_positions(
        self,
    ) -> list[BrokerPosition]:
        """Return all open broker positions."""