import json
from pathlib import Path

from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.news_analysis_validator import (
    NewsAnalysisValidator,
)
from research.benchmark_dataset import (
    BenchmarkDataset,
)
from research.news_benchmark import (
    run_news_benchmark,
    save_report,
)


class FakeAnalyser:
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        return NewsAnalysis(
            impact_term=(
                NewsImpactTerm.SHORTTERM
            ),
            impact_scope=(
                NewsImpactScope.STOCK
            ),
            scope_items=("AAPL",),
            highlights=(
                "Apple reported stronger revenue",
                "Apple raised its guidance",
            ),
            sentiment=(
                NewsSentiment.POSITIVE
            ),
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


def create_dataset(
    tmp_path: Path,
) -> BenchmarkDataset:
    articles = tmp_path / "articles"
    labels = tmp_path / "labels"

    write_json(
        articles / "BENCH-0001.json",
        {
            "benchmark_id": "BENCH-0001",
            "headline": (
                "Apple raises guidance"
            ),
            "source": "Manual benchmark",
            "category": "guidance",
            "sector": "Technology",
            "company": "Apple",
            "ticker": "AAPL",
            "difficulty": "easy",
            "published_at": (
                "2026-07-14T00:00:00Z"
            ),
            "article_text": (
                "Apple reported stronger revenue "
                "and raised its guidance."
            ),
        },
    )

    write_json(
        labels / "BENCH-0001.json",
        {
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
        },
    )

    dataset = BenchmarkDataset(
        articles_directory=articles,
        labels_directory=labels,
    )

    dataset.load()

    return dataset


def test_runs_managed_dataset_benchmark(
    tmp_path: Path,
) -> None:
    report = run_news_benchmark(
        analyser=FakeAnalyser(),
        validator=NewsAnalysisValidator(),
        dataset=create_dataset(tmp_path),
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    assert report.total_articles == 1
    assert report.parse_success_count == 1
    assert (
        report.validation_approved_count
        == 1
    )
    assert report.parse_success_rate == 1.0
    assert (
        report.validation_approval_rate
        == 1.0
    )
    assert report.sentiment_accuracy == 1.0
    assert report.impact_term_accuracy == 1.0
    assert report.impact_scope_accuracy == 1.0
    assert report.average_scope_precision == 1.0
    assert report.average_scope_recall == 1.0
    assert (
        report.average_highlight_similarity
        == 1.0
    )
    assert report.average_overall_score == 1.0


def test_report_contains_gold_label_metrics(
    tmp_path: Path,
) -> None:
    report = run_news_benchmark(
        analyser=FakeAnalyser(),
        validator=NewsAnalysisValidator(),
        dataset=create_dataset(tmp_path),
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    file_path = tmp_path / "report.json"

    save_report(
        report=report,
        file_path=file_path,
    )

    data = json.loads(
        file_path.read_text(
            encoding="utf-8"
        )
    )

    assert data["dataset_version"] == "v1"
    assert data["sentiment_accuracy"] == 1.0
    assert data["impact_term_accuracy"] == 1.0
    assert data["impact_scope_accuracy"] == 1.0
    assert (
        data["average_highlight_similarity"]
        == 1.0
    )
    assert data["average_overall_score"] == 1.0

    item = data["items"][0]

    assert item["benchmark_id"] == (
        "BENCH-0001"
    )

    assert item["evaluation"][
        "overall_score"
    ] == 1.0


def test_invalid_dataset_is_rejected(
    tmp_path: Path,
) -> None:
    dataset = BenchmarkDataset(
        articles_directory=(
            tmp_path / "articles"
        ),
        labels_directory=(
            tmp_path / "labels"
        ),
    )

    dataset.load()

    report = run_news_benchmark(
        analyser=FakeAnalyser(),
        validator=NewsAnalysisValidator(),
        dataset=dataset,
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    assert report.total_articles == 0
    assert report.average_overall_score == 0.0