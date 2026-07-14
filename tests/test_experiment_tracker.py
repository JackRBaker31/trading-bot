import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from research.experiment_tracker import (
    ExperimentJournal,
    create_experiment,
)


def create_test_experiment():
    return create_experiment(
        experiment_id="EXP-0001",
        created_at=datetime(
            2026,
            7,
            14,
            13,
            0,
            tzinfo=timezone.utc,
        ),
        model_name="qwen-stocks",
        prompt_version="v3",
        dataset_version="v1",
        total_articles=100,
        parse_success_rate=1.0,
        grounding_approval_rate=0.95,
        sentiment_accuracy=0.92,
        impact_term_accuracy=0.90,
        impact_scope_accuracy=0.91,
        average_scope_precision=0.94,
        average_scope_recall=0.89,
        average_highlight_similarity=0.87,
        average_overall_score=0.91,
        average_duration_seconds=2.8,
    )


def test_creates_valid_experiment() -> None:
    experiment = create_test_experiment()

    assert experiment.experiment_id == (
        "EXP-0001"
    )
    assert experiment.model_name == (
        "qwen-stocks"
    )
    assert experiment.prompt_version == "v3"
    assert experiment.dataset_version == "v1"
    assert experiment.total_articles == 100
    assert experiment.average_overall_score == (
        0.91
    )


def test_rejects_metric_above_one() -> None:
    with pytest.raises(
        ValueError,
        match="sentiment_accuracy",
    ):
        create_experiment(
            model_name="model",
            prompt_version="v1",
            dataset_version="v1",
            total_articles=1,
            parse_success_rate=1.0,
            grounding_approval_rate=1.0,
            sentiment_accuracy=1.1,
            impact_term_accuracy=1.0,
            impact_scope_accuracy=1.0,
            average_scope_precision=1.0,
            average_scope_recall=1.0,
            average_highlight_similarity=1.0,
            average_overall_score=1.0,
            average_duration_seconds=1.0,
        )


def test_records_experiment_as_jsonl(
    tmp_path: Path,
) -> None:
    file_path = (
        tmp_path / "experiments.jsonl"
    )

    journal = ExperimentJournal(
        file_path=str(file_path)
    )

    journal.record(
        create_test_experiment()
    )

    lines = file_path.read_text(
        encoding="utf-8",
    ).splitlines()

    assert len(lines) == 1

    data = json.loads(lines[0])

    assert data["experiment_id"] == (
        "EXP-0001"
    )
    assert data["model_name"] == (
        "qwen-stocks"
    )
    assert data["prompt_version"] == "v3"
    assert data["dataset_version"] == "v1"
    assert data["average_overall_score"] == (
        0.91
    )


def test_loads_recorded_experiments(
    tmp_path: Path,
) -> None:
    file_path = (
        tmp_path / "experiments.jsonl"
    )

    journal = ExperimentJournal(
        file_path=str(file_path)
    )

    expected = create_test_experiment()

    journal.record(expected)

    loaded = journal.load_all()

    assert loaded == [expected]


def test_load_returns_empty_for_missing_file(
    tmp_path: Path,
) -> None:
    journal = ExperimentJournal(
        file_path=str(
            tmp_path / "missing.jsonl"
        )
    )

    assert journal.load_all() == []