import os

from app.alpha_vantage_news_runtime import (
    create_alpha_vantage_news_article_source,
)
from app.news_storage_factory import (
    create_news_analysis_provider,
)
from app.news_analysis_refresh_service import (
    NewsAnalysisRefreshService,
)
from app.news_analysis_service import (
    NewsAnalysisService,
)
from app.news_analysis_validator import (
    NewsAnalysisValidator,
)
from app.news_model_client import (
    NewsModelClient,
)
from app.news_runtime_environment import (
    load_news_analysis_ttl_seconds,
)
from app.news_runtime_pipeline import (
    NewsRuntimePipeline,
)
from app.news_source_runtime import (
    create_news_article_source_from_environment,
)
from app.ollama_news_transport import (
    OllamaNewsTransport,
)


DEFAULT_MODEL_NAME = (
    "hf.co/VaibTFU/"
    "qwen-0.5b-stocks-news-v2-GGUF:Q4_K_M"
)


def create_news_runtime_pipeline(
    *,
    source_name: str = "http",
) -> NewsRuntimePipeline:
    model_name = os.getenv(
        "OLLAMA_NEWS_MODEL",
        DEFAULT_MODEL_NAME,
    ).strip()

    analysis_ttl_seconds = (
        load_news_analysis_ttl_seconds()
    )

    transport = OllamaNewsTransport(
        model_name=model_name,
    )

    model_client = NewsModelClient(
        transport=transport,
    )

    analyser = NewsAnalysisService(
        model_client=model_client,
    )

    provider = create_news_analysis_provider()

    normalised_source_name = (
        source_name.lower().strip()
    )

    if normalised_source_name == "alpha_vantage":
        article_source = (
            create_alpha_vantage_news_article_source()
        )
    elif normalised_source_name == "http":
        article_source = (
            create_news_article_source_from_environment()
        )
    else:
        raise ValueError(
            "Unsupported news source: "
            f"{source_name}"
        )

    refresh_service = NewsAnalysisRefreshService(
        analyser=analyser,
        validator=NewsAnalysisValidator(),
        provider=provider,
        article_source=article_source,
        analysis_ttl_seconds=(
            analysis_ttl_seconds
        ),
    )

    return NewsRuntimePipeline(
        provider=provider,
        refresh_service=refresh_service,
    )