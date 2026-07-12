from app.paper_trading_gate import (
    GateDecision,
    PaperTradingGate,
)


def test_gate_decision_can_be_created() -> None:
    decision = GateDecision(
        approved=True,
        reason="OK",
    )

    assert decision.approved is True
    assert decision.reason == "OK"


def test_gate_blocks_when_paper_trading_is_disabled() -> None:
    gate = PaperTradingGate()

    decision = gate.evaluate(
        paper_trading_enabled=False,
        broker_environment="DEMO",
        reconciliation_passed=True,
        market_is_open=True,
        risk_approved=True,
        order_execution_permission_confirmed=True,
    )

    assert decision.approved is False
    assert decision.reason == "Paper trading is disabled."


def test_gate_blocks_non_demo_environment() -> None:
    gate = PaperTradingGate()

    decision = gate.evaluate(
        paper_trading_enabled=True,
        broker_environment="LIVE",
        reconciliation_passed=True,
        market_is_open=True,
        risk_approved=True,
        order_execution_permission_confirmed=True,
    )

    assert decision.approved is False
    assert "DEMO" in decision.reason


def test_gate_blocks_failed_reconciliation() -> None:
    gate = PaperTradingGate()

    decision = gate.evaluate(
        paper_trading_enabled=True,
        broker_environment="DEMO",
        reconciliation_passed=False,
        market_is_open=True,
        risk_approved=True,
        order_execution_permission_confirmed=True,
    )

    assert decision.approved is False
    assert decision.reason == (
        "Broker reconciliation failed."
    )


def test_gate_blocks_when_market_is_closed() -> None:
    gate = PaperTradingGate()

    decision = gate.evaluate(
        paper_trading_enabled=True,
        broker_environment="DEMO",
        reconciliation_passed=True,
        market_is_open=False,
        risk_approved=True,
        order_execution_permission_confirmed=True,
    )

    assert decision.approved is False
    assert decision.reason == "Market is closed."


def test_gate_blocks_when_risk_checks_fail() -> None:
    gate = PaperTradingGate()

    decision = gate.evaluate(
        paper_trading_enabled=True,
        broker_environment="DEMO",
        reconciliation_passed=True,
        market_is_open=True,
        risk_approved=False,
        order_execution_permission_confirmed=True,
    )

    assert decision.approved is False
    assert decision.reason == (
        "Order failed risk checks."
    )


def test_gate_cleans_environment_value() -> None:
    gate = PaperTradingGate()

    decision = gate.evaluate(
        paper_trading_enabled=True,
        broker_environment=" demo ",
        reconciliation_passed=True,
        market_is_open=True,
        risk_approved=True,
        order_execution_permission_confirmed=True,
    )

    assert decision.approved is True


def test_gate_allows_safe_demo_state() -> None:
    gate = PaperTradingGate()

    decision = gate.evaluate(
        paper_trading_enabled=True,
        broker_environment="DEMO",
        reconciliation_passed=True,
        market_is_open=True,
        risk_approved=True,
        order_execution_permission_confirmed=True,
    )

    assert decision.approved is True
    assert decision.reason == (
        "Paper trading safety checks passed."
    )

def test_gate_blocks_unconfirmed_execution_permission() -> None:
    gate = PaperTradingGate()

    decision = gate.evaluate(
        paper_trading_enabled=True,
        broker_environment="DEMO",
        reconciliation_passed=True,
        market_is_open=True,
        risk_approved=True,
        order_execution_permission_confirmed=False,
    )

    assert decision.approved is False
    assert decision.reason == (
        "Order-execution permission has "
        "not been confirmed."
    )