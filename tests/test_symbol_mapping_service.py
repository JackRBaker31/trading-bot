from app.broker import BrokerInstrument
from app.symbol_mapping_service import (
    SymbolMappingService,
)


class FakeBroker:
    def __init__(
        self,
        instruments: list[BrokerInstrument],
    ) -> None:
        self.instruments = instruments
        self.calls = 0

    def get_instruments(
        self,
    ) -> list[BrokerInstrument]:
        self.calls += 1
        return self.instruments


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


def test_resolves_symbols_using_broker_catalogue() -> None:
    broker = FakeBroker(
        instruments=[
            create_instrument("AAPL_US_EQ"),
            create_instrument("MSFT_US_EQ"),
        ]
    )

    mapping = SymbolMappingService().resolve(
        broker=broker,
        configured_symbols=[
            "AAPL",
            "MSFT",
        ],
    )

    assert broker.calls == 1
    assert mapping == {
        "AAPL": "AAPL_US_EQ",
        "MSFT": "MSFT_US_EQ",
    }