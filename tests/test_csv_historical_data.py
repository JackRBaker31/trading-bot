from datetime import date
from pathlib import Path

import pytest

from app.csv_historical_data import (
    HistoricalDataError,
    load_historical_prices_from_csv,
)


def write_csv(
    file_path: Path,
    contents: str,
) -> None:
    file_path.write_text(
        contents,
        encoding="utf-8",
    )


def test_loads_historical_prices(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "prices.csv"

    write_csv(
        file_path,
        (
            "date,AAPL,MSFT\n"
            "2026-01-02,150.00,320.00\n"
            "2026-01-03,146.00,318.00\n"
        ),
    )

    prices = load_historical_prices_from_csv(
        str(file_path)
    )

    assert len(prices) == 2

    assert prices[0].trading_date == date(
        2026,
        1,
        2,
    )

    assert prices[0].prices == {
        "AAPL": 150.00,
        "MSFT": 320.00,
    }


def test_rows_are_sorted_by_date(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "prices.csv"

    write_csv(
        file_path,
        (
            "date,AAPL\n"
            "2026-01-03,146.00\n"
            "2026-01-02,150.00\n"
        ),
    )

    prices = load_historical_prices_from_csv(
        str(file_path)
    )

    assert prices[0].trading_date == date(
        2026,
        1,
        2,
    )

    assert prices[1].trading_date == date(
        2026,
        1,
        3,
    )


def test_missing_file_raises_error(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "missing.csv"

    with pytest.raises(
        FileNotFoundError,
    ):
        load_historical_prices_from_csv(
            str(file_path)
        )


def test_missing_date_column_is_rejected(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "prices.csv"

    write_csv(
        file_path,
        (
            "AAPL,MSFT\n"
            "150.00,320.00\n"
        ),
    )

    with pytest.raises(
        HistoricalDataError,
        match="date",
    ):
        load_historical_prices_from_csv(
            str(file_path)
        )


def test_invalid_date_is_rejected(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "prices.csv"

    write_csv(
        file_path,
        (
            "date,AAPL\n"
            "not-a-date,150.00\n"
        ),
    )

    with pytest.raises(
        HistoricalDataError,
        match="Invalid date",
    ):
        load_historical_prices_from_csv(
            str(file_path)
        )


def test_duplicate_date_is_rejected(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "prices.csv"

    write_csv(
        file_path,
        (
            "date,AAPL\n"
            "2026-01-02,150.00\n"
            "2026-01-02,151.00\n"
        ),
    )

    with pytest.raises(
        HistoricalDataError,
        match="Duplicate date",
    ):
        load_historical_prices_from_csv(
            str(file_path)
        )


def test_missing_price_is_rejected(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "prices.csv"

    write_csv(
        file_path,
        (
            "date,AAPL,MSFT\n"
            "2026-01-02,150.00,\n"
        ),
    )

    with pytest.raises(
        HistoricalDataError,
        match="Missing price",
    ):
        load_historical_prices_from_csv(
            str(file_path)
        )


def test_invalid_price_is_rejected(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "prices.csv"

    write_csv(
        file_path,
        (
            "date,AAPL\n"
            "2026-01-02,invalid\n"
        ),
    )

    with pytest.raises(
        HistoricalDataError,
        match="Invalid price",
    ):
        load_historical_prices_from_csv(
            str(file_path)
        )


def test_non_positive_price_is_rejected(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "prices.csv"

    write_csv(
        file_path,
        (
            "date,AAPL\n"
            "2026-01-02,0\n"
        ),
    )

    with pytest.raises(
        HistoricalDataError,
        match="must be positive",
    ):
        load_historical_prices_from_csv(
            str(file_path)
        )


def test_empty_data_file_is_rejected(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "prices.csv"

    write_csv(
        file_path,
        "date,AAPL\n",
    )

    with pytest.raises(
        HistoricalDataError,
        match="no data rows",
    ):
        load_historical_prices_from_csv(
            str(file_path)
        )