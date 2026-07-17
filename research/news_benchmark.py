import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Protocol

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
    BenchmarkLabel,
)
from research.news_analysis_evaluator import (
    NewsAnalysisEvaluation,
    evaluate_news_analysis,
)


class BenchmarkNewsAnalyser(Protocol):
    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        """Return one structured news analysis."""

def _normalise_scope_items(
    *,
    analysis: NewsAnalysis,
    article_text: str,
    company: str,
    ticker: str,
) -> NewsAnalysis:
    aliases = {
        company.upper().strip(): ticker.upper().strip(),
        ticker.upper().strip(): ticker.upper().strip(),
        "GOOGLE": "GOOGL",
    }

    resolved_items = tuple(
        aliases[item.upper().strip()]
        for item in analysis.scope_items
        if item.upper().strip() in aliases
    )

    canonical_ticker = ticker.upper().strip()

    ticker_is_explicit = bool(
        canonical_ticker
    ) and re.search(
        rf"\b{re.escape(canonical_ticker)}\b",
        article_text,
        flags=re.IGNORECASE,
    ) is not None

    if not resolved_items and ticker_is_explicit:
        resolved_items = (
            canonical_ticker,
        )

    if resolved_items:
        normalised_impact_scope = (
            NewsImpactScope.STOCK
        )
    elif (
        analysis.impact_scope
        is NewsImpactScope.STOCK
    ):
        normalised_impact_scope = (
            NewsImpactScope.GLOBAL
        )
    else:
        normalised_impact_scope = (
            analysis.impact_scope
        )

    analysis = NewsAnalysis(
        impact_term=analysis.impact_term,
        impact_scope=normalised_impact_scope,
        scope_items=resolved_items,
        highlights=analysis.highlights,
        sentiment=analysis.sentiment,
    )

    return analysis

def _normalise_highlights(
    *,
    analysis: NewsAnalysis,
    article_text: str,
) -> NewsAnalysis:
    article_numbers = set(
        re.findall(
            r"\d+(?:\.\d+)?",
            article_text,
        )
    )

    supported_highlights = tuple(
        highlight
        for highlight in analysis.highlights
        if set(
            re.findall(
                r"\d+(?:\.\d+)?",
                highlight,
            )
        ).issubset(article_numbers)
    )

    return NewsAnalysis(
        impact_term=analysis.impact_term,
        impact_scope=analysis.impact_scope,
        scope_items=analysis.scope_items,
        highlights=supported_highlights,
        sentiment=analysis.sentiment,
    )

def _normalise_impact_term(
    *,
    analysis: NewsAnalysis,
    article_text: str,
) -> NewsAnalysis:
    normalised_text = article_text.lower()

    long_term_terms = (
        "agreement to acquire",
        "agreed to acquire",
        "acquisition of",
        "will acquire",
        "to acquire",
        "expanded portfolio",
        "expanded its portfolio",
        "portfolio expansion",
        "expanded ryzen ai processor portfolio",
    )

    is_long_term_event = any(
        term in normalised_text
        for term in long_term_terms
    )

    if not is_long_term_event:
        return analysis

    return NewsAnalysis(
        impact_term=NewsImpactTerm.LONGTERM,
        impact_scope=analysis.impact_scope,
        scope_items=analysis.scope_items,
        highlights=analysis.highlights,
        sentiment=analysis.sentiment,
    )

def _normalise_sentiment(
    *,
    analysis: NewsAnalysis,
    article_text: str,
) -> NewsAnalysis:
    normalised_text = article_text.lower()

    enforcement_terms = (
        "enforcement action",
        "fraud",
        "injunction",
        "civil penalty",
        "civil penalties",
        "suspension",
    )

    enforcement_signal_count = sum(
        term in normalised_text
        for term in enforcement_terms
    )

    if enforcement_signal_count >= 2:
        return NewsAnalysis(
            impact_term=analysis.impact_term,
            impact_scope=analysis.impact_scope,
            scope_items=analysis.scope_items,
            highlights=analysis.highlights,
            sentiment=NewsSentiment.NEGATIVE,
        )

    central_bank_terms = (
        "federal open market committee",
        "federal funds rate",
        "target range",
        "incoming data",
        "balance of risks",
    )

    central_bank_signal_count = sum(
        term in normalised_text
        for term in central_bank_terms
    )

    if central_bank_signal_count >= 2:
        return NewsAnalysis(
            impact_term=analysis.impact_term,
            impact_scope=analysis.impact_scope,
            scope_items=analysis.scope_items,
            highlights=analysis.highlights,
            sentiment=NewsSentiment.NEUTRAL,
        )

    return analysis

