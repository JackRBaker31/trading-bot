from app.expiring_news_analysis_provider import (
    ExpiringNewsAnalysisProvider,
)
from app.news_runtime_environment import (
    load_news_analysis_ttl_seconds,
)
from app.news_storage_environment import (
    load_news_database_path,
    load_news_storage_backend,
)
from app.sqlite_news_analysis_provider import (
    SQLiteNewsAnalysisProvider,
)
from app.sqlite_news_analysis_repository import (
    SQLiteNewsAnalysisRepository,
)


def create_news_analysis_provider():
    storage_backend = (
        load_news_storage_backend()
    )

    if storage_backend == "memory":
        ttl_seconds = (
            load_news_analysis_ttl_seconds()
        )

        return ExpiringNewsAnalysisProvider(
            time_to_live_seconds=(
                ttl_seconds
            ),
        )

    if storage_backend == "sqlite":
        repository = (
            SQLiteNewsAnalysisRepository(
                database_path=(
                    load_news_database_path()
                )
            )
        )

        return SQLiteNewsAnalysisProvider(
            repository=repository,
        )

    raise ValueError(
        "Unsupported news storage backend: "
        f"{storage_backend}"
    )