from datetime import (
    datetime,
    timezone,
)

import pytest

from app.news_observation_service import (
    NewsObservationService,
)
from app.news_signal_classifier import (
    FixedNewsSignalClassifier,
    NewsArticleInput,
)
from app.news_signal_store import (
    NewsSignalStore,
)


class FakeSource:
    def __init__(
        self,
        articles: list[NewsArticleInput],
    ) -> None:
        self.articles = articles
        self.received_symbols: list[
            str
        ] = []

    def fetch_articles(
        self,
        *,
        symbols: list[str],
    ) -> list[NewsArticleInput]:
        self.received_symbols = symbols
        return list(
            self.articles
        )


def create_article(
    article_id: str = "article-1",
) -> NewsArticleInput:
    return NewsArticleInput(
        article_id=article_id,
        symbol="AAPL",
        headline="Apple raises guidance",
        summary="Guidance increased.",
        source="Example News",
        published_at=datetime(
            2026,
            7,
            18,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )


def create_classifier(
) -> FixedNewsSignalClassifier:
    return FixedNewsSignalClassifier(
        sentiment=0.7,
        relevance=0.9,
        confidence=0.8,
        event_type="GUIDANCE_RAISED",
        is_material=True,
    )


def test_observes_and_stores_articles(
    tmp_path,
) -> None:
    source = FakeSource(
        [
            create_article(),
        ]
    )
    store = NewsSignalStore(
        file_path=str(
            tmp_path
            / "signals.jsonl"
        )
    )

    summary = NewsObservationService(
        source=source,
        classifier=create_classifier(),
        store=store,
    ).run(
        symbols=[
            " aapl ",
            "MSFT",
            "AAPL",
        ]
    )

    assert source.received_symbols == [
        "AAPL",
        "MSFT",
    ]
    assert summary.article_count == 1
    assert summary.signal_count == 1
    assert (
        summary.skipped_duplicate_count
        == 0
    )
    assert len(
        store.load_all()
    ) == 1


def test_skips_previously_stored_article(
    tmp_path,
) -> None:
    source = FakeSource(
        [
            create_article(),
        ]
    )
    store = NewsSignalStore(
        file_path=str(
            tmp_path
            / "signals.jsonl"
        )
    )
    service = NewsObservationService(
        source=source,
        classifier=create_classifier(),
        store=store,
    )

    service.run(
        symbols=["AAPL"]
    )
    summary = service.run(
        symbols=["AAPL"]
    )

    assert summary.signal_count == 0
    assert (
        summary.skipped_duplicate_count
        == 1
    )
    assert len(
        store.load_all()
    ) == 1


def test_rejects_empty_symbols(
    tmp_path,
) -> None:
    service = NewsObservationService(
        source=FakeSource([]),
        classifier=create_classifier(),
        store=NewsSignalStore(
            file_path=str(
                tmp_path
                / "signals.jsonl"
            )
        ),
    )

    with pytest.raises(
        ValueError,
        match="At least one symbol",
    ):
        service.run(
            symbols=[
                " ",
            ]
        )