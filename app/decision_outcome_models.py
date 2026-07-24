from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class DecisionOutcomeObservation:
    outcome_id: str
    decision_id: str
    symbol: str
    horizon_days: int
    target_date: date
    observed_at: datetime
    entry_price: float
    observed_price: float
    absolute_return: float
    benchmark_symbol: str
    benchmark_entry_price: float
    benchmark_observed_price: float
    benchmark_return: float
    alpha: float
    maximum_favourable_excursion: float
    maximum_drawdown: float
    status: str

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "outcome_id": self.outcome_id,
            "decision_id": self.decision_id,
            "symbol": self.symbol,
            "horizon_days": (
                self.horizon_days
            ),
            "target_date": (
                self.target_date.isoformat()
            ),
            "observed_at": (
                self.observed_at.isoformat()
            ),
            "entry_price": self.entry_price,
            "observed_price": (
                self.observed_price
            ),
            "absolute_return": (
                self.absolute_return
            ),
            "benchmark_symbol": (
                self.benchmark_symbol
            ),
            "benchmark_entry_price": (
                self.benchmark_entry_price
            ),
            "benchmark_observed_price": (
                self.benchmark_observed_price
            ),
            "benchmark_return": (
                self.benchmark_return
            ),
            "alpha": self.alpha,
            "maximum_favourable_excursion": (
                self
                .maximum_favourable_excursion
            ),
            "maximum_drawdown": (
                self.maximum_drawdown
            ),
            "status": self.status,
        }


@dataclass(frozen=True)
class DecisionOutcomeSchedule:
    decision_id: str
    symbol: str
    decision_date: date
    entry_price: float
    benchmark_symbol: str
    benchmark_entry_price: float
    completed_horizons: tuple[
        int,
        ...
    ]
    pending_horizons: tuple[
        int,
        ...
    ]

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "symbol": self.symbol,
            "decision_date": (
                self.decision_date.isoformat()
            ),
            "entry_price": self.entry_price,
            "benchmark_symbol": (
                self.benchmark_symbol
            ),
            "benchmark_entry_price": (
                self.benchmark_entry_price
            ),
            "completed_horizons": list(
                self.completed_horizons
            ),
            "pending_horizons": list(
                self.pending_horizons
            ),
        }


@dataclass(frozen=True)
class DecisionOutcomeCaptureResult:
    evaluated_decision_count: int
    created_observation_count: int
    skipped_decision_count: int
    observations: tuple[
        DecisionOutcomeObservation,
        ...
    ]

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "evaluated_decision_count": (
                self.evaluated_decision_count
            ),
            "created_observation_count": (
                self.created_observation_count
            ),
            "skipped_decision_count": (
                self.skipped_decision_count
            ),
            "observations": [
                item.to_dictionary()
                for item in self.observations
            ],
        }


@dataclass(frozen=True)
class DecisionOutcomeOverview:
    generated_at: datetime
    tracked_decision_count: int
    observation_count: int
    positive_outcome_count: int
    negative_outcome_count: int
    average_return: float | None
    average_alpha: float | None
    latest: tuple[
        DecisionOutcomeObservation,
        ...
    ]

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "generated_at": (
                self.generated_at.isoformat()
            ),
            "tracked_decision_count": (
                self.tracked_decision_count
            ),
            "observation_count": (
                self.observation_count
            ),
            "positive_outcome_count": (
                self.positive_outcome_count
            ),
            "negative_outcome_count": (
                self.negative_outcome_count
            ),
            "average_return": (
                self.average_return
            ),
            "average_alpha": (
                self.average_alpha
            ),
            "latest": [
                item.to_dictionary()
                for item in self.latest
            ],
        }
