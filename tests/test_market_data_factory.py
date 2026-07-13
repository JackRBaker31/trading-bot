import pytest

from app.market_data_factory import (
    create_market_data_provider,
)
from app.simulated_market_data import (
    SimulatedMarketDataProvider,
)
from app.twelve_data_market_data import (
    TwelveDataMarketDataProvider,
)


def test_factory_creates_simulated_provider() -> None:
    provider = create_market_data_provider(
        provider_name="SIMULATED",
        symbols=["AAPL", "MSFT"],
    )

    assert isinstance(
        provider,
        SimulatedMarketDataProvider,
    )


def test_factory_creates_twelve_data_provider(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "TWELVE_DATA_API_KEY",
        "test-key",
    )

    provider = create_market_data_provider(
        provider_name="TWELVE_DATA",
        symbols=["AAPL"],
    )

    assert isinstance(
        provider,
        TwelveDataMarketDataProvider,
    )


def test_factory_requires_twelve_data_key(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "TWELVE_DATA_API_KEY",
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match="TWELVE_DATA_API_KEY",
    ):
        create_market_data_provider(
            provider_name="TWELVE_DATA",
            symbols=["AAPL"],
        )


def test_factory_rejects_unknown_provider() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported",
    ):
        create_market_data_provider(
            provider_name="UNKNOWN",
            symbols=["AAPL"],
        )


def test_factory_rejects_missing_simulated_price() -> None:
    with pytest.raises(
        ValueError,
        match="No simulated starting price",
    ):
        create_market_data_provider(
            provider_name="SIMULATED",
            symbols=["NVDA"],
        )

def test_factory_rejects_blank_twelve_data_api_key(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "TWELVE_DATA_API_KEY",
        "   ",
    )

    with pytest.raises(
        RuntimeError,
        match="TWELVE_DATA_API_KEY",
    ):
        create_market_data_provider(
            "TWELVE_DATA",
            ["AAPL"],
        )