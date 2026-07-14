import argparse
from app.config import AppConfig
from app.orders import Order, OrderSide
from typing import Protocol
from app.orders import Order


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--confirm-demo-order",
        action="store_true",
        required=False,
        dest="confirm_demo_order",
        help=(
            "Explicitly confirm submission "
            "of one demo order."
        ),
    )

    args = parser.parse_args(argv)

    if not args.confirm_demo_order:
        parser.error(
            "--confirm-demo-order "
            "is required."
        )

    return args


def validate_config(
    config: AppConfig,
) -> None:
    if config.mode != "PAPER":
        raise RuntimeError(
            "One-shot demo order requires "
            "PAPER mode."
        )

    if not config.paper_trading.enabled:
        raise RuntimeError(
            "Paper trading is disabled."
        )

    if (
        config.paper_trading.broker_environment
        != "DEMO"
    ):
        raise RuntimeError(
            "One-shot demo order requires "
            "the DEMO broker environment."
        )

    if not (
        config.paper_trading
        .order_execution_permission_confirmed
    ):
        raise RuntimeError(
            "Order-execution permission has "
            "not been confirmed."
        )

def build_demo_order(
    symbol: str,
    price: float,
) -> Order:
    return Order(
        symbol=symbol,
        side=OrderSide.BUY,
        quantity=1,
        price=price,
    )

class OrderExecutionAdapter(Protocol):
    def submit_order(
        self,
        order: Order,
        current_prices: dict[str, float],
    ) -> bool:
        """Submit one order through the safe pipeline."""


def execute_demo_order(
    adapter: OrderExecutionAdapter,
    order: Order,
) -> bool:
    return adapter.submit_order(
        order=order,
        current_prices={
            order.symbol: order.price,
        },
    )

def main() -> None:
    parse_args()


if __name__ == "__main__":
    main()