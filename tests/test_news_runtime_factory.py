from app.news_runtime_factory import (
    create_news_runtime_pipeline,
)
from app.sqlite_news_analysis_provider import (
    SQLiteNewsAnalysisProvider,
)

def test_creates_runtime_pipeline(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "NEWS_SOURCE_URL_TEMPLATE",
        "https://example.test/news/{symbol}",
    )
    monkeypatch.setenv(
        "NEWS_SOURCE_TIMEOUT_SECONDS",
        "12.0",
    )
    monkeypatch.setenv(
        "NEWS_SOURCE_USER_AGENT",
        "trading-bot-runtime/1.0",
    )
    monkeypatch.setenv(
        "OLLAMA_NEWS_MODEL",
        "fake-news-model",
    )

    pipeline = create_news_runtime_pipeline()

    assert pipeline.provider is not None
    assert pipeline.refresh_service is not None
    
def test_creates_alpha_vantage_runtime_pipeline(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "ALPHA_VANTAGE_API_KEY",
        "test-key",
    )
    monkeypatch.setenv(
        "OLLAMA_NEWS_MODEL",
        "fake-news-model",
    )

    pipeline = (
        create_news_runtime_pipeline(
            source_name="alpha_vantage",
        )
    )

    assert pipeline.provider is not None
    assert pipeline.refresh_service is not None
    
def test_runtime_pipeline_uses_sqlite_storage(
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
    monkeypatch.setenv(
        "NEWS_SOURCE_URL_TEMPLATE",
        "https://example.test/news/{symbol}",
    )
    monkeypatch.setenv(
        "OLLAMA_NEWS_MODEL",
        "fake-news-model",
    )

    pipeline = create_news_runtime_pipeline()

    assert isinstance(
        pipeline.provider,
        SQLiteNewsAnalysisProvider,
    )
    assert database_path.exists()