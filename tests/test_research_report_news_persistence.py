import csv
import json

from app.research_report import (
    ResearchReport,
    save_research_report_csv,
    save_research_report_json,
)


def create_report() -> ResearchReport:
    return ResearchReport(
        strategy_name="Example",
        generated_at=(
            "2026-07-18T20:00:00+01:00"
        ),
        verdict="PROMISING",
        passed_check_count=5,
        total_check_count=5,
        decision_reasons=(
            "Example reason.",
        ),
        gross_completed_trades=10,
        net_completed_trades=10,
        gross_backtest_return_percent=7.0,
        net_backtest_return_percent=5.0,
        gross_monte_carlo_median_percent=7.0,
        net_monte_carlo_median_percent=5.0,
        gross_fifth_percentile_percent=-1.0,
        net_fifth_percentile_percent=-2.0,
        gross_ninety_fifth_percentile_percent=15.0,
        net_ninety_fifth_percentile_percent=13.0,
        gross_loss_probability_percent=6.0,
        net_loss_probability_percent=11.0,
        gross_average_drawdown_percent=2.0,
        net_average_drawdown_percent=3.0,
        gross_worst_drawdown_percent=8.0,
        net_worst_drawdown_percent=10.0,
        slippage_percent=0.1,
        commission_percent=0.1,
        minimum_fee=0.0,
        walk_forward_training_return_percent=8.0,
        walk_forward_validation_return_percent=3.0,
        rolling_window_count=5,
        rolling_positive_window_percent=60.0,
        rolling_average_return_percent=1.7,
        rolling_worst_return_percent=-2.0,
        news_signal_count=4,
        news_outcome_count=3,
        news_unmatched_outcome_count=0,
        news_sentiment_group_count=2,
        news_materiality_group_count=2,
        news_event_type_group_count=3,
        news_confidence_group_count=2,
        news_research_details={
            "signal_count": 4,
            "outcome_count": 3,
            "sentiment_groups": [
                {
                    "group_name": "POSITIVE",
                    "horizon_name": "1D",
                    "sample_size": 2,
                }
            ],
        },
    )


def test_json_contains_full_news_details(
    tmp_path,
) -> None:
    output_path = (
        tmp_path / "report.json"
    )

    save_research_report_json(
        report=create_report(),
        output_path=str(output_path),
    )

    payload = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    assert payload["news_signal_count"] == 4
    assert (
        payload["news_research_details"]
        ["sentiment_groups"][0]
        ["group_name"]
        == "POSITIVE"
    )


def test_csv_contains_compact_news_counts(
    tmp_path,
) -> None:
    output_path = (
        tmp_path / "report.csv"
    )

    save_research_report_csv(
        report=create_report(),
        output_path=str(output_path),
    )

    with output_path.open(
        mode="r",
        encoding="utf-8",
        newline="",
    ) as file:
        row = next(
            csv.DictReader(file)
        )

    assert row["news_signal_count"] == "4"
    assert row["news_outcome_count"] == "3"
    assert (
        "news_research_details"
        not in row
    )