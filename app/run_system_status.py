import argparse

from app.environment import load_environment
from app.system_status_service import (
    SystemStatusRequest,
    SystemStatusResult,
    SystemStatusService,
)


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Display local trading-platform system status."
        )
    )
    parser.add_argument(
        "--config",
        default="config.json",
    )
    parser.add_argument(
        "--portfolio",
        default="data/portfolio.json",
    )
    parser.add_argument(
        "--journal",
        default="order_journal.jsonl",
    )
    parser.add_argument(
        "--report",
        default="data/research_report.json",
    )
    parser.add_argument(
        "--signals",
        default="data/news_signals.jsonl",
    )
    parser.add_argument(
        "--outcomes",
        default="data/news_signal_outcomes.jsonl",
    )
    return parser.parse_args(argv)


def format_system_status(
    result: SystemStatusResult,
) -> str:
    positions = (
        "None"
        if not result.positions
        else ", ".join(
            f"{symbol}={quantity}"
            for symbol, quantity
            in sorted(result.positions.items())
        )
    )
    unresolved_symbols = (
        "None"
        if not result.unresolved_order_symbols
        else ", ".join(
            result.unresolved_order_symbols
        )
    )

    return "\n".join(
        [
            "SYSTEM STATUS",
            "",
            "APPLICATION",
            f"Mode: {result.application_mode}",
            (
                "Market-data provider: "
                f"{result.market_data_provider}"
            ),
            (
                "Configured symbols: "
                + ", ".join(
                    result.configured_symbols
                )
            ),
            (
                "Real-money trading: "
                + (
                    "ENABLED"
                    if result.real_money_trading_enabled
                    else "DISABLED"
                )
            ),
            "",
            "PAPER TRADING",
            (
                "Enabled: "
                f"{result.paper_trading_enabled}"
            ),
            (
                "Broker environment: "
                f"{result.broker_environment}"
            ),
            (
                "Execution permission confirmed: "
                f"{result.execution_permission_confirmed}"
            ),
            (
                "Market hours enforced: "
                f"{result.market_hours_enforced}"
            ),
            "",
            "NEWS POLICY",
            f"Mode: {result.news_policy_mode}",
            (
                "Shadow mode: "
                f"{result.news_policy_shadow_mode}"
            ),
            (
                "Enforce mode: "
                f"{result.news_policy_enforce_mode}"
            ),
            "",
            "PORTFOLIO",
            f"Exists: {result.portfolio_exists}",
            f"Cash: {result.portfolio_cash}",
            f"Positions: {positions}",
            "",
            "OPERATIONS",
            (
                "Unresolved orders: "
                f"{result.unresolved_order_count}"
            ),
            (
                "Unresolved symbols: "
                f"{unresolved_symbols}"
            ),
            (
                "Research report exists: "
                f"{result.research_report_exists}"
            ),
            (
                "Latest research report: "
                f"{result.latest_research_report_at}"
            ),
            f"News signals: {result.news_signal_count}",
            f"News outcomes: {result.news_outcome_count}",
        ]
    )


def main() -> None:
    load_environment()
    args = parse_args()

    result = SystemStatusService().get_status(
        request=SystemStatusRequest(
            config_path=args.config,
            portfolio_path=args.portfolio,
            order_journal_path=args.journal,
            research_report_path=args.report,
            news_signals_path=args.signals,
            news_outcomes_path=args.outcomes,
        )
    )

    print(format_system_status(result))


if __name__ == "__main__":
    main()