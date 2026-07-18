import csv
import json

from app.research_report import (
    ResearchReport,
    save_research_report_csv,
    save_research_report_json,
)


def create_report() -> ResearchReport:
    return ResearchReport(
        strategy_name=(
            "Drop=3 SMA=None "
            "RSI=3/30 Cooldown=0"
        ),
        generated_at=(
            "2026-07-18T15:00:00+01:00"
        ),
        verdict="PROMISING",
        passed_check_count=5,
        total_check_count=5,
        decision_reasons=(
            "Net return is positive.",
            "Walk-forward validation return is positive.",
            "Rolling positive-window rate meets the minimum.",
            "Monte Carlo loss probability is within the limit.",
            "Monte Carlo worst drawdown is within the limit.",
        ),
        gross_completed_trades=42,
        net_completed_trades=42,
        gross_backtest_return_percent=7.0490009,
        net_backtest_return_percent=5.3340547,
        gross_monte_carlo_median_percent=7.0526714,
        net_monte_carlo_median_percent=5.3266254,
        gross_fifth_percentile_percent=-0.3521579,
        net_fifth_percentile_percent=-2.0857737,
        gross_ninety_fifth_percentile_percent=14.5993444,
        net_ninety_fifth_percentile_percent=12.8565058,
        gross_loss_probability_percent=5.9,
        net_loss_probability_percent=11.2,
        gross_average_drawdown_percent=2.4627632,
        net_average_drawdown_percent=2.8642019,
        gross_worst_drawdown_percent=8.1619148,
        net_worst_drawdown_percent=9.7013397,
        slippage_percent=0.1,
        commission_percent=0.1,
        minimum_fee=0.0,
        walk_forward_training_return_percent=8.29,
        walk_forward_validation_return_percent=3.30,
        rolling_window_count=5,
        rolling_positive_window_percent=60.0,
        rolling_average_return_percent=1.73,
        rolling_worst_return_percent=-2.02,
    )


def test_converts_report_to_dictionary() -> None:
    report = create_report()

    data = report.to_dictionary()

    assert data["strategy_name"].startswith(
        "Drop=3"
    )
    assert data["gross_completed_trades"] == 42
    assert (
        data["net_backtest_return_percent"]
        == 5.3340547
    )
    assert data["verdict"] == "PROMISING"
    assert data["passed_check_count"] == 5


def test_saves_report_as_json(
    tmp_path,
) -> None:
    output_path = (
        tmp_path / "research_report.json"
    )

    save_research_report_json(
        report=create_report(),
        output_path=str(output_path),
    )

    data = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    assert data["net_completed_trades"] == 42
    assert (
        data["rolling_window_count"]
        == 5
    )
    assert data["verdict"] == "PROMISING"
    assert len(data["decision_reasons"]) == 5


def test_saves_report_as_csv(
    tmp_path,
) -> None:
    output_path = (
        tmp_path / "research_report.csv"
    )

    save_research_report_csv(
        report=create_report(),
        output_path=str(output_path),
    )

    with output_path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(
            csv.DictReader(file)
        )

    assert len(rows) == 1
    assert rows[0]["strategy_name"].startswith(
        "Drop=3"
    )
    assert (
        rows[0]["gross_backtest_return_percent"]
        == "7.049"
    )
    assert (
        rows[0]["net_monte_carlo_median_percent"]
        == "5.3266"
    )