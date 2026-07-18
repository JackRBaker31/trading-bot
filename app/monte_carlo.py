from dataclasses import dataclass
import random


@dataclass(frozen=True)
class MonteCarloResult:
    simulation_number: int
    ending_return_percent: float
    maximum_drawdown_percent: float


class MonteCarloSimulator:
    def run(
        self,
        *,
        trade_returns_percent: list[float],
        simulation_count: int,
        random_seed: int | None = None,
    ) -> list[MonteCarloResult]:
        if not trade_returns_percent:
            raise ValueError(
                "At least one trade return is required."
            )

        if simulation_count <= 0:
            raise ValueError(
                "Simulation count must be positive."
            )

        random_generator = random.Random(
            random_seed
        )

        results: list[
            MonteCarloResult
        ] = []

        for simulation_number in range(
            1,
            simulation_count + 1,
        ):
            sampled_returns = [
                random_generator.choice(
                    trade_returns_percent
                )
                for _ in trade_returns_percent
            ]

            equity = 1.0
            peak_equity = 1.0
            maximum_drawdown_percent = 0.0

            for trade_return_percent in (
                sampled_returns
            ):
                equity *= (
                    1.0
                    + trade_return_percent
                    / 100.0
                )

                peak_equity = max(
                    peak_equity,
                    equity,
                )

                drawdown_percent = (
                    (
                        peak_equity
                        - equity
                    )
                    / peak_equity
                    * 100.0
                )

                maximum_drawdown_percent = max(
                    maximum_drawdown_percent,
                    drawdown_percent,
                )

            ending_return_percent = (
                equity - 1.0
            ) * 100.0

            results.append(
                MonteCarloResult(
                    simulation_number=(
                        simulation_number
                    ),
                    ending_return_percent=(
                        ending_return_percent
                    ),
                    maximum_drawdown_percent=(
                        maximum_drawdown_percent
                    ),
                )
            )

        return results

    def run_from_trade_profits(
        self,
        *,
        starting_equity: float,
        trade_profits: list[float],
        simulation_count: int,
        random_seed: int | None = None,
    ) -> list[MonteCarloResult]:
        if starting_equity <= 0:
            raise ValueError(
                "Starting equity must be positive."
            )

        if not trade_profits:
            raise ValueError(
                "At least one trade profit is required."
            )

        if simulation_count <= 0:
            raise ValueError(
                "Simulation count must be positive."
            )

        random_generator = random.Random(
            random_seed
        )

        results: list[
            MonteCarloResult
        ] = []

        for simulation_number in range(
            1,
            simulation_count + 1,
        ):
            sampled_profits = [
                random_generator.choice(
                    trade_profits
                )
                for _ in trade_profits
            ]

            equity = starting_equity
            peak_equity = starting_equity
            maximum_drawdown_percent = 0.0

            for trade_profit in sampled_profits:
                equity += trade_profit

                peak_equity = max(
                    peak_equity,
                    equity,
                )

                drawdown_percent = (
                    (
                        peak_equity
                        - equity
                    )
                    / peak_equity
                    * 100.0
                )

                maximum_drawdown_percent = max(
                    maximum_drawdown_percent,
                    drawdown_percent,
                )

            ending_return_percent = (
                (
                    equity
                    - starting_equity
                )
                / starting_equity
                * 100.0
            )

            results.append(
                MonteCarloResult(
                    simulation_number=(
                        simulation_number
                    ),
                    ending_return_percent=(
                        ending_return_percent
                    ),
                    maximum_drawdown_percent=(
                        maximum_drawdown_percent
                    ),
                )
            )

        return results