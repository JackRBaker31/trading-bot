from app.run_news_research_summary import (
    parse_args,
)


def test_parses_news_research_paths() -> None:
    args = parse_args(
        [
            "--signals",
            "signals.jsonl",
            "--outcomes",
            "outcomes.jsonl",
        ]
    )

    assert args.signals == "signals.jsonl"
    assert args.outcomes == "outcomes.jsonl"