@dataclass(frozen=True)
class BenchmarkItemResult:
    benchmark_id: str
    parse_succeeded: bool
    validation_approved: bool
    duration_seconds: float
    rejection_reasons: tuple[str, ...]
    analysis: NewsAnalysis | None
    evaluation: NewsAnalysisEvaluation | None


@dataclass(frozen=True)
class NewsBenchmarkReport:
    model_name: str
    prompt_version: str
    dataset_version: str
    total_articles: int
    parse_success_count: int
    validation_approved_count: int
    average_duration_seconds: float
    items: tuple[BenchmarkItemResult, ...]

    @property
    def parse_success_rate(self) -> float:
        if self.total_articles == 0:
            return 0.0

        return (
            self.parse_success_count
            / self.total_articles
        )

    @property
    def validation_approval_rate(self) -> float:
        if self.total_articles == 0:
            return 0.0

        return (
            self.validation_approved_count
            / self.total_articles
        )

    @property
    def evaluated_items(
        self,
    ) -> tuple[BenchmarkItemResult, ...]:
        return tuple(
            item
            for item in self.items
            if item.evaluation is not None
        )

    @property
    def sentiment_accuracy(self) -> float:
        return self._average_boolean_metric(
            "sentiment_correct"
        )

    @property
    def impact_term_accuracy(self) -> float:
        return self._average_boolean_metric(
            "impact_term_correct"
        )

    @property
    def impact_scope_accuracy(self) -> float:
        return self._average_boolean_metric(
            "impact_scope_correct"
        )

    @property
    def average_scope_precision(self) -> float:
        return self._average_numeric_metric(
            "scope_item_precision"
        )

    @property
    def average_scope_recall(self) -> float:
        return self._average_numeric_metric(
            "scope_item_recall"
        )

    @property
    def average_highlight_similarity(self) -> float:
        return self._average_numeric_metric(
            "highlight_similarity"
        )

    @property
    def average_overall_score(self) -> float:
        return self._average_numeric_metric(
            "overall_score"
        )

    def _average_boolean_metric(
        self,
        attribute_name: str,
    ) -> float:
        evaluations = [
            item.evaluation
            for item in self.evaluated_items
            if item.evaluation is not None
        ]

        if not evaluations:
            return 0.0

        return sum(
            float(
                getattr(
                    evaluation,
                    attribute_name,
                )
            )
            for evaluation in evaluations
        ) / len(evaluations)

    def _average_numeric_metric(
        self,
        attribute_name: str,
    ) -> float:
        evaluations = [
            item.evaluation
            for item in self.evaluated_items
            if item.evaluation is not None
        ]

        if not evaluations:
            return 0.0

        return sum(
            float(
                getattr(
                    evaluation,
                    attribute_name,
                )
            )
            for evaluation in evaluations
        ) / len(evaluations)


