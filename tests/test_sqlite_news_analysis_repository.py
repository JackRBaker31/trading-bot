from datetime import (
    datetime,
    timezone,
)

from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.sqlite_news_analysis_repository import (
    SQLiteNewsAnalysisRepository,
)
from app.stored_news_analysis import (
    StoredNewsAnalysis,
)
from dataclasses import replace
from datetime import timedelta

def create_stored_analysis() -> StoredNewsAnalysis:
    analysed_at = datetime(
        2026,
        7,
        17,
        12,
        0,
        tzinfo=timezone.utc,
    )

    return StoredNewsAnalysis(
        analysis=NewsAnalysis(
            impact_term=(
                NewsImpactTerm.SHORTTERM
            ),
            impact_scope=(
                NewsImpactScope.STOCK
            ),
            scope_items=("AAPL",),
            highlights=(
                "Apple reported stronger revenue",
            ),
            sentiment=(
                NewsSentiment.POSITIVE
            ),
        ),
        analysed_at=analysed_at,
        expires_at=datetime(
            2026,
            7,
            17,
            12,
            30,
            tzinfo=timezone.utc,
        ),
        article_title=(
            "Apple reports stronger revenue"
        ),
        article_url=(
            "https://example.test/apple"
        ),
        published_at=datetime(
            2026,
            7,
            17,
            11,
            30,
            tzinfo=timezone.utc,
        ),
        relevance_score=0.92,
        source_sentiment_label=(
            "Somewhat-Bullish"
        ),
        source_sentiment_score=0.35,
        model_name="fake-model",
        prompt_version="v3",
    )


def test_saves_and_loads_latest_analysis(
    tmp_path,
) -> None:
    repository = SQLiteNewsAnalysisRepository(
        database_path=(
            tmp_path
            / "news.db"
        )
    )

    stored = create_stored_analysis()

    repository.save(
        symbol=" aapl ",
        stored_analysis=stored,
    )

    loaded = repository.get_latest(
        "AAPL"
    )

    assert loaded == stored


def test_returns_none_when_symbol_has_no_analysis(
    tmp_path,
) -> None:
    repository = SQLiteNewsAnalysisRepository(
        database_path=(
            tmp_path
            / "news.db"
        )
    )

    assert (
        repository.get_latest("MSFT")
        is None
    )

def test_returns_most_recent_saved_analysis(
    tmp_path,
) -> None:
    repository = SQLiteNewsAnalysisRepository(
        database_path=(
            tmp_path
            / "news.db"
        )
    )

    first = create_stored_analysis()

    second_analysis = NewsAnalysis(
        impact_term=NewsImpactTerm.SHORTTERM,
        impact_scope=NewsImpactScope.STOCK,
        scope_items=("AAPL",),
        highlights=(
            "Apple received negative news",
        ),
        sentiment=NewsSentiment.NEGATIVE,
    )

    second = replace(
        first,
        analysis=second_analysis,
        analysed_at=(
            first.analysed_at
            + timedelta(minutes=10)
        ),
        expires_at=(
            first.expires_at
            + timedelta(minutes=10)
        ),
        article_title=(
            "Apple receives negative news"
        ),
    )

    repository.save(
        symbol="AAPL",
        stored_analysis=first,
    )

    repository.save(
        symbol="AAPL",
        stored_analysis=second,
    )

    assert (
        repository.get_latest("AAPL")
        == second
    )