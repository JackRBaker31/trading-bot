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

def test_pending_order_is_unfinished(
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
    journal.record(
        order=order,
        event="PENDING",
        broker_order_id=123456,
    )

    unfinished = journal.load_unfinished_orders()

    assert len(unfinished) == 1
    assert unfinished[0].event == "PENDING"
    assert unfinished[0].broker_order_id == 123456

def test_filled_order_is_not_unfinished(
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

    assert journal.load_unfinished_orders() == []

def test_only_recoverable_orders_are_returned(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)

    pending_order = create_order(
        symbol="AAPL",
    )
    failed_order = create_order(
        symbol="MSFT",
    )
    unknown_order = create_order(
        symbol="TSLA",
    )

    journal.record(
        order=pending_order,
        event="PENDING",
        broker_order_id=111,
    )
    journal.record(
        order=failed_order,
        event="FAILED",
        broker_order_id=222,
    )
    journal.record(
        order=unknown_order,
        event="UNKNOWN",
        broker_order_id=333,
    )

    unfinished = journal.load_unfinished_orders()

    unfinished_by_key = {
        entry.reservation_key: entry
        for entry in unfinished
    }

    assert set(unfinished_by_key) == {
        "AAPL:BUY:2",
        "TSLA:BUY:2",
    }
    assert (
        unfinished_by_key[
            "AAPL:BUY:2"
        ].event
        == "PENDING"
    )
    assert (
        unfinished_by_key[
            "TSLA:BUY:2"
        ].event
        == "UNKNOWN"
    )

def test_record_from_entry_preserves_order_identity(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)

    source_entry = journal.record(
        order=create_order(),
        event="PENDING",
        broker_order_id=123456,
    )

    recovered_entry = journal.record_from_entry(
        source_entry=source_entry,
        event="FAILED",
        broker_order_id=123456,
        reason="Recovered terminal failure.",
        metadata={
            "recovered_on_startup": True,
        },
    )

    assert recovered_entry.reservation_key == (
        source_entry.reservation_key
    )
    assert recovered_entry.symbol == (
        source_entry.symbol
    )
    assert recovered_entry.side == source_entry.side
    assert recovered_entry.quantity == (
        source_entry.quantity
    )
    assert recovered_entry.event == "FAILED"
    assert recovered_entry.broker_order_id == 123456
    assert recovered_entry.metadata == {
        "recovered_on_startup": True,
    }

def test_record_from_entry_is_persisted(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)

    source_entry = journal.record(
        order=create_order(),
        event="SUBMITTED",
        broker_order_id=123456,
    )

    journal.record_from_entry(
        source_entry=source_entry,
        event="REJECTED",
        broker_order_id=123456,
        reason="Broker rejected the order.",
    )

    entries = journal.load_entries()

    assert len(entries) == 2
    assert entries[-1].event == "REJECTED"
    assert entries[-1].reservation_key == (
        source_entry.reservation_key
    )

def test_record_from_entry_rejects_empty_event(
    tmp_path,
) -> None:
    journal = create_journal(tmp_path)

    source_entry = journal.record(
        order=create_order(),
        event="PENDING",
        broker_order_id=123456,
    )

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        journal.record_from_entry(
            source_entry=source_entry,
            event=" ",
        )
