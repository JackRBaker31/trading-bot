import json
from datetime import datetime, timezone

import pytest

from app.application_errors import (
    ConfigurationError,
    DataStoreError,
)
from app.config import (
    AppConfig,
    MarketSessionConfig,
    PaperTradingConfig,
    RiskConfig,
    StrategyConfig,
    TradingLoopConfig,
)
from app.news_policy_runtime_factory import (
    NewsPolicyRuntime,
)
from app.news_policy_runtime_config import (
    NewsPolicyRuntimeConfig,
)
from app.orders import Order, OrderSide
from app.order_journal import OrderJournal
from app.portfolio import Portfolio
from app.portfolio_store import PortfolioStore
from app.system_status_service import (
    SystemStatusRequest,
    SystemStatusService,
)


def create_config() -> AppConfig:
    return AppConfig(
        mode="PAPER",
        market_data_provider="SIMULATED",
        starting_cash=5_000.0,
        symbols=["AAPL", "MSFT"],
        risk=RiskConfig(
            max_order_value=2_000.0,
            max_position_value=3_000.0,
            max_portfolio_exposure=0.5,
            max_trades_per_session=3,
        ),
        strategy=StrategyConfig(
            drop_threshold_percent=2.0,
            target_allocation_percent=10.0,
            cooldown_cycles=2,
        ),
        trading_loop=TradingLoopConfig(
            cycles=5,
            interval_seconds=60.0,
        ),
        market_session=MarketSessionConfig(
            enforce_market_hours=False,
            timezone="America/New_York",
            opening_time="09:30",
            closing_time="16:00",
            trading_weekdays=[0, 1, 2, 3, 4],
        ),
        paper_trading=PaperTradingConfig(
            enabled=True,
            broker_environment="DEMO",
            order_execution_permission_confirmed=False,
        ),
    )


def create_policy_runtime() -> NewsPolicyRuntime:
    return NewsPolicyRuntime(
        config=NewsPolicyRuntimeConfig(
            mode="shadow",
            observation_path=(
                "data/news-policy.jsonl"
            ),
        ),
        observation_log=None,
    )


def test_builds_status_from_local_state(
    tmp_path,
) -> None:
    portfolio_path = tmp_path / "portfolio.json"
    journal_path = tmp_path / "orders.jsonl"
    report_path = tmp_path / "report.json"
    signals_path = tmp_path / "signals.jsonl"
    outcomes_path = tmp_path / "outcomes.jsonl"

    portfolio = Portfolio(starting_cash=5_000.0)
    portfolio.buy(
        symbol="AAPL",
        quantity=2,
        price=100.0,
    )
    PortfolioStore(
        file_path=str(portfolio_path)
    ).save(portfolio)

    OrderJournal(path=journal_path).record(
        order=Order(
            symbol="MSFT",
            side=OrderSide.BUY,
            quantity=1,
            price=200.0,
        ),
        event="PENDING",
        broker_order_id=123,
    )

    report_path.write_text(
        json.dumps(
            {
                "generated_at": (
                    "2026-07-19T12:00:00+00:00"
                )
            }
        ),
        encoding="utf-8",
    )
    signals_path.write_text(
        "{}\n{}\n",
        encoding="utf-8",
    )
    outcomes_path.write_text(
        "{}\n",
        encoding="utf-8",
    )

    service = SystemStatusService(
        config_loader=lambda _: create_config(),
        news_policy_runtime_factory=(
            create_policy_runtime
        ),
        now_provider=lambda: datetime(
            2026,
            7,
            19,
            13,
            0,
            tzinfo=timezone.utc,
        ),
    )

    result = service.get_status(
        request=SystemStatusRequest(
            portfolio_path=str(portfolio_path),
            order_journal_path=str(journal_path),
            research_report_path=str(report_path),
            news_signals_path=str(signals_path),
            news_outcomes_path=str(outcomes_path),
        )
    )

    assert result.application_mode == "PAPER"
    assert result.real_money_trading_enabled is False
    assert result.news_policy_mode == "shadow"
    assert result.portfolio_cash == 4_800.0
    assert result.positions == {"AAPL": 2}
    assert result.unresolved_order_count == 1
    assert result.unresolved_order_symbols == ("MSFT",)
    assert result.news_signal_count == 2
    assert result.news_outcome_count == 1
    assert result.latest_research_report_at == (
        "2026-07-19T12:00:00+00:00"
    )


def test_missing_optional_files_are_empty(
    tmp_path,
) -> None:
    service = SystemStatusService(
        config_loader=lambda _: create_config(),
        news_policy_runtime_factory=(
            create_policy_runtime
        ),
    )

    result = service.get_status(
        request=SystemStatusRequest(
            portfolio_path=str(
                tmp_path / "portfolio.json"
            ),
            order_journal_path=str(
                tmp_path / "orders.jsonl"
            ),
            research_report_path=str(
                tmp_path / "report.json"
            ),
            news_signals_path=str(
                tmp_path / "signals.jsonl"
            ),
            news_outcomes_path=str(
                tmp_path / "outcomes.jsonl"
            ),
        )
    )

    assert result.portfolio_exists is False
    assert result.position_count == 0
    assert result.unresolved_order_count == 0
    assert result.research_report_exists is False
    assert result.news_signal_count == 0
    assert result.news_outcome_count == 0


def test_wraps_config_failure() -> None:
    service = SystemStatusService(
        config_loader=lambda _: (_ for _ in ()).throw(
            RuntimeError("broken config")
        ),
        news_policy_runtime_factory=(
            create_policy_runtime
        ),
    )

    with pytest.raises(
        ConfigurationError,
        match="could not be loaded",
    ) as captured:
        service.get_status(
            request=SystemStatusRequest()
        )

    assert captured.value.code == (
        "SYSTEM_STATUS_CONFIG_FAILED"
    )
    assert isinstance(
        captured.value.__cause__,
        RuntimeError,
    )


def test_invalid_report_is_data_store_error(
    tmp_path,
) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(
        "not-json",
        encoding="utf-8",
    )

    service = SystemStatusService(
        config_loader=lambda _: create_config(),
        news_policy_runtime_factory=(
            create_policy_runtime
        ),
    )

    with pytest.raises(
        DataStoreError,
        match="Research report status",
    ):
        service.get_status(
            request=SystemStatusRequest(
                portfolio_path=str(
                    tmp_path / "portfolio.json"
                ),
                order_journal_path=str(
                    tmp_path / "orders.jsonl"
                ),
                research_report_path=str(
                    report_path
                ),
                news_signals_path=str(
                    tmp_path / "signals.jsonl"
                ),
                news_outcomes_path=str(
                    tmp_path / "outcomes.jsonl"
                ),
            )
        )