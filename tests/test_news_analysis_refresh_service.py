import pytest
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
from app.news_analysis_provider import (
    InMemoryNewsAnalysisProvider,
)
from app.news_article_source import (
    InMemoryNewsArticleSource,
)
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.expiring_news_analysis_provider import (
    ExpiringNewsAnalysisProvider,
)
from app.news_article import (
    NewsArticle,
)


class FakeAnalyser:
    def __init__(
        self,
        analysis: NewsAnalysis,
    ) -> None:
        self.analysis = analysis
        self.article_texts: list[str] = []

    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        self.article_texts.append(
            article_text
        )

        return self.analysis

class FailingArticleSource:
    def get_latest_article(
        self,
        symbol: str,
    ) -> str | None:
        raise RuntimeError(
            "News source unavailable."
        )

def test_analyses_validates_and_stores_article() -> None:
    analysis = NewsAnalysis(
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
    )

    analyser = FakeAnalyser(
        analysis=analysis
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={}
    )

    service = NewsAnalysisRefreshService(
        analyser=analyser,
        validator=NewsAnalysisValidator(),
        provider=provider,
    )

    result = service.refresh(
        symbol=" aapl ",
        article_text=(
            "Apple reported stronger revenue."
        ),
    )

    assert result is analysis
    assert analyser.article_texts == [
        "Apple reported stronger revenue."
    ]
    assert (
        provider.get_analysis("AAPL")
        is analysis
    )

class StructuredArticleSource:
    def __init__(
        self,
        article: NewsArticle,
    ) -> None:
        self.article = article
        self.symbols: list[str] = []

    def get_latest_news_article(
        self,
        symbol: str,
    ) -> NewsArticle | None:
        self.symbols.append(
            symbol.upper().strip()
        )

        return self.article
   
def test_rejects_and_does_not_store_invalid_analysis() -> None:
    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("MSFT",),
        highlights=(
            "Microsoft reported stronger revenue",
        ),
        sentiment=(
            NewsSentiment.POSITIVE
        ),
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={}
    )

    service = NewsAnalysisRefreshService(
        analyser=FakeAnalyser(
            analysis=analysis
        ),
        validator=NewsAnalysisValidator(),
        provider=provider,
    )

    with pytest.raises(
        ValueError,
        match="failed validation",
    ):
        service.refresh(
            symbol="AAPL",
            article_text=(
                "Apple reported stronger revenue."
            ),
        )

    assert (
        provider.get_analysis("AAPL")
        is None
    )
   
def test_invalid_refresh_preserves_existing_analysis() -> None:
    existing_analysis = NewsAnalysis(
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
    )

    invalid_analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("MSFT",),
        highlights=(
            "Microsoft reported stronger revenue",
        ),
        sentiment=(
            NewsSentiment.POSITIVE
        ),
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={
            "AAPL": existing_analysis,
        }
    )

    service = NewsAnalysisRefreshService(
        analyser=FakeAnalyser(
            analysis=invalid_analysis
        ),
        validator=NewsAnalysisValidator(),
        provider=provider,
    )

    with pytest.raises(
        ValueError,
        match="failed validation",
    ):
        service.refresh(
            symbol="AAPL",
            article_text=(
                "Apple reported stronger revenue."
            ),
        )

    assert (
        provider.get_analysis("AAPL")
        is existing_analysis
    )
 
def test_missing_article_preserves_existing_analysis() -> None:
    existing_analysis = NewsAnalysis(
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
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={
            "AAPL": existing_analysis,
        }
    )

    service = NewsAnalysisRefreshService(
        analyser=FakeAnalyser(
            analysis=existing_analysis
        ),
        validator=NewsAnalysisValidator(),
        provider=provider,
        article_source=InMemoryNewsArticleSource(
            articles={}
        ),
    )

    with pytest.raises(
        ValueError,
        match="No news article was found for AAPL",
    ):
        service.refresh_symbol(
            symbol=" aapl ",
        )

    assert (
        provider.get_analysis("AAPL")
        is existing_analysis
    )

