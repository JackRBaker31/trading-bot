from abc import ABC, abstractmethod

from app.orders import Order
from app.portfolio import Portfolio


class Strategy(ABC):
    @abstractmethod
    def generate_orders(
        self,
        prices: dict[str, float],
        portfolio: Portfolio,
    ) -> list[Order]:
        """Generate proposed orders."""