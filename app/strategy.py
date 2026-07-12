from abc import ABC, abstractmethod

from app.orders import Order


class Strategy(ABC):

    @abstractmethod
    def generate_orders(
        self,
        prices: dict[str, float],
    ) -> list[Order]:
        """Generate proposed orders."""