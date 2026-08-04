from dataclasses import asdict, dataclass
from typing import Mapping


@dataclass(frozen=True)
class ShadowPerformanceGroup:
    name: str
    sample_count: int
    profitable_count: int
    directional_success_percent: float
    average_return_percent: float
    median_return_percent: float
    average_net_return_percent: float

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ShadowHorizonPerformance:
    horizon: str
    decision_count: int
    measured_count: int
    coverage_percent: float
    profitable_count: int
    directional_success_percent: float
    profitable_after_cost_count: int
    profitable_after_cost_percent: float
    average_return_percent: float
    median_return_percent: float
    average_net_return_percent: float
    best_return_percent: float
    worst_return_percent: float
    maximum_drawdown_percent: float
    rolling_window_count: int
    positive_rolling_window_percent: float
    by_action: tuple[ShadowPerformanceGroup, ...]
    by_score_band: tuple[ShadowPerformanceGroup, ...]
    by_confidence_band: tuple[ShadowPerformanceGroup, ...]
    by_event_type: tuple[ShadowPerformanceGroup, ...]
    by_materiality: tuple[ShadowPerformanceGroup, ...]

    def to_dictionary(self) -> dict[str, object]:
        payload = asdict(self)
        return payload


@dataclass(frozen=True)
class ShadowPerformanceReport:
    model_version: str
    total_decision_count: int
    execution_cost_percent: float
    horizons: tuple[ShadowHorizonPerformance, ...]
    trading_impact: str = "NONE"

    def to_dictionary(self) -> dict[str, object]:
        payload = asdict(self)
        payload.update(
            {
                "available": self.total_decision_count > 0,
                "generated_at": None,
                "periods": {
                    horizon.horizon.lower(): {
                        "directional_success": (
                            horizon.directional_success_percent / 100
                        ),
                        "profitable_after_costs": (
                            horizon.profitable_after_cost_percent / 100
                        ),
                        "average_return": (
                            horizon.average_return_percent / 100
                        ),
                        "average_net_return": (
                            horizon.average_net_return_percent / 100
                        ),
                        "maximum_drawdown": (
                            horizon.maximum_drawdown_percent / 100
                        ),
                        "rolling_stability": (
                            horizon.positive_rolling_window_percent / 100
                        ),
                        "coverage": horizon.coverage_percent / 100,
                        "sample_count": horizon.measured_count,
                    }
                    for horizon in self.horizons
                },
            }
        )
        return payload
