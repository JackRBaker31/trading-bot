import pytest

from app.news_storage_environment import (
    load_news_database_path,
    load_news_storage_backend,
)


def test_loads_memory_storage_backend_by_default(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "NEWS_STORAGE_BACKEND",
        raising=False,
    )

    assert (
        load_news_storage_backend()
        == "memory"
    )


def test_loads_sqlite_storage_backend(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "NEWS_STORAGE_BACKEND",
        " sqlite ",
    )

    assert (
        load_news_storage_backend()
        == "sqlite"
    )


def test_rejects_unknown_storage_backend(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "NEWS_STORAGE_BACKEND",
        "postgres",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported news storage backend",
    ):
        load_news_storage_backend()


def test_loads_default_news_database_path(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "NEWS_DATABASE_PATH",
        raising=False,
    )

    assert (
        str(load_news_database_path())
        == "data\\news.db"
        or str(load_news_database_path())
        == "data/news.db"
    )


def test_loads_configured_news_database_path(
    monkeypatch,
    tmp_path,
) -> None:
    database_path = (
        tmp_path
        / "custom-news.db"
    )

    monkeypatch.setenv(
        "NEWS_DATABASE_PATH",
        str(database_path),
    )

    assert (
        load_news_database_path()
        == database_path
    )