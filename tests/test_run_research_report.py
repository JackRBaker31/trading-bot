from types import SimpleNamespace

from app.news_research_summary import (
    NewsResearchSummary,
)
from run_research_report import (
    format_research_report_result,
)


def test_formats_research_report_result() -> None:
    report = SimpleNamespace(
        strategy_name="Example",
        verdict="PROMISING",
        passed_check_count=5,
        total_check_count=5,
        decision_reasons=("Reason.",),
        gross_backtest_return_percent=7.0,
        net_backtest_return_percent=5.0,
        net_completed_trades=42,
        net_monte_carlo_median_percent=5.0,
        net_fifth_percentile_percent=-2.0,
        net_loss_probability_percent=10.0,
        net_worst_drawdown_percent=8.0,
        walk_forward_training_return_percent=8.0,
        walk_forward_validation_return_percent=3.0,
        rolling_window_count=5,
        rolling_positive_window_percent=60.0,
        rolling_average_return_percent=1.7,
        rolling_worst_return_percent=-2.0,
    )

    result = SimpleNamespace(
        report=report,
        news_summary=NewsResearchSummary(
            signal_count=2,
            outcome_count=0,
            unmatched_outcome_count=0,
            sentiment_groups=(),
            materiality_groups=(),
            event_type_groups=(),
            confidence_groups=(),
        ),
        artifacts=SimpleNamespace(
            json_path="report.json",
            csv_path="report.csv",
            equity_curve_path="equity.png",
            drawdown_path="drawdown.png",
            monte_carlo_path="monte.png",
            rolling_returns_path="rolling.png",
        ),
    )

    text = format_research_report_result(
        result
    )

    assert "RESEARCH REPORT" in text
    assert "Verdict: PROMISING" in text
    assert "Signals: 2" in text
    assert "Saved JSON report to report.json" in text