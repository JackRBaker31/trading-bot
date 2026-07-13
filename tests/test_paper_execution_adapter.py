from dataclasses import dataclass

from app.orders import Order, OrderSide
from app.paper_execution_adapter import (
    PaperExecutionAdapter,
)
from app.paper_order_workflow import (
    PaperOrderWorkflowResult,
)
from app.paper_trading_gate import (
    GateDecision,
    PaperTradingGate,
)
from app.portfolio import Portfolio
from app.risk import RiskDecision
from app.trade_log import TradeLog


class FakeWorkflow:
    def __init__(
        self,
        result: PaperOrderWorkflowResult,
    ) -> None:
        self.result = result
        self.execute_calls: list[
            dict[str, object]
        ] = []

    def execute(
        self,
        order: Order,
        gate_decision: GateDecision,
    ) -> PaperOrderWorkflowResult:
        self.execute_calls.append(
            {
                "order": order,
                "gate_decision": gate_decision,
            }
        )

        return self.result


class FakeRiskEngine:
    def __init__(
        self,
        approved: bool,
        reason: str = "Risk checks passed.",
    ) -> None:
        self.approved = approved
        self.reason = reason
        self.evaluate_calls: list[
            dict[str, object]
        ] = []
        self.record_calls = 0

    def evaluate(
        self,
        order: Order,
        portfolio: Portfolio,
        current_prices: dict[str, float],
    ) -> RiskDecision:
        self.evaluate_calls.append(
            {
                "order": order,
                "portfolio": portfolio,
                "current_prices": current_prices,
            }
        )

        return RiskDecision(
            approved=self.approved,
            reason=self.reason,
        )

    def record_executed_trade(self) -> None:
        self.record_calls += 1


@dataclass(frozen=True)
class FakeMarketStatus:
    is_open: bool


class FakeMarketSession:
    def __init__(
        self,
        is_open: bool,
    ) -> None:
        self.is_open = is_open
        self.status_calls = 0

    def get_status(self) -> FakeMarketStatus:
        self.status_calls += 1

        return FakeMarketStatus(
            is_open=self.is_open
        )


def create_order() -> Order:
    return Order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        price=150.00,
    )


def create_adapter(
    *,
    workflow_result: PaperOrderWorkflowResult,
    risk_approved: bool = True,
    permission_confirmed: bool = True,
    market_session: FakeMarketSession | None = None,
    enforce_market_hours: bool = False,
) -> tuple[
    PaperExecutionAdapter,
    FakeWorkflow,
    FakeRiskEngine,
    TradeLog,
]:
    portfolio = Portfolio(
        starting_cash=5_000.00
    )

    workflow = FakeWorkflow(
        result=workflow_result
    )

    risk_engine = FakeRiskEngine(
        approved=risk_approved
    )

    trade_log = TradeLog()

    adapter = PaperExecutionAdapter(
        workflow=workflow,
        gate=PaperTradingGate(),
        portfolio=portfolio,
        risk_engine=risk_engine,
        trade_log=trade_log,
        paper_trading_enabled=True,
        broker_environment="DEMO",
        order_execution_permission_confirmed=(
            permission_confirmed
        ),
        market_session=market_session,
        enforce_market_hours=(
            enforce_market_hours
        ),
    )

    return (
        adapter,
        workflow,
        risk_engine,
        trade_log,
    )


def test_approved_filled_order_returns_true() -> None:
    (
        adapter,
        workflow,
        risk_engine,
        trade_log,
    ) = create_adapter(
        workflow_result=PaperOrderWorkflowResult(
            submitted=True,
            portfolio_updated=True,
            reason=(
                "Broker order was fully filled and "
                "the local portfolio was updated."
            ),
        )
    )

    order = create_order()

    executed = adapter.submit_order(
        order=order,
        current_prices={
            "AAPL": 150.00,
        },
    )

    assert executed is True
    assert risk_engine.record_calls == 1
    assert len(workflow.execute_calls) == 1

    gate_decision = (
        workflow.execute_calls[0][
            "gate_decision"
        ]
    )

    assert gate_decision.approved is True
    assert len(trade_log.entries) == 1
    assert trade_log.entries[0].executed is True


def test_risk_rejection_blocks_submission() -> None:
    (
        adapter,
        workflow,
        risk_engine,
        trade_log,
    ) = create_adapter(
        workflow_result=PaperOrderWorkflowResult(
            submitted=False,
            portfolio_updated=False,
            reason=(
                "Order blocked by paper-trading gate."
            ),
        ),
        risk_approved=False,
    )

    order = create_order()

    executed = adapter.submit_order(
        order=order,
        current_prices={
            "AAPL": 150.00,
        },
    )

    assert executed is False
    assert risk_engine.record_calls == 0

    gate_decision = (
        workflow.execute_calls[0][
            "gate_decision"
        ]
    )

    assert gate_decision.approved is False
    assert gate_decision.reason == (
        "Order failed risk checks."
    )
    assert trade_log.entries[0].executed is False


def test_missing_permission_blocks_submission() -> None:
    (
        adapter,
        workflow,
        risk_engine,
        _,
    ) = create_adapter(
        workflow_result=PaperOrderWorkflowResult(
            submitted=False,
            portfolio_updated=False,
            reason=(
                "Order blocked by paper-trading gate."
            ),
        ),
        permission_confirmed=False,
    )

    adapter.submit_order(
        order=create_order(),
        current_prices={
            "AAPL": 150.00,
        },
    )

    gate_decision = (
        workflow.execute_calls[0][
            "gate_decision"
        ]
    )

    assert gate_decision.approved is False
    assert "permission" in (
        gate_decision.reason.lower()
    )
    assert risk_engine.record_calls == 0

def test_closed_market_blocks_submission() -> None:
    market_session = FakeMarketSession(
        is_open=False
    )

    (
        adapter,
        workflow,
        _,
        _,
    ) = create_adapter(
        workflow_result=PaperOrderWorkflowResult(
            submitted=False,
            portfolio_updated=False,
            reason=(
                "Order blocked by paper-trading gate."
            ),
        ),
        market_session=market_session,
        enforce_market_hours=True,
    )

    adapter.submit_order(
        order=create_order(),
        current_prices={
            "AAPL": 150.00,
        },
    )

    gate_decision = (
        workflow.execute_calls[0][
            "gate_decision"
        ]
    )

    assert market_session.status_calls == 1
    assert gate_decision.approved is False
    assert gate_decision.reason == (
        "Market is closed."
    )