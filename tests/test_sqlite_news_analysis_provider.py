from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.sqlite_news_analysis_provider import (
    SQLiteNewsAnalysisProvider,
)
from app.sqlite_news_analysis_repository import (
    SQLiteNewsAnalysisRepository,
)
from app.stored_news_analysis import (
    StoredNewsAnalysis,
)


def create_stored_analysis(
    *,
    analysed_at: datetime,
) -> StoredNewsAnalysis:
    return StoredNewsAnalysis(
        analysis=NewsAnalysis(
            impact_term=NewsImpactTerm.SHORTTERM,
            impact_scope=NewsImpactScope.STOCK,
            scope_items=("AAPL",),
            highlights=(
                "Apple received negative news",
            ),
            sentiment=NewsSentiment.NEGATIVE,
        ),
        analysed_at=analysed_at,
        expires_at=(
            analysed_at
            + timedelta(minutes=30)
        ),
        article_title=(
            "Apple receives negative news"
        ),
        article_url=(
            "https://example.test/apple"
        ),
        published_at=(
            analysed_at
            - timedelta(minutes=15)
        ),
        relevance_score=0.92,
        source_sentiment_label=(
            "Somewhat-Bearish"
        ),
        source_sentiment_score=-0.35,
        model_name="fake-model",
        prompt_version="v3",
    )


def test_returns_unexpired_analysis_from_repository(
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

    repository = SQLiteNewsAnalysisRepository(
        database_path=(
            tmp_path
            / "news.db"
        )
    )

    stored = create_stored_analysis(
        analysed_at=now,
    )

    repository.save(
        symbol="AAPL",
        stored_analysis=stored,
    )

    provider = SQLiteNewsAnalysisProvider(
        repository=repository,
        now_provider=lambda: now,
    )

    assert (
        provider.get_analysis(" aapl ")
        == stored.analysis
    )
    assert (
        provider.get_stored_analysis("AAPL")
        == stored
    )


def test_returns_none_when_latest_analysis_expired(
    tmp_path,
) -> None:
    analysed_at = datetime(
        2026,
        7,
        17,
        12,
        0,
        tzinfo=timezone.utc,
    )

    repository = SQLiteNewsAnalysisRepository(
        database_path=(
            tmp_path
            / "news.db"
        )
    )

    repository.save(
        symbol="AAPL",
        stored_analysis=create_stored_analysis(
            analysed_at=analysed_at,
        ),
    )

    provider = SQLiteNewsAnalysisProvider(
        repository=repository,
        now_provider=lambda: (
            analysed_at
            + timedelta(minutes=31)
        ),
    )

    assert (
        provider.get_analysis("AAPL")
        is None
    )
    assert (
        provider.get_stored_analysis("AAPL")
        is None
    )


def test_saves_stored_analysis_to_repository(
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

    repository = SQLiteNewsAnalysisRepository(
        database_path=(
            tmp_path
            / "news.db"
        )
    )

    provider = SQLiteNewsAnalysisProvider(
        repository=repository,
        now_provider=lambda: now,
    )

    stored = create_stored_analysis(
        analysed_at=now,
    )

    provider.set_stored_analysis(
        symbol=" aapl ",
        stored_analysis=stored,
    )

    assert (
        repository.get_latest("AAPL")
        == stored
    )