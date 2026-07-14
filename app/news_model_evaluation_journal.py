import json
from dataclasses import asdict
from pathlib import Path

from app.news_model_evaluation import (
    NewsModelEvaluation,
)


class NewsModelEvaluationJournal:
    def __init__(
        self,
        file_path: str = (
            "data/news_model_evaluations.jsonl"
        ),
    ) -> None:
        self.file_path = Path(
            file_path
        )

    def record(
        self,
        evaluation: NewsModelEvaluation,
    ) -> None:
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = asdict(
            evaluation
        )

        analysis = data.get(
            "analysis"
        )

        if isinstance(analysis, dict):
            source = evaluation.analysis

            if source is None:
                raise TypeError(
                    "Evaluation analysis was missing."
                )

            analysis["impact_term"] = (
                source.impact_term.value
            )
            analysis["impact_scope"] = (
                source.impact_scope.value
            )
            analysis["sentiment"] = (
                source.sentiment.value
            )
            analysis["scope_items"] = list(
                source.scope_items
            )
            analysis["highlights"] = list(
                source.highlights
            )

        data["rejection_reasons"] = list(
            evaluation.rejection_reasons
        )

        with self.file_path.open(
            mode="a",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
            )
            file.write("\n")