def test_article_source_failure_preserves_existing_analysis() -> None:
    existing_analysis = NewsAnalysis(
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
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={
            "AAPL": existing_analysis,
        }
    )

    service = NewsAnalysisRefreshService(
        analyser=FakeAnalyser(
            analysis=existing_analysis
        ),
        validator=NewsAnalysisValidator(),
        provider=provider,
        article_source=FailingArticleSource(),
    )

    with pytest.raises(
        RuntimeError,
        match="News source unavailable",
    ):
        service.refresh_symbol(
            symbol="AAPL",
        )

    assert (
        provider.get_analysis("AAPL")
        is existing_analysis
    )

class SelectiveArticleSource:
    def __init__(
        self,
        articles: dict[str, str],
    ) -> None:
        self._articles = articles

    def get_latest_article(
        self,
        symbol: str,
    ) -> str | None:
        return self._articles.get(
            symbol.upper().strip()
        )

def test_refreshes_from_article_source() -> None:
    analysis = NewsAnalysis(
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
    )

    analyser = FakeAnalyser(
        analysis=analysis
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={}
    )

    article_source = InMemoryNewsArticleSource(
        articles={
            "AAPL": (
                "Apple reported stronger revenue."
            ),
        }
    )

    service = NewsAnalysisRefreshService(
        analyser=analyser,
        validator=NewsAnalysisValidator(),
        provider=provider,
        article_source=article_source,
    )

    result = service.refresh_symbol(
        symbol=" aapl ",
    )

    assert result is analysis
    assert analyser.article_texts == [
        "Apple reported stronger revenue."
    ]
    assert (
        provider.get_analysis("AAPL")
        is analysis
    )
    
def test_refreshes_available_symbols_and_reports_missing_ones() -> None:
    analysis = NewsAnalysis(
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
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={}
    )

    service = NewsAnalysisRefreshService(
        analyser=FakeAnalyser(
            analysis=analysis
        ),
        validator=NewsAnalysisValidator(),
        provider=provider,
        article_source=SelectiveArticleSource(
            articles={
                "AAPL": (
                    "Apple reported stronger revenue."
                ),
            }
        ),
    )

    results = service.refresh_symbols(
        symbols=[
            " aapl ",
            "MSFT",
        ]
    )

    assert results["AAPL"] is analysis
    assert results["MSFT"] is None
    assert (
        provider.get_analysis("AAPL")
        is analysis
    )
    assert (
        provider.get_analysis("MSFT")
        is None
    )
    
def test_batch_refresh_logs_symbol_failure(
    caplog,
) -> None:
    analysis = NewsAnalysis(
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
    )

    service = NewsAnalysisRefreshService(
        analyser=FakeAnalyser(
            analysis=analysis
        ),
        validator=NewsAnalysisValidator(),
        provider=InMemoryNewsAnalysisProvider(
            analyses={}
        ),
        article_source=SelectiveArticleSource(
            articles={}
        ),
    )

    with caplog.at_level(
        "WARNING",
        logger=(
            "app.news_analysis_refresh_service"
        ),
    ):
        results = service.refresh_symbols(
            symbols=["AAPL"]
        )

    assert results == {
        "AAPL": None,
    }
    assert (
        "news_analysis_refresh_failed "
        "symbol=AAPL"
        in caplog.text
    )
    
def test_verified_ticker_marker_normalises_company_name() -> None:
    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("APPLE",),
        highlights=(
            "Apple reported stronger revenue",
        ),
        sentiment=(
            NewsSentiment.POSITIVE
        ),
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={}
    )

    service = NewsAnalysisRefreshService(
        analyser=FakeAnalyser(
            analysis=analysis
        ),
        validator=NewsAnalysisValidator(),
        provider=provider,
    )

    result = service.refresh(
        symbol="AAPL",
        article_text=(
            "Ticker: AAPL\n\n"
            "Apple reported stronger revenue."
        ),
    )

    assert result.scope_items == (
        "AAPL",
    )
    assert (
        provider.get_analysis("AAPL")
        is result
    )
    
