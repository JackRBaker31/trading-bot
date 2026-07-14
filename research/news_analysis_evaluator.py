import re
from dataclasses import dataclass

from app.news_analysis import NewsAnalysis
from research.benchmark_dataset import (
    BenchmarkLabel,
)


@dataclass(frozen=True)
class NewsAnalysisEvaluation:
    sentiment_correct: bool
    impact_term_correct: bool
    impact_scope_correct: bool
    scope_item_precision: float
    scope_item_recall: float
    highlight_similarity: float
    overall_score: float


def evaluate_news_analysis(
    *,
    analysis: NewsAnalysis,
    expected: BenchmarkLabel,
) -> NewsAnalysisEvaluation:
    sentiment_correct = (
        analysis.sentiment.value
        == expected.sentiment
    )

    impact_term_correct = (
        analysis.impact_term.value
        == expected.impact_term
    )

    impact_scope_correct = (
        analysis.impact_scope.value
        == expected.impact_scope
    )

    scope_item_precision = (
        _calculate_precision(
            predicted=set(
                analysis.scope_items
            ),
            expected=set(
                expected.scope_items
            ),
        )
    )

    scope_item_recall = (
        _calculate_recall(
            predicted=set(
                analysis.scope_items
            ),
            expected=set(
                expected.scope_items
            ),
        )
    )

    highlight_similarity = (
        _calculate_highlight_similarity(
            predicted=(
                analysis.highlights
            ),
            expected=(
                expected.highlights
            ),
        )
    )

    component_scores = (
        float(sentiment_correct),
        float(impact_term_correct),
        float(impact_scope_correct),
        scope_item_precision,
        scope_item_recall,
        highlight_similarity,
    )

    overall_score = (
        sum(component_scores)
        / len(component_scores)
    )

    return NewsAnalysisEvaluation(
        sentiment_correct=(
            sentiment_correct
        ),
        impact_term_correct=(
            impact_term_correct
        ),
        impact_scope_correct=(
            impact_scope_correct
        ),
        scope_item_precision=(
            scope_item_precision
        ),
        scope_item_recall=(
            scope_item_recall
        ),
        highlight_similarity=(
            highlight_similarity
        ),
        overall_score=overall_score,
    )


def _calculate_precision(
    *,
    predicted: set[str],
    expected: set[str],
) -> float:
    if not predicted:
        return (
            1.0
            if not expected
            else 0.0
        )

    correct = len(
        predicted & expected
    )

    return correct / len(predicted)


def _calculate_recall(
    *,
    predicted: set[str],
    expected: set[str],
) -> float:
    if not expected:
        return (
            1.0
            if not predicted
            else 0.0
        )

    correct = len(
        predicted & expected
    )

    return correct / len(expected)


def _calculate_highlight_similarity(
    *,
    predicted: tuple[str, ...],
    expected: tuple[str, ...],
) -> float:
    predicted_tokens = _tokenize(
        " ".join(predicted)
    )

    expected_tokens = _tokenize(
        " ".join(expected)
    )

    if not predicted_tokens:
        return (
            1.0
            if not expected_tokens
            else 0.0
        )

    if not expected_tokens:
        return 0.0

    intersection = len(
        predicted_tokens
        & expected_tokens
    )

    union = len(
        predicted_tokens
        | expected_tokens
    )

    if union == 0:
        return 1.0

    return intersection / union


def _tokenize(
    text: str,
) -> set[str]:
    return {
        token.lower()
        for token in re.findall(
            r"[A-Za-z0-9]+",
            text,
        )
    }