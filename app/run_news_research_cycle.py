import argparse

from app.config import load_config
from app.environment import load_environment
from app.market_data_factory import (
    create_market_data_provider,
)
from app.news_research_cycle_service import (
    NewsResearchCycleRequest,
    NewsResearchCycleResult,
    NewsResearchCycleService,
)
from app.news_research_report import (
    format_news_research_summary,
)
from app.run_history_repository import (
    RunHistoryRepository,
)
from app.run_history_service import (
    RunHistoryService,
)
from app.run_news_observation import (
    create_service as create_observation_service,
)
from app.run_news_signal_outcomes import (
    SUPPORTED_PROVIDERS,
    resolve_provider_name,
)
from app.watchlist_loader import load_watchlist


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one complete AI-news research "
            "cycle without affecting trading."
        )
    )

    symbol_group = (
        parser.add_mutually_exclusive_group(
            required=True
        )
    )

    symbol_group.add_argument(
        "--symbols",
        nargs="+",
        help=(
            "Symbols to observe, for example "
            "AAPL MSFT AMZN."
        ),
    )

    symbol_group.add_argument(
        "--watchlist",
        help=(
            "Path to a text file containing "
            "one symbol per line."
        ),
    )

    parser.add_argument(
        "--provider",
        choices=SUPPORTED_PROVIDERS,
        default=None,
        type=str.upper,
        help=(
            "Override the configured market-data "
            "provider for research only."
        ),
    )
    parser.add_argument(
        "--signals",
        default="data/news_signals.jsonl",
    )
    parser.add_argument(
        "--snapshots",
        default=(
            "data/"
            "news_signal_price_snapshots.jsonl"
        ),
    )
    parser.add_argument(
        "--outcomes",
        default=(
            "data/news_signal_outcomes.jsonl"
        ),
    )
    parser.add_argument(
        "--max-price-requests",
        type=int,
        default=5,
        help=(
            "Maximum market-price requests per "
            "stage in one cycle."
        ),
    )

    return parser.parse_args(argv)


def resolve_symbols(
    *,
    symbols: list[str] | None,
    watchlist_path: str | None,
) -> list[str]:
    if watchlist_path is not None:
        return load_watchlist(
            file_path=watchlist_path
        )

    assert symbols is not None

    cleaned_symbols: list[str] = []
    seen: set[str] = set()

    for symbol in symbols:
        cleaned = symbol.upper().strip()

        if not cleaned or cleaned in seen:
            continue

        seen.add(cleaned)
        cleaned_symbols.append(cleaned)

    if not cleaned_symbols:
        raise ValueError(
            "At least one symbol is required."
        )

    return cleaned_symbols


def create_cycle_service(
) -> NewsResearchCycleService:
    run_history_service = RunHistoryService(
        repository=RunHistoryRepository(
            database_path="data/application.db"
        )
    )
    run_history_service.initialize()

    return NewsResearchCycleService(
        observation_service_factory=(
            lambda store_path: (
                create_observation_service(
                    store_path=store_path
                )
            )
        ),
        market_data_provider_factory=(
            lambda provider_name, symbols: (
                create_market_data_provider(
                    provider_name=provider_name,
                    symbols=symbols,
                )
            )
        ),
        run_history_service=(
            run_history_service
        ),
    )


def format_cycle_result(
    *,
    result: NewsResearchCycleResult,
) -> str:
    observation = result.observation_summary
    snapshot = result.snapshot_summary
    outcome = result.outcome_summary

    lines = [
        "AI NEWS RESEARCH CYCLE",
        (
            "Market-data provider: "
            f"{result.provider_name}"
        ),
        (
            "Symbols: "
            + ", ".join(result.symbols)
        ),
        "",
        "OBSERVATION",
        (
            "Articles fetched: "
            f"{observation.article_count}"
        ),
        (
            "Signals stored: "
            f"{observation.signal_count}"
        ),
        (
            "Duplicates skipped: "
            f"{observation.skipped_duplicate_count}"
        ),
        "",
        "OUTCOMES",
    ]

    if snapshot is None or outcome is None:
        lines.append(
            "No signals are available."
        )
    else:
        lines.extend(
            [
                (
                    "Snapshots captured: "
                    f"{snapshot.captured_count}"
                ),
                (
                    "Existing snapshots skipped: "
                    f"{snapshot.skipped_existing_count}"
                ),
                (
                    "Snapshot failures: "
                    f"{snapshot.failed_count}"
                ),
                (
                    "Snapshots deferred: "
                    f"{snapshot.deferred_count}"
                ),
            ]
        )

        if snapshot.failed_symbols:
            lines.append(
                "Snapshot failed symbols: "
                + ", ".join(
                    snapshot.failed_symbols
                )
            )

        lines.extend(
            [
                (
                    "Outcomes recorded: "
                    f"{outcome.recorded_count}"
                ),
                (
                    "Existing outcomes skipped: "
                    f"{outcome.skipped_existing_count}"
                ),
                (
                    "Outcomes not due: "
                    f"{outcome.not_due_count}"
                ),
                (
                    "Missing snapshots: "
                    f"{outcome.missing_snapshot_count}"
                ),
                (
                    "Outcome failures: "
                    f"{outcome.failed_count}"
                ),
                (
                    "Outcomes deferred: "
                    f"{outcome.deferred_count}"
                ),
                (
                    "Stale outcomes deferred: "
                    f"{outcome.stale_quote_count}"
                )
            ]
        )

        if outcome.failed_symbols:
            lines.append(
                "Outcome failed symbols: "
                + ", ".join(
                    outcome.failed_symbols
                )
            )

    lines.extend(
        [
            "",
            format_news_research_summary(
                summary=result.research_summary
            ),
            "",
            (
                "Trading impact: NONE "
                "(research-only mode)"
            ),
        ]
    )

    return "\n".join(lines)


def main() -> None:
    load_environment()
    args = parse_args()
    config = load_config()

    requested_symbols = resolve_symbols(
        symbols=args.symbols,
        watchlist_path=args.watchlist,
    )

    provider_name = resolve_provider_name(
        configured_provider_name=(
            config.market_data_provider
        ),
        provider_override=args.provider,
    )

    request = NewsResearchCycleRequest(
        symbols=tuple(requested_symbols),
        provider_name=provider_name,
        signals_path=args.signals,
        snapshots_path=args.snapshots,
        outcomes_path=args.outcomes,
        max_price_requests=(
            args.max_price_requests
        ),
    )

    result = create_cycle_service().run(
        request=request
    )

    print(
        format_cycle_result(
            result=result
        )
    )


if __name__ == "__main__":
    main()