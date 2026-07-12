from dataclasses import dataclass


@dataclass(frozen=True)
class GateDecision:
    approved: bool
    reason: str


class PaperTradingGate:
    def evaluate(
        self,
        paper_trading_enabled: bool,
        broker_environment: str,
        reconciliation_passed: bool,
        market_is_open: bool,
        risk_approved: bool,
    ) -> GateDecision:
        if not paper_trading_enabled:
            return GateDecision(
                approved=False,
                reason="Paper trading is disabled.",
            )

        cleaned_environment = (
            broker_environment.upper().strip()
        )

        if cleaned_environment != "DEMO":
            return GateDecision(
                approved=False,
                reason=(
                    "Paper trading requires the "
                    "DEMO broker environment."
                ),
            )

        if not reconciliation_passed:
            return GateDecision(
                approved=False,
                reason="Broker reconciliation failed.",
            )

        if not market_is_open:
            return GateDecision(
                approved=False,
                reason="Market is closed.",
            )

        if not risk_approved:
            return GateDecision(
                approved=False,
                reason="Order failed risk checks.",
            )

        return GateDecision(
            approved=True,
            reason="Paper trading safety checks passed.",
        )