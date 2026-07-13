from abc import ABC, abstractmethod
from dataclasses import dataclass


class BrokerError(Exception):
    """Raised when broker communication fails."""

class BrokerOrderRejectedError(BrokerError):
    """Raised when the broker definitively rejects an order."""


class BrokerOrderSubmissionUnknownError(BrokerError):
    """
    Raised when order submission may have reached
    the broker but confirmation was not received.
    """

class BrokerResourceNotFoundError(BrokerError):
    """Raised when a requested broker resource does not exist."""


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

    @abstractmethod
    def get_active_orders(
        self,
    ) -> list["BrokerOrderResult"]:
        """Return all active broker orders."""

    @abstractmethod
    def get_pending_order(
        self,
        order_id: int,
    ) -> "BrokerOrderResult":
        """Return a pending broker order."""

    @abstractmethod
    def find_historical_order(
        self,
        order_id: int,
        max_pages: int = 5,
    ) -> "BrokerOrderResult | None":
        """Search broker order history."""


@dataclass(frozen=True)
class BrokerOrderResult:
    order_id: int
    ticker: str
    quantity: float
    side: str
    status: str
    order_type: str
    filled_quantity: float
    filled_value: float
    currency: str