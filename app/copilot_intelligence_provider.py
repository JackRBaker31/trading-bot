from collections.abc import Callable
from typing import Any

SnapshotProvider = Callable[
    [],
    dict[str, Any],
]

GraduationProvider = Callable[
    [],
    dict[str, Any],
]


class CopilotIntelligenceProvider:
    def __init__(
        self,
        *,
        snapshot_provider: SnapshotProvider,
        graduation_provider: GraduationProvider,
    ) -> None:
        self._snapshot_provider = (
            snapshot_provider
        )
        self._graduation_provider = (
            graduation_provider
        )

    def intelligence_snapshot(
        self,
    ) -> dict[str, Any]:
        return dict(
            self._snapshot_provider()
        )

    def graduation_snapshot(
        self,
    ) -> dict[str, Any]:
        return dict(
            self._graduation_provider()
        )