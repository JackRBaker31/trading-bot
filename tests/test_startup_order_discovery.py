from app.broker import BrokerOrderResult
from app.startup_order_discovery import (
    StartupOrderDiscoveryService,
)


class FakeBroker:
    def get_active_orders(
        self,
    ) -> list[BrokerOrderResult]:
        return [
            BrokerOrderResult(
                order_id=987654,
                ticker="AAPL_US_EQ",
                quantity=1,
                side="BUY",
                status="NEW",
                order_type="MARKET",
                filled_quantity=0,
                filled_value=0,
                currency="GBP",
            )
        ]


class FakeJournal:
    def find_unfinished_order_by_broker_order_id(
        self,
        broker_order_id: int,
    ) -> None:
        return None


def test_unknown_active_order_blocks_startup() -> None:
    service = StartupOrderDiscoveryService(
        broker=FakeBroker(),
        journal=FakeJournal(),
    )

    result = service.discover()

    assert result.approved is False
    assert result.unknown_order_ids == (
        987654,
    )
    assert result.reason == (
        "PAPER startup blocked by unknown "
        "active broker orders."
    )
    assert result.known_order_count == 0
    assert result.unknown_order_count == 1

class KnownJournal:
    def find_unfinished_order_by_broker_order_id(
        self,
        broker_order_id: int,
    ) -> object:
        return object()


def test_known_active_order_is_approved() -> None:
    service = StartupOrderDiscoveryService(
        broker=FakeBroker(),
        journal=KnownJournal(),
    )

    result = service.discover()

    assert result.approved is True
    assert result.unknown_order_ids == ()
    assert result.reason == (
        "PAPER startup order discovery "
        "completed safely."
    )
    assert result.known_order_ids == (
        987654,
    )
    assert result.known_order_count == 1
    assert result.unknown_order_count == 0