from app.run_news_observation import (
    parse_args,
)


def test_parses_observation_arguments() -> None:
    args = parse_args(
        [
            "--symbols",
            "AAPL",
            "MSFT",
            "--store",
            "data/test-signals.jsonl",
        ]
    )

    assert args.symbols == [
        "AAPL",
        "MSFT",
    ]
    assert args.store == (
        "data/test-signals.jsonl"
    )