from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.market_session import MarketSession


def create_session() -> MarketSession:
    return MarketSession(
        timezone_name="America/New_York",
        opening_time="09:30",
        closing_time="16:00",
        trading_weekdays={
            0,
            1,
            2,
            3,
            4,
        },
    )


def test_market_is_open_during_session() -> None:
    session = create_session()

    current_time = datetime(
        2026,
        7,
        13,
        10,
        30,
        tzinfo=ZoneInfo(
            "America/New_York"
        ),
    )

    status = session.get_status(
        current_time=current_time
    )

    assert status.is_open is True
    assert "open" in status.reason.lower()


def test_market_is_closed_before_open() -> None:
    session = create_session()

    current_time = datetime(
        2026,
        7,
        13,
        8,
        30,
        tzinfo=ZoneInfo(
            "America/New_York"
        ),
    )

    status = session.get_status(
        current_time=current_time
    )

    assert status.is_open is False
    assert "not opened" in status.reason.lower()


def test_market_is_closed_after_close() -> None:
    session = create_session()

    current_time = datetime(
        2026,
        7,
        13,
        16,
        30,
        tzinfo=ZoneInfo(
            "America/New_York"
        ),
    )

    status = session.get_status(
        current_time=current_time
    )

    assert status.is_open is False
    assert "closed" in status.reason.lower()


def test_market_is_closed_on_weekend() -> None:
    session = create_session()

    current_time = datetime(
        2026,
        7,
        12,
        12,
        0,
        tzinfo=ZoneInfo(
            "America/New_York"
        ),
    )

    status = session.get_status(
        current_time=current_time
    )

    assert status.is_open is False
    assert "closed today" in status.reason.lower()


def test_timezone_conversion_is_applied() -> None:
    session = create_session()

    london_time = datetime(
        2026,
        7,
        13,
        15,
        0,
        tzinfo=ZoneInfo(
            "Europe/London"
        ),
    )

    status = session.get_status(
        current_time=london_time
    )

    assert status.is_open is True
    assert (
        status.local_time.hour == 10
    )


def test_invalid_timezone_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid timezone",
    ):
        MarketSession(
            timezone_name="Invalid/Timezone",
            opening_time="09:30",
            closing_time="16:00",
        )


def test_invalid_session_times_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Opening time",
    ):
        MarketSession(
            timezone_name="America/New_York",
            opening_time="16:00",
            closing_time="09:30",
        )


def test_invalid_time_format_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid time",
    ):
        MarketSession(
            timezone_name="America/New_York",
            opening_time="morning",
            closing_time="16:00",
        )