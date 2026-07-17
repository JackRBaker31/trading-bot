from app.expiring_news_analysis_provider import (
    ExpiringNewsAnalysisProvider,
)
from app.news_storage_factory import (
    create_news_analysis_provider,
)
from app.sqlite_news_analysis_provider import (
    SQLiteNewsAnalysisProvider,
)


def test_creates_memory_provider(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "NEWS_STORAGE_BACKEND",
        "memory",
    )
    monkeypatch.setenv(
        "NEWS_ANALYSIS_TTL_SECONDS",
        "1800",
    )

    provider = create_news_analysis_provider()

    assert isinstance(
        provider,
        ExpiringNewsAnalysisProvider,
    )


def test_creates_sqlite_provider(
    monkeypatch,
    tmp_path,
) -> None:
    database_path = (
        tmp_path
        / "news.db"
    )

    monkeypatch.setenv(
        "NEWS_STORAGE_BACKEND",
        "sqlite",
    )
    monkeypatch.setenv(
        "NEWS_DATABASE_PATH",
        str(database_path),
    )

    provider = create_news_analysis_provider()

    assert isinstance(
        provider,
        SQLiteNewsAnalysisProvider,
    )
    assert database_path.exists()