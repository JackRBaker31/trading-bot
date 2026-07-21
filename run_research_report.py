from app.config import load_config
from app.news_research_report import (
    format_news_research_summary,
)
from app.run_history_repository import (
    RunHistoryRepository,
)
from app.run_history_service import (
    RunHistoryService,
)
from app.research_report_service import (
    ResearchReportRequest,
    ResearchReportResult,
    ResearchReportService,
)


def format_research_report_result(
    result: ResearchReportResult,
) -> str:
    report = result.report
    artifacts = result.artifacts

    lines = [
        "RESEARCH REPORT",
        f"Strategy: {report.strategy_name}",
        "",
        "DECISION",
        f"Verdict: {report.verdict}",
        (
            "Checks passed: "
            f"{report.passed_check_count}/"
            f"{report.total_check_count}"
        ),
    ]

    lines.extend(
        f"- {reason}"
        for reason in report.decision_reasons
    )

    lines.extend(
        [
            "",
            "BACKTEST",
            (
                "Gross return: "
                f"{report.gross_backtest_return_percent:.2f}%"
            ),
            (
                "Net return: "
                f"{report.net_backtest_return_percent:.2f}%"
            ),
            (
                "Completed trades: "
                f"{report.net_completed_trades}"
            ),
            "",
            "MONTE CARLO",
            (
                "Net median return: "
                f"{report.net_monte_carlo_median_percent:.2f}%"
            ),
            (
                "Net 5th percentile: "
                f"{report.net_fifth_percentile_percent:.2f}%"
            ),
            (
                "Net loss probability: "
                f"{report.net_loss_probability_percent:.2f}%"
            ),
            (
                "Net worst drawdown: "
                f"{report.net_worst_drawdown_percent:.2f}%"
            ),
            "",
            "WALK FORWARD",
            (
                "Training return: "
                f"{report.walk_forward_training_return_percent:.2f}%"
            ),
            (
                "Validation return: "
                f"{report.walk_forward_validation_return_percent:.2f}%"
            ),
            "",
            "ROLLING VALIDATION",
            (
                "Windows: "
                f"{report.rolling_window_count}"
            ),
            (
                "Positive windows: "
                f"{report.rolling_positive_window_percent:.2f}%"
            ),
            (
                "Average return: "
                f"{report.rolling_average_return_percent:.2f}%"
            ),
            (
                "Worst return: "
                f"{report.rolling_worst_return_percent:.2f}%"
            ),
            "",
            "AI NEWS VALIDATION",
            format_news_research_summary(
                summary=result.news_summary
            ),
            "",
            (
                "Saved JSON report to "
                f"{artifacts.json_path}"
            ),
            (
                "Saved CSV report to "
                f"{artifacts.csv_path}"
            ),
            (
                "Saved equity chart to "
                f"{artifacts.equity_curve_path}"
            ),
            (
                "Saved drawdown chart to "
                f"{artifacts.drawdown_path}"
            ),
            (
                "Saved Monte Carlo chart to "
                f"{artifacts.monte_carlo_path}"
            ),
            (
                "Saved rolling returns chart to "
                f"{artifacts.rolling_returns_path}"
            ),
        ]
    )

    return "\n".join(lines)


def main() -> None:
    config = load_config()

    run_history_service = RunHistoryService(
        repository=RunHistoryRepository(
            database_path="data/application.db"
        )
    )
    run_history_service.initialize()

    result = ResearchReportService(
        run_history_service=run_history_service
    ).run(
        request=ResearchReportRequest(
            starting_cash=config.starting_cash,
            max_order_value=(
                config.risk.max_order_value
            ),
            max_position_value=(
                config.risk.max_position_value
            ),
            max_portfolio_exposure=(
                config.risk.max_portfolio_exposure
            ),
            target_allocation_percent=(
                config.strategy
                .target_allocation_percent
            ),
        )
    )

    print(
        format_research_report_result(
            result
        )
    )


if __name__ == "__main__":
    main()