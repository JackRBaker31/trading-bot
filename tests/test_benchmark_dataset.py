import json
from pathlib import Path

from research.benchmark_dataset import (
    BenchmarkDataset,
)


def write_json(
    file_path: Path,
    data: dict[str, object],
) -> None:
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        json.dumps(data),
        encoding="utf-8",
    )


def create_article(
    benchmark_id: str,
) -> dict[str, object]:
    return {
        "benchmark_id": benchmark_id,
        "headline": "Apple reports results",
        "source": "Apple Investor Relations",
        "category": "earnings",
        "sector": "Technology",
        "company": "Apple",
        "ticker": "AAPL",
        "difficulty": "easy",
        "published_at": (
            "2026-07-14T12:00:00Z"
        ),
        "article_text": (
            "Apple reported quarterly results."
        ),
        "status": "ready",
    }


def create_label(
    benchmark_id: str,
) -> dict[str, object]:
    return {
        "benchmark_id": benchmark_id,
        "impact_term": "SHORTTERM",
        "impact_scope": "STOCK",
        "scope_items": ["AAPL"],
        "highlights": [
            "Apple reported quarterly results."
        ],
        "sentiment": "NEUTRAL",
    }


def test_loads_and_validates_dataset(
    tmp_path: Path,
) -> None:
    articles = tmp_path / "articles"
    labels = tmp_path / "labels"

    write_json(
        articles / "BENCH-0001.json",
        create_article("BENCH-0001"),
    )

    write_json(
        labels / "BENCH-0001.json",
        create_label("BENCH-0001"),
    )

    dataset = BenchmarkDataset(
        articles_directory=articles,
        labels_directory=labels,
    )

    dataset.load()

    result = dataset.validate()

    assert result.approved is True
    assert result.errors == ()
    assert len(dataset.articles) == 1
    assert len(dataset.labels) == 1


def test_missing_label_is_rejected(
    tmp_path: Path,
) -> None:
    articles = tmp_path / "articles"
    labels = tmp_path / "labels"

    write_json(
        articles / "BENCH-0001.json",
        create_article("BENCH-0001"),
    )

    dataset = BenchmarkDataset(
        articles_directory=articles,
        labels_directory=labels,
    )

    dataset.load()

    result = dataset.validate()

    assert result.approved is False
    assert result.errors == (
        "Missing label for BENCH-0001.",
    )


def test_statistics_are_calculated(
    tmp_path: Path,
) -> None:
    articles = tmp_path / "articles"
    labels = tmp_path / "labels"

    write_json(
        articles / "BENCH-0001.json",
        create_article("BENCH-0001"),
    )

    write_json(
        labels / "BENCH-0001.json",
        create_label("BENCH-0001"),
    )

    dataset = BenchmarkDataset(
        articles_directory=articles,
        labels_directory=labels,
    )

    dataset.load()

    statistics = dataset.statistics()

    assert statistics.article_count == 1
    assert statistics.label_count == 1
    assert statistics.categories == {
        "earnings": 1,
    }
    assert statistics.sources == {
        "Apple Investor Relations": 1,
    }
    assert statistics.sectors == {
        "Technology": 1,
    }
    assert statistics.companies == {
        "Apple": 1,
    }
    assert statistics.difficulties == {
        "easy": 1,
    }


def test_creates_next_templates(
    tmp_path: Path,
) -> None:
    articles = tmp_path / "articles"
    labels = tmp_path / "labels"

    write_json(
        articles / "BENCH-0001.json",
        create_article("BENCH-0001"),
    )

    write_json(
        labels / "BENCH-0001.json",
        create_label("BENCH-0001"),
    )

    dataset = BenchmarkDataset(
        articles_directory=articles,
        labels_directory=labels,
    )

    dataset.load()

    article_path, label_path = (
        dataset.create_templates()
    )

    assert article_path.name == (
        "BENCH-0002.json"
    )
    assert label_path.name == (
        "BENCH-0002.json"
    )
    assert article_path.exists()
    assert label_path.exists()


