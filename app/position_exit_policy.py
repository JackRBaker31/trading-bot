from dataclasses import dataclass

from app.position_state import (
    PositionState,
)


@dataclass(frozen=True)
class PositionExitDecision:
    should_exit: bool
    reason: str


class PositionExitPolicy:
    def __init__(
        self,
        *,
        stop_loss_percent: float,
        take_profit_percent: float,
        trailing_stop_percent: float,
        trailing_activation_percent: float,
    ) -> None:
        if stop_loss_percent <= 0:
            raise ValueError(
                "Stop-loss percentage must be positive."
            )

        if take_profit_percent <= 0:
            raise ValueError(
                "Take-profit percentage must be positive."
            )

        if trailing_stop_percent <= 0:
            raise ValueError(
                "Trailing-stop percentage must be positive."
            )

        if trailing_activation_percent <= 0:
            raise ValueError(
                "Trailing activation percentage "
                "must be positive."
            )
        self._trailing_activation_percent = (
            trailing_activation_percent
        )

        self._stop_loss_percent = (
            stop_loss_percent
        )
        self._take_profit_percent = (
            take_profit_percent
        )
        self._trailing_stop_percent = (
            trailing_stop_percent
        )

    def evaluate(
        self,
        *,
        position: PositionState,
        current_price: float,
    ) -> PositionExitDecision:
        if current_price <= 0:
            raise ValueError(
                "Current price must be positive."
            )

        return_percent = (
            position.return_percent(
                current_price=current_price
            )
        )

        drawdown_percent = (
            position
            .drawdown_from_high_percent(
                current_price=current_price
            )
        )

        if (
            return_percent
            <= -self._stop_loss_percent
        ):
            return PositionExitDecision(
                should_exit=True,
                reason="STOP_LOSS",
            )

        if (
            return_percent
            >= self._take_profit_percent
        ):
            return PositionExitDecision(
                should_exit=True,
                reason="TAKE_PROFIT",
            )

        highest_return_percent = (
            (
                position.highest_price
                - position.average_entry_price
            )
            / position.average_entry_price
            * 100.0
        )

        if (
            highest_return_percent
            >= self._trailing_activation_percent
            and drawdown_percent
            <= -self._trailing_stop_percent
        ):
            return PositionExitDecision(
                should_exit=True,
                reason="TRAILING_STOP",
            )

        return PositionExitDecision(
            should_exit=False,
            reason="HOLD",
        )