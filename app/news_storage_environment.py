import os
from pathlib import Path


DEFAULT_NEWS_STORAGE_BACKEND = "memory"
DEFAULT_NEWS_DATABASE_PATH = Path(
    "data/news.db"
)

SUPPORTED_NEWS_STORAGE_BACKENDS = {
    "memory",
    "sqlite",
}


def load_news_storage_backend() -> str:
    backend = os.getenv(
        "NEWS_STORAGE_BACKEND",
        DEFAULT_NEWS_STORAGE_BACKEND,
    ).strip().lower()

    if backend not in (
        SUPPORTED_NEWS_STORAGE_BACKENDS
    ):
        raise ValueError(
            "Unsupported news storage backend: "
            f"{backend}"
        )

    return backend


def load_news_database_path() -> Path:
    raw_path = os.getenv(
        "NEWS_DATABASE_PATH",
        str(DEFAULT_NEWS_DATABASE_PATH),
    ).strip()

    if not raw_path:
        raise ValueError(
            "NEWS_DATABASE_PATH must not be empty."
        )

    return Path(
        raw_path
    )