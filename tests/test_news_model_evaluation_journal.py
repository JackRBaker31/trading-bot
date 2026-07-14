import json
from pathlib import Path

from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.news_model_evaluation import (
    NewsModelEvaluation,
)
from app.news_model_evaluation_journal import (
    NewsModelEvaluationJournal,
)


def test_records_grounded_evaluation_as_jsonl(
    tmp_path: Path,
) -> None:
    file_path = (
        tmp_path
        / "news_model_evaluations.jsonl"
    )

    journal = NewsModelEvaluationJournal(
        file_path=str(file_path)
    )

    evaluation = NewsModelEvaluation(
        model_name="stocks-news",
        prompt_version="v1",
        parse_succeeded=True,
        validation_approved=True,
        duration_seconds=1.25,
        analysis=NewsAnalysis(
            impact_term=(
                NewsImpactTerm.SHORTTERM
            ),
            impact_scope=(
                NewsImpactScope.STOCK
            ),
            scope_items=("AAPL",),
            highlights=(
                "Apple raised its guidance.",
            ),
            sentiment=(
                NewsSentiment.POSITIVE
            ),
        ),
        rejection_reasons=(),
    )

    journal.record(
        evaluation
    )

    lines = file_path.read_text(
        encoding="utf-8",
    ).splitlines()

    assert len(lines) == 1

    data = json.loads(
        lines[0]
    )

    assert data["model_name"] == (
        "stocks-news"
    )
    assert data["prompt_version"] == "v1"
    assert data["parse_succeeded"] is True
    assert (
        data["validation_approved"]
        is True
    )
    assert data["duration_seconds"] == 1.25
    assert data["rejection_reasons"] == []

    assert data["analysis"] == {
        "impact_term": "SHORTTERM",
        "impact_scope": "STOCK",
        "scope_items": ["AAPL"],
        "highlights": [
            "Apple raised its guidance."
        ],
        "sentiment": "POSITIVE",
    }


def test_records_parse_failure_without_analysis(
    tmp_path: Path,
) -> None:
    file_path = (
        tmp_path
        / "news_model_evaluations.jsonl"
    )

    journal = NewsModelEvaluationJournal(
        file_path=str(file_path)
    )

    journal.record(
        NewsModelEvaluation(
            model_name="stocks-news",
            prompt_version="v1",
            parse_succeeded=False,
            validation_approved=False,
            duration_seconds=0.5,
            analysis=None,
            rejection_reasons=(
                "Output was not valid JSON.",
            ),
        )
    )

    data = json.loads(
        file_path.read_text(
            encoding="utf-8",
        ).strip()
    )

    assert data["analysis"] is None
    assert data["parse_succeeded"] is False
    assert data["validation_approved"] is False
    assert data["rejection_reasons"] == [
        "Output was not valid JSON."
    ]