from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from app.backtest_models import (
    HistoricalPriceBar,
)
from app.decision_memory_models import (
    DecisionMemoryRecord,
)
from app.decision_outcome_models import (
    DecisionOutcomeCaptureResult,
    DecisionOutcomeObservation,
    DecisionOutcomeOverview,
)
from app.decision_outcome_repository import (
    DecisionOutcomeRepository,
)


HistoricalBarsProvider = Callable[
    [str, int],
    list[HistoricalPriceBar],
]
DecisionProvider = Callable[
    [int],
    tuple[
        DecisionMemoryRecord,
        ...
    ],
]
NowProvider = Callable[
    [],
    datetime,
]


class DecisionOutcomeService:
    DEFAULT_HORIZONS = (
        1,
        7,
        30,
        90,
        180,
        365,
    )

    def __init__(
        self,
        *,
        repository: (
            DecisionOutcomeRepository
        ),
        decisions_provider: (
            DecisionProvider
        ),
        bars_provider: (
            HistoricalBarsProvider
        ),
        now_provider: (
            NowProvider | None
        ) = None,
        benchmark_symbol: str = "SPY",
        horizons: tuple[
            int,
            ...
        ] = DEFAULT_HORIZONS,
    ) -> None:
        if not horizons:
            raise ValueError(
                "At least one outcome "
                "horizon is required."
            )

        if any(
            horizon <= 0
            for horizon in horizons
        ):
            raise ValueError(
                "Outcome horizons must "
                "be positive."
            )

        self._repository = repository
        self._decisions_provider = (
            decisions_provider
        )
        self._bars_provider = bars_provider
        self._now_provider = (
            now_provider
            or (
                lambda: datetime.now(
                    timezone.utc
                )
            )
        )
        self._benchmark_symbol = (
            benchmark_symbol
            .upper()
            .strip()
        )
        self._horizons = tuple(
            sorted(set(horizons))
        )

    def initialize(
        self,
    ) -> None:
        self._repository.initialize()

    def capture_due(
        self,
        *,
        decision_limit: int = 500,
    ) -> DecisionOutcomeCaptureResult:
        now = self._utc_now()
        today = now.date()
        decisions = (
            self._decisions_provider(
                decision_limit
            )
        )

        created: list[
            DecisionOutcomeObservation
        ] = []
        skipped = 0

        benchmark_bars: (
            list[HistoricalPriceBar]
            | None
        ) = None

        for decision in decisions:
            completed = set(
                self._repository
                .completed_horizons(
                    decision_id=(
                        decision.decision_id
                    )
                )
            )

            due = [
                horizon
                for horizon
                in self._horizons
                if (
                    horizon not in completed
                    and (
                        decision
                        .thesis_generated_at
                        .date()
                        + timedelta(
                            days=horizon
                        )
                    )
                    <= today
                )
            ]

            if not due:
                skipped += 1
                continue

            try:
                symbol_bars = (
                    self._bars_provider(
                        decision.symbol,
                        500,
                    )
                )

                if benchmark_bars is None:
                    benchmark_bars = (
                        self._bars_provider(
                            self._benchmark_symbol,
                            500,
                        )
                    )

                observations = (
                    self._observations(
                        decision=decision,
                        symbol_bars=(
                            symbol_bars
                        ),
                        benchmark_bars=(
                            benchmark_bars
                        ),
                        horizons=tuple(due),
                        observed_at=now,
                    )
                )
            except Exception:
                skipped += 1
                continue

            for observation in observations:
                if (
                    self._repository
                    .save_if_new(
                        observation=(
                            observation
                        )
                    )
                ):
                    created.append(
                        observation
                    )

        return DecisionOutcomeCaptureResult(
            evaluated_decision_count=len(
                decisions
            ),
            created_observation_count=len(
                created
            ),
            skipped_decision_count=skipped,
            observations=tuple(created),
        )

    def overview(
        self,
        *,
        limit: int = 20,
    ) -> DecisionOutcomeOverview:
        return DecisionOutcomeOverview(
            generated_at=self._utc_now(),
            tracked_decision_count=(
                self._repository
                .count_decisions()
            ),
            observation_count=(
                self._repository
                .count_all()
            ),
            positive_outcome_count=(
                self._repository
                .count_positive()
            ),
            negative_outcome_count=(
                self._repository
                .count_negative()
            ),
            average_return=(
                self._repository
                .average_return()
            ),
            average_alpha=(
                self._repository
                .average_alpha()
            ),
            latest=(
                self._repository
                .list_recent(
                    limit=limit
                )
            ),
        )

    def for_decision(
        self,
        *,
        decision_id: str,
    ) -> tuple[
        DecisionOutcomeObservation,
        ...
    ]:
        return (
            self._repository
            .list_for_decision(
                decision_id=decision_id
            )
        )

    def _observations(
        self,
        *,
        decision: DecisionMemoryRecord,
        symbol_bars: list[
            HistoricalPriceBar
        ],
        benchmark_bars: list[
            HistoricalPriceBar
        ],
        horizons: tuple[int, ...],
        observed_at: datetime,
    ) -> tuple[
        DecisionOutcomeObservation,
        ...
    ]:
        symbol_ordered = sorted(
            symbol_bars,
            key=lambda bar: (
                bar.trading_date
            ),
        )
        benchmark_ordered = sorted(
            benchmark_bars,
            key=lambda bar: (
                bar.trading_date
            ),
        )

        decision_date = (
            decision
            .thesis_generated_at
            .date()
        )

        symbol_entry = (
            self._first_on_or_after(
                bars=symbol_ordered,
                target=decision_date,
            )
        )
        benchmark_entry = (
            self._first_on_or_after(
                bars=benchmark_ordered,
                target=decision_date,
            )
        )

        results: list[
            DecisionOutcomeObservation
        ] = []

        for horizon in horizons:
            target = (
                decision_date
                + timedelta(
                    days=horizon
                )
            )

            symbol_exit = (
                self._first_on_or_after(
                    bars=symbol_ordered,
                    target=target,
                )
            )
            benchmark_exit = (
                self._first_on_or_after(
                    bars=benchmark_ordered,
                    target=target,
                )
            )

            path = [
                bar
                for bar in symbol_ordered
                if (
                    symbol_entry
                    .trading_date
                    <= bar.trading_date
                    <= symbol_exit
                    .trading_date
                )
            ]

            absolute_return = (
                symbol_exit.close_price
                / symbol_entry.close_price
                - 1
            )
            benchmark_return = (
                benchmark_exit.close_price
                / benchmark_entry.close_price
                - 1
            )

            maximum_favourable = max(
                (
                    bar.high_price
                    / symbol_entry.close_price
                    - 1
                )
                for bar in path
            )
            maximum_drawdown = min(
                (
                    bar.low_price
                    / symbol_entry.close_price
                    - 1
                )
                for bar in path
            )

            status = (
                "POSITIVE"
                if absolute_return > 0
                else "NEGATIVE"
                if absolute_return < 0
                else "FLAT"
            )

            results.append(
                DecisionOutcomeObservation(
                    outcome_id=(
                        "OUTCOME-"
                        + uuid4().hex[
                            :16
                        ].upper()
                    ),
                    decision_id=(
                        decision.decision_id
                    ),
                    symbol=decision.symbol,
                    horizon_days=horizon,
                    target_date=target,
                    observed_at=(
                        observed_at
                    ),
                    entry_price=round(
                        symbol_entry
                        .close_price,
                        6,
                    ),
                    observed_price=round(
                        symbol_exit
                        .close_price,
                        6,
                    ),
                    absolute_return=round(
                        absolute_return,
                        8,
                    ),
                    benchmark_symbol=(
                        self
                        ._benchmark_symbol
                    ),
                    benchmark_entry_price=round(
                        benchmark_entry
                        .close_price,
                        6,
                    ),
                    benchmark_observed_price=round(
                        benchmark_exit
                        .close_price,
                        6,
                    ),
                    benchmark_return=round(
                        benchmark_return,
                        8,
                    ),
                    alpha=round(
                        absolute_return
                        - benchmark_return,
                        8,
                    ),
                    maximum_favourable_excursion=round(
                        maximum_favourable,
                        8,
                    ),
                    maximum_drawdown=round(
                        maximum_drawdown,
                        8,
                    ),
                    status=status,
                )
            )

        return tuple(results)

    @staticmethod
    def _first_on_or_after(
        *,
        bars: list[
            HistoricalPriceBar
        ],
        target: date,
    ) -> HistoricalPriceBar:
        for bar in bars:
            if (
                bar.trading_date
                >= target
            ):
                return bar

        raise ValueError(
            "No market bar exists on or "
            "after the target date."
        )

    def _utc_now(
        self,
    ) -> datetime:
        value = self._now_provider()

        if value.tzinfo is None:
            raise ValueError(
                "Outcome Tracking clock "
                "must be timezone-aware."
            )

        return value.astimezone(
            timezone.utc
        )
