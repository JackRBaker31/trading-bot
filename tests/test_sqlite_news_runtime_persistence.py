from datetime import (
    datetime,
    timezone,
)

from app.expiring_news_analysis_provider import (
    ExpiringNewsAnalysisProvider,
)
from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.news_analysis_refresh_service import (
    NewsAnalysisRefreshService,
)
from app.news_analysis_validator import (
    NewsAnalysisValidator,
)
from app.news_article import (
    NewsArticle,
)
from app.sqlite_news_analysis_provider import (
    SQLiteNewsAnalysisProvider,
)
from app.sqlite_news_analysis_repository import (
    SQLiteNewsAnalysisRepository,
)


class FakeAnalyser:
    def __init__(
        self,
        *,
        analysis: NewsAnalysis,
    ) -> None:
        self.analysis = analysis

    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        return self.analysis


def test_structured_analysis_survives_provider_restart(
    tmp_path,
) -> None:
    now = datetime(
        2026,
        7,
        17,
        12,
        0,
        tzinfo=timezone.utc,
    )

    database_path = (
        tmp_path
        / "news.db"
    )

    repository_a = SQLiteNewsAnalysisRepository(
        database_path=database_path,
    )

    provider_a = SQLiteNewsAnalysisProvider(
        repository=repository_a,
        now_provider=lambda: now,
    )

    analysis = NewsAnalysis(
        impact_term=NewsImpactTerm.SHORTTERM,
        impact_scope=NewsImpactScope.STOCK,
        scope_items=("AAPL",),
        highlights=(
            "Apple lawsuit may face complications",
        ),
        sentiment=NewsSentiment.NEGATIVE,
    )

    article = NewsArticle(
        symbol="AAPL",
        title=(
            "Apple lawsuit faces complication"
        ),
        summary=(
            "A legal error could complicate "
            "Apple's initial case."
        ),
        published_at=datetime(
            2026,
            7,
            17,
            11,
            30,
            tzinfo=timezone.utc,
        ),
        source="alpha_vantage",
        url=(
            "https://example.test/apple"
        ),
        relevance_score=0.92,
        source_sentiment_label=(
            "Somewhat-Bearish"
        ),
        source_sentiment_score=-0.35,
    )

    service = NewsAnalysisRefreshService(
        analyser=FakeAnalyser(
            analysis=analysis
        ),
        validator=NewsAnalysisValidator(),
        provider=provider_a,
        now_provider=lambda: now,
        analysis_ttl_seconds=1_800,
    )

    service.refresh_article(
        article=article,
        model_name="fake-model",
        prompt_version="v3",
    )

    repository_b = SQLiteNewsAnalysisRepository(
        database_path=database_path,
    )

    provider_b = SQLiteNewsAnalysisProvider(
        repository=repository_b,
        now_provider=lambda: now,
    )

    restored = provider_b.get_stored_analysis(
        "AAPL"
    )

    assert restored is not None
    assert restored.analysis == analysis
    assert restored.article_title == (
        "Apple lawsuit faces complication"
    )
    assert restored.model_name == "fake-model"
    assert restored.prompt_version == "v3"