def test_verified_ticker_marker_normalises_global_scope_to_stock() -> None:
    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.GLOBAL
        ),
        scope_items=("AAPL",),
        highlights=(
            "Apple's lawsuit may face complications",
        ),
        sentiment=(
            NewsSentiment.POSITIVE
        ),
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={}
    )

    service = NewsAnalysisRefreshService(
        analyser=FakeAnalyser(
            analysis=analysis
        ),
        validator=NewsAnalysisValidator(),
        provider=provider,
    )

    result = service.refresh(
        symbol="AAPL",
        article_text=(
            "Ticker: AAPL\n\n"
            "Apple's lawsuit may face complications."
        ),
    )

    assert (
        result.impact_scope
        is NewsImpactScope.STOCK
    )
    assert result.scope_items == (
        "AAPL",
    )
    
def test_verified_bearish_source_sentiment_normalises_to_negative() -> None:
    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("AAPL",),
        highlights=(
            "Apple's lawsuit may face complications",
        ),
        sentiment=(
            NewsSentiment.POSITIVE
        ),
    )

    provider = InMemoryNewsAnalysisProvider(
        analyses={}
    )

    service = NewsAnalysisRefreshService(
        analyser=FakeAnalyser(
            analysis=analysis
        ),
        validator=NewsAnalysisValidator(),
        provider=provider,
    )

    result = service.refresh(
        symbol="AAPL",
        article_text=(
            "Ticker: AAPL\n\n"
            "Source sentiment: Somewhat-Bearish "
            "(-0.35)\n\n"
            "Apple's lawsuit may face complications."
        ),
    )

    assert (
        result.sentiment
        is NewsSentiment.NEGATIVE
    )

def test_refreshes_structured_article_into_stored_analysis() -> None:
    now = datetime(
        2026,
        7,
        17,
        12,
        0,
        tzinfo=timezone.utc,
    )

    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("AAPL",),
        highlights=(
            "Apple lawsuit may face complications",
        ),
        sentiment=(
            NewsSentiment.NEGATIVE
        ),
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

    provider = ExpiringNewsAnalysisProvider(
        time_to_live_seconds=1_800,
        now_provider=lambda: now,
    )

    service = NewsAnalysisRefreshService(
        analyser=FakeAnalyser(
            analysis=analysis
        ),
        validator=NewsAnalysisValidator(),
        provider=provider,
        now_provider=lambda: now,
        analysis_ttl_seconds=1_800,
    )

    result = service.refresh_article(
        article=article,
        model_name="fake-model",
        prompt_version="v3",
    )

    assert result == analysis

    stored = provider.get_stored_analysis(
        "AAPL"
    )

    assert stored is not None
    assert stored.analysis == analysis
    assert stored.analysed_at == now
    assert stored.expires_at == (
        now + timedelta(
            seconds=1_800
        )
    )
    assert stored.article_title == (
        "Apple lawsuit faces complication"
    )
    assert stored.article_url == (
        "https://example.test/apple"
    )
    assert stored.published_at == (
        article.published_at
    )
    assert stored.relevance_score == 0.92
    assert stored.source_sentiment_label == (
        "Somewhat-Bearish"
    )
    assert stored.source_sentiment_score == -0.35
    assert stored.model_name == "fake-model"
    assert stored.prompt_version == "v3"
    
def test_refresh_symbol_uses_structured_article_when_available() -> None:
    now = datetime(
        2026,
        7,
        17,
        12,
        0,
        tzinfo=timezone.utc,
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

    provider = ExpiringNewsAnalysisProvider(
        time_to_live_seconds=1_800,
        now_provider=lambda: now,
    )

    article_source = StructuredArticleSource(
        article=article
    )

    service = NewsAnalysisRefreshService(
        analyser=FakeAnalyser(
            analysis=analysis
        ),
        validator=NewsAnalysisValidator(),
        provider=provider,
        article_source=article_source,
        now_provider=lambda: now,
        analysis_ttl_seconds=1_800,
    )

    result = service.refresh_symbol(
        symbol=" aapl ",
        model_name="fake-model",
        prompt_version="v3",
    )

    assert result == analysis
    assert article_source.symbols == [
        "AAPL",
    ]

    stored = provider.get_stored_analysis(
        "AAPL"
    )

    assert stored is not None
    assert stored.article_title == (
        "Apple lawsuit faces complication"
    )
    assert stored.model_name == "fake-model"
    assert stored.prompt_version == "v3"