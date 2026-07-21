import argparse

from app.config import load_config
from app.environment import (
    load_environment,
)
from app.market_data_factory import (
    create_market_data_provider,
)
from app.news_signal_outcome_store import (
    NewsSignalOutcomeStore,
)
from app.news_signal_outcome_tracker import (
    NewsSignalOutcomeTracker,
)
from app.news_signal_price_snapshot_store import (
    NewsSignalPriceSnapshotStore,
)
from app.news_signal_price_snapshot_service import (
    NewsSignalPriceSnapshotService,
)
from app.news_signal_store import (
    NewsSignalStore,
)


SUPPORTED_PROVIDERS = (
    "SIMULATED",
    "TWELVE_DATA",
)


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Capture news-signal price snapshots "
            "and record due outcomes."
        )
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
        "--provider",
        choices=SUPPORTED_PROVIDERS,
        default=None,
        type=str.upper,
        help=(
            "Override the configured market-data "
            "provider for news research only."
        ),
    )

    return parser.parse_args(argv)


def resolve_provider_name(
    *,
    configured_provider_name: str,
    provider_override: str | None,
) -> str:
    if provider_override is not None:
        return provider_override.upper().strip()

    return configured_provider_name.upper().strip()


def main() -> None:
    load_environment()
    args = parse_args()
    config = load_config()

    signals = NewsSignalStore(
        file_path=args.signals
    ).load_all()

    if not signals:
        print(
            "No news signals are available."
        )
        return

    symbols = sorted(
        {
            signal.symbol
            for signal in signals
        }
    )

    provider_name = resolve_provider_name(
        configured_provider_name=(
            config.market_data_provider
        ),
        provider_override=args.provider,
    )

    market_data_provider = (
        create_market_data_provider(
            provider_name=provider_name,
            symbols=symbols,
        )
    )

    snapshot_store = (
        NewsSignalPriceSnapshotStore(
            file_path=args.snapshots
        )
    )

    snapshot_summary = (
        NewsSignalPriceSnapshotService(
            market_data_provider=(
                market_data_provider
            ),
            snapshot_store=(
                snapshot_store
            ),
        )
        .run(
            signals=signals
        )
    )

    outcome_summary = (
        NewsSignalOutcomeTracker(
            market_data_provider=(
                market_data_provider
            ),
            outcome_store=(
                NewsSignalOutcomeStore(
                    file_path=args.outcomes
                )
            ),
            reference_snapshot_provider=(
                lambda signal: (
                    snapshot_store
                    .get_by_article_id(
                        signal.article_id
                    )
                )
            ),
        )
        .run(
            signals=signals
        )
    )

    print("NEWS SIGNAL OUTCOMES")
    print(
        f"Market-data provider: "
        f"{provider_name}"
    )
    print(
        f"Signals loaded: {len(signals)}"
    )
    print(
        f"Snapshots captured: "
        f"{snapshot_summary.captured_count}"
    )
    print(
        f"Existing snapshots skipped: "
        f"{snapshot_summary.skipped_existing_count}"
    )
    print(
        f"Outcomes recorded: "
        f"{outcome_summary.recorded_count}"
    )
    print(
        f"Existing outcomes skipped: "
        f"{outcome_summary.skipped_existing_count}"
    )
    print(
        f"Outcomes not due: "
        f"{outcome_summary.not_due_count}"
    )
    print(
        f"Missing snapshots: "
        f"{outcome_summary.missing_snapshot_count}"
    )
    print(
        "Trading impact: NONE "
        "(research-only mode)"
    )


if __name__ == "__main__":
    main()