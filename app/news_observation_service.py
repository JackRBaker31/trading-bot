from dataclasses import dataclass
from typing import Protocol

from app.news_signal import NewsSignal
from app.news_signal_classifier import (
    NewsArticleInput,
    NewsSignalClassifier,
)
from app.news_signal_store import (
    NewsSignalStore,
)


class NewsObservationSource(Protocol):
    def fetch_articles(
        self,
        *,
        symbols: list[str],
    ) -> list[NewsArticleInput]:
        ...


@dataclass(frozen=True)
class NewsObservationSummary:
    article_count: int
    signal_count: int
    skipped_duplicate_count: int
    symbols: tuple[str, ...]


class NewsObservationService:
    def __init__(
        self,
        *,
        source: NewsObservationSource,
        classifier: NewsSignalClassifier,
        store: NewsSignalStore,
    ) -> None:
        self.source = source
        self.classifier = classifier
        self.store = store

    def run(
        self,
        *,
        symbols: list[str],
    ) -> NewsObservationSummary:
        cleaned_symbols = sorted(
            {
                symbol.upper().strip()
                for symbol in symbols
                if symbol.strip()
            }
        )

        if not cleaned_symbols:
            raise ValueError(
                "At least one symbol is required."
            )

        existing_article_ids = {
            signal.article_id
            for signal in self.store.load_all()
        }

        articles = self.source.fetch_articles(
            symbols=cleaned_symbols,
        )

        signal_count = 0
        skipped_duplicate_count = 0

        for article in articles:
            if (
                article.article_id
                in existing_article_ids
            ):
                skipped_duplicate_count += 1
                continue

            signal = self.classifier.classify(
                article=article,
            )

            self.store.append(
                signal=signal,
            )

            existing_article_ids.add(
                signal.article_id
            )
            signal_count += 1

        return NewsObservationSummary(
            article_count=len(articles),
            signal_count=signal_count,
            skipped_duplicate_count=(
                skipped_duplicate_count
            ),
            symbols=tuple(
                cleaned_symbols
            ),
        )