import pytest

from app.market_data import MarketDataError, PriceQuote
from app.simulated_market_data import SimulatedMarketDataProvider


def test_price_quote_cleans_symbol() -> None:
    quote = PriceQuote(
        symbol=" aapl ",
        price=150.00,
    )

    assert quote.symbol == "AAPL"
    assert quote.price == 150.00


def test_price_quote_rejects_invalid_price() -> None:
    with pytest.raises(
        ValueError,
        match="Price must be greater than zero",
    ):
        PriceQuote(
            symbol="AAPL",
            price=0,
        )


def test_provider_returns_price() -> None:
    provider = SimulatedMarketDataProvider(
        prices={"AAPL": 150.00}
    )

    quote = provider.get_price("aapl")

    assert quote.symbol == "AAPL"
    assert quote.price == 150.00


def test_provider_returns_multiple_prices() -> None:
    provider = SimulatedMarketDataProvider(
        prices={
            "AAPL": 150.00,
            "MSFT": 320.00,
        }
    )

    prices = provider.get_prices(
        ["AAPL", "MSFT"]
    )

    assert prices == {
        "AAPL": 150.00,
        "MSFT": 320.00,
    }


def test_provider_rejects_unknown_symbol() -> None:
    provider = SimulatedMarketDataProvider(
        prices={"AAPL": 150.00}
    )

    with pytest.raises(
        MarketDataError,
        match="No simulated price",
    ):
        provider.get_price("MSFT")


def test_provider_can_update_price() -> None:
    provider = SimulatedMarketDataProvider(
        prices={"AAPL": 150.00}
    )

    provider.set_price("AAPL", 155.00)

    quote = provider.get_price("AAPL")

    assert quote.price == 155.00