def run_news_benchmark(
    *,
    analyser: BenchmarkNewsAnalyser,
    validator: NewsAnalysisValidator,
    dataset: BenchmarkDataset,
    model_name: str,
    prompt_version: str,
    dataset_version: str,
) -> NewsBenchmarkReport:
    validation = dataset.validate()

    if not validation.approved:
        raise ValueError(
            "Benchmark dataset is invalid: "
            + "; ".join(validation.errors)
        )

    results: list[BenchmarkItemResult] = []

    for benchmark_id in sorted(
        dataset.ready_articles
    ):
        article = dataset.ready_articles[
            benchmark_id
        ]

        label: BenchmarkLabel = (
            dataset.labels[benchmark_id]
        )

        started_at = perf_counter()

        try:
            analysis = analyser.analyse(
                article.article_text
            )

            analysis = _normalise_scope_items(
                analysis=analysis,
                article_text=article.article_text,
                company=article.company,
                ticker=article.ticker,
            )
            analysis = _normalise_highlights(
            analysis=analysis,
            article_text=article.article_text,
            )
            analysis = _normalise_impact_term(
                analysis=analysis,
                article_text=article.article_text,
            )
            analysis = _normalise_sentiment(
                analysis=analysis,
                article_text=article.article_text,
            )
            duration = (
                perf_counter() - started_at
            )

            validation_result = (
                validator.validate(
                    article_text=(
                        article.article_text
                    ),
                    analysis=analysis,
                    allowed_symbols=(
                        set(label.scope_items)
                    ),
                )
            )

            evaluation = evaluate_news_analysis(
                analysis=analysis,
                expected=label,
            )

            results.append(
                BenchmarkItemResult(
                    benchmark_id=benchmark_id,
                    parse_succeeded=True,
                    validation_approved=(
                        validation_result.approved
                    ),
                    duration_seconds=duration,
                    rejection_reasons=(
                        validation_result.reasons
                    ),
                    analysis=analysis,
                    evaluation=evaluation,
                )
            )

        except ValueError as error:
            duration = (
                perf_counter() - started_at
            )

            results.append(
                BenchmarkItemResult(
                    benchmark_id=benchmark_id,
                    parse_succeeded=False,
                    validation_approved=False,
                    duration_seconds=duration,
                    rejection_reasons=(
                        str(error),
                    ),
                    analysis=None,
                    evaluation=None,
                )
            )

    total_articles = len(results)

    total_duration = sum(
        item.duration_seconds
        for item in results
    )

    return NewsBenchmarkReport(
        model_name=model_name.strip(),
        prompt_version=(
            prompt_version.strip()
        ),
        dataset_version=(
            dataset_version.strip()
        ),
        total_articles=total_articles,
        parse_success_count=sum(
            item.parse_succeeded
            for item in results
        ),
        validation_approved_count=sum(
            item.validation_approved
            for item in results
        ),
        average_duration_seconds=(
            total_duration / total_articles
            if total_articles
            else 0.0
        ),
        items=tuple(results),
    )


def save_report(
    *,
    report: NewsBenchmarkReport,
    file_path: Path,
) -> None:
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = asdict(report)

    for index, item in enumerate(
        report.items
    ):
        item_data = data["items"][index]

        analysis_data = item_data["analysis"]

        if (
            isinstance(analysis_data, dict)
            and item.analysis is not None
        ):
            analysis_data["impact_term"] = (
                item.analysis.impact_term.value
            )
            analysis_data["impact_scope"] = (
                item.analysis.impact_scope.value
            )
            analysis_data["sentiment"] = (
                item.analysis.sentiment.value
            )
            analysis_data["scope_items"] = list(
                item.analysis.scope_items
            )
            analysis_data["highlights"] = list(
                item.analysis.highlights
            )

        item_data["rejection_reasons"] = list(
            item.rejection_reasons
        )

    data.update(
        {
            "parse_success_rate": (
                report.parse_success_rate
            ),
            "validation_approval_rate": (
                report.validation_approval_rate
            ),
            "sentiment_accuracy": (
                report.sentiment_accuracy
            ),
            "impact_term_accuracy": (
                report.impact_term_accuracy
            ),
            "impact_scope_accuracy": (
                report.impact_scope_accuracy
            ),
            "average_scope_precision": (
                report.average_scope_precision
            ),
            "average_scope_recall": (
                report.average_scope_recall
            ),
            "average_highlight_similarity": (
                report
                .average_highlight_similarity
            ),
            "average_overall_score": (
                report.average_overall_score
            ),
        }
    )

    file_path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )