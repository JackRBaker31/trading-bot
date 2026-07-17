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

def test_calculates_gross_profit_and_loss() -> None:
    tracker = CompletedTradeTracker()

    tracker.record_buy(
        symbol="AAPL",
        quantity=2,
        price=100.00,
    )
    tracker.record_sell(
        symbol="AAPL",
        quantity=2,
        price=120.00,
    )

    tracker.record_buy(
        symbol="MSFT",
        quantity=3,
        price=100.00,
    )
    tracker.record_sell(
        symbol="MSFT",
        quantity=3,
        price=90.00,
    )

    assert tracker.gross_profit == pytest.approx(
        40.00
    )
    assert tracker.gross_loss == pytest.approx(
        30.00
    )


def test_calculates_profit_factor() -> None:
    tracker = CompletedTradeTracker()

    tracker.record_buy(
        symbol="AAPL",
        quantity=2,
        price=100.00,
    )
    tracker.record_sell(
        symbol="AAPL",
        quantity=2,
        price=120.00,
    )

    tracker.record_buy(
        symbol="MSFT",
        quantity=3,
        price=100.00,
    )
    tracker.record_sell(
        symbol="MSFT",
        quantity=3,
        price=90.00,
    )

    assert tracker.profit_factor == pytest.approx(
        40.00 / 30.00
    )


def test_profit_factor_is_infinite_without_losses() -> None:
    tracker = CompletedTradeTracker()

    tracker.record_buy(
        symbol="AAPL",
        quantity=2,
        price=100.00,
    )
    tracker.record_sell(
        symbol="AAPL",
        quantity=2,
        price=120.00,
    )

    assert tracker.profit_factor == float("inf")


def test_profit_factor_is_zero_without_profit() -> None:
    empty_tracker = CompletedTradeTracker()

    assert empty_tracker.profit_factor == 0.0

    losing_tracker = CompletedTradeTracker()

    losing_tracker.record_buy(
        symbol="AAPL",
        quantity=2,
        price=100.00,
    )
    losing_tracker.record_sell(
        symbol="AAPL",
        quantity=2,
        price=90.00,
    )

    assert losing_tracker.profit_factor == 0.0

def test_calculates_average_winning_and_losing_trades() -> None:
    tracker = CompletedTradeTracker()

    tracker.record_buy(
        symbol="AAPL",
        quantity=1,
        price=100.00,
    )
    tracker.record_sell(
        symbol="AAPL",
        quantity=1,
        price=120.00,
    )

    tracker.record_buy(
        symbol="MSFT",
        quantity=1,
        price=100.00,
    )
    tracker.record_sell(
        symbol="MSFT",
        quantity=1,
        price=140.00,
    )

    tracker.record_buy(
        symbol="AMZN",
        quantity=1,
        price=100.00,
    )
    tracker.record_sell(
        symbol="AMZN",
        quantity=1,
        price=90.00,
    )

    tracker.record_buy(
        symbol="GOOG",
        quantity=1,
        price=100.00,
    )
    tracker.record_sell(
        symbol="GOOG",
        quantity=1,
        price=70.00,
    )

    assert tracker.average_winning_trade == pytest.approx(
        30.00
    )
    assert tracker.average_losing_trade == pytest.approx(
        -20.00
    )


def test_calculates_largest_winner_and_loser() -> None:
    tracker = CompletedTradeTracker()

    tracker.record_buy(
        symbol="AAPL",
        quantity=1,
        price=100.00,
    )
    tracker.record_sell(
        symbol="AAPL",
        quantity=1,
        price=120.00,
    )

    tracker.record_buy(
        symbol="MSFT",
        quantity=1,
        price=100.00,
    )
    tracker.record_sell(
        symbol="MSFT",
        quantity=1,
        price=150.00,
    )

    tracker.record_buy(
        symbol="AMZN",
        quantity=1,
        price=100.00,
    )
    tracker.record_sell(
        symbol="AMZN",
        quantity=1,
        price=90.00,
    )

    tracker.record_buy(
        symbol="GOOG",
        quantity=1,
        price=100.00,
    )
    tracker.record_sell(
        symbol="GOOG",
        quantity=1,
        price=60.00,
    )

    assert tracker.largest_winning_trade == pytest.approx(
        50.00
    )
    assert tracker.largest_losing_trade == pytest.approx(
        -40.00
    )


def test_calculates_expectancy_per_completed_trade() -> None:
    tracker = CompletedTradeTracker()

    tracker.record_buy(
        symbol="AAPL",
        quantity=1,
        price=100.00,
    )
    tracker.record_sell(
        symbol="AAPL",
        quantity=1,
        price=130.00,
    )

    tracker.record_buy(
        symbol="MSFT",
        quantity=1,
        price=100.00,
    )
    tracker.record_sell(
        symbol="MSFT",
        quantity=1,
        price=90.00,
    )

    assert tracker.expectancy == pytest.approx(
        10.00
    )


def test_trade_analytics_are_zero_without_matching_trades() -> None:
    tracker = CompletedTradeTracker()

    assert tracker.average_winning_trade == 0.0
    assert tracker.average_losing_trade == 0.0
    assert tracker.largest_winning_trade == 0.0
    assert tracker.largest_losing_trade == 0.0
    assert tracker.expectancy == 0.0

def test_calculates_win_rate_from_completed_trades() -> None:
    tracker = CompletedTradeTracker()

    tracker.record_buy(
        symbol="AAPL",
        quantity=1,
        price=100.00,
    )
    tracker.record_sell(
        symbol="AAPL",
        quantity=1,
        price=120.00,
    )

    tracker.record_buy(
        symbol="MSFT",
        quantity=1,
        price=100.00,
    )
    tracker.record_sell(
        symbol="MSFT",
        quantity=1,
        price=90.00,
    )

    tracker.record_buy(
        symbol="AMZN",
        quantity=1,
        price=100.00,
    )
    tracker.record_sell(
        symbol="AMZN",
        quantity=1,
        price=110.00,
    )

    assert tracker.win_rate_percent == pytest.approx(
        200.0 / 3.0
    )


def test_win_rate_is_zero_without_completed_trades() -> None:
    tracker = CompletedTradeTracker()

    assert tracker.win_rate_percent == 0.0

def test_calculates_maximum_consecutive_wins() -> None:
    tracker = CompletedTradeTracker()

    for symbol, exit_price in [
        ("AAPL", 110.0),
        ("MSFT", 120.0),
        ("AMZN", 90.0),
        ("GOOG", 115.0),
    ]:
        tracker.record_buy(
            symbol=symbol,
            quantity=1,
            price=100.0,
        )
        tracker.record_sell(
            symbol=symbol,
            quantity=1,
            price=exit_price,
        )

    assert tracker.maximum_consecutive_wins == 2


def test_calculates_maximum_consecutive_losses() -> None:
    tracker = CompletedTradeTracker()

    for symbol, exit_price in [
        ("AAPL", 90.0),
        ("MSFT", 80.0),
        ("AMZN", 110.0),
        ("GOOG", 70.0),
    ]:
        tracker.record_buy(
            symbol=symbol,
            quantity=1,
            price=100.0,
        )
        tracker.record_sell(
            symbol=symbol,
            quantity=1,
            price=exit_price,
        )

    assert tracker.maximum_consecutive_losses == 2


def test_consecutive_trade_streaks_are_zero_without_completed_trades() -> None:
    tracker = CompletedTradeTracker()

    assert tracker.maximum_consecutive_wins == 0
    assert tracker.maximum_consecutive_losses == 0