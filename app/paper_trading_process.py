import os
from dataclasses import dataclass
from enum import Enum


class PaperTradingProcessState(
    str,
    Enum,
):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOP_REQUESTED = "STOP_REQUESTED"


@dataclass(frozen=True)
class PaperTradingProcessStatus:
    state: PaperTradingProcessState
    process_id: int | None
    lock_present: bool
    stop_requested: bool
    stale_state_cleaned: bool = False

    @property
    def active(self) -> bool:
        return self.state in {
            PaperTradingProcessState.STARTING,
            PaperTradingProcessState.RUNNING,
            PaperTradingProcessState.STOP_REQUESTED,
        }

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "state": self.state.value,
            "active": self.active,
            "process_id": self.process_id,
            "lock_present": self.lock_present,
            "stop_requested": self.stop_requested,
            "stale_state_cleaned": (
                self.stale_state_cleaned
            ),
        }
