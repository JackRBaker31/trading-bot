import json
from pathlib import Path

from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.news_analysis_validator import (
    NewsAnalysisValidator,
)
from research.benchmark_dataset import (
    BenchmarkDataset,
)
from research.news_benchmark import (
    run_news_benchmark,
    save_report,
)


class FakeAnalyser:
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        return NewsAnalysis(
            impact_term=(
                NewsImpactTerm.SHORTTERM
            ),
            impact_scope=(
                NewsImpactScope.STOCK
            ),
            scope_items=("AAPL",),
            highlights=(
                "Apple reported stronger revenue",
                "Apple raised its guidance",
            ),
            sentiment=(
                NewsSentiment.POSITIVE
            ),
        )

class GoogleNameAnalyser:
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        return NewsAnalysis(
            impact_term=(
                NewsImpactTerm.LONGTERM
            ),
            impact_scope=(
                NewsImpactScope.STOCK
            ),
            scope_items=("GOOGLE",),
            highlights=(
                "Google announced a major investment",
            ),
            sentiment=(
                NewsSentiment.POSITIVE
            ),
        )

class CountingAnalyser:
    def __init__(self) -> None:
        self.call_count = 0

    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        self.call_count += 1

        return NewsAnalysis(
            impact_term=(
                NewsImpactTerm.SHORTTERM
            ),
            impact_scope=(
                NewsImpactScope.STOCK
            ),
            scope_items=("AAPL",),
            highlights=(
                "Apple reported stronger revenue",
                "Apple raised its guidance",
            ),
            sentiment=(
                NewsSentiment.POSITIVE
            ),
        )

class GlobalScopeWithTickerAnalyser:
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        return NewsAnalysis(
            impact_term=(
                NewsImpactTerm.SHORTTERM
            ),
            impact_scope=(
                NewsImpactScope.GLOBAL
            ),
            scope_items=("AAPL",),
            highlights=(
                "Apple reported stronger revenue",
            ),
            sentiment=(
                NewsSentiment.POSITIVE
            ),
        )

class EmptyScopeAnalyser:
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        return NewsAnalysis(
            impact_term=(
                NewsImpactTerm.SHORTTERM
            ),
            impact_scope=(
                NewsImpactScope.GLOBAL
            ),
            scope_items=(),
            highlights=(
                "Tesla reported first-quarter deliveries",
            ),
            sentiment=(
                NewsSentiment.NEUTRAL
            ),
        )

class UnknownScopeItemAnalyser:
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        return NewsAnalysis(
            impact_term=(
                NewsImpactTerm.SHORTTERM
            ),
            impact_scope=(
                NewsImpactScope.STOCK
            ),
            scope_items=(
                "FEDERAL OPEN MARKET COMMITTEE",
            ),
            highlights=(
                "Interest rates were left unchanged",
            ),
            sentiment=(
                NewsSentiment.NEUTRAL
            ),
        )

class UnsupportedNumberAnalyser:
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        return NewsAnalysis(
            impact_term=(
                NewsImpactTerm.SHORTTERM
            ),
            impact_scope=(
                NewsImpactScope.STOCK
            ),
            scope_items=("MSFT",),
            highlights=(
                "Microsoft reported revenue growth",
                "Revenue increased by 31.9 percent",
            ),
            sentiment=(
                NewsSentiment.POSITIVE
            ),
        )

class ShortTermAcquisitionAnalyser:
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        return NewsAnalysis(
            impact_term=(
                NewsImpactTerm.SHORTTERM
            ),
            impact_scope=(
                NewsImpactScope.STOCK
            ),
            scope_items=("GOOGL",),
            highlights=(
                "Google agreed to acquire Wiz",
            ),
            sentiment=(
                NewsSentiment.POSITIVE
            ),
        )

class ShortTermPortfolioExpansionAnalyser:
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        return NewsAnalysis(
            impact_term=(
                NewsImpactTerm.SHORTTERM
            ),
            impact_scope=(
                NewsImpactScope.STOCK
            ),
            scope_items=("AMD",),
            highlights=(
                "AMD expanded its Ryzen AI "
                "processor portfolio",
            ),
            sentiment=(
                NewsSentiment.POSITIVE
            ),
        )

