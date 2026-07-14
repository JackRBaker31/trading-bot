import json
import sys
from pathlib import Path

import pytest

import benchmark_dataset_manager
from benchmark_dataset_manager import (
    main,
    promote_draft,
    promote_ready,
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
        json.dumps(
            data,
            indent=2,
        ),
        encoding="utf-8",
    )


def create_complete_article(
    *,
    status: str = "draft",
) -> dict[str, object]:
    return {
        "benchmark_id": "BENCH-0001",
        "status": status,
        "headline": "Apple raises guidance",
        "source": "Manual benchmark",
        "category": "guidance",
        "sector": "Technology",
        "company": "Apple",
        "ticker": "AAPL",
        "difficulty": "easy",
        "published_at": "2026-07-14",
        "article_text": (
            "Apple reported stronger revenue "
            "and raised its guidance."
        ),
    }


def create_complete_label() -> dict[str, object]:
    return {
        "benchmark_id": "BENCH-0001",
        "impact_term": "SHORTTERM",
        "impact_scope": "STOCK",
        "scope_items": [
            "AAPL",
        ],
        "highlights": [
            "Apple reported stronger revenue",
            "Apple raised its guidance",
        ],
        "sentiment": "POSITIVE",
    }


def configure_directories(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[Path, Path]:
    articles = tmp_path / "articles"
    labels = tmp_path / "labels"

    monkeypatch.setattr(
        benchmark_dataset_manager,
        "ARTICLES_DIRECTORY",
        articles,
    )

    monkeypatch.setattr(
        benchmark_dataset_manager,
        "LABELS_DIRECTORY",
        labels,
    )

    monkeypatch.setattr(
        benchmark_dataset_manager,
        "BACKUP_DIRECTORY",
        tmp_path / "backup",
    )

    return articles, labels


def test_promote_ready_succeeds(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    articles, labels = configure_directories(
        monkeypatch,
        tmp_path,
    )

    article_path = (
        articles / "BENCH-0001.json"
    )

    write_json(
        article_path,
        create_complete_article(),
    )

    write_json(
        labels / "BENCH-0001.json",
        create_complete_label(),
    )

    promote_ready("bench-0001")

    data = json.loads(
        article_path.read_text(
            encoding="utf-8",
        )
    )

    assert data["status"] == "ready"


def test_failed_promotion_rolls_back_to_draft(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    articles, labels = configure_directories(
        monkeypatch,
        tmp_path,
    )

    article_path = (
        articles / "BENCH-0001.json"
    )

    incomplete_article = (
        create_complete_article()
    )
    incomplete_article["headline"] = ""

    write_json(
        article_path,
        incomplete_article,
    )

    write_json(
        labels / "BENCH-0001.json",
        create_complete_label(),
    )

    with pytest.raises(
        SystemExit,
    ) as error:
        promote_ready(
            "BENCH-0001"
        )

    assert error.value.code == 1

    data = json.loads(
        article_path.read_text(
            encoding="utf-8",
        )
    )

    assert data["status"] == "draft"


def test_promote_draft_changes_ready_article(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    articles, _ = configure_directories(
        monkeypatch,
        tmp_path,
    )

    article_path = (
        articles / "BENCH-0001.json"
    )

    write_json(
        article_path,
        create_complete_article(
            status="ready",
        ),
    )

    promote_draft(
        "bench-0001"
    )

    data = json.loads(
        article_path.read_text(
            encoding="utf-8",
        )
    )

    assert data["status"] == "draft"


def test_promote_ready_rejects_unknown_id(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_directories(
        monkeypatch,
        tmp_path,
    )

    with pytest.raises(
        SystemExit,
        match="BENCH-9999 not found",
    ):
        promote_ready(
            "BENCH-9999"
        )


def test_promote_draft_rejects_unknown_id(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_directories(
        monkeypatch,
        tmp_path,
    )

    with pytest.raises(
        SystemExit,
        match="BENCH-9999 not found",
    ):
        promote_draft(
            "BENCH-9999"
        )


def test_main_requires_id_for_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark_dataset_manager.py",
            "ready",
        ],
    )

    with pytest.raises(
        SystemExit,
        match="Benchmark ID required",
    ):
        main()


def test_main_requires_id_for_draft(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark_dataset_manager.py",
            "draft",
        ],
    )

    with pytest.raises(
        SystemExit,
        match="Benchmark ID required",
    ):
        main()