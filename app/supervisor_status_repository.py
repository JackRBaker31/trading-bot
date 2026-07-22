from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class SupervisorStatusSnapshot:
    generated_at: datetime
    supervisor_status: str
    supervisor_process_id: int | None
    restart_enabled: bool
    processes: tuple[dict[str, object], ...]


class SupervisorStatusRepository:
    def __init__(
        self,
        *,
        status_path: str | Path = "data/supervisor_status.json",
        process_alive: Callable[[int], bool] | None = None,
    ) -> None:
        self._status_path = Path(status_path)
        self._process_alive = process_alive or self._default_process_alive

    @property
    def status_path(self) -> Path:
        return self._status_path

    def load(self) -> SupervisorStatusSnapshot | None:
        if not self._status_path.exists():
            return None

        try:
            payload = json.loads(
                self._status_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError, UnicodeError) as error:
            raise ValueError(
                f"Supervisor status could not be read: {error}"
            ) from error

        if not isinstance(payload, dict):
            raise ValueError("Supervisor status must contain a JSON object.")

        generated_at = self._parse_datetime(payload.get("generated_at"))
        supervisor_status = str(
            payload.get("supervisor_status") or "UNKNOWN"
        ).upper()
        process_id = self._optional_positive_int(
            payload.get("supervisor_process_id")
        )
        restart_enabled = bool(payload.get("restart_enabled", False))
        raw_processes = payload.get("processes", [])
        if not isinstance(raw_processes, list):
            raise ValueError("Supervisor processes must be a JSON list.")

        processes: list[dict[str, object]] = []
        for item in raw_processes:
            if isinstance(item, dict):
                processes.append(dict(item))

        return SupervisorStatusSnapshot(
            generated_at=generated_at,
            supervisor_status=supervisor_status,
            supervisor_process_id=process_id,
            restart_enabled=restart_enabled,
            processes=tuple(processes),
        )

    def process_is_alive(self, process_id: int | None) -> bool:
        return (
            process_id is not None
            and self._process_alive(process_id)
        )

    @staticmethod
    def _parse_datetime(value: object) -> datetime:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Supervisor status generated_at is required.")
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as error:
            raise ValueError(
                "Supervisor status generated_at must be ISO-8601."
            ) from error
        if parsed.tzinfo is None:
            raise ValueError(
                "Supervisor status generated_at must be timezone-aware."
            )
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _optional_positive_int(value: object) -> int | None:
        if value is None:
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    @staticmethod
    def _default_process_alive(process_id: int) -> bool:
        import os

        try:
            os.kill(process_id, 0)
        except OSError:
            return False
        return True