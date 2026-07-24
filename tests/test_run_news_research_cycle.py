import pytest

from app.run_news_research_cycle import (
    parse_args,
    resolve_symbols,
)


def test_parses_symbol_arguments() -> None:
    args = parse_args(
        [
            "--symbols",
            "AAPL",
            "MSFT",
            "--provider",
            "twelve_data",
        ]
    )

    assert args.symbols == [
        "AAPL",
        "MSFT",
    ]
    assert args.watchlist is None
    assert args.provider == "TWELVE_DATA"


def test_parses_watchlist_argument() -> None:
    args = parse_args(
        [
            "--watchlist",
            "data/watchlists/core_universe.txt",
        ]
    )

    assert args.symbols is None
    assert args.watchlist == (
        "data/watchlists/core_universe.txt"
    )


def test_rejects_symbols_and_watchlist_together() -> None:
    with pytest.raises(
        SystemExit,
    ):
        parse_args(
            [
                "--symbols",
                "AAPL",
                "--watchlist",
                "watchlist.txt",
            ]
        )


def test_resolves_inline_symbols() -> None:
    assert resolve_symbols(
        symbols=[
            "aapl",
            "MSFT",
            "AAPL",
        ],
        watchlist_path=None,
    ) == [
        "AAPL",
        "MSFT",
    ]