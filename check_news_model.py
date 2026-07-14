import argparse
import hashlib
import os
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from app.logging_config import setup_logging
from app.news_analysis import NewsAnalysis
from app.news_analysis_service import (
    NewsAnalysisService,
)
from app.news_journal import (
    NewsJournal,
    NewsJournalEntry,
)
from app.news_model_client import NewsModelClient
from app.ollama_news_transport import (
    OllamaNewsTransport,
)


DEFAULT_MODEL_NAME = (
    "hf.co/VaibTFU/"
    "qwen-0.5b-stocks-news-v2-GGUF:Q4_K_M"
)


class NewsAnalyser(Protocol):
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        """Return validated analysis."""


class NewsJournalWriter(Protocol):
    def record(
        self,
        entry: NewsJournalEntry,
    ) -> None:
        """Append one news-journal entry."""


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyse one financial-news article "
            "using the local Ollama model."
        )
    )

    parser.add_argument(
        "--headline",
        required=True,
        help="Article headline.",
    )

    parser.add_argument(
        "--source",
        default="Manual input",
        help="Article publisher or source.",
    )

    article_group = (
        parser.add_mutually_exclusive_group(
            required=True
        )
    )

    article_group.add_argument(
        "--article",
        help="Article text supplied directly.",
    )

    article_group.add_argument(
        "--article-file",
        help=(
            "Path to a UTF-8 text file containing "
            "the article."
        ),
    )

    return parser.parse_args(argv)


def load_article_text(
    *,
    article: str | None,
    article_file: str | None,
) -> str:
    if article is not None:
        cleaned_article = article.strip()
    elif article_file is not None:
        file_path = Path(article_file)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Article file does not exist: "
                f"{file_path}"
            )

        cleaned_article = file_path.read_text(
            encoding="utf-8",
        ).strip()
    else:
        raise ValueError(
            "Article text or an article file "
            "is required."
        )

    if not cleaned_article:
        raise ValueError(
            "News article text is required."
        )

    return cleaned_article


def create_article_id(
    *,
    headline: str,
    source: str,
    article_text: str,
) -> str:
    identity = "\n".join(
        (
            source.strip(),
            headline.strip(),
            article_text.strip(),
        )
    )

    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()


def analyse_and_record(
    *,
    analyser: NewsAnalyser,
    journal: NewsJournalWriter,
    headline: str,
    source: str,
    article_text: str,
    now: Callable[[], datetime] = (
        lambda: datetime.now(timezone.utc)
    ),
) -> NewsJournalEntry:
    cleaned_headline = headline.strip()
    cleaned_source = source.strip()
    cleaned_article = article_text.strip()

    if not cleaned_headline:
        raise ValueError(
            "News headline is required."
        )

    if not cleaned_source:
        raise ValueError(
            "News source is required."
        )

    if not cleaned_article:
        raise ValueError(
            "News article text is required."
        )

    analysis = analyser.analyse(
        cleaned_article
    )

    entry = NewsJournalEntry(
        timestamp=now(),
        article_id=create_article_id(
            headline=cleaned_headline,
            source=cleaned_source,
            article_text=cleaned_article,
        ),
        headline=cleaned_headline,
        source=cleaned_source,
        article_text=cleaned_article,
        analysis=analysis,
    )

    journal.record(entry)

    return entry


def display_entry(
    entry: NewsJournalEntry,
) -> None:
    analysis = entry.analysis

    print()
    print("=" * 60)
    print("NEWS MODEL CHECK")
    print("=" * 60)
    print(f"Headline: {entry.headline}")
    print(f"Source: {entry.source}")
    print(f"Article ID: {entry.article_id}")
    print("-" * 60)
    print(
        f"Sentiment: "
        f"{analysis.sentiment.value}"
    )
    print(
        f"Impact term: "
        f"{analysis.impact_term.value}"
    )
    print(
        f"Impact scope: "
        f"{analysis.impact_scope.value}"
    )

    if analysis.scope_items:
        print(
            "Affected items: "
            + ", ".join(
                analysis.scope_items
            )
        )
    else:
        print("Affected items: None identified")

    print("Highlights:")

    if analysis.highlights:
        for highlight in analysis.highlights:
            print(f"- {highlight}")
    else:
        print("- None identified")

    print("-" * 60)
    print(
        "Journal: data/news_journal.jsonl"
    )
    print(
        "Trading influence: NONE "
        "(shadow-analysis mode)"
    )
    print("=" * 60)


def main() -> None:
    setup_logging()

    args = parse_args()

    article_text = load_article_text(
        article=args.article,
        article_file=args.article_file,
    )

    model_name = os.getenv(
        "OLLAMA_NEWS_MODEL",
        DEFAULT_MODEL_NAME,
    ).strip()

    transport = OllamaNewsTransport(
        model_name=model_name,
    )

    model_client = NewsModelClient(
        transport=transport
    )

    analysis_service = NewsAnalysisService(
        model_client=model_client
    )

    journal = NewsJournal(
        file_path=(
            "data/news_journal.jsonl"
        )
    )

    entry = analyse_and_record(
        analyser=analysis_service,
        journal=journal,
        headline=args.headline,
        source=args.source,
        article_text=article_text,
    )

    display_entry(entry)


if __name__ == "__main__":
    main()