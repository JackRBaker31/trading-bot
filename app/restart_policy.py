from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RestartPolicyConfig:
    max_restarts: int = 5
    restart_window_seconds: float = 300.0
    recovery_grace_seconds: float = 15.0
    maximum_backoff_seconds: float = 30.0

    def __post_init__(self) -> None:
        if self.max_restarts < 0:
            raise ValueError("Maximum restarts cannot be negative.")
        if self.restart_window_seconds <= 0:
            raise ValueError("Restart window must be positive.")
        if self.recovery_grace_seconds < 0:
            raise ValueError("Recovery grace cannot be negative.")
        if self.maximum_backoff_seconds <= 0:
            raise ValueError("Maximum backoff must be positive.")


@dataclass(frozen=True)
class RestartDecision:
    allowed: bool
    delay_seconds: float
    restart_number: int
    state: str
    detail: str


class RestartPolicy:
    """Make bounded restart decisions without interacting with processes."""

    def __init__(self, config: RestartPolicyConfig | None = None) -> None:
        self.config = config or RestartPolicyConfig()

    def decide(
        self,
        *,
        restart_times: deque[float],
        now: float,
        reason: str,
    ) -> RestartDecision:
        self.prune(restart_times=restart_times, now=now)
        if len(restart_times) >= self.config.max_restarts:
            return RestartDecision(
                allowed=False,
                delay_seconds=0.0,
                restart_number=len(restart_times),
                state="FAILED",
                detail=(
                    "Restart limit reached within the configured window; "
                    f"manual review is required. Last reason: {reason}"
                ),
            )

        restart_number = len(restart_times) + 1
        delay = min(
            self.config.maximum_backoff_seconds,
            float(2 ** min(restart_number - 1, 5)),
        )
        return RestartDecision(
            allowed=True,
            delay_seconds=delay,
            restart_number=restart_number,
            state="RESTART_PENDING",
            detail=f"Restart {restart_number} approved: {reason}",
        )

    def record_restart(self, *, restart_times: deque[float], now: float) -> None:
        restart_times.append(now)

    def prune(self, *, restart_times: deque[float], now: float) -> None:
        while restart_times and (
            now - restart_times[0] > self.config.restart_window_seconds
        ):
            restart_times.popleft()

    def within_recovery_grace(
        self,
        *,
        started_monotonic: float | None,
        now: float,
    ) -> bool:
        if started_monotonic is None:
            return False
        return (
            now - started_monotonic
            < self.config.recovery_grace_seconds
        )