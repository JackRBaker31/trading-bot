from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.news_analysis_validator import (
    NewsAnalysisValidator,
)


def test_rejects_unsupported_numeric_claims() -> None:
    analysis = NewsAnalysis(
        impact_term=NewsImpactTerm.SHORTTERM,
        impact_scope=NewsImpactScope.STOCK,
        scope_items=("AAPL",),
        highlights=(
            "Revenue grew 14 percent.",
        ),
        sentiment=NewsSentiment.POSITIVE,
    )

    result = NewsAnalysisValidator().validate(
        article_text=(
            "Apple reported stronger revenue."
        ),
        analysis=analysis,
        allowed_symbols={"AAPL"},
    )

    assert result.approved is False
    assert "14" in result.reasons[0]


def test_accepts_grounded_analysis() -> None:
    analysis = NewsAnalysis(
        impact_term=NewsImpactTerm.SHORTTERM,
        impact_scope=NewsImpactScope.STOCK,
        scope_items=("AAPL",),
        highlights=(
            "Apple reported stronger revenue.",
            "Apple raised its guidance.",
        ),
        sentiment=NewsSentiment.POSITIVE,
    )

    result = NewsAnalysisValidator().validate(
        article_text=(
            "Apple reported stronger revenue "
            "and raised its guidance."
        ),
        analysis=analysis,
        allowed_symbols={"AAPL"},
    )

    assert result.approved is True
    assert result.reasons == ()


def test_rejects_unknown_scope_item() -> None:
    analysis = NewsAnalysis(
        impact_term=NewsImpactTerm.SHORTTERM,
        impact_scope=NewsImpactScope.STOCK,
        scope_items=("APPLE",),
        highlights=(
            "Apple raised its guidance.",
        ),
        sentiment=NewsSentiment.POSITIVE,
    )

    result = NewsAnalysisValidator().validate(
        article_text=(
            "Apple raised its guidance."
        ),
        analysis=analysis,
        allowed_symbols={"AAPL"},
    )

    assert result.approved is False
    assert "APPLE" in result.reasons[0]