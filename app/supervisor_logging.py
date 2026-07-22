from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LogRotationConfig:
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5

    def __post_init__(self) -> None:
        if self.max_bytes <= 0:
            raise ValueError("Maximum log size must be positive.")
        if self.backup_count < 0:
            raise ValueError("Backup count cannot be negative.")


def rotate_file(path: str | Path, config: LogRotationConfig) -> bool:
    target = Path(path)
    if not target.exists() or target.stat().st_size < config.max_bytes:
        return False

    if config.backup_count == 0:
        target.unlink(missing_ok=True)
        return True

    oldest = target.with_name(f"{target.name}.{config.backup_count}")
    oldest.unlink(missing_ok=True)
    for index in range(config.backup_count - 1, 0, -1):
        source = target.with_name(f"{target.name}.{index}")
        if source.exists():
            source.replace(target.with_name(f"{target.name}.{index + 1}"))
    target.replace(target.with_name(f"{target.name}.1"))
    return True


class SupervisorEventLogger:
    def __init__(
        self,
        path: str | Path,
        *,
        rotation: LogRotationConfig | None = None,
    ) -> None:
        self.path = Path(path)
        self.rotation = rotation or LogRotationConfig()

    def log(self, event_type: str, **fields: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        rotate_file(self.path, self.rotation)
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "supervisor_process_id": os.getpid(),
            **fields,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, default=str) + "\n")


def tail_lines(path: str | Path, line_count: int = 20) -> list[str]:
    if line_count <= 0:
        return []
    target = Path(path)
    if not target.exists():
        return []
    with target.open("r", encoding="utf-8", errors="replace") as handle:
        return [line.rstrip("\r\n") for line in handle.readlines()[-line_count:]]