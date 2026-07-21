from app.run_system_status import (
    format_system_status,
    parse_args,
)
from app.system_status_service import (
    SystemStatusResult,
)


def test_parses_status_paths() -> None:
    args = parse_args(
        [
            "--config",
            "custom.json",
            "--portfolio",
            "portfolio.json",
        ]
    )

    assert args.config == "custom.json"
    assert args.portfolio == "portfolio.json"


def test_formats_system_status() -> None:
    result = SystemStatusResult(
        generated_at=(
            "2026-07-19T13:00:00+00:00"
        ),
        application_mode="PAPER",
        market_data_provider="SIMULATED",
        configured_symbols=("AAPL",),
        real_money_trading_enabled=False,
        paper_trading_enabled=True,
        broker_environment="DEMO",
        execution_permission_confirmed=False,
        market_hours_enforced=False,
        news_policy_mode="shadow",
        news_policy_shadow_mode=True,
        news_policy_enforce_mode=False,
        portfolio_exists=True,
        portfolio_starting_cash=5_000.0,
        portfolio_cash=4_800.0,
        position_count=1,
        positions={"AAPL": 2},
        unresolved_order_count=0,
        unresolved_order_symbols=(),
        research_report_exists=True,
        latest_research_report_at=(
            "2026-07-19T12:00:00+00:00"
        ),
        news_signal_count=12,
        news_outcome_count=3,
    )

    output = format_system_status(result)

    assert "Mode: PAPER" in output
    assert "Real-money trading: DISABLED" in output
    assert "AAPL=2" in output
    assert "News signals: 12" in output