class PositiveMultiSignalEnforcementAnalyser:
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        return NewsAnalysis(
            impact_term=(
                NewsImpactTerm.SHORTTERM
            ),
            impact_scope=(
                NewsImpactScope.STOCK
            ),
            scope_items=("TIO",),
            highlights=(
                "The SEC imposed civil penalties",
            ),
            sentiment=(
                NewsSentiment.POSITIVE
            ),
        )

class PositiveCentralBankDecisionAnalyser:
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        return NewsAnalysis(
            impact_term=(
                NewsImpactTerm.SHORTTERM
            ),
            impact_scope=(
                NewsImpactScope.GLOBAL
            ),
            scope_items=(),
            highlights=(
                "The Federal Reserve lowered "
                "the target range",
            ),
            sentiment=(
                NewsSentiment.POSITIVE
            ),
        )

def write_json(
    file_path: Path,
    data: dict[str, object],
) -> None:
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        json.dumps(data),
        encoding="utf-8",
    )


def create_dataset(
    tmp_path: Path,
) -> BenchmarkDataset:
    articles = tmp_path / "articles"
    labels = tmp_path / "labels"

    write_json(
        articles / "BENCH-0001.json",
        {
            "benchmark_id": "BENCH-0001",
            "headline": (
                "Apple raises guidance"
            ),
            "source": "Manual benchmark",
            "category": "guidance",
            "sector": "Technology",
            "company": "Apple",
            "ticker": "AAPL",
            "difficulty": "easy",
            "published_at": (
                "2026-07-14T00:00:00Z"
            ),
            "article_text": (
                "Apple reported stronger revenue "
                "and raised its guidance."
            ),
        },
    )

    write_json(
        labels / "BENCH-0001.json",
        {
            "benchmark_id": "BENCH-0001",
            "impact_term": "SHORTTERM",
            "impact_scope": "STOCK",
            "scope_items": [
                "AAPL",
            ],
            "highlights": [
                "Apple reported stronger revenue",
                "Apple raised its guidance",
            ],
            "sentiment": "POSITIVE",
        },
    )

    dataset = BenchmarkDataset(
        articles_directory=articles,
        labels_directory=labels,
    )

    dataset.load()

    return dataset