def test_migrates_legacy_article(
    tmp_path: Path,
) -> None:
    articles = tmp_path / "articles"
    labels = tmp_path / "labels"
    backup = tmp_path / "backup"

    write_json(
        articles / "apple-guidance.json",
        {
            "article_id": "apple-guidance-001",
            "headline": (
                "Apple raises guidance"
            ),
            "source": "Manual benchmark",
            "article_text": (
                "Apple raised guidance."
            ),
            "allowed_symbols": [
                "AAPL"
            ],
        },
    )

    dataset = BenchmarkDataset(
        articles_directory=articles,
        labels_directory=labels,
    )

    result = (
        dataset.migrate_legacy_articles(
            backup_directory=backup,
        )
    )

    assert result.migrated_count == 1
    assert result.skipped_count == 0

    article_path = (
        articles / "BENCH-0001.json"
    )
    label_path = (
        labels / "BENCH-0001.json"
    )
    backup_path = (
        backup / "apple-guidance.json"
    )

    assert article_path.exists()
    assert label_path.exists()
    assert backup_path.exists()

    assert not (
        articles / "apple-guidance.json"
    ).exists()

    article_data = json.loads(
        article_path.read_text(
            encoding="utf-8"
        )
    )

    label_data = json.loads(
        label_path.read_text(
            encoding="utf-8"
        )
    )

    assert article_data["benchmark_id"] == (
        "BENCH-0001"
    )
    assert article_data["ticker"] == "AAPL"

    assert label_data["benchmark_id"] == (
        "BENCH-0001"
    )
    assert label_data["scope_items"] == [
        "AAPL"
    ]


def test_migration_skips_current_schema(
    tmp_path: Path,
) -> None:
    articles = tmp_path / "articles"
    labels = tmp_path / "labels"
    backup = tmp_path / "backup"

    write_json(
        articles / "BENCH-0001.json",
        create_article("BENCH-0001"),
    )

    dataset = BenchmarkDataset(
        articles_directory=articles,
        labels_directory=labels,
    )

    result = (
        dataset.migrate_legacy_articles(
            backup_directory=backup,
        )
    )

    assert result.migrated_count == 0
    assert result.skipped_count == 1
    assert (
        articles / "BENCH-0001.json"
    ).exists()

def test_draft_article_may_be_incomplete(
    tmp_path: Path,
) -> None:
    articles = tmp_path / "articles"
    labels = tmp_path / "labels"

    write_json(
        articles / "BENCH-0001.json",
        {
            "benchmark_id": "BENCH-0001",
            "status": "draft",
            "headline": "",
            "source": "",
            "category": "misc",
            "sector": "",
            "company": "",
            "ticker": "",
            "difficulty": "medium",
            "published_at": "",
            "article_text": "",
        },
    )

    dataset = BenchmarkDataset(
        articles_directory=articles,
        labels_directory=labels,
    )

    dataset.load()

    result = dataset.validate()

    assert result.approved is True
    assert result.errors == ()
    assert len(dataset.draft_articles) == 1
    assert len(dataset.ready_articles) == 0

def test_ready_article_requires_complete_data(
    tmp_path: Path,
) -> None:
    articles = tmp_path / "articles"
    labels = tmp_path / "labels"

    write_json(
        articles / "BENCH-0001.json",
        {
            "benchmark_id": "BENCH-0001",
            "status": "ready",
            "headline": "",
            "source": "",
            "category": "guidance",
            "sector": "Technology",
            "company": "Apple",
            "ticker": "AAPL",
            "difficulty": "easy",
            "published_at": "",
            "article_text": "",
        },
    )

    dataset = BenchmarkDataset(
        articles_directory=articles,
        labels_directory=labels,
    )

    dataset.load()

    result = dataset.validate()

    assert result.approved is False
    assert (
        "BENCH-0001: headline is required."
        in result.errors
    )
