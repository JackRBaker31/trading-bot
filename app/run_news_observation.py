import argparse
import os

from app.environment import (
    load_environment,
)
from app.alpha_vantage_news_observation_source import (
    AlphaVantageNewsObservationSource,
)
from app.alpha_vantage_news_runtime import (
    create_alpha_vantage_news_article_source,
)
from app.news_analysis_service import (
    NewsAnalysisService,
)
from app.news_analysis_signal_classifier import (
    NewsAnalysisSignalClassifier,
)
from app.news_model_client import (
    NewsModelClient,
)
from app.news_observation_service import (
    NewsObservationService,
)
from app.news_runtime_factory import (
    DEFAULT_MODEL_NAME,
)
from app.news_signal_store import (
    NewsSignalStore,
)
from app.ollama_news_transport import (
    OllamaNewsTransport,
)


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch and classify live news in "
            "observation-only mode."
        )
    )

    parser.add_argument(
        "--symbols",
        nargs="+",
        required=True,
        help=(
            "Symbols to observe, for example "
            "AAPL MSFT AMZN."
        ),
    )
    parser.add_argument(
        "--store",
        default="data/news_signals.jsonl",
        help="JSONL output path.",
    )

    return parser.parse_args(
        argv
    )


def create_service(
    *,
    store_path: str,
) -> NewsObservationService:
    model_name = os.getenv(
        "OLLAMA_NEWS_MODEL",
        DEFAULT_MODEL_NAME,
    ).strip()

    analyser = NewsAnalysisService(
        model_client=NewsModelClient(
            transport=OllamaNewsTransport(
                model_name=model_name
            )
        )
    )

    return NewsObservationService(
        source=AlphaVantageNewsObservationSource(
            article_source=(
                create_alpha_vantage_news_article_source()
            )
        ),
        classifier=NewsAnalysisSignalClassifier(
            analyser=analyser
        ),
        store=NewsSignalStore(
            file_path=store_path
        ),
    )


def main() -> None:
    load_environment()
    args = parse_args()

    summary = create_service(
        store_path=args.store
    ).run(
        symbols=args.symbols
    )

    print("NEWS OBSERVATION")
    print(
        f"Symbols: "
        f"{', '.join(summary.symbols)}"
    )
    print(
        f"Articles fetched: "
        f"{summary.article_count}"
    )
    print(
        f"Signals stored: "
        f"{summary.signal_count}"
    )
    print(
        f"Duplicates skipped: "
        f"{summary.skipped_duplicate_count}"
    )
    print(
        f"Store: {args.store}"
    )
    print(
        "Trading impact: NONE "
        "(observation-only mode)"
    )


if __name__ == "__main__":
    main()