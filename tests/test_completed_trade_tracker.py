import pytest

from app.completed_trade_tracker import (
    CompletedTrade,
    CompletedTradeTracker,
)


def test_records_winning_trade() -> None:
    tracker = CompletedTradeTracker()

    tracker.record_buy(
        symbol="AAPL",
        quantity=2,
        price=100.00,
    )

    completed = tracker.record_sell(
        symbol="AAPL",
        quantity=2,
        price=120.00,
    )

    assert completed == CompletedTrade(
        symbol="AAPL",
        quantity=2,
        average_entry_price=100.00,
        exit_price=120.00,
        realised_profit=40.00,
    )

    assert tracker.winning_trade_count == 1
    assert tracker.losing_trade_count == 0


def test_records_losing_trade() -> None:
    tracker = CompletedTradeTracker()

    tracker.record_buy(
        symbol="AAPL",
        quantity=3,
        price=100.00,
    )

    completed = tracker.record_sell(
        symbol="AAPL",
        quantity=3,
        price=90.00,
    )

    assert completed.realised_profit == pytest.approx(
        -30.00
    )

    assert tracker.winning_trade_count == 0
    assert tracker.losing_trade_count == 1


def test_uses_weighted_average_entry_price() -> None:
    tracker = CompletedTradeTracker()

    tracker.record_buy(
        symbol="AAPL",
        quantity=2,
        price=100.00,
    )

    tracker.record_buy(
        symbol="AAPL",
        quantity=1,
        price=130.00,
    )

    completed = tracker.record_sell(
        symbol="AAPL",
        quantity=3,
        price=120.00,
    )

    assert completed.average_entry_price == pytest.approx(
        110.00
    )

    assert completed.realised_profit == pytest.approx(
        30.00
    )


def test_partial_sell_keeps_remaining_position() -> None:
    tracker = CompletedTradeTracker()

    tracker.record_buy(
        symbol="AAPL",
        quantity=4,
        price=100.00,
    )

    first = tracker.record_sell(
        symbol="AAPL",
        quantity=2,
        price=110.00,
    )

    second = tracker.record_sell(
        symbol="AAPL",
        quantity=2,
        price=90.00,
    )

    assert first.realised_profit == pytest.approx(
        20.00
    )

    assert second.realised_profit == pytest.approx(
        -20.00
    )

    assert tracker.winning_trade_count == 1
    assert tracker.losing_trade_count == 1


def test_rejects_sell_without_position() -> None:
    tracker = CompletedTradeTracker()

    with pytest.raises(
        ValueError,
        match="position",
    ):
        tracker.record_sell(
            symbol="AAPL",
            quantity=1,
            price=100.00,
        )


def test_rejects_sell_larger_than_position() -> None:
    tracker = CompletedTradeTracker()

    tracker.record_buy(
        symbol="AAPL",
        quantity=1,
        price=100.00,
    )

    with pytest.raises(
        ValueError,
        match="quantity",
    ):
        tracker.record_sell(
            symbol="AAPL",
            quantity=2,
            price=100.00,
        )