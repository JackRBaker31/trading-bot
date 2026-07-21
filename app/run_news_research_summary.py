import argparse

from app.news_research_report import (
    format_news_research_summary,
)
from app.news_research_summary import (
    summarize_news_research,
)
from app.news_signal_outcome_store import (
    NewsSignalOutcomeStore,
)
from app.news_signal_store import (
    NewsSignalStore,
)


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize measured AI news "
            "signal outcomes."
        )
    )

    parser.add_argument(
        "--signals",
        default="data/news_signals.jsonl",
    )
    parser.add_argument(
        "--outcomes",
        default=(
            "data/news_signal_outcomes.jsonl"
        ),
    )

    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()

    signals = NewsSignalStore(
        file_path=args.signals
    ).load_all()

    outcomes = NewsSignalOutcomeStore(
        file_path=args.outcomes
    ).load_all()

    summary = summarize_news_research(
        signals=signals,
        outcomes=outcomes,
    )

    print(
        format_news_research_summary(
            summary=summary
        )
    )


if __name__ == "__main__":
    main()