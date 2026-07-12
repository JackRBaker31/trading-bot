from dataclasses import dataclass, field

from app.broker import BrokerAccountSummary, BrokerPosition
from app.portfolio import Portfolio


@dataclass(frozen=True)
class ReconciliationIssue:
    category: str
    message: str


@dataclass(frozen=True)
class ReconciliationReport:
    is_reconciled: bool
    local_cash: float
    broker_cash: float
    local_positions: dict[str, float]
    broker_positions: dict[str, float]
    issues: list[ReconciliationIssue] = field(
        default_factory=list
    )

    @property
    def safe_to_trade(self) -> bool:
        return self.is_reconciled

    def display(self) -> None:
        print("\n================================")
        print("BROKER RECONCILIATION")
        print("================================")
        print(f"Local cash: £{self.local_cash:.2f}")
        print(f"Broker cash: £{self.broker_cash:.2f}")
        print(f"Local positions: {self.local_positions}")
        print(f"Broker positions: {self.broker_positions}")
        print(
            "Reconciled: "
            f"{'YES' if self.is_reconciled else 'NO'}"
        )
        print(
            "Safe to trade: "
            f"{'YES' if self.safe_to_trade else 'NO'}"
        )

        if self.issues:
            print("\nIssues:")

            for issue in self.issues:
                print(
                    f"- [{issue.category}] "
                    f"{issue.message}"
                )

        print("================================")


class BrokerReconciler:
    def __init__(
        self,
        symbol_mapping: dict[str, str],
        cash_tolerance: float = 0.01,
        quantity_tolerance: float = 0.000001,
    ) -> None:
        if cash_tolerance < 0:
            raise ValueError(
                "Cash tolerance cannot be negative."
            )

        if quantity_tolerance < 0:
            raise ValueError(
                "Quantity tolerance cannot be negative."
            )

        self.symbol_mapping = {
            local_symbol.upper().strip(): (
                broker_ticker.upper().strip()
            )
            for local_symbol, broker_ticker
            in symbol_mapping.items()
        }

        self.cash_tolerance = cash_tolerance
        self.quantity_tolerance = (
            quantity_tolerance
        )

    def reconcile(
        self,
        portfolio: Portfolio,
        account_summary: BrokerAccountSummary,
        broker_positions: list[BrokerPosition],
    ) -> ReconciliationReport:
        issues: list[ReconciliationIssue] = []

        local_cash = float(portfolio.cash)

        broker_cash = float(
            account_summary.available_to_trade
        )

        if (
            abs(local_cash - broker_cash)
            > self.cash_tolerance
        ):
            issues.append(
                ReconciliationIssue(
                    category="CASH",
                    message=(
                        f"Local cash £{local_cash:.2f} "
                        f"does not match broker cash "
                        f"£{broker_cash:.2f}."
                    ),
                )
            )

        local_positions = {
            symbol.upper().strip(): float(quantity)
            for symbol, quantity
            in portfolio.positions.items()
        }

        broker_positions_by_ticker = {
            position.ticker.upper().strip(): (
                float(position.quantity)
            )
            for position in broker_positions
        }

        normalised_broker_positions: dict[
            str,
            float,
        ] = {}

        mapped_broker_tickers = set(
            self.symbol_mapping.values()
        )

        for local_symbol, broker_ticker in (
            self.symbol_mapping.items()
        ):
            broker_quantity = (
                broker_positions_by_ticker.get(
                    broker_ticker,
                    0.0,
                )
            )

            if (
                local_symbol in local_positions
                or broker_quantity != 0
            ):
                normalised_broker_positions[
                    local_symbol
                ] = broker_quantity

        for broker_ticker, quantity in (
            broker_positions_by_ticker.items()
        ):
            if broker_ticker not in mapped_broker_tickers:
                issues.append(
                    ReconciliationIssue(
                        category="UNMAPPED_POSITION",
                        message=(
                            f"Broker position "
                            f"{broker_ticker} with quantity "
                            f"{quantity} has no local "
                            f"symbol mapping."
                        ),
                    )
                )

        all_symbols = (
            set(local_positions)
            | set(normalised_broker_positions)
        )

        for symbol in sorted(all_symbols):
            local_quantity = local_positions.get(
                symbol,
                0.0,
            )

            broker_quantity = (
                normalised_broker_positions.get(
                    symbol,
                    0.0,
                )
            )

            if (
                abs(local_quantity - broker_quantity)
                > self.quantity_tolerance
            ):
                issues.append(
                    ReconciliationIssue(
                        category="POSITION",
                        message=(
                            f"{symbol} local quantity "
                            f"{local_quantity} does not "
                            f"match broker quantity "
                            f"{broker_quantity}."
                        ),
                    )
                )

        return ReconciliationReport(
            is_reconciled=not issues,
            local_cash=local_cash,
            broker_cash=broker_cash,
            local_positions=local_positions,
            broker_positions=(
                normalised_broker_positions
            ),
            issues=issues,
        )