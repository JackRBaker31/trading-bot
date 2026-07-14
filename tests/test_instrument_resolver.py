import pytest

from app.broker import BrokerInstrument
from app.instrument_resolver import (
    InstrumentResolver,
)


def create_instrument(
    ticker: str,
) -> BrokerInstrument:
    return BrokerInstrument(
        ticker=ticker,
        name=ticker,
        short_name=ticker,
        currency_code="USD",
        instrument_type="STOCK",
        isin="US0000000000",
        extended_hours=False,
        max_open_quantity=1_000.0,
        working_schedule_id=1,
    )


def test_resolves_configured_symbols_to_broker_tickers() -> None:
    resolver = InstrumentResolver(
        instruments=[
            create_instrument("AAPL_US_EQ"),
            create_instrument("MSFT_US_EQ"),
        ]
    )

    mapping = resolver.resolve_symbols(
        ["aapl", "MSFT"]
    )

    assert mapping == {
        "AAPL": "AAPL_US_EQ",
        "MSFT": "MSFT_US_EQ",
    }


def test_rejects_unknown_symbol() -> None:
    resolver = InstrumentResolver(
        instruments=[
            create_instrument("AAPL_US_EQ"),
        ]
    )

    with pytest.raises(
        ValueError,
        match="MSFT",
    ):
        resolver.resolve_symbols(
            ["MSFT"]
        )

def test_rejects_ambiguous_symbol() -> None:
    resolver = InstrumentResolver(
        instruments=[
            create_instrument("ABC_US_EQ"),
            create_instrument("ABC_GB_EQ"),
        ]
    )

    with pytest.raises(
        ValueError,
        match="ambiguous",
    ):
        resolver.resolve_symbols(
            ["ABC"]
        )