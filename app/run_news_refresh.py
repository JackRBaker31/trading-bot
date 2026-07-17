from typing import Protocol

from app.news_analysis import (
    NewsAnalysis,
)
import argparse

from app.news_runtime_factory import (
    create_news_runtime_pipeline,
)

class SymbolRefreshService(Protocol):
    def refresh_symbol(
        self,
        *,
        symbol: str,
    ) -> NewsAnalysis:
        ...


def refresh_symbol(
    *,
    symbol: str,
    refresh_service: SymbolRefreshService,
) -> NewsAnalysis:
    normalised_symbol = (
        symbol.upper().strip()
    )

    return refresh_service.refresh_symbol(
        symbol=normalised_symbol,
    )
    
def print_analysis(
    *,
    symbol: str,
    analysis: NewsAnalysis,
) -> None:
    normalised_symbol = (
        symbol.upper().strip()
    )

    scope_items = (
        ", ".join(
            analysis.scope_items
        )
        if analysis.scope_items
        else "None"
    )

    print(
        f"Symbol: {normalised_symbol}"
    )
    print(
        "Sentiment: "
        f"{analysis.sentiment.value}"
    )
    print(
        "Impact term: "
        f"{analysis.impact_term.value}"
    )
    print(
        "Impact scope: "
        f"{analysis.impact_scope.value}"
    )
    print(
        f"Scope items: {scope_items}"
    )
    print(
        "Highlights:"
    )

    for highlight in analysis.highlights:
        print(
            f"- {highlight}"
        )
        
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh and display news analysis "
            "for one trading symbol."
        )
    )

    parser.add_argument(
        "symbol",
        help="Trading symbol to refresh.",
    )

    parser.add_argument(
        "--source",
        choices=(
            "http",
            "alpha_vantage",
        ),
        default="http",
        help="Configured news source.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    pipeline = create_news_runtime_pipeline(
        source_name=args.source,
    )

    analysis = refresh_symbol(
        symbol=args.symbol,
        refresh_service=(
            pipeline.refresh_service
        ),
    )

    print_analysis(
        symbol=args.symbol,
        analysis=analysis,
    )


if __name__ == "__main__":
    main()