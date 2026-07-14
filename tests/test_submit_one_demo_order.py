import pytest
from app.config import (
    AppConfig,
    MarketSessionConfig,
    PaperTradingConfig,
    RiskConfig,
    StrategyConfig,
    TradingLoopConfig,
)
from submit_one_demo_order import (
    build_demo_order,
    execute_demo_order,
    parse_args,
    validate_config,
)
from app.paper_order_workflow import (
    PaperOrderWorkflowResult,
)
def test_requires_confirmation_flag() -> None:
    with pytest.raises(SystemExit):
        parse_args([])


def test_accepts_confirmation_flag() -> None:
    args = parse_args(
        ["--confirm-demo-order"]
    )

    assert args.confirm_demo_order is True

def create_config(
    *,
    mode: str = "PAPER",
    enabled: bool = True,
    environment: str = "DEMO",
    permission_confirmed: bool = True,
) -> AppConfig:
    return AppConfig(
        mode=mode,
        market_data_provider="TWELVE_DATA",
        starting_cash=5_000.00,
        symbols=["AAPL"],
        risk=RiskConfig(
            max_order_value=100.00,
            max_position_value=500.00,
            max_portfolio_exposure=1_000.00,
            max_trades_per_session=1,
        ),
        strategy=StrategyConfig(
            drop_threshold_percent=5.0,
            target_allocation_percent=1.0,
            cooldown_cycles=1,
        ),
        trading_loop=TradingLoopConfig(
            cycles=1,
            interval_seconds=0,
        ),
        market_session=MarketSessionConfig(
            enforce_market_hours=True,
            timezone="Europe/London",
            opening_time="14:30",
            closing_time="21:00",
            trading_weekdays=[0, 1, 2, 3, 4],
        ),
        paper_trading=PaperTradingConfig(
            enabled=enabled,
            broker_environment=environment,
            order_execution_permission_confirmed=(
                permission_confirmed
            ),
        ),
    )


def test_valid_demo_configuration_is_accepted() -> None:
    validate_config(
        create_config()
    )


@pytest.mark.parametrize(
    ("config", "message"),
    [
        (
            create_config(mode="SIMULATION"),
            "PAPER mode",
        ),
        (
            create_config(enabled=False),
            "disabled",
        ),
        (
            create_config(environment="LIVE"),
            "DEMO",
        ),
        (
            create_config(
                permission_confirmed=False
            ),
            "permission",
        ),
    ],
)
def test_unsafe_configuration_is_rejected(
    config: AppConfig,
    message: str,
) -> None:
    with pytest.raises(
        RuntimeError,
        match=message,
    ):
        validate_config(config)

def test_build_demo_order_creates_one_share_buy() -> None:
    order = build_demo_order(
        symbol="aapl",
        price=317.31,
    )

    assert order.symbol == "AAPL"
    assert order.side.value == "BUY"
    assert order.quantity == 1
    assert order.price == 317.31
    assert order.value == 317.31

class FakeExecutionAdapter:
    def __init__(
        self,
        result: PaperOrderWorkflowResult,
    ) -> None:
        self.result = result
        self.calls: list[
            dict[str, object]
        ] = []

    def submit_order_with_result(
        self,
        order,
        current_prices,
    ) -> PaperOrderWorkflowResult:
        self.calls.append(
            {
                "order": order,
                "current_prices": current_prices,
            }
        )

        return self.result


def test_execute_demo_order_submits_exactly_once() -> None:
    expected_result = PaperOrderWorkflowResult(
        submitted=True,
        portfolio_updated=True,
        reason="Filled.",
    )

    adapter = FakeExecutionAdapter(
        result=expected_result
    )

    order = build_demo_order(
        symbol="AAPL",
        price=317.31,
    )

    result = execute_demo_order(
        adapter=adapter,
        order=order,
    )

    assert result == expected_result
    assert len(adapter.calls) == 1
    assert adapter.calls[0]["order"] == order
    assert adapter.calls[0]["current_prices"] == {
        "AAPL": 317.31,
    }

def test_rejects_simulated_market_data() -> None:
    config = create_config()

    config = AppConfig(
        mode=config.mode,
        market_data_provider="SIMULATED",
        starting_cash=config.starting_cash,
        symbols=config.symbols,
        risk=config.risk,
        strategy=config.strategy,
        trading_loop=config.trading_loop,
        market_session=config.market_session,
        paper_trading=config.paper_trading,
    )

    with pytest.raises(
        RuntimeError,
        match="TWELVE_DATA",
    ):
        validate_config(config)