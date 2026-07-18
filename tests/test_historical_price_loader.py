from datetime import date

import pytest

from app.backtest_models import HistoricalPriceBar
from app.historical_price_loader import (
    HistoricalPriceLoader,
)


class FakeHistoricalClient:
    def __init__(
        self,
        bars_by_symbol: dict[
            str,
            list[HistoricalPriceBar],
        ],
    ) -> None:
        self.bars_by_symbol = bars_by_symbol
        self.requests: list[
            tuple[str, int]
        ] = []

    def get_daily_bars(
        self,
        *,
        symbol: str,
        output_size: int,
    ) -> list[HistoricalPriceBar]:
        self.requests.append(
            (
                symbol,
                output_size,
            )
        )

        return self.bars_by_symbol[symbol]


def create_bar(
    *,
    symbol: str,
    trading_date: date,
    close_price: float,
) -> HistoricalPriceBar:
    return HistoricalPriceBar(
        symbol=symbol,
        trading_date=trading_date,
        open_price=close_price,
        high_price=close_price,
        low_price=close_price,
        close_price=close_price,
        volume=1_000,
    )


def test_loads_prices_for_shared_dates() -> None:
    client = FakeHistoricalClient(
        {
            "AAPL": [
                create_bar(
                    symbol="AAPL",
                    trading_date=date(
                        2026,
                        1,
                        2,
                    ),
                    close_price=100.0,
                ),
                create_bar(
                    symbol="AAPL",
                    trading_date=date(
                        2026,
                        1,
                        3,
                    ),
                    close_price=101.0,
                ),
            ],
            "MSFT": [
                create_bar(
                    symbol="MSFT",
                    trading_date=date(
                        2026,
                        1,
                        2,
                    ),
                    close_price=200.0,
                ),
                create_bar(
                    symbol="MSFT",
                    trading_date=date(
                        2026,
                        1,
                        3,
                    ),
                    close_price=202.0,
                ),
            ],
        }
    )

    loader = HistoricalPriceLoader(
        client=client,  # type: ignore[arg-type]
    )

    prices = loader.load_daily_prices(
        symbols=[
            " aapl ",
            "msft",
        ],
        output_size=500,
    )

    assert [
        price.trading_date
        for price in prices
    ] == [
        date(2026, 1, 2),
        date(2026, 1, 3),
    ]

    assert prices[0].prices == {
        "AAPL": 100.0,
        "MSFT": 200.0,
    }

    assert client.requests == [
        ("AAPL", 500),
        ("MSFT", 500),
    ]


def test_excludes_dates_missing_for_any_symbol() -> None:
    client = FakeHistoricalClient(
        {
            "AAPL": [
                create_bar(
                    symbol="AAPL",
                    trading_date=date(
                        2026,
                        1,
                        2,
                    ),
                    close_price=100.0,
                ),
                create_bar(
                    symbol="AAPL",
                    trading_date=date(
                        2026,
                        1,
                        3,
                    ),
                    close_price=101.0,
                ),
            ],
            "MSFT": [
                create_bar(
                    symbol="MSFT",
                    trading_date=date(
                        2026,
                        1,
                        3,
                    ),
                    close_price=202.0,
                ),
            ],
        }
    )

    loader = HistoricalPriceLoader(
        client=client,  # type: ignore[arg-type]
    )

    prices = loader.load_daily_prices(
        symbols=[
            "AAPL",
            "MSFT",
        ],
        output_size=500,
    )

    assert len(prices) == 1
    assert prices[0].trading_date == date(
        2026,
        1,
        3,
    )


@pytest.mark.parametrize(
    "symbols",
    [
        [],
        [""],
        ["AAPL", "aapl"],
    ],
)
def test_rejects_invalid_symbols(
    symbols: list[str],
) -> None:
    loader = HistoricalPriceLoader(
        client=FakeHistoricalClient({}),  # type: ignore[arg-type]
    )

    with pytest.raises(ValueError):
        loader.load_daily_prices(
            symbols=symbols,
            output_size=500,
        )