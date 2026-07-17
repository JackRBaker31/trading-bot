from app.news_analysis_provider import (
    InMemoryNewsAnalysisProvider,
)
from app.news_runtime_pipeline import (
    NewsRuntimePipeline,
)


def test_runtime_pipeline_exposes_provider() -> None:
    provider = InMemoryNewsAnalysisProvider(
        analyses={}
    )

    pipeline = NewsRuntimePipeline(
        provider=provider,
        refresh_service=object(),
    )

    assert pipeline.provider is provider