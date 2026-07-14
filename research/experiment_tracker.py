import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class NewsBenchmarkExperiment:
    experiment_id: str
    created_at: datetime
    model_name: str
    prompt_version: str
    dataset_version: str
    total_articles: int
    parse_success_rate: float
    grounding_approval_rate: float
    sentiment_accuracy: float
    impact_term_accuracy: float
    impact_scope_accuracy: float
    average_scope_precision: float
    average_scope_recall: float
    average_highlight_similarity: float
    average_overall_score: float
    average_duration_seconds: float

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        data = asdict(self)

        data["created_at"] = (
            self.created_at
            .astimezone(timezone.utc)
            .isoformat()
        )

        return data


def create_experiment(
    *,
    model_name: str,
    prompt_version: str,
    dataset_version: str,
    total_articles: int,
    parse_success_rate: float,
    grounding_approval_rate: float,
    sentiment_accuracy: float,
    impact_term_accuracy: float,
    impact_scope_accuracy: float,
    average_scope_precision: float,
    average_scope_recall: float,
    average_highlight_similarity: float,
    average_overall_score: float,
    average_duration_seconds: float,
    experiment_id: str | None = None,
    created_at: datetime | None = None,
) -> NewsBenchmarkExperiment:
    cleaned_model_name = model_name.strip()
    cleaned_prompt_version = prompt_version.strip()
    cleaned_dataset_version = dataset_version.strip()

    if not cleaned_model_name:
        raise ValueError(
            "Model name is required."
        )

    if not cleaned_prompt_version:
        raise ValueError(
            "Prompt version is required."
        )

    if not cleaned_dataset_version:
        raise ValueError(
            "Dataset version is required."
        )

    if total_articles < 0:
        raise ValueError(
            "Total articles cannot be negative."
        )

    metrics = {
        "parse_success_rate": parse_success_rate,
        "grounding_approval_rate": (
            grounding_approval_rate
        ),
        "sentiment_accuracy": sentiment_accuracy,
        "impact_term_accuracy": (
            impact_term_accuracy
        ),
        "impact_scope_accuracy": (
            impact_scope_accuracy
        ),
        "average_scope_precision": (
            average_scope_precision
        ),
        "average_scope_recall": (
            average_scope_recall
        ),
        "average_highlight_similarity": (
            average_highlight_similarity
        ),
        "average_overall_score": (
            average_overall_score
        ),
    }

    for metric_name, metric_value in (
        metrics.items()
    ):
        if not 0.0 <= metric_value <= 1.0:
            raise ValueError(
                f"{metric_name} must be between "
                "0 and 1."
            )

    if average_duration_seconds < 0:
        raise ValueError(
            "Average duration cannot be negative."
        )

    resolved_experiment_id = (
        experiment_id.strip()
        if experiment_id is not None
        else f"EXP-{uuid4().hex[:12].upper()}"
    )

    if not resolved_experiment_id:
        raise ValueError(
            "Experiment ID is required."
        )

    resolved_created_at = (
        created_at
        if created_at is not None
        else datetime.now(timezone.utc)
    )

    if resolved_created_at.tzinfo is None:
        raise ValueError(
            "Experiment timestamp must be "
            "timezone-aware."
        )

    return NewsBenchmarkExperiment(
        experiment_id=resolved_experiment_id,
        created_at=resolved_created_at,
        model_name=cleaned_model_name,
        prompt_version=cleaned_prompt_version,
        dataset_version=cleaned_dataset_version,
        total_articles=total_articles,
        parse_success_rate=parse_success_rate,
        grounding_approval_rate=(
            grounding_approval_rate
        ),
        sentiment_accuracy=sentiment_accuracy,
        impact_term_accuracy=(
            impact_term_accuracy
        ),
        impact_scope_accuracy=(
            impact_scope_accuracy
        ),
        average_scope_precision=(
            average_scope_precision
        ),
        average_scope_recall=(
            average_scope_recall
        ),
        average_highlight_similarity=(
            average_highlight_similarity
        ),
        average_overall_score=(
            average_overall_score
        ),
        average_duration_seconds=(
            average_duration_seconds
        ),
    )


class ExperimentJournal:
    def __init__(
        self,
        file_path: str = (
            "research/experiments/"
            "news_benchmark_experiments.jsonl"
        ),
    ) -> None:
        self.file_path = Path(file_path)

    def record(
        self,
        experiment: NewsBenchmarkExperiment,
    ) -> None:
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.file_path.open(
            mode="a",
            encoding="utf-8",
        ) as file:
            json.dump(
                experiment.to_dictionary(),
                file,
                ensure_ascii=False,
            )
            file.write("\n")

    def load_all(
        self,
    ) -> list[NewsBenchmarkExperiment]:
        if not self.file_path.exists():
            return []

        experiments: list[
            NewsBenchmarkExperiment
        ] = []

        for line_number, raw_line in enumerate(
            self.file_path.read_text(
                encoding="utf-8"
            ).splitlines(),
            start=1,
        ):
            if not raw_line.strip():
                continue

            try:
                data = json.loads(raw_line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    "Invalid experiment JSON on "
                    f"line {line_number}."
                ) from error

            if not isinstance(data, dict):
                raise ValueError(
                    "Experiment entry must be an "
                    f"object on line {line_number}."
                )

            try:
                created_at = datetime.fromisoformat(
                    str(data["created_at"])
                )

                experiment = create_experiment(
                    experiment_id=str(
                        data["experiment_id"]
                    ),
                    created_at=created_at,
                    model_name=str(
                        data["model_name"]
                    ),
                    prompt_version=str(
                        data["prompt_version"]
                    ),
                    dataset_version=str(
                        data["dataset_version"]
                    ),
                    total_articles=int(
                        data["total_articles"]
                    ),
                    parse_success_rate=float(
                        data["parse_success_rate"]
                    ),
                    grounding_approval_rate=float(
                        data[
                            "grounding_approval_rate"
                        ]
                    ),
                    sentiment_accuracy=float(
                        data["sentiment_accuracy"]
                    ),
                    impact_term_accuracy=float(
                        data["impact_term_accuracy"]
                    ),
                    impact_scope_accuracy=float(
                        data[
                            "impact_scope_accuracy"
                        ]
                    ),
                    average_scope_precision=float(
                        data[
                            "average_scope_precision"
                        ]
                    ),
                    average_scope_recall=float(
                        data[
                            "average_scope_recall"
                        ]
                    ),
                    average_highlight_similarity=float(
                        data[
                            "average_highlight_similarity"
                        ]
                    ),
                    average_overall_score=float(
                        data[
                            "average_overall_score"
                        ]
                    ),
                    average_duration_seconds=float(
                        data[
                            "average_duration_seconds"
                        ]
                    ),
                )
            except (
                KeyError,
                TypeError,
                ValueError,
            ) as error:
                raise ValueError(
                    "Experiment entry did not match "
                    "the required schema on line "
                    f"{line_number}."
                ) from error

            experiments.append(experiment)

        return experiments