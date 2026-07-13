import json
from datetime import datetime, timezone

import pytest

from app.order_journal import OrderJournal
from app.orders import Order, OrderSide


FIXED_TIME = datetime(
    2026,
    7,
    13,
    12,
    30,
    tzinfo=timezone.utc,
)


def create_order(
    symbol: str = "AAPL",
    side: OrderSide = OrderSide.BUY,
    quantity: int = 2,
) -> Order:
    return Order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=150.00,
    )


def create_journal(tmp_path) -> OrderJournal:
    return OrderJournal(
        path=tmp_path / "order_journal.jsonl",
        clock=lambda: FIXED_TIME,
    )


def test_record_creates_journal_file(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)
    order = create_order()

    entry = journal.record(
        order=order,
        event="RESERVED",
    )

    assert journal.path.exists()
    assert entry.event == "RESERVED"
    assert entry.symbol == "AAPL"
    assert entry.reservation_key == (
        "AAPL:BUY:2"
    )


def test_record_persists_json_line(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)

    journal.record(
        order=create_order(),
        event="SUBMITTED",
        broker_order_id=123456,
        reason="Broker accepted the order.",
    )

    lines = journal.path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    stored_entry = json.loads(lines[0])

    assert stored_entry["event"] == "SUBMITTED"
    assert (
        stored_entry["broker_order_id"]
        == 123456
    )
    assert stored_entry["timestamp"] == (
        FIXED_TIME.isoformat()
    )


def test_multiple_events_are_appended(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)
    order = create_order()

    journal.record(
        order=order,
        event="RESERVED",
    )
    journal.record(
        order=order,
        event="FILLED",
        broker_order_id=123456,
    )

    entries = journal.load_entries()

    assert len(entries) == 2
    assert entries[0].event == "RESERVED"
    assert entries[1].event == "FILLED"


def test_missing_journal_returns_empty_list(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)

    assert journal.load_entries() == []


def test_latest_entry_is_returned_per_order(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)
    order = create_order()

    journal.record(
        order=order,
        event="RESERVED",
    )
    journal.record(
        order=order,
        event="SUBMITTED",
        broker_order_id=123456,
    )

    latest = journal.latest_entries()

    assert latest["AAPL:BUY:2"].event == (
        "SUBMITTED"
    )


def test_active_reservation_is_recovered(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)
    order = create_order()

    journal.record(
        order=order,
        event="SUBMITTED",
        broker_order_id=123456,
    )

    assert journal.active_reservation_keys() == {
        "AAPL:BUY:2",
    }


def test_terminal_event_is_not_active(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)
    order = create_order()

    journal.record(
        order=order,
        event="SUBMITTED",
        broker_order_id=123456,
    )
    journal.record(
        order=order,
        event="FILLED",
        broker_order_id=123456,
    )

    assert (
        journal.active_reservation_keys()
        == set()
    )


def test_different_orders_are_tracked_separately(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)

    journal.record(
        order=create_order(symbol="AAPL"),
        event="SUBMITTED",
        broker_order_id=111,
    )
    journal.record(
        order=create_order(symbol="MSFT"),
        event="FILLED",
        broker_order_id=222,
    )

    assert journal.active_reservation_keys() == {
        "AAPL:BUY:2",
    }


def test_invalid_broker_order_id_is_rejected(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)

    with pytest.raises(
        ValueError,
        match="Broker order ID",
    ):
        journal.record(
            order=create_order(),
            event="SUBMITTED",
            broker_order_id=0,
        )


def test_empty_event_is_rejected(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)

    with pytest.raises(
        ValueError,
        match="event cannot be empty",
    ):
        journal.record(
            order=create_order(),
            event=" ",
        )


def test_corrupt_journal_line_is_rejected(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)

    journal.path.write_text(
        '{"event": invalid json}\n',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="line 1",
    ):
        journal.load_entries()

def test_record_persists_metadata(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)

    entry = journal.record(
        order=create_order(),
        event="RELEASED",
        broker_order_id=123456,
        reason=(
            "Duplicate reservation released."
        ),
        metadata={
            "release_reason": (
                "workflow_complete"
            ),
        },
    )

    assert entry.metadata == {
        "release_reason": "workflow_complete",
    }

    loaded_entries = journal.load_entries()

    assert loaded_entries[0].metadata == {
        "release_reason": "workflow_complete",
    }

def test_entry_without_metadata_is_loaded(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)

    legacy_entry = {
        "timestamp": FIXED_TIME.isoformat(),
        "reservation_key": "AAPL:BUY:2",
        "event": "SUBMITTED",
        "symbol": "AAPL",
        "side": "BUY",
        "quantity": 2,
        "broker_order_id": 123456,
        "reason": "Broker accepted the order.",
    }

    journal.path.write_text(
        json.dumps(legacy_entry) + "\n",
        encoding="utf-8",
    )

    entries = journal.load_entries()

    assert len(entries) == 1
    assert entries[0].event == "SUBMITTED"
    assert entries[0].metadata is None

