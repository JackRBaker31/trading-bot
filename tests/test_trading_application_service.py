from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from app.application_errors import TradingOperationError
from app.trading_application import (
    TradingApplicationRequest,
)
from app.trading_application_service import (
    TradingApplicationService,
)


class FakeTradingLoop:
    def __init__(self) -> None:
        self.position_states = {}
        self.received_stop = None

    def run(
        self,
        *,
        cycles,
        before_cycle,
        stop_requested=None,
    ) -> None:
        del cycles
        before_cycle(1)
        self.received_stop = stop_requested


class FakeStore:
    def __init__(self) -> None:
        self.saved = []

    def save(self, value) -> None:
        self.saved.append(value)


class FakeMarketData:
    def get_prices(self, symbols):
        return {
            symbol: 100.0
            for symbol in symbols
        }


class FakePortfolio:
    def __init__(self) -> None:
        self.cash = 900.0
        self.positions = {"AAPL": 1}
        self.display_count = 0

    def display(self, prices) -> None:
        del prices
        self.display_count += 1


class FakeTradeLog:
    def __init__(self) -> None:
        self.display_count = 0

    def display(self) -> None:
        self.display_count += 1


class FakeRuntimeFactory:
    def __init__(self, runtime) -> None:
        self.runtime = runtime
        self.config_path = None

    def build(self, *, config_path: str):
        self.config_path = config_path
        return self.runtime


class FakePaperStartupService:
    def __init__(self, *, approved: bool) -> None:
        self.approved = approved

    def start(self, *, start_trading):
        if self.approved:
            start_trading()
        return SimpleNamespace(
            trading_started=self.approved,
            reason=(
                "PAPER startup completed safely."
                if self.approved
                else "Reconciliation failed."
            ),
        )


class FakeFillImporter:
    def import_unapplied_fills(self):
        return SimpleNamespace(
            imported_order_ids=(),
            skipped_order_ids=(),
        )


class FakeSummaryBuilder:
    def build(self, *, startup_result):
        return SimpleNamespace(
            outcome=SimpleNamespace(value="APPROVED"),
            startup_approved=(
                startup_result.trading_started
            ),
        )


def create_runtime(*, mode="SIMULATION", approved=True):
    portfolio = FakePortfolio()
    loop = FakeTradingLoop()
    return SimpleNamespace(
        config=SimpleNamespace(
            mode=mode,
            market_data_provider="SIMULATED",
            symbols=["AAPL"],
            trading_loop=SimpleNamespace(
                cycles=1,
            ),
        ),
        market_data=FakeMarketData(),
        portfolio=portfolio,
        portfolio_store=FakeStore(),
        position_state_store=FakeStore(),
        risk_engine=SimpleNamespace(
            executed_trade_count=2
        ),
        trade_log=FakeTradeLog(),
        trading_loop=loop,
        prepare_cycle=lambda cycle: None,
        paper_startup_service=(
            FakePaperStartupService(
                approved=approved
            )
            if mode == "PAPER"
            else None
        ),
        historical_fill_importer=(
            FakeFillImporter()
            if mode == "PAPER"
            else None
        ),
        startup_summary_builder=(
            FakeSummaryBuilder()
            if mode == "PAPER"
            else None
        ),
    )


def test_runs_simulation_and_persists_state() -> None:
    runtime = create_runtime()
    factory = FakeRuntimeFactory(runtime)
    service = TradingApplicationService(
        runtime_factory=factory
    )

    result = service.run(
        request=TradingApplicationRequest(
            config_path="test-config.json"
        )
    )

    assert factory.config_path == "test-config.json"
    assert result.trading_started is True
    assert result.executed_trade_count == 2
    assert runtime.portfolio_store.saved == [
        runtime.portfolio
    ]
    assert runtime.position_state_store.saved == [
        {}
    ]


def test_passes_stop_callback_to_loop() -> None:
    runtime = create_runtime()
    service = TradingApplicationService(
        runtime_factory=FakeRuntimeFactory(
            runtime
        )
    )
    stop = lambda: True

    result = service.run(
        request=TradingApplicationRequest(),
        stop_requested=stop,
    )

    assert runtime.trading_loop.received_stop is stop
    assert result.stopped_by_request is True


def test_paper_startup_refusal_is_returned() -> None:
    runtime = create_runtime(
        mode="PAPER",
        approved=False,
    )
    service = TradingApplicationService(
        runtime_factory=FakeRuntimeFactory(
            runtime
        )
    )

    result = service.run(
        request=TradingApplicationRequest(
            require_paper_mode=True
        )
    )

    assert result.trading_started is False
    assert result.reason == "Reconciliation failed."
    assert runtime.portfolio_store.saved == []


def test_worker_requirement_rejects_simulation() -> None:
    service = TradingApplicationService(
        runtime_factory=FakeRuntimeFactory(
            create_runtime()
        )
    )

    with pytest.raises(
        TradingOperationError,
        match="requires PAPER mode",
    ):
        service.run(
            request=TradingApplicationRequest(
                require_paper_mode=True
            )
        )
