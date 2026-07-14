import os
from datetime import datetime, timezone
from pathlib import Path

from app.news_analysis_service import (
    NewsAnalysisService,
)
from app.news_analysis_validator import (
    NewsAnalysisValidator,
)
from app.news_model_client import (
    NewsModelClient,
)
from app.ollama_news_transport import (
    OllamaNewsTransport,
)
from research.benchmark_dataset import (
    BenchmarkDataset,
)
from research.experiment_tracker import (
    ExperimentJournal,
    create_experiment,
)
from research.news_benchmark import (
    run_news_benchmark,
    save_report,
)


DEFAULT_MODEL_NAME = (
    "hf.co/VaibTFU/"
    "qwen-0.5b-stocks-news-v2-GGUF:Q4_K_M"
)

PROMPT_VERSION = "v3"
DATASET_VERSION = "v1"


def main() -> None:
    model_name = os.getenv(
        "OLLAMA_NEWS_MODEL",
        DEFAULT_MODEL_NAME,
    ).strip()

    dataset = BenchmarkDataset(
        articles_directory=Path(
            "research/articles"
        ),
        labels_directory=Path(
            "research/labels"
        ),
    )

    dataset.load()

    dataset_validation = dataset.validate()

    if not dataset_validation.approved:
        print()
        print(
            "Benchmark dataset validation failed."
        )

        for error in dataset_validation.errors:
            print(f"- {error}")

        raise SystemExit(1)

    transport = OllamaNewsTransport(
        model_name=model_name,
    )

    model_client = NewsModelClient(
        transport=transport,
    )

    analyser = NewsAnalysisService(
        model_client=model_client,
    )

    report = run_news_benchmark(
        analyser=analyser,
        validator=NewsAnalysisValidator(),
        dataset=dataset,
        model_name=model_name,
        prompt_version=PROMPT_VERSION,
        dataset_version=DATASET_VERSION,
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    report_path = (
        Path("research/reports")
        / f"news-benchmark-{timestamp}.json"
    )

    save_report(
        report=report,
        file_path=report_path,
    )

    experiment = create_experiment(
        model_name=report.model_name,
        prompt_version=(
            report.prompt_version
        ),
        dataset_version=(
            report.dataset_version
        ),
        total_articles=(
            report.total_articles
        ),
        parse_success_rate=(
            report.parse_success_rate
        ),
        grounding_approval_rate=(
            report.validation_approval_rate
        ),
        sentiment_accuracy=(
            report.sentiment_accuracy
        ),
        impact_term_accuracy=(
            report.impact_term_accuracy
        ),
        impact_scope_accuracy=(
            report.impact_scope_accuracy
        ),
        average_scope_precision=(
            report.average_scope_precision
        ),
        average_scope_recall=(
            report.average_scope_recall
        ),
        average_highlight_similarity=(
            report
            .average_highlight_similarity
        ),
        average_overall_score=(
            report.average_overall_score
        ),
        average_duration_seconds=(
            report.average_duration_seconds
        ),
    )

    experiment_journal = ExperimentJournal()

    experiment_journal.record(
        experiment
    )

    print()
    print("=" * 60)
    print("NEWS MODEL BENCHMARK")
    print("=" * 60)
    print(f"Model: {report.model_name}")
    print(
        "Prompt version: "
        f"{report.prompt_version}"
    )
    print(
        "Dataset version: "
        f"{report.dataset_version}"
    )
    print(
        f"Articles: {report.total_articles}"
    )
    print(
        "Schema success: "
        f"{report.parse_success_count}/"
        f"{report.total_articles} "
        f"({report.parse_success_rate:.1%})"
    )
    print(
        "Grounding approved: "
        f"{report.validation_approved_count}/"
        f"{report.total_articles} "
        f"({report.validation_approval_rate:.1%})"
    )
    print(
        "Sentiment accuracy: "
        f"{report.sentiment_accuracy:.1%}"
    )
    print(
        "Impact-term accuracy: "
        f"{report.impact_term_accuracy:.1%}"
    )
    print(
        "Impact-scope accuracy: "
        f"{report.impact_scope_accuracy:.1%}"
    )
    print(
        "Scope precision: "
        f"{report.average_scope_precision:.1%}"
    )
    print(
        "Scope recall: "
        f"{report.average_scope_recall:.1%}"
    )
    print(
        "Highlight similarity: "
        f"{report.average_highlight_similarity:.1%}"
    )
    print(
        "Overall score: "
        f"{report.average_overall_score:.1%}"
    )
    print(
        "Average latency: "
        f"{report.average_duration_seconds:.3f}s"
    )
    print("-" * 60)

    for item in report.items:
        outcome = (
            "APPROVED"
            if item.validation_approved
            else "REJECTED"
        )

        print(
            f"{item.benchmark_id}: "
            f"{outcome} "
            f"({item.duration_seconds:.3f}s)"
        )

        if item.evaluation is not None:
            print(
                "  Gold-label score: "
                f"{item.evaluation.overall_score:.1%}"
            )

        for reason in item.rejection_reasons:
            print(f"  - {reason}")

    print("-" * 60)
    print(f"Report saved: {report_path}")
    print(
        "Experiment recorded: "
        f"{experiment.experiment_id}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()