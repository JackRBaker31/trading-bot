import csv
import json
from dataclasses import (
    asdict,
    dataclass,
)
from pathlib import Path


@dataclass(frozen=True)
class ResearchReport:
    strategy_name: str
    generated_at: str
    verdict: str
    passed_check_count: int
    total_check_count: int
    decision_reasons: tuple[str, ...]
    gross_completed_trades: int
    net_completed_trades: int
    gross_backtest_return_percent: float
    net_backtest_return_percent: float
    gross_monte_carlo_median_percent: float
    net_monte_carlo_median_percent: float
    gross_fifth_percentile_percent: float
    net_fifth_percentile_percent: float
    gross_ninety_fifth_percentile_percent: float
    net_ninety_fifth_percentile_percent: float
    gross_loss_probability_percent: float
    net_loss_probability_percent: float
    gross_average_drawdown_percent: float
    net_average_drawdown_percent: float
    gross_worst_drawdown_percent: float
    net_worst_drawdown_percent: float
    slippage_percent: float
    commission_percent: float
    minimum_fee: float
    walk_forward_training_return_percent: float
    walk_forward_validation_return_percent: float
    rolling_window_count: int
    rolling_positive_window_percent: float
    rolling_average_return_percent: float
    rolling_worst_return_percent: float
    news_signal_count: int = 0
    news_outcome_count: int = 0
    news_unmatched_outcome_count: int = 0
    news_sentiment_group_count: int = 0
    news_materiality_group_count: int = 0
    news_event_type_group_count: int = 0
    news_confidence_group_count: int = 0
    news_research_details: (
        dict[str, object] | None
    ) = None

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return asdict(self)

    def to_csv_dictionary(
        self,
    ) -> dict[str, object]:
        data = self.to_dictionary()
        data.pop(
            "news_research_details",
            None,
        )
        return data


def save_research_report_json(
    *,
    report: ResearchReport,
    output_path: str,
) -> None:
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        mode="w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report.to_dictionary(),
            file,
            indent=2,
        )
        file.write("\n")


def save_research_report_csv(
    *,
    report: ResearchReport,
    output_path: str,
) -> None:
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = report.to_csv_dictionary()

    with path.open(
        mode="w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(
                data.keys()
            ),
        )

        writer.writeheader()
        writer.writerow(
            {
                key: _normalise_csv_value(
                    value
                )
                for key, value in data.items()
            }
        )


def _normalise_csv_value(
    value: object,
) -> object:
    if isinstance(value, float):
        return round(
            value,
            4,
        )

    return value