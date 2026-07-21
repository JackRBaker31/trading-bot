from app.run_news_research_cycle import (
    parse_args,
)


def test_defaults_price_request_budget() -> None:
    args = parse_args(
        [
            "--symbols",
            "AAPL",
        ]
    )

    assert args.max_price_requests == 5


def test_parses_price_request_budget() -> None:
    args = parse_args(
        [
            "--symbols",
            "AAPL",
            "--max-price-requests",
            "3",
        ]
    )

    assert args.max_price_requests == 3