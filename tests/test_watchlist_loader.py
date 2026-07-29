import pytest

from app.watchlist_loader import (
    load_watchlist,
)


def test_loads_normalised_unique_symbols(
    tmp_path,
) -> None:
    path = tmp_path / "watchlist.txt"
    path.write_text(
        """
# Technology
aapl
MSFT

AAPL
amzn
""".strip(),
        encoding="utf-8",
    )

    assert load_watchlist(
        file_path=str(path)
    ) == [
        "AAPL",
        "MSFT",
        "AMZN",
    ]


def test_rejects_empty_watchlist(
    tmp_path,
) -> None:
    path = tmp_path / "watchlist.txt"
    path.write_text(
        "# No symbols\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="at least one symbol",
    ):
        load_watchlist(
            file_path=str(path)
        )

def test_rejects_malformed_symbols(tmp_path) -> None:
    path = tmp_path / "watchlist.txt"
    path.write_text("AAPL\nBAD SYMBOL\n", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid symbol"):
        load_watchlist(file_path=str(path))
