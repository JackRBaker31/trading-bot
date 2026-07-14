import pytest

from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.news_analysis_validator import (
    NewsAnalysisValidationResult,
)
from app.news_model_evaluation import (
    create_news_model_evaluation,
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
            "Apple raised its guidance.",
        ),
        sentiment=(
            NewsSentiment.POSITIVE
        ),
    )


def test_records_successful_grounded_evaluation() -> None:
    analysis = create_analysis()

    evaluation = (
        create_news_model_evaluation(
            model_name="stocks-news",
            prompt_version="v1",
            duration_seconds=1.25,
            analysis=analysis,
            validation_result=(
                NewsAnalysisValidationResult(
                    approved=True,
                    reasons=(),
                )
            ),
        )
    )

    assert evaluation.parse_succeeded is True
    assert evaluation.validation_approved is True
    assert evaluation.schema_valid is True
    assert evaluation.grounded is True
    assert evaluation.analysis == analysis
    assert evaluation.rejection_reasons == ()


def test_records_grounding_rejection() -> None:
    evaluation = (
        create_news_model_evaluation(
            model_name="stocks-news",
            prompt_version="v1",
            duration_seconds=2.0,
            analysis=create_analysis(),
            validation_result=(
                NewsAnalysisValidationResult(
                    approved=False,
                    reasons=(
                        "Unsupported numeric claim: 14",
                    ),
                )
            ),
        )
    )

    assert evaluation.parse_succeeded is True
    assert evaluation.validation_approved is False
    assert evaluation.grounded is False
    assert evaluation.rejection_reasons == (
        "Unsupported numeric claim: 14",
    )


def test_records_parse_failure() -> None:
    evaluation = (
        create_news_model_evaluation(
            model_name="stocks-news",
            prompt_version="v1",
            duration_seconds=0.5,
            analysis=None,
            validation_result=None,
            parse_error=(
                "Output was not valid JSON."
            ),
        )
    )

    assert evaluation.parse_succeeded is False
    assert evaluation.schema_valid is False
    assert evaluation.grounded is False
    assert evaluation.analysis is None
    assert evaluation.rejection_reasons == (
        "Output was not valid JSON.",
    )


def test_rejects_negative_duration() -> None:
    with pytest.raises(
        ValueError,
        match="Duration",
    ):
        create_news_model_evaluation(
            model_name="stocks-news",
            prompt_version="v1",
            duration_seconds=-1,
            analysis=None,
            validation_result=None,
        )