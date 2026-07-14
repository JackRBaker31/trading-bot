import json
from datetime import datetime, timezone
from pathlib import Path

from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.news_journal import (
    NewsJournal,
    NewsJournalEntry,
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
        sentiment=(
            NewsSentiment.POSITIVE
        ),
    )


def test_records_news_analysis_as_jsonl(
    tmp_path: Path,
) -> None:
    file_path = (
        tmp_path / "news_journal.jsonl"
    )

    journal = NewsJournal(
        file_path=str(file_path)
    )

    entry = NewsJournalEntry(
        timestamp=datetime(
            2026,
            7,
            14,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        article_id="article-123",
        headline=(
            "Apple reports stronger revenue"
        ),
        source="Example News",
        article_text=(
            "Apple reported stronger revenue."
        ),
        analysis=create_analysis(),
    )

    journal.record(
        entry
    )

    lines = file_path.read_text(
        encoding="utf-8",
    ).splitlines()

    assert len(lines) == 1

    data = json.loads(
        lines[0]
    )

    assert data["article_id"] == (
        "article-123"
    )
    assert data["headline"] == (
        "Apple reports stronger revenue"
    )
    assert data["source"] == (
        "Example News"
    )
    assert data["analysis"] == {
        "impact_term": "SHORTTERM",
        "impact_scope": "STOCK",
        "scope_items": ["AAPL"],
        "highlights": [
            "Revenue exceeded expectations."
        ],
        "sentiment": "POSITIVE",
    }


def test_appends_multiple_entries(
    tmp_path: Path,
) -> None:
    file_path = (
        tmp_path / "news_journal.jsonl"
    )

    journal = NewsJournal(
        file_path=str(file_path)
    )

    for article_id in (
        "article-1",
        "article-2",
    ):
        journal.record(
            NewsJournalEntry(
                timestamp=datetime.now(
                    timezone.utc
                ),
                article_id=article_id,
                headline="Headline",
                source="Source",
                article_text="Article text.",
                analysis=create_analysis(),
            )
        )

    lines = file_path.read_text(
        encoding="utf-8",
    ).splitlines()

    assert len(lines) == 2

    assert json.loads(
        lines[0]
    )["article_id"] == "article-1"

    assert json.loads(
        lines[1]
    )["article_id"] == "article-2"