def test_runs_managed_dataset_benchmark(
    tmp_path: Path,
) -> None:
    report = run_news_benchmark(
        analyser=FakeAnalyser(),
        validator=NewsAnalysisValidator(),
        dataset=create_dataset(tmp_path),
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    assert report.total_articles == 1
    assert report.parse_success_count == 1
    assert (
        report.validation_approved_count
        == 1
    )
    assert report.parse_success_rate == 1.0
    assert (
        report.validation_approval_rate
        == 1.0
    )
    assert report.sentiment_accuracy == 1.0
    assert report.impact_term_accuracy == 1.0
    assert report.impact_scope_accuracy == 1.0
    assert report.average_scope_precision == 1.0
    assert report.average_scope_recall == 1.0
    assert (
        report.average_highlight_similarity
        == 1.0
    )
    assert report.average_overall_score == 1.0

def test_analyser_is_called_once_per_article(
    tmp_path: Path,
) -> None:
    analyser = CountingAnalyser()

    run_news_benchmark(
        analyser=analyser,
        validator=NewsAnalysisValidator(),
        dataset=create_dataset(tmp_path),
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    assert analyser.call_count == 1

def test_non_empty_scope_items_normalise_scope_to_stock(
    tmp_path: Path,
) -> None:
    report = run_news_benchmark(
        analyser=GlobalScopeWithTickerAnalyser(),
        validator=NewsAnalysisValidator(),
        dataset=create_dataset(tmp_path),
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    item = report.items[0]

    assert item.analysis is not None
    assert (
        item.analysis.impact_scope
        is NewsImpactScope.STOCK
    )
    assert item.analysis.scope_items == (
        "AAPL",
    )

def test_explicit_article_ticker_restores_empty_scope(
    tmp_path: Path,
) -> None:
    dataset = create_dataset(tmp_path)

    article_path = (
        tmp_path
        / "articles"
        / "BENCH-0001.json"
    )

    article_data = json.loads(
        article_path.read_text(
            encoding="utf-8"
        )
    )
    article_data.update(
        {
            "company": "Tesla",
            "ticker": "TSLA",
            "article_text": (
                "Tesla (NASDAQ: TSLA) reported "
                "first-quarter deliveries."
            ),
        }
    )
    write_json(article_path, article_data)

    dataset.load()

    report = run_news_benchmark(
        analyser=EmptyScopeAnalyser(),
        validator=NewsAnalysisValidator(),
        dataset=dataset,
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    item = report.items[0]

    assert item.analysis is not None
    assert (
        item.analysis.impact_scope
        is NewsImpactScope.STOCK
    )
    assert item.analysis.scope_items == (
        "TSLA",
    )

def test_empty_canonical_ticker_does_not_restore_scope(
    tmp_path: Path,
) -> None:
    dataset = create_dataset(tmp_path)

    article_path = (
        tmp_path
        / "articles"
        / "BENCH-0001.json"
    )

    article_data = json.loads(
        article_path.read_text(
            encoding="utf-8"
        )
    )
    article_data.update(
        {
            "company": "",
            "ticker": "",
            "article_text": (
                "The Federal Open Market Committee "
                "left interest rates unchanged."
            ),
        }
    )
    write_json(article_path, article_data)

    dataset.load()

    report = run_news_benchmark(
        analyser=EmptyScopeAnalyser(),
        validator=NewsAnalysisValidator(),
        dataset=dataset,
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    item = report.items[0]

    assert item.analysis is not None
    assert (
        item.analysis.impact_scope
        is NewsImpactScope.GLOBAL
    )
    assert item.analysis.scope_items == ()

def test_unknown_scope_item_is_removed(
    tmp_path: Path,
) -> None:
    dataset = create_dataset(tmp_path)

    article_path = (
        tmp_path
        / "articles"
        / "BENCH-0001.json"
    )

    article_data = json.loads(
        article_path.read_text(
            encoding="utf-8"
        )
    )
    article_data.update(
        {
            "company": "",
            "ticker": "",
            "article_text": (
                "The Federal Open Market Committee "
                "left interest rates unchanged."
            ),
        }
    )
    write_json(article_path, article_data)

    dataset.load()

    report = run_news_benchmark(
        analyser=UnknownScopeItemAnalyser(),
        validator=NewsAnalysisValidator(),
        dataset=dataset,
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    item = report.items[0]

    assert item.analysis is not None
    assert item.analysis.scope_items == ()
    assert (
        item.analysis.impact_scope
        is NewsImpactScope.GLOBAL
    )
    assert item.validation_approved

def test_highlight_with_unsupported_number_is_removed(
    tmp_path: Path,
) -> None:
    dataset = create_dataset(tmp_path)

    article_path = (
        tmp_path
        / "articles"
        / "BENCH-0001.json"
    )
    label_path = (
        tmp_path
        / "labels"
        / "BENCH-0001.json"
    )

    article_data = json.loads(
        article_path.read_text(
            encoding="utf-8"
        )
    )
    article_data.update(
        {
            "company": "Microsoft",
            "ticker": "MSFT",
            "article_text": (
                "Microsoft reported revenue growth "
                "during the quarter."
            ),
        }
    )
    write_json(article_path, article_data)

    label_data = json.loads(
        label_path.read_text(
            encoding="utf-8"
        )
    )
    label_data.update(
        {
            "scope_items": ["MSFT"],
        }
    )
    write_json(label_path, label_data)

    dataset.load()

    report = run_news_benchmark(
        analyser=UnsupportedNumberAnalyser(),
        validator=NewsAnalysisValidator(),
        dataset=dataset,
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    item = report.items[0]

    assert item.analysis is not None
    assert item.analysis.highlights == (
        "Microsoft reported revenue growth",
    )
    assert item.validation_approved

def test_acquisition_normalises_to_long_term(
    tmp_path: Path,
) -> None:
    dataset = create_dataset(tmp_path)

    article_path = (
        tmp_path
        / "articles"
        / "BENCH-0001.json"
    )
    label_path = (
        tmp_path
        / "labels"
        / "BENCH-0001.json"
    )

    article_data = json.loads(
        article_path.read_text(
            encoding="utf-8"
        )
    )
    article_data.update(
        {
            "company": "Alphabet",
            "ticker": "GOOGL",
            "article_text": (
                "Google announced an agreement "
                "to acquire Wiz for $32 billion. "
                "Wiz would join Google Cloud."
            ),
        }
    )
    write_json(article_path, article_data)

    label_data = json.loads(
        label_path.read_text(
            encoding="utf-8"
        )
    )
    label_data.update(
        {
            "impact_term": "LONGTERM",
            "scope_items": ["GOOGL"],
        }
    )
    write_json(label_path, label_data)

    dataset.load()

    report = run_news_benchmark(
        analyser=ShortTermAcquisitionAnalyser(),
        validator=NewsAnalysisValidator(),
        dataset=dataset,
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    item = report.items[0]

    assert item.analysis is not None
    assert (
        item.analysis.impact_term
        is NewsImpactTerm.LONGTERM
    )

def test_product_portfolio_expansion_normalises_to_long_term(
    tmp_path: Path,
) -> None:
    dataset = create_dataset(tmp_path)

    article_path = (
        tmp_path
        / "articles"
        / "BENCH-0001.json"
    )
    label_path = (
        tmp_path
        / "labels"
        / "BENCH-0001.json"
    )

    article_data = json.loads(
        article_path.read_text(
            encoding="utf-8"
        )
    )
    article_data.update(
        {
            "company": (
                "Advanced Micro Devices"
            ),
            "ticker": "AMD",
            "article_text": (
                "AMD announced an expanded "
                "Ryzen AI processor portfolio."
            ),
        }
    )
    write_json(article_path, article_data)

    label_data = json.loads(
        label_path.read_text(
            encoding="utf-8"
        )
    )
    label_data.update(
        {
            "impact_term": "LONGTERM",
            "scope_items": ["AMD"],
        }
    )
    write_json(label_path, label_data)

    dataset.load()

    report = run_news_benchmark(
        analyser=(
            ShortTermPortfolioExpansionAnalyser()
        ),
        validator=NewsAnalysisValidator(),
        dataset=dataset,
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    item = report.items[0]

    assert item.analysis is not None
    assert (
        item.analysis.impact_term
        is NewsImpactTerm.LONGTERM
    )

def test_multiple_enforcement_signals_normalise_to_negative(
    tmp_path: Path,
) -> None:
    dataset = create_dataset(tmp_path)

    article_path = (
        tmp_path
        / "articles"
        / "BENCH-0001.json"
    )
    label_path = (
        tmp_path
        / "labels"
        / "BENCH-0001.json"
    )

    article_data = json.loads(
        article_path.read_text(
            encoding="utf-8"
        )
    )
    article_data.update(
        {
            "company": "Tingo Group",
            "ticker": "TIO",
            "article_text": (
                "The SEC announced an enforcement "
                "action involving fraud. The settlement "
                "included permanent injunctions, civil "
                "penalties and a six-year suspension."
            ),
        }
    )
    write_json(article_path, article_data)

    label_data = json.loads(
        label_path.read_text(
            encoding="utf-8"
        )
    )
    label_data.update(
        {
            "sentiment": "NEGATIVE",
            "scope_items": ["TIO"],
        }
    )
    write_json(label_path, label_data)

    dataset.load()

    report = run_news_benchmark(
        analyser=(
            PositiveMultiSignalEnforcementAnalyser()
        ),
        validator=NewsAnalysisValidator(),
        dataset=dataset,
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    item = report.items[0]

    assert item.analysis is not None
    assert (
        item.analysis.sentiment
        is NewsSentiment.NEGATIVE
    )

def test_central_bank_rate_decision_normalises_to_neutral(
    tmp_path: Path,
) -> None:
    dataset = create_dataset(tmp_path)

    article_path = (
        tmp_path
        / "articles"
        / "BENCH-0001.json"
    )
    label_path = (
        tmp_path
        / "labels"
        / "BENCH-0001.json"
    )

    article_data = json.loads(
        article_path.read_text(
            encoding="utf-8"
        )
    )
    article_data.update(
        {
            "company": "",
            "ticker": "",
            "article_text": (
                "The Federal Open Market Committee "
                "lowered the target range for the "
                "federal funds rate by 0.25 percentage "
                "point. Future adjustments would depend "
                "on incoming data and the balance of risks."
            ),
        }
    )
    write_json(article_path, article_data)

    label_data = json.loads(
        label_path.read_text(
            encoding="utf-8"
        )
    )
    label_data.update(
        {
            "impact_scope": "GLOBAL",
            "scope_items": [],
            "sentiment": "NEUTRAL",
        }
    )
    write_json(label_path, label_data)

    dataset.load()

    report = run_news_benchmark(
        analyser=(
            PositiveCentralBankDecisionAnalyser()
        ),
        validator=NewsAnalysisValidator(),
        dataset=dataset,
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    item = report.items[0]

    assert item.analysis is not None
    assert (
        item.analysis.sentiment
        is NewsSentiment.NEUTRAL
    )

def test_normalises_google_company_name_to_googl(
    tmp_path: Path,
) -> None:
    dataset = create_dataset(tmp_path)

    article_path = (
        tmp_path
        / "articles"
        / "BENCH-0001.json"
    )
    label_path = (
        tmp_path
        / "labels"
        / "BENCH-0001.json"
    )

    article_data = json.loads(
        article_path.read_text(
            encoding="utf-8"
        )
    )
    article_data.update(
        {
            "headline": (
                "Google announces investment"
            ),
            "company": "Alphabet",
            "ticker": "GOOGL",
            "article_text": (
                "Google announced a major "
                "investment."
            ),
        }
    )
    write_json(article_path, article_data)

    label_data = json.loads(
        label_path.read_text(
            encoding="utf-8"
        )
    )
    label_data.update(
        {
            "impact_term": "LONGTERM",
            "scope_items": ["GOOGL"],
            "highlights": [
                "Google announced a major investment",
            ],
        }
    )
    write_json(label_path, label_data)

    dataset.load()

    report = run_news_benchmark(
        analyser=GoogleNameAnalyser(),
        validator=NewsAnalysisValidator(),
        dataset=dataset,
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    item = report.items[0]

    assert item.analysis is not None
    assert item.analysis.scope_items == (
        "GOOGL",
    )
    assert item.validation_approved

def test_report_contains_gold_label_metrics(
    tmp_path: Path,
) -> None:
    report = run_news_benchmark(
        analyser=FakeAnalyser(),
        validator=NewsAnalysisValidator(),
        dataset=create_dataset(tmp_path),
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    file_path = tmp_path / "report.json"

    save_report(
        report=report,
        file_path=file_path,
    )

    data = json.loads(
        file_path.read_text(
            encoding="utf-8"
        )
    )

    assert data["dataset_version"] == "v1"
    assert data["sentiment_accuracy"] == 1.0
    assert data["impact_term_accuracy"] == 1.0
    assert data["impact_scope_accuracy"] == 1.0
    assert (
        data["average_highlight_similarity"]
        == 1.0
    )
    assert data["average_overall_score"] == 1.0

    item = data["items"][0]

    assert item["benchmark_id"] == (
        "BENCH-0001"
    )

    assert item["evaluation"][
        "overall_score"
    ] == 1.0


def test_invalid_dataset_is_rejected(
    tmp_path: Path,
) -> None:
    dataset = BenchmarkDataset(
        articles_directory=(
            tmp_path / "articles"
        ),
        labels_directory=(
            tmp_path / "labels"
        ),
    )

    dataset.load()

    report = run_news_benchmark(
        analyser=FakeAnalyser(),
        validator=NewsAnalysisValidator(),
        dataset=dataset,
        model_name="fake-model",
        prompt_version="v3",
        dataset_version="v1",
    )

    assert report.total_articles == 0
    assert report.average_overall_score == 0.0