import json
from pathlib import Path

from app.portfolio import Portfolio


class PortfolioStore:
    def __init__(
        self,
        file_path: str = "data/portfolio.json",
    ) -> None:
        self.file_path = Path(file_path)

    def save(self, portfolio: Portfolio) -> None:
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "starting_cash": portfolio.starting_cash,
            "cash": portfolio.cash,
            "positions": portfolio.positions,
        }

        temporary_path = self.file_path.with_suffix(".tmp")

        temporary_path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

        temporary_path.replace(self.file_path)

    def load(self) -> Portfolio:
        if not self.file_path.exists():
            raise FileNotFoundError(
                f"Portfolio file does not exist: {self.file_path}"
            )

        data = json.loads(
            self.file_path.read_text(
                encoding="utf-8",
            )
        )

        portfolio = Portfolio(
            starting_cash=float(data["starting_cash"])
        )

        portfolio.cash = float(data["cash"])

        portfolio.positions = {
            str(symbol): int(quantity)
            for symbol, quantity in data["positions"].items()
        }

        return portfolio

    def load_or_create(
        self,
        starting_cash: float,
    ) -> Portfolio:
        if self.file_path.exists():
            return self.load()

        portfolio = Portfolio(
            starting_cash=starting_cash
        )

        self.save(portfolio)

        return portfolio