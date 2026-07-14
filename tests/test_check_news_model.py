from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from check_news_model import (
    analyse_and_record,
    create_article_id,
    load_article_text,
)


def create_analysis() -> NewsAnalysis:
    return NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("AAPL",),
        highlights=(
            "Revenue exceeded expectations.",
        ),
        sentiment=NewsSentiment.POSITIVE,
    )


class FakeAnalyser:
    def __init__(self) -> None:
        self.articles: list[str] = []

    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        self.articles.append(article_text)
        return create_analysis()


class FakeJournal:
    def __init__(self) -> None:
        self.entries = []

    def record(
        self,
        entry,
    ) -> None:
        self.entries.append(entry)


def test_analyses_and_records_one_article() -> None:
    analyser = FakeAnalyser()
    journal = FakeJournal()

    timestamp = datetime(
        2026,
        7,
        14,
        12,
        0,
        tzinfo=timezone.utc,
    )

    entry = analyse_and_record(
        analyser=analyser,
        journal=journal,
        headline="Apple raises guidance",
        source="Example News",
        article_text=(
            "Apple reported stronger revenue."
        ),
        now=lambda: timestamp,
    )

    assert analyser.articles == [
        "Apple reported stronger revenue."
    ]

    assert journal.entries == [entry]
    assert entry.timestamp == timestamp
    assert entry.headline == (
        "Apple raises guidance"
    )
    assert entry.analysis.sentiment == (
        NewsSentiment.POSITIVE
    )


def test_article_id_is_deterministic() -> None:
    first = create_article_id(
        headline="Headline",
        source="Source",
        article_text="Article text.",
    )

    second = create_article_id(
        headline="Headline",
        source="Source",
        article_text="Article text.",
    )

    assert first == second
    assert len(first) == 64


def test_loads_article_from_file(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "article.txt"

    file_path.write_text(
        " Example article. ",
        encoding="utf-8",
    )

    result = load_article_text(
        article=None,
        article_file=str(file_path),
    )

    assert result == "Example article."


def test_rejects_empty_article() -> None:
    with pytest.raises(
        ValueError,
        match="article text",
    ):
        load_article_text(
            article="   ",
            article_file=None,
        )