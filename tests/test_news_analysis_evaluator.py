import pytest

from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from research.benchmark_dataset import (
    BenchmarkLabel,
)
from research.news_analysis_evaluator import (
    evaluate_news_analysis,
)


def create_expected_label() -> BenchmarkLabel:
    return BenchmarkLabel(
        benchmark_id="BENCH-0001",
        impact_term="SHORTTERM",
        impact_scope="STOCK",
        scope_items=("AAPL",),
        highlights=(
            "Apple reported stronger revenue.",
            "Apple raised its guidance.",
        ),
        sentiment="POSITIVE",
    )


def test_exact_analysis_scores_one() -> None:
    expected = create_expected_label()

    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("AAPL",),
        highlights=(
            "Apple reported stronger revenue.",
            "Apple raised its guidance.",
        ),
        sentiment=(
            NewsSentiment.POSITIVE
        ),
    )

    result = evaluate_news_analysis(
        analysis=analysis,
        expected=expected,
    )

    assert result.sentiment_correct is True
    assert result.impact_term_correct is True
    assert result.impact_scope_correct is True
    assert result.scope_item_precision == 1.0
    assert result.scope_item_recall == 1.0
    assert result.highlight_similarity == 1.0
    assert result.overall_score == 1.0


def test_wrong_classifications_reduce_score() -> None:
    expected = create_expected_label()

    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.LONGTERM
        ),
        impact_scope=(
            NewsImpactScope.GLOBAL
        ),
        scope_items=("AAPL",),
        highlights=(
            "Apple reported stronger revenue.",
            "Apple raised its guidance.",
        ),
        sentiment=(
            NewsSentiment.NEGATIVE
        ),
    )

    result = evaluate_news_analysis(
        analysis=analysis,
        expected=expected,
    )

    assert result.sentiment_correct is False
    assert result.impact_term_correct is False
    assert result.impact_scope_correct is False

    assert result.overall_score == pytest.approx(
        0.5
    )


def test_scope_item_precision_and_recall() -> None:
    expected = BenchmarkLabel(
        benchmark_id="BENCH-0002",
        impact_term="SHORTTERM",
        impact_scope="STOCK",
        scope_items=(
            "AAPL",
            "MSFT",
        ),
        highlights=(),
        sentiment="NEUTRAL",
    )

    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=(
            "AAPL",
            "NVDA",
        ),
        highlights=(),
        sentiment=(
            NewsSentiment.NEUTRAL
        ),
    )

    result = evaluate_news_analysis(
        analysis=analysis,
        expected=expected,
    )

    assert (
        result.scope_item_precision
        == 0.5
    )

    assert (
        result.scope_item_recall
        == 0.5
    )


def test_empty_scope_items_match() -> None:
    expected = BenchmarkLabel(
        benchmark_id="BENCH-0003",
        impact_term="SHORTTERM",
        impact_scope="GLOBAL",
        scope_items=(),
        highlights=(),
        sentiment="NEUTRAL",
    )

    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.GLOBAL
        ),
        scope_items=(),
        highlights=(),
        sentiment=(
            NewsSentiment.NEUTRAL
        ),
    )

    result = evaluate_news_analysis(
        analysis=analysis,
        expected=expected,
    )

    assert (
        result.scope_item_precision
        == 1.0
    )

    assert (
        result.scope_item_recall
        == 1.0
    )

    assert (
        result.highlight_similarity
        == 1.0
    )


def test_highlight_similarity_is_partial() -> None:
    expected = create_expected_label()

    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("AAPL",),
        highlights=(
            "Apple raised guidance.",
        ),
        sentiment=(
            NewsSentiment.POSITIVE
        ),
    )

    result = evaluate_news_analysis(
        analysis=analysis,
        expected=expected,
    )

    assert (
        0.0
        < result.highlight_similarity
        < 1.0
    )

    assert (
        0.0
        < result.overall_score
        < 1.0
    )