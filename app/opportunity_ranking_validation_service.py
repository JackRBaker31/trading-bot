from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import date, datetime, timezone
from math import sqrt
from statistics import mean, median

from app.backtest_models import HistoricalPriceBar
from app.opportunity_ranking_history_models import OpportunityRankingSnapshot
from app.opportunity_ranking_history_repository import (
    OpportunityRankingHistoryRepository,
)
from app.opportunity_ranking_validation_models import (
    OpportunityForwardOutcome,
    OpportunityRankingValidationReport,
    OpportunityValidationBucket,
    OpportunityValidationCaptureResult,
    OpportunityValidationHorizon,
)
from app.opportunity_ranking_validation_repository import (
    OpportunityRankingValidationRepository,
)


HistoricalBarsProvider = Callable[[str, int], list[HistoricalPriceBar]]
NowProvider = Callable[[], datetime]


class OpportunityRankingValidationService:
    """Measures whether advisory opportunity ranks predict forward returns.

    Validation uses the first retained ranking snapshot for each symbol and UTC
    date. Entry is the next available trading session open, preventing the
    same-day close from leaking into the result. A 1D horizon exits at that
    session's close; longer horizons exit after the requested number of trading
    sessions. The service is observational and never changes ranking or trading
    behaviour.
    """

    METHODOLOGY_VERSION = "KAIRO-RVALID-1.0"
    METHODOLOGY_SUMMARY = (
        "Advisory forward-return validation using one daily cohort per symbol, "
        "entry at the next trading-session open, exit after 1, 5 or 20 trading "
        "sessions, and SPY-relative alpha. Results do not alter ranking, risk "
        "or execution controls."
    )
    DEFAULT_HORIZONS = (1, 5, 20)

    def __init__(
        self,
        *,
        history_repository: OpportunityRankingHistoryRepository,
        validation_repository: OpportunityRankingValidationRepository,
        bars_provider: HistoricalBarsProvider,
        now_provider: NowProvider | None = None,
        benchmark_symbol: str = "SPY",
        horizons: tuple[int, ...] = DEFAULT_HORIZONS,
        maximum_history_snapshots: int = 10000,
    ) -> None:
        if not horizons or any(value <= 0 for value in horizons):
            raise ValueError("Validation horizons must be positive.")
        if maximum_history_snapshots <= 0:
            raise ValueError("Maximum history snapshots must be positive.")
        cleaned_benchmark = benchmark_symbol.upper().strip()
        if not cleaned_benchmark:
            raise ValueError("A validation benchmark symbol is required.")

        self._history_repository = history_repository
        self._validation_repository = validation_repository
        self._bars_provider = bars_provider
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )
        self._benchmark_symbol = cleaned_benchmark
        self._horizons = tuple(sorted(set(horizons)))
        self._maximum_history_snapshots = maximum_history_snapshots

    def initialize(self) -> None:
        self._history_repository.initialize()
        self._validation_repository.initialize()

    def capture_due(self) -> OpportunityValidationCaptureResult:
        now = self._utc_now()
        candidates = self._daily_candidates()
        completed_by_snapshot = {
            snapshot.snapshot_id: set(
                self._validation_repository.completed_horizons(
                    snapshot_id=snapshot.snapshot_id
                )
            )
            for snapshot in candidates
        }

        evaluated = 0
        created = 0
        existing = 0
        pending = 0
        failed_symbols: list[str] = []
        warnings: list[str] = []

        actionable = [
            snapshot
            for snapshot in candidates
            if snapshot.captured_at.date() < now.date()
            and any(
                horizon not in completed_by_snapshot[snapshot.snapshot_id]
                for horizon in self._horizons
            )
        ]

        if not actionable:
            pending = sum(
                len(self._horizons)
                - len(completed_by_snapshot[snapshot.snapshot_id])
                for snapshot in candidates
            )
            return OpportunityValidationCaptureResult(
                evaluated_snapshot_count=0,
                created_outcome_count=0,
                existing_outcome_count=0,
                pending_outcome_count=pending,
                failed_symbol_count=0,
                failed_symbols=(),
                warnings=(),
            )

        try:
            benchmark_bars = self._ordered_bars(
                self._benchmark_symbol,
                self._bars_provider(self._benchmark_symbol, 500),
            )
        except Exception as error:
            warning = (
                f"Benchmark history was unavailable for "
                f"{self._benchmark_symbol}: {type(error).__name__}: {error}"
            )
            return OpportunityValidationCaptureResult(
                evaluated_snapshot_count=0,
                created_outcome_count=0,
                existing_outcome_count=0,
                pending_outcome_count=sum(
                    len(self._horizons)
                    - len(completed_by_snapshot[snapshot.snapshot_id])
                    for snapshot in candidates
                ),
                failed_symbol_count=1,
                failed_symbols=(self._benchmark_symbol,),
                warnings=(warning,),
            )

        grouped: dict[str, list[OpportunityRankingSnapshot]] = defaultdict(list)
        for snapshot in actionable:
            grouped[snapshot.symbol].append(snapshot)

        for symbol, symbol_snapshots in grouped.items():
            try:
                symbol_bars = self._ordered_bars(
                    symbol,
                    self._bars_provider(symbol, 500),
                )
            except Exception as error:
                failed_symbols.append(symbol)
                warnings.append(
                    f"Forward-return history was unavailable for {symbol}: "
                    f"{type(error).__name__}: {error}"
                )
                continue

            for snapshot in symbol_snapshots:
                evaluated += 1
                completed = completed_by_snapshot[snapshot.snapshot_id]
                for horizon in self._horizons:
                    if horizon in completed:
                        existing += 1
                        continue
                    outcome = self._outcome(
                        snapshot=snapshot,
                        horizon_days=horizon,
                        symbol_bars=symbol_bars,
                        benchmark_bars=benchmark_bars,
                        observed_at=now,
                    )
                    if outcome is None:
                        pending += 1
                        continue
                    if self._validation_repository.save_if_new(outcome=outcome):
                        created += 1
                        completed.add(horizon)
                    else:
                        existing += 1
                        completed.add(horizon)

        failed_set = tuple(dict.fromkeys(failed_symbols))
        pending += sum(
            len(self._horizons)
            - len(completed_by_snapshot[snapshot.snapshot_id])
            for snapshot in candidates
            if snapshot.symbol in failed_set
            or snapshot.captured_at.date() >= now.date()
        )

        return OpportunityValidationCaptureResult(
            evaluated_snapshot_count=evaluated,
            created_outcome_count=created,
            existing_outcome_count=existing,
            pending_outcome_count=pending,
            failed_symbol_count=len(failed_set),
            failed_symbols=failed_set,
            warnings=tuple(dict.fromkeys(warnings)),
        )

    def get_report(
        self,
        *,
        horizon_days: int = 1,
    ) -> OpportunityRankingValidationReport:
        selected = self._validated_horizon(horizon_days)
        generated_at = self._utc_now()
        candidates = self._daily_candidates()
        outcomes = self._validation_repository.list_all(limit=20000)
        selected_outcomes = tuple(
            item for item in outcomes if item.horizon_days == selected
        )

        horizon_reports = tuple(
            self._horizon_report(
                horizon_days=horizon,
                outcomes=tuple(
                    item for item in outcomes if item.horizon_days == horizon
                ),
                tracked_snapshot_count=len(candidates),
            )
            for horizon in self._horizons
        )
        selected_report = next(
            item
            for item in horizon_reports
            if item.horizon_days == selected
        )

        score_bands = (
            self._bucket(
                code="SCORE_80_PLUS",
                label="Score 80–100",
                outcomes=(
                    item for item in selected_outcomes if item.opportunity_score >= 80
                ),
            ),
            self._bucket(
                code="SCORE_70_79",
                label="Score 70–79.9",
                outcomes=(
                    item
                    for item in selected_outcomes
                    if 70 <= item.opportunity_score < 80
                ),
            ),
            self._bucket(
                code="SCORE_60_69",
                label="Score 60–69.9",
                outcomes=(
                    item
                    for item in selected_outcomes
                    if 60 <= item.opportunity_score < 70
                ),
            ),
            self._bucket(
                code="SCORE_BELOW_60",
                label="Score below 60",
                outcomes=(
                    item for item in selected_outcomes if item.opportunity_score < 60
                ),
            ),
        )
        rank_buckets = (
            self._bucket(
                code="RANK_TOP_3",
                label="Rank #1–#3",
                outcomes=(item for item in selected_outcomes if item.original_rank <= 3),
            ),
            self._bucket(
                code="RANK_4_10",
                label="Rank #4–#10",
                outcomes=(
                    item for item in selected_outcomes if 4 <= item.original_rank <= 10
                ),
            ),
            self._bucket(
                code="RANK_11_PLUS",
                label="Rank #11+",
                outcomes=(item for item in selected_outcomes if item.original_rank >= 11),
            ),
        )
        readiness_buckets = (
            self._bucket(
                code="EXECUTION_READY",
                label="Execution ready",
                outcomes=(
                    item for item in selected_outcomes if item.eligible_for_execution
                ),
            ),
            self._bucket(
                code="EXECUTION_BLOCKED",
                label="Execution blocked",
                outcomes=(
                    item
                    for item in selected_outcomes
                    if not item.eligible_for_execution
                ),
            ),
        )

        symbol_performance = self._group_buckets(
            outcomes=selected_outcomes,
            key=lambda item: item.symbol,
            prefix="SYMBOL",
            limit=20,
        )
        sector_performance = self._group_buckets(
            outcomes=selected_outcomes,
            key=lambda item: item.sector or "Other",
            prefix="SECTOR",
            limit=20,
        )

        warnings: list[str] = [
            "Forward-return validation is observational and remains advisory only."
        ]
        if not candidates:
            warnings.append(
                "No opportunity-history cohorts exist yet. Run Intelligence Cycles "
                "to create ranking snapshots."
            )
        elif not selected_outcomes:
            warnings.append(
                f"No {selected}D outcomes are mature yet. The first result can only "
                "be measured after a later trading session is available."
            )
        elif len(selected_outcomes) < 10:
            warnings.append(
                "The selected horizon has fewer than 10 outcomes; treat hit rates "
                "and correlations as immature."
            )

        return OpportunityRankingValidationReport(
            generated_at=generated_at,
            methodology_version=self.METHODOLOGY_VERSION,
            methodology_summary=self.METHODOLOGY_SUMMARY,
            advisory_only=True,
            benchmark_symbol=self._benchmark_symbol,
            selected_horizon_days=selected,
            available_horizons=self._horizons,
            tracked_snapshot_count=len(candidates),
            measured_outcome_count=len(outcomes),
            pending_outcome_count=max(
                0,
                len(candidates) * len(self._horizons) - len(outcomes),
            ),
            latest_observed_at=max(
                (item.observed_at for item in outcomes),
                default=None,
            ),
            selected_horizon=selected_report,
            horizons=horizon_reports,
            score_bands=score_bands,
            rank_buckets=rank_buckets,
            readiness_buckets=readiness_buckets,
            symbol_performance=symbol_performance,
            sector_performance=sector_performance,
            latest_outcomes=selected_outcomes[:20],
            warnings=tuple(warnings),
        )

    def _daily_candidates(self) -> tuple[OpportunityRankingSnapshot, ...]:
        snapshots = self._history_repository.list_all(
            limit=self._maximum_history_snapshots
        )
        first_by_day: dict[tuple[str, date], OpportunityRankingSnapshot] = {}
        for snapshot in snapshots:
            key = (snapshot.symbol, snapshot.captured_at.date())
            first_by_day.setdefault(key, snapshot)
        return tuple(
            sorted(
                first_by_day.values(),
                key=lambda item: (item.captured_at, item.snapshot_id),
            )
        )

    def _outcome(
        self,
        *,
        snapshot: OpportunityRankingSnapshot,
        horizon_days: int,
        symbol_bars: list[HistoricalPriceBar],
        benchmark_bars: list[HistoricalPriceBar],
        observed_at: datetime,
    ) -> OpportunityForwardOutcome | None:
        entry_index = next(
            (
                index
                for index, bar in enumerate(symbol_bars)
                if bar.trading_date > snapshot.captured_at.date()
            ),
            None,
        )
        if entry_index is None:
            return None
        exit_index = entry_index + horizon_days - 1
        if exit_index >= len(symbol_bars):
            return None

        entry_bar = symbol_bars[entry_index]
        exit_bar = symbol_bars[exit_index]
        benchmark_entry = self._first_on_or_after(
            benchmark_bars,
            entry_bar.trading_date,
        )
        benchmark_exit = self._first_on_or_after(
            benchmark_bars,
            exit_bar.trading_date,
        )
        if benchmark_entry is None or benchmark_exit is None:
            return None

        entry_price = entry_bar.open_price
        observed_price = exit_bar.close_price
        benchmark_entry_price = benchmark_entry.open_price
        benchmark_observed_price = benchmark_exit.close_price
        path = symbol_bars[entry_index : exit_index + 1]

        return_percent = (observed_price / entry_price - 1.0) * 100.0
        benchmark_return = (
            benchmark_observed_price / benchmark_entry_price - 1.0
        ) * 100.0
        favourable = max(
            (bar.high_price / entry_price - 1.0) * 100.0 for bar in path
        )
        drawdown = min(
            (bar.low_price / entry_price - 1.0) * 100.0 for bar in path
        )

        return OpportunityForwardOutcome(
            outcome_id=0,
            snapshot_id=snapshot.snapshot_id,
            captured_at=snapshot.captured_at,
            symbol=snapshot.symbol,
            horizon_days=horizon_days,
            entry_date=entry_bar.trading_date,
            exit_date=exit_bar.trading_date,
            observed_at=observed_at,
            entry_price=round(entry_price, 6),
            observed_price=round(observed_price, 6),
            return_percent=round(return_percent, 6),
            benchmark_symbol=self._benchmark_symbol,
            benchmark_entry_price=round(benchmark_entry_price, 6),
            benchmark_observed_price=round(benchmark_observed_price, 6),
            benchmark_return_percent=round(benchmark_return, 6),
            alpha_percent=round(return_percent - benchmark_return, 6),
            maximum_favourable_excursion_percent=round(favourable, 6),
            maximum_drawdown_percent=round(drawdown, 6),
            status=(
                "POSITIVE"
                if return_percent > 0
                else "NEGATIVE"
                if return_percent < 0
                else "FLAT"
            ),
            original_rank=snapshot.rank,
            opportunity_score=snapshot.opportunity_score,
            calibrated_confidence=snapshot.calibrated_confidence,
            expected_return_percent=snapshot.expected_return_percent,
            evidence_coverage_percent=snapshot.evidence_coverage_percent,
            eligible_for_execution=snapshot.eligible_for_execution,
            category=snapshot.category,
            sector=snapshot.sector,
            historical_match_count=snapshot.historical_match_count,
            measured_case_count=snapshot.measured_case_count,
            universe_version_id=snapshot.universe_version_id,
            universe_size=snapshot.universe_size,
        )

    def _horizon_report(
        self,
        *,
        horizon_days: int,
        outcomes: tuple[OpportunityForwardOutcome, ...],
        tracked_snapshot_count: int,
    ) -> OpportunityValidationHorizon:
        values = [item.return_percent for item in outcomes]
        alphas = [item.alpha_percent for item in outcomes]
        drawdowns = [item.maximum_drawdown_percent for item in outcomes]
        top_three = [
            item.return_percent for item in outcomes if item.original_rank <= 3
        ]
        others = [
            item.return_percent for item in outcomes if item.original_rank > 3
        ]
        positive = sum(1 for value in values if value > 0)
        return OpportunityValidationHorizon(
            horizon_days=horizon_days,
            label=f"{horizon_days}D",
            sample_count=len(outcomes),
            pending_count=max(0, tracked_snapshot_count - len(outcomes)),
            positive_count=positive,
            hit_rate_percent=self._percent(positive, len(outcomes)),
            average_return_percent=self._average(values),
            median_return_percent=self._median(values),
            average_alpha_percent=self._average(alphas),
            median_alpha_percent=self._median(alphas),
            average_drawdown_percent=self._average(drawdowns),
            top_three_average_return_percent=self._average(top_three),
            other_average_return_percent=self._average(others),
            score_return_correlation=self._correlation(
                [item.opportunity_score for item in outcomes],
                values,
            ),
            rank_return_correlation=self._correlation(
                [-float(item.original_rank) for item in outcomes],
                values,
            ),
            maturity=self._maturity(len(outcomes)),
        )

    def _bucket(
        self,
        *,
        code: str,
        label: str,
        outcomes: Iterable[OpportunityForwardOutcome],
    ) -> OpportunityValidationBucket:
        items = tuple(outcomes)
        returns = [item.return_percent for item in items]
        alphas = [item.alpha_percent for item in items]
        drawdowns = [item.maximum_drawdown_percent for item in items]
        positive = sum(1 for value in returns if value > 0)
        return OpportunityValidationBucket(
            code=code,
            label=label,
            sample_count=len(items),
            positive_count=positive,
            hit_rate_percent=self._percent(positive, len(items)),
            average_return_percent=self._average(returns),
            median_return_percent=self._median(returns),
            average_alpha_percent=self._average(alphas),
            median_alpha_percent=self._median(alphas),
            average_drawdown_percent=self._average(drawdowns),
        )

    def _group_buckets(
        self,
        *,
        outcomes: tuple[OpportunityForwardOutcome, ...],
        key: Callable[[OpportunityForwardOutcome], str],
        prefix: str,
        limit: int,
    ) -> tuple[OpportunityValidationBucket, ...]:
        grouped: dict[str, list[OpportunityForwardOutcome]] = defaultdict(list)
        for outcome in outcomes:
            grouped[key(outcome)].append(outcome)
        buckets = [
            self._bucket(
                code=f"{prefix}_{name.upper().replace(' ', '_')}",
                label=name,
                outcomes=items,
            )
            for name, items in grouped.items()
        ]
        buckets.sort(
            key=lambda item: (
                item.sample_count,
                item.average_return_percent
                if item.average_return_percent is not None
                else float("-inf"),
                item.label,
            ),
            reverse=True,
        )
        return tuple(buckets[:limit])

    def _validated_horizon(self, value: int) -> int:
        if value not in self._horizons:
            allowed = ", ".join(str(item) for item in self._horizons)
            raise ValueError(f"Horizon must be one of: {allowed}.")
        return value

    @staticmethod
    def _ordered_bars(
        symbol: str,
        bars: list[HistoricalPriceBar],
    ) -> list[HistoricalPriceBar]:
        ordered = sorted(bars, key=lambda item: item.trading_date)
        if not ordered:
            raise ValueError(f"No historical bars exist for {symbol}.")
        return ordered

    @staticmethod
    def _first_on_or_after(
        bars: list[HistoricalPriceBar],
        target: date,
    ) -> HistoricalPriceBar | None:
        return next((bar for bar in bars if bar.trading_date >= target), None)

    @staticmethod
    def _average(values: list[float]) -> float | None:
        return None if not values else round(mean(values), 3)

    @staticmethod
    def _median(values: list[float]) -> float | None:
        return None if not values else round(median(values), 3)

    @staticmethod
    def _percent(numerator: int, denominator: int) -> float | None:
        if denominator <= 0:
            return None
        return round(numerator / denominator * 100.0, 2)

    @staticmethod
    def _maturity(sample_count: int) -> str:
        if sample_count < 10:
            return "IMMATURE"
        if sample_count < 30:
            return "DEVELOPING"
        return "MATURE"

    @staticmethod
    def _correlation(x_values: list[float], y_values: list[float]) -> float | None:
        if len(x_values) < 3 or len(x_values) != len(y_values):
            return None
        x_mean = mean(x_values)
        y_mean = mean(y_values)
        x_deviation = [value - x_mean for value in x_values]
        y_deviation = [value - y_mean for value in y_values]
        denominator = sqrt(
            sum(value * value for value in x_deviation)
            * sum(value * value for value in y_deviation)
        )
        if denominator <= 0:
            return None
        return round(
            sum(
                left * right
                for left, right in zip(x_deviation, y_deviation)
            )
            / denominator,
            3,
        )

    def _utc_now(self) -> datetime:
        value = self._now_provider()
        if value.tzinfo is None:
            raise ValueError("Ranking validation clock must be timezone-aware.")
        return value.astimezone(timezone.utc)
