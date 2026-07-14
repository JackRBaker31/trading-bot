from dataclasses import dataclass

from app.news_analysis import NewsAnalysis
from app.news_analysis_validator import (
    NewsAnalysisValidationResult,
)


@dataclass(frozen=True)
class NewsModelEvaluation:
    model_name: str
    prompt_version: str
    parse_succeeded: bool
    validation_approved: bool
    duration_seconds: float
    analysis: NewsAnalysis | None
    rejection_reasons: tuple[str, ...]

    @property
    def schema_valid(
        self,
    ) -> bool:
        return self.parse_succeeded

    @property
    def grounded(
        self,
    ) -> bool:
        return (
            self.parse_succeeded
            and self.validation_approved
        )


def create_news_model_evaluation(
    *,
    model_name: str,
    prompt_version: str,
    duration_seconds: float,
    analysis: NewsAnalysis | None,
    validation_result: (
        NewsAnalysisValidationResult | None
    ),
    parse_error: str | None = None,
) -> NewsModelEvaluation:
    cleaned_model_name = model_name.strip()
    cleaned_prompt_version = (
        prompt_version.strip()
    )

    if not cleaned_model_name:
        raise ValueError(
            "Model name is required."
        )

    if not cleaned_prompt_version:
        raise ValueError(
            "Prompt version is required."
        )

    if duration_seconds < 0:
        raise ValueError(
            "Duration cannot be negative."
        )

    parse_succeeded = analysis is not None

    if not parse_succeeded:
        reasons = (
            (parse_error.strip(),)
            if parse_error
            and parse_error.strip()
            else (
                "Model output could not be parsed.",
            )
        )

        return NewsModelEvaluation(
            model_name=cleaned_model_name,
            prompt_version=cleaned_prompt_version,
            parse_succeeded=False,
            validation_approved=False,
            duration_seconds=duration_seconds,
            analysis=None,
            rejection_reasons=reasons,
        )

    if validation_result is None:
        raise ValueError(
            "Validation result is required "
            "when parsing succeeds."
        )

    return NewsModelEvaluation(
        model_name=cleaned_model_name,
        prompt_version=cleaned_prompt_version,
        parse_succeeded=True,
        validation_approved=(
            validation_result.approved
        ),
        duration_seconds=duration_seconds,
        analysis=analysis,
        rejection_reasons=(
            validation_result.reasons
